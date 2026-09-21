# Runbook cutover: não đang chạy → javis-quan, gốc → manager
#
# Cấm: docker volume rm, compose down -v, tạo project mới mà không external volume.
# Làm từng phase. Sai health thì rollback Caddy trong project, chưa làm phase sau.
#
# 0. DNS: deploy/org/DNS.md  (`dig +short javis-quan.vietmycollege.com` = 14.225.205.248)
# 1. Preflight (chỉ đọc):  bash scripts/org_cutover_preflight.sh
# 2. Backup:               bash scripts/org_backup_volumes.sh
# 3. Proxy, VẪN domain gốc: bash scripts/org_cutover_to_proxy.sh
#    Kiểm tra https://javis.vietmycollege.com (cùng não).
# 4. Đổi domain quan + dựng manager: chỉ khi bước 3 xanh VÀ DNS javis-quan đã có.
#    bash scripts/org_cutover_split_domains.sh
#
# Workflow GitHub: "Org split javis-quan" (confirm ORG_SPLIT_JAVIS, phase=...).
