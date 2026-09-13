#!/usr/bin/env bash
# Bo tem quarantine Apple gan khi tai ZIP. Source sau khi cd ve goc repo.
# Double-click file .command VAN bi chan LAN DAU (Gatekeeper).
# Chay qua Terminal thi qua duoc, va lenh nay go tem de lan sau bam duoc:
#   cd ~/Javis && xattr -c *.command && chmod +x *.command && bash ./1-Cai-dat.command
[ "$(uname -s 2>/dev/null)" = "Darwin" ] || return 0
command -v xattr >/dev/null 2>&1 || return 0
for f in *.command "JAVIS OS.app"; do
  [ -e "$f" ] || continue
  xattr -c "$f" 2>/dev/null || xattr -cr "$f" 2>/dev/null || true
done
chmod +x ./*.command 2>/dev/null || true
return 0
