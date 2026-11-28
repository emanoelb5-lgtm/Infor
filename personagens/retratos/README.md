# Seu João e Dona Maria a partir das imagens

[Baixar o arquivo Blender com os dois personagens](https://github.com/emanoelb5-lgtm/Infor/releases/download/agrofloresta-da-folha-ao-solo-retratos/Elenco_Infor_Seu_Joao_e_Dona_Maria_Referencias.blend).
As coleções têm malhas, materiais empacotados e rig de 55 ossos. Os gestos e as
passadas podem ser reutilizados pelo Editor de ações do Blender. Para anexar
outro personagem ao filme, use **Arquivo → Anexar → Collection**.

O volume vem de uma execução local no CPU do [TripoSR](https://github.com/VAST-AI-Research/TripoSR),
com licença MIT. A malha foi alinhada à silhueta de cada referência, e a
textura UV frontal conserva as cores e os detalhes do desenho. O volume, a
textura das laterais e as costas são estimativas da reconstrução.
As malhas em produção são 3D. O rosto mantém a expressão da referência e
acompanha o osso da cabeça.

- `preparar.py` recebe uma imagem de referência e a malha convertida. Escreve
  a malha calibrada e a textura usadas pelo Blender.
- `modelar.py` constrói o rig, cria os materiais e distribui os pesos.
- `exportar_retratos.py` empacota as duas coleções e verifica suas ações.
- `assets` guarda as malhas calibradas e as texturas finais do Infor.

A [edição da agrofloresta com os dois retratos](https://github.com/emanoelb5-lgtm/Infor/releases/tag/agrofloresta-da-folha-ao-solo-retratos)
usa as mesmas malhas na abertura e no retorno à muda.
