#!/bin/bash
# Veröffentlicht die Novi-Seite: kopiert den Stand aus Google Drive, entfernt die Entwurfs-Hinweise und pusht zu GitHub Pages.
set -euo pipefail
QUELLE="$HOME/Library/CloudStorage/GoogleDrive-stephan.bohr@googlemail.com/Meine Ablage/04 - Haus   Wohnen/35 - Mövenpick Accor/06 - Webseite Empfehlung"
cd "$(dirname "$0")"
rsync -a --delete --exclude '.DS_Store' "$QUELLE/bilder/" bilder/
python3 - "$QUELLE/index.html" <<'PY'
import re, sys
s = open(sys.argv[1], encoding='utf-8').read()
s = s.replace('<body class="entwurf">', '<body>')
s = re.sub(r'\s*<i class="pruefen">.*?</i>', '', s, flags=re.S)
s = re.sub(r'\s*<div class="entwurf-leiste">.*?</div>', '', s, flags=re.S)
s = re.sub(r'<!-- ENTWURF:.*?-->\s*', '', s, flags=re.S)
assert 'pruefen">' not in s and 'class="entwurf"' not in s
open('index.html', 'w', encoding='utf-8').write(s)
PY
git add -A
git diff --cached --quiet && { echo "Keine Änderungen."; exit 0; }
git commit -q -m "${1:-Seite aktualisiert}"
git push -q origin main
echo "Veröffentlicht: https://stephanbohr-stbc.github.io/novi-vinodolski/"
