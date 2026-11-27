#!/usr/bin/env bash
set -euo pipefail

final="$1"
titulo="${2:-Agrofloresta da semente à sombra}"
notas="${3:-Curta do Infor com Dona Luzia e Rafael, um corte animado da germinação do feijão e o Diário de Campo do AgroHere.}"
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
if git fetch --no-tags origin "$COPIA"; then
  git switch -c "$COPIA" FETCH_HEAD
  git merge --no-edit --no-ff "$GITHUB_SHA"
else
  git switch -c "$COPIA"
fi
mkdir -p "$EPISODIO/dist"
cp "$final" "$EPISODIO/dist/$VIDEO"
git add -f "$EPISODIO/dist/$VIDEO"
if ! git diff --cached --quiet; then
  git commit -m 'Guardar o curta final sobre agrofloresta'
fi
git show "HEAD:$EPISODIO/dist/$VIDEO" | cmp -s - "$final"
git push origin "HEAD:$COPIA"
if gh release view "$TAG" --repo "$GITHUB_REPOSITORY" >/dev/null 2>&1; then
  gh release upload "$TAG" "$final" --repo "$GITHUB_REPOSITORY" --clobber
else
  gh release create "$TAG" "$final" --repo "$GITHUB_REPOSITORY" --target "$GITHUB_SHA" \
    --title "$titulo" --notes "$notas"
fi
local_sha="$(sha256sum "$final" | cut -d ' ' -f 1)"
remoto="$(gh api "repos/$GITHUB_REPOSITORY/releases/tags/$TAG" \
  --jq ".assets[] | select(.name == \"$VIDEO\") | .digest")"
test "$remoto" = "sha256:$local_sha"
gh release delete "$RASCUNHO" --repo "$GITHUB_REPOSITORY" --yes
