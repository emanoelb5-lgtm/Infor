#!/usr/bin/env bash
set -euo pipefail

if command -v ffmpeg >/dev/null 2>&1; then
  exit 0
fi
fontes="$(mktemp --suffix=.sources)"
trap 'rm -f "$fontes"' EXIT
cat > "$fontes" <<'APT'
Types: deb
URIs: http://archive.ubuntu.com/ubuntu/
Suites: noble noble-updates
Components: main universe multiverse restricted
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
APT
opcoes=(-o "Dir::Etc::sourcelist=$fontes" -o Dir::Etc::sourceparts=-)
sudo apt-get "${opcoes[@]}" update
sudo apt-get "${opcoes[@]}" install -y ffmpeg
