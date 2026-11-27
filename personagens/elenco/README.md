# Elenco do Infor

Seu João e Dona Maria têm coleções independentes no arquivo
[Elenco_Infor_Seu_Joao_e_Dona_Maria.blend](https://github.com/emanoelb5-lgtm/Infor/releases/download/agrofloresta-da-folha-ao-solo-elenco/Elenco_Infor_Seu_Joao_e_Dona_Maria.blend).
No Blender 4.3 ou posterior, use **Arquivo → Anexar → Collection** e escolha a
coleção do personagem. A malha ponderada, a armadura de 55 ossos e os materiais
acompanham a coleção.

A cena tem 192 quadros a 24 fps. Os marcadores indicam caminhada, passo lateral
e gesto. Para incorporar os movimentos em outra cena, abra o **Editor de ações**
do rig. Os pontos de apoio dos pés são definidos em coordenadas da cena, e a pose
dos joelhos, quadris e braços é calculada a partir desses contatos. Os dedos,
os olhos e a cabeça podem ser posados separadamente.

## Produção

- [modelos.py](modelos.py) define a anatomia, as roupas, os cabelos e a armadura.
- [movimento.py](movimento.py) contém as poses, os passos e os pontos de apoio.
- [exportar.py](exportar.py) gera o arquivo Blender e verifica a armadura, os
  pesos das malhas e o deslocamento da caminhada.
- O [episódio da agrofloresta](../../episodios/agrofloresta-solo/render_elenco.py)
  usa os mesmos modelos na abertura e no retorno à muda.

Para gerar uma nova cópia com Blender 4.3, Python e NumPy:

```sh
python personagens/elenco/obter-dados.py .cache/infor-mpfb
INFOR_MPFB_DATA="$PWD/.cache/infor-mpfb" blender -b --python-exit-code 1 \
  --python personagens/elenco/exportar.py -- Elenco_Infor_Seu_Joao_e_Dona_Maria.blend
```

A topologia, as bases dos pesos e os alvos anatômicos vêm dos
[recursos gráficos CC0 do MPFB](https://github.com/makehumancommunity/mpfb2/blob/d9648f3257a0b9712281d466245f30d656250154/LICENSE.ASSETS.md).
A revisão é fixa no script. Os figurinos, penteados, movimentos e materiais
foram criados para o Infor a partir das referências do projeto.
