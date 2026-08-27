# One-shot: install deploy key + migrate VPS to git-synced Javis.
# Password via env JAVIS_VPS_PASSWORD only (not stored in repo).
import os
import sys
import time

import paramiko

HOST = os.environ.get("JAVIS_VPS_HOST", "165.101.46.238")
USER = os.environ.get("JAVIS_VPS_USER", "root")
PASSWORD = os.environ.get("JAVIS_VPS_PASSWORD", "")
PUBKEY_PATH = os.path.expanduser(os.environ.get("JAVIS_VPS_PUBKEY", "~/.ssh/javis_vps_ed25519.pub"))
REPO = "https://github.com/duongcanhquan/javisOS.git"
REMOTE_DIR = os.environ.get("JAVIS_VPS_DIR", "/root/javis-os")


def run(ssh: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str, str]:
    print(f"$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    def _safe(s: str) -> str:
        return s.encode("ascii", errors="replace").decode("ascii")

    if out.strip():
        print(_safe(out[-4000:]))
    if err.strip():
        print(_safe(err[-2000:]), file=sys.stderr)
    return code, out, err


def main() -> int:
    if not PASSWORD:
        print("Set JAVIS_VPS_PASSWORD", file=sys.stderr)
        return 2
    with open(PUBKEY_PATH, encoding="utf-8") as f:
        pubkey = f.read().strip()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting {USER}@{HOST} ...")
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)

    # Install deploy pubkey
    run(
        ssh,
        "mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
        f"grep -qxF '{pubkey}' ~/.ssh/authorized_keys 2>/dev/null || echo '{pubkey}' >> ~/.ssh/authorized_keys && "
        "chmod 600 ~/.ssh/authorized_keys",
    )

    # Ensure docker works
    code, _, _ = run(ssh, "docker --version && docker compose version")
    if code != 0:
        print("Docker missing on VPS", file=sys.stderr)
        return 1

    # Stop old compose in ~/javis if present (keep volumes)
    run(ssh, "if [ -d ~/javis ]; then cd ~/javis && docker compose --profile tunnel down || true; fi")

    # Clone or update repo
    run(
        ssh,
        f"if [ -d {REMOTE_DIR}/.git ]; then cd {REMOTE_DIR} && git fetch origin && git reset --hard origin/main; "
        f"else git clone {REPO} {REMOTE_DIR}; fi",
    )

    # Preserve volumes from previous project name "javis"
    run(
        ssh,
        f"cd {REMOTE_DIR} && "
        "printf '%s\\n' 'COMPOSE_PROJECT_NAME=javis' > .env.compose && "
        "chmod +x scripts/vps-deploy.sh && "
        "export COMPOSE_PROJECT_NAME=javis && "
        "bash scripts/vps-deploy.sh",
        timeout=1200,
    )

    ssh.close()
    print("VPS setup complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
