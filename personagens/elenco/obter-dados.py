"""Obtém apenas os arquivos gráficos necessários, na revisão fixa do MPFB."""

import argparse
from pathlib import Path
from urllib.request import urlopen

from dados import REVISAO_MPFB, expressoes, recursos

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("destino", type=Path)
destino = p.parse_args().destino
base = f"https://raw.githubusercontent.com/makehumancommunity/mpfb2/{REVISAO_MPFB}/src/mpfb/data"
arquivos = (
    "3dobjs/base.obj",
    "rigs/standard/rig.mixamo.json",
    "rigs/standard/weights.mixamo.json",
    *recursos("female"), *recursos("male"), *(nome for nome, _ in expressoes()),
)
for nome in arquivos:
    caminho = destino / nome
    if caminho.is_file():
        continue
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".part")
    with urlopen(f"{base}/{nome}", timeout=60) as resposta:
        temporario.write_bytes(resposta.read())
    temporario.replace(caminho)
