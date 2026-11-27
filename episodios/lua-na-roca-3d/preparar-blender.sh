#!/usr/bin/env bash
set -euo pipefail

pasta_blender="$1"
versao=4.3.2
nome="blender-$versao-linux-x64"
arquivo="$nome.tar.xz"
origens=(
  'https://download.blender.org/release/Blender4.3'
  'https://mirror.nju.edu.cn/blender/release/Blender4.3'
  'https://mirror.freedif.org/blender/release/Blender4.3'
)
if [[ -x "$pasta_blender/$nome/blender" ]]; then
  "$pasta_blender/$nome/blender" --version
  exit 0
fi

mkdir -p "$pasta_blender"
trabalho="$(mktemp -d)"
trap 'rm -rf "$trabalho"' EXIT
for origem in "${origens[@]}"; do
  if ! curl -fsSL --retry 1 --retry-all-errors --max-time 30 \
      "$origem/blender-$versao.sha256" -o "$trabalho/somas"; then
    continue
  fi
  if ! curl -fsSL --retry 1 --retry-all-errors --max-time 155 \
      "$origem/$arquivo" -o "$trabalho/$arquivo"; then
    continue
  fi
  if (cd "$trabalho" && awk -v arq="$arquivo" '{nome=$2; sub(/^\*/, "", nome); if (nome == arq) print $1 "  " arq}' somas | sha256sum -c -); then
    tar -xf "$trabalho/$arquivo" -C "$pasta_blender"
    "$pasta_blender/$nome/blender" --version
    exit 0
  fi
done
printf 'Não foi possível obter a distribuição Blender %s.\n' "$versao" >&2
exit 1
