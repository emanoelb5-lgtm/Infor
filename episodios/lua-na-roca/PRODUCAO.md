# Produção do Reel

## Ferramentas pesquisadas no GitHub

| Etapa | Projeto | Aplicação neste Reel |
| --- | --- | --- |
| Animação e composição | [HyperFrames](https://github.com/heygen-com/hyperframes), Apache-2.0 | Guias `hyperframes` e `media-use` instalados no projeto de produção. Serviram de referência para ritmo vertical, movimentos determinados pela linha do tempo e desenho sonoro. |
| Roteiro, montagem e revisão | [video-editing](https://github.com/prathameshp107/video-editing) | Guias `story-editor`, `audio-finisher` e `render-review` instalados localmente. Ajudaram a ligar cada fala à sua imagem, revisar os planos e medir o arquivo final. |
| Narração | [edge-tts](https://github.com/rany2/edge-tts) | Geração em trechos com `pt-BR-ThalitaMultilingualNeural` e ritmo ajustado por trecho. Usa o serviço de leitura do Edge. |
| Render e mixagem | [FFmpeg](https://github.com/FFmpeg/FFmpeg), [Pillow](https://github.com/python-pillow/Pillow) e [NumPy](https://github.com/numpy/numpy) | Composição quadro a quadro, síntese da trilha, edição de áudio e exportação em MP4. |
| Alternativa de animação | [Remotion Agent Skills](https://github.com/remotion-dev/skills) | Opção para motion graphics em React, com [gratuidade conforme o perfil de uso](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md). |
| Alternativa de voz | [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx/blob/main/examples/portuguese.py) | Síntese em português brasileiro que roda localmente após baixar os modelos, com voz diferente da Thalita. |

Os guias foram obtidos de `heygen-com/hyperframes@f00e93479546eca4c7d841859174fe32d53b2564` e `prathameshp107/video-editing@b344da99bfaeb496c048703b82bf1a034d732f2a`. Os primeiros vêm de `skills/` e os segundos de `.agents/skills/` nos repositórios de origem. As pastas escolhidas foram copiadas para `.agents/skills/` no projeto de produção.

## Fontes do roteiro

- A sequência das fases e os aproximadamente 29,5 dias entre duas luas novas seguem a explicação da [NASA](https://science.nasa.gov/moon/moon-phases/). A animação representa a iluminação da esfera lunar. O relevo e a inclinação são ilustrativos.
- A cena de conversa entre gerações foi inspirada em relatos de transmissão oral de práticas ligadas às fases lunares, descritos na [Gaia Scientia](https://periodicos.ufpb.br/index.php/gaia/article/view/61513).
- A revisão de Mayoral e colaboradores fundamenta a fala sobre a falta de comprovação consistente para definir práticas agrícolas pela fase lunar. [Agronomy](https://doi.org/10.3390/agronomy10070955)
- A decisão de plantio considera a cultura e as condições locais. No Brasil, há janelas por cultura, município, solo e ciclo quando existe indicação no [Zoneamento Agrícola de Risco Climático](https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/zoneamento-agricola).

## Créditos das mídias

- Ilustrações originais geradas para o episódio, com ambientação inspirada no nordeste paraense. As pessoas e a propriedade são fictícias.
- A iluminação da Lua, os movimentos de câmera, os pictogramas e os efeitos de cena são compostos em `visuais.py`. A cena do celular é ilustrativa.
- Ícone do AgroHere a partir do acervo do aplicativo, usado no encerramento.
- Trilha e ambiência originais sintetizadas em `som.py`.
