"""Substitui os dois planos de corpo inteiro na edição aprovada."""

import argparse
import json
from pathlib import Path

from montagem_elenco import EPISODIO, QUADROS, editar, lotes, renderizar

FONTE = "8e5891f4f655e940efde802b6228356cad1322f6f4010e578340eee6dceacafd"
PLANOS = tuple((nome,quadros,30 if nome in ("copa","ciclo") else None) for nome,quadros,_ in QUADROS)
LOTES = 20


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="acao",required=True)
    sub.add_parser("lotes")
    render = sub.add_parser("renderizar")
    render.add_argument("lote",type=int)
    render.add_argument("blender",type=Path)
    render.add_argument("saida",type=Path)
    edicao = sub.add_parser("editar")
    edicao.add_argument("origem",type=Path)
    edicao.add_argument("pacotes",type=Path)
    edicao.add_argument("saida",type=Path)
    a = p.parse_args()
    if a.acao == "lotes":
        print(json.dumps(list(range(len(lotes(PLANOS, LOTES))))))
    elif a.acao == "renderizar":
        renderizar(a.blender,a.lote,a.saida,quadros=PLANOS,numero_lotes=LOTES,
                   script=EPISODIO/"render_retratos.py")
    else:
        editar(a.origem,a.pacotes,a.saida,quadros=PLANOS,numero_lotes=LOTES,fonte_sha=FONTE)


if __name__=="__main__":
    main()
