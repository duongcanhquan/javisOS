# Cài OpenMontage (ngoài Javis)

```bash
git clone https://github.com/calesthio/OpenMontage.git
cd OpenMontage
# Theo README upstream: Python deps, ffmpeg, Node nếu pipeline cần
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # hoặc theo doc bản đang clone
export OPENMONTAGE_HOME="$PWD"
```

VPS: đặt `OPENMONTAGE_HOME` trong môi trường shell của user chạy agent (không nhét mã AGPL vào `/app` Javis).

Doctor tối thiểu: thư mục tồn tại, `python3`, `ffmpeg`, (tuỳ pipeline) `node`.
Đọc thêm: upstream `AGENT_GUIDE.md`, `docs/PROVIDERS.md`.
