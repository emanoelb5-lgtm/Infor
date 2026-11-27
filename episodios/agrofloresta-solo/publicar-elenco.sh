#!/usr/bin/env bash
set -euo pipefail

video="$1"
elenco="$2"
titulo='Agrofloresta da folha ao solo · Edição com o elenco Infor'
notas='Curta vertical com novos modelos 3D do Seu João e da Dona Maria. Inclui o arquivo Blender com os dois esqueletos e uma ação de demonstração de caminhada, passo lateral e gesto.'

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
if git fetch --no-tags origin "$COPIA"; then
  git switch -c "$COPIA" FETCH_HEAD
  git merge --no-edit --no-ff "$GITHUB_SHA"
else
  git switch -c "$COPIA"
fi
for item in "$video" "$elenco"; do
  if [[ "$item" == "$video" ]]; then
    destino="$EPISODIO/dist/$(basename "$item")"
  else
    destino="$MODELOS/dist/$(basename "$item")"
  fi
  mkdir -p "$(dirname "$destino")"
  cp "$item" "$destino"
  git add -f "$destino"
done
if ! git diff --cached --quiet; then
  git commit -m 'Guardar o curta revisado e o elenco animável'
fi
git push origin "HEAD:$COPIA"
if gh release view "$TAG" --repo "$GITHUB_REPOSITORY" >/dev/null 2>&1; then
  gh release upload "$TAG" "$video" "$elenco" --repo "$GITHUB_REPOSITORY" --clobber
else
  gh release create "$TAG" "$video" "$elenco" --repo "$GITHUB_REPOSITORY" \
    --target "$GITHUB_SHA" --title "$titulo" --notes "$notas"
fi
for item in "$video" "$elenco"; do
  local_sha="$(sha256sum "$item" | cut -d ' ' -f 1)"
  nome="$(basename "$item")"
  remoto="$(gh api "repos/$GITHUB_REPOSITORY/releases/tags/$TAG" \
    --jq ".assets[] | select(.name == \"$nome\" and .state == \"uploaded\") | .digest")"
  test "$remoto" = "sha256:$local_sha"
done
gh release delete "$RASCUNHO" --repo "$GITHUB_REPOSITORY" --yes
