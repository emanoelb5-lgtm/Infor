"""Exporta o elenco com a ação de caminhada e as texturas incorporadas."""

import argparse
from pathlib import Path
import sys

PASTA=Path(__file__).resolve().parent
sys.path[:0]=[str(PASTA),str(PASTA.parent/"elenco")]
from exportar import main
from caminhada import AtorEmMarcha, Caminhada


def coreografia(centro,rumo,s):
    fim=(centro,.02,0)
    trajeto=Caminhada((centro+s*.019,.83,0),fim,.041,.419,0,rumo,s)
    lateral=Caminhada(fim,(centro+s*.370,.02,0),.521,.792,rumo,rumo,s,lateral=True)
    return trajeto,lateral


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("saida",type=Path)
    a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
    main(a.saida,fabricar=AtorEmMarcha,coreografia=coreografia,denoise=False,
         fonte_arte="Os retratos têm as texturas incorporadas e a caminhada usa marcas de apoio.",
         fonte_codigo="personagens/retratos")
