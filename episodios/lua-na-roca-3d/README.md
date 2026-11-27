# A Lua e o tempo da roça

Curta vertical do Infor para o Reels. Dona Luzia e Rafael observam o céu e acompanham o cultivo do feijão, da semente à colheita. O calendário lunar entra como referência de tempo e tradição rural. A decisão de plantar também passa pela umidade da terra, pela previsão de chuva e pela época recomendada para a cultura.

[Baixar a edição 3D refinada](https://github.com/emanoelb5-lgtm/Infor/releases/download/lua-na-roca-3d-refinada/A_Lua_e_o_Tempo_da_Roca_Reel.mp4) · [Edição anterior](https://github.com/emanoelb5-lgtm/Infor/releases/download/lua-na-roca-3d/A_Lua_e_o_Tempo_da_Roca_Reel.mp4)

## Produção

A edição refinada remodela os rostos de Dona Luzia e Rafael, as roupas e as mãos. Os dedos compartilham a malha da palma e o braço dobra sem peças soltas no cotovelo. Os pontos de pegada ligam a mão ao lápis e à alça do cesto. A semeadura, a queda dos grãos na tigela e a pesagem usam posições de apoio e trajetórias próprias. Doze planos foram renderizados nesta revisão, e os dois diagramas astronômicos vêm da edição anterior.

- O Blender gera 14 planos, com geometria, luzes e materiais próprios. Os braços têm alvos de contato calculados por cinemática inversa. As mãos articulam os dedos. As sementes caem e se acomodam conforme o plano, e as folhas se abrem conforme o caule cresce.
- O Cycles usa shaders procedurais para o relevo, os veios, a cor e a rugosidade dos objetos. O desenho da Lua projeta o terminador sobre esferas. No diagrama da órbita, há uma esfera separada para representar a fase vista da Terra. A ilustração usa proporções livres.
- A renderização produz 540 × 960 pixels e 15 poses por segundo. A exportação em 1080 × 1920 e 30 quadros por segundo mantém a cadência de miniatura e inclui voz em português, trilha, sons de cena e legendas selecionáveis.
- O roteiro e os arquivos de locução da Thalita vêm de [lua-na-roca](../lua-na-roca). O encerramento mostra [capturas do próprio AgroHere](../lua-na-roca/assets/capturas/ORIGEM.md).

## Referências da pesquisa no GitHub

Os números representam instalações reportadas pelo diretório Skills.sh na consulta de novembro de 2026.

| Guia | Instalações aproximadas | Aplicação no curta |
| --- | ---: | --- |
| [Scenario Blender Animation](https://skills.sh/scenario-labs/skills/scenario-blender-animation) | 1,5 mil | Poses de antecipação, contato e recuperação durante o gesto |
| [Blender Character Rigging](https://skills.sh/el4cteo/blender-skills/blender-character-rigging) | 1,2 mil | Articulação do olhar, dos braços e de cada dedo |
| [Blender PBR Materials](https://skills.sh/el4cteo/blender-skills/blender-pbr-materials) | 1 mil | Rugosidade e relevo procedurais de terra, tecido, madeira e palha |
| [Scenario Blender Previs & Storyboard](https://skills.sh/scenario-labs/skills/scenario-blender-previs-storyboard) | 970 | Decupagem vertical e testes de enquadramento antes da renderização |
| [Blender Lighting & Lookdev](https://skills.sh/el4cteo/blender-skills/blender-lighting-lookdev) | 950 | Luz principal, recorte e preenchimento por ambiente |

As referências são de [scenario-labs/skills](https://github.com/scenario-labs/skills/tree/3c4d18cd0be2e5280a5accebfeef9ddc98b9a15b) e [el4cteo/blender-skills](https://github.com/el4cteo/blender-skills/tree/1a1cc6c49312f9f370aae86f52b7b907f29c94f6). A produção usa Blender e FFmpeg localmente e nos executores padrão gratuitos do repositório público.

## Renderizar

Com Blender 4.3, FFmpeg com libass, as fontes DejaVu e Python 3.10+ com NumPy, execute da raiz do repositório:

```bash
episode=episodios/lua-na-roca-3d
python "$episode/montagem.py" planos | python -c 'import json,sys; print("\n".join(json.load(sys.stdin)))' |
  while IFS= read -r plano; do
    python "$episode/montagem.py" render "$plano" || exit 1
  done
python "$episode/montagem.py" montar
```

Use `--denoise` no comando de renderização se o Blender foi compilado com Open Image Denoise. O fluxo do GitHub renderiza os planos em paralelo com a distribuição oficial do Blender e publica o vídeo depois de conferir a duração, as dimensões, a contagem de quadros e a decodificação dos arquivos.
