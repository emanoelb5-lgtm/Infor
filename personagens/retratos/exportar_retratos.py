"""Empacota o elenco da reconstrução de imagem num arquivo Blender independente."""
import argparse
from functools import partial
from pathlib import Path
import sys

PASTA=Path(__file__).resolve().parent
sys.path[:0]=[str(PASTA),str(PASTA.parent/"elenco")]
from exportar import main
from modelar import criar_retrato
from movimento import Ator

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("saida",type=Path)
    a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
    main(a.saida,fabricar=partial(Ator,construir=criar_retrato),denoise=False,
         fonte_arte="Volume TripoSR e textura frontal das referências do Infor.",
         fonte_codigo="personagens/retratos")
