# A Lua e o tempo da roça

O que a Lua ensinou a quem planta? O Reel parte de uma conversa no terreiro para mostrar como a tradição de observar o céu pode virar um hábito de planejamento. Um exemplo com feijão acompanha a semeadura, a chuva, a brotação e a pesagem na colheita.

[Baixar o Reel em MP4](https://github.com/emanoelb5-lgtm/Infor/releases/download/lua-na-roca-v1/A_Lua_e_o_Tempo_da_Roca_Reel.mp4)

| Material | Arquivo |
| --- | --- |
| Texto da narração, pausas e direção de voz | [roteiro.json](roteiro.json) |
| Ordem dos planos e movimentos de câmera | [planos.json](planos.json) |
| Texto para a publicação | [PUBLICACAO.md](PUBLICACAO.md) |
| Ferramentas, referências e créditos | [PRODUCAO.md](PRODUCAO.md) |

## Exportar localmente

Requer Python 3.12 e FFmpeg com `libx264`. As artes e os trechos narrados estão em `assets/`.

```sh
python -m pip install -r episodios/lua-na-roca/requirements.txt
python episodios/lua-na-roca/montar.py
```

O MP4 sai em `episodios/lua-na-roca/dist/`, acompanhado de um JSON com os tempos reais das cenas e da locução. Use `--previa` para um teste em 360 × 640 e `--saida caminho.mp4` para mudar o destino. A exportação final é 1080 × 1920, 30 fps, H.264, áudio AAC, em formato 9:16.

Para regravar após mudar o roteiro, instale `edge-tts==7.3.1` e execute `python episodios/lua-na-roca/narrar.py`. Essa etapa usa a voz Thalita do serviço de leitura do Microsoft Edge e precisa de conexão. Com os áudios gravados, a montagem e a exportação rodam localmente.
