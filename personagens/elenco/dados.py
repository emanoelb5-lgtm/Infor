"""Carrega os recursos CC0 do MPFB usados na base anatômica do elenco."""

from functools import lru_cache
import gzip
import json
import os
from pathlib import Path

import numpy as np

REVISAO_MPFB = "d9648f3257a0b9712281d466245f30d656250154"
ALVOS = "targets/macrodetails"


def recursos(sexo):
    neutros = ("asian", "caucasian", "african")
    return tuple(f"{ALVOS}/{base}-{sexo}-old.target.gz" for base in neutros) + (
        f"{ALVOS}/universal-{sexo}-old-averagemuscle-maxweight.target.gz",
    )


@lru_cache(maxsize=1)
def fonte():
    caminho = os.environ.get("INFOR_MPFB_DATA")
    if not caminho:
        raise ValueError("Indique a pasta de dados CC0 do MPFB em INFOR_MPFB_DATA.")
    return Path(caminho)


@lru_cache(maxsize=1)
def geometria():
    vertices, uvs, grupos = [], [], {}
    grupo = None
    with (fonte() / "3dobjs/base.obj").open(encoding="utf-8") as arquivo:
        for linha in arquivo:
            itens = linha.split()
            if not itens:
                continue
            tag, *valores = itens
            if tag == "v":
                vertices.append(tuple(map(float, valores)))
            elif tag == "vt":
                uvs.append(tuple(map(float, valores[:2])))
            elif tag == "g":
                grupo = valores[0]
            elif tag == "f":
                face = tuple(tuple(int(i) - 1 for i in v.split("/")[:2]) for v in valores)
                grupos.setdefault(grupo, []).append(face)
    return np.asarray(vertices), uvs, grupos


@lru_cache(maxsize=2)
def formas(sexo):
    base, _, _ = geometria()
    vertices = base.copy()
    pesos = (.52, .31, .17, .46 if sexo == "female" else .51)
    for nome, peso in zip(recursos(sexo), pesos, strict=True):
        with gzip.open(fonte() / nome, "rt", encoding="utf-8") as arquivo:
            for linha in arquivo:
                itens = linha.split()
                if itens and itens[0].isdigit():
                    vertices[int(itens[0])] += peso * np.asarray(itens[1:4], dtype=float)
    x, z, frente = vertices.T.copy()
    vertices[:, 0], vertices[:, 1], vertices[:, 2] = x, -frente, z
    vertices *= .1
    _, _, grupos = geometria()
    sola = min(vertices[i, 2] for f in grupos["body"] for i, _ in f)
    vertices[:, 2] -= sola
    return vertices


@lru_cache(maxsize=1)
def esqueleto():
    raiz = fonte() / "rigs/standard"
    ossos = json.loads((raiz / "rig.mixamo.json").read_text(encoding="utf-8"))["bones"]
    pesos = json.loads((raiz / "weights.mixamo.json").read_text(encoding="utf-8"))["weights"]
    prefixo = "mixamorig:"
    nomes = {nome: nome.removeprefix(prefixo) for nome in ossos}
    ossos = {nomes[nome]: {**valor, "parent": nomes.get(valor["parent"])} for nome, valor in ossos.items()}
    pesos = {nomes[nome]: pesos[nome] for nome in nomes}
    return ossos, pesos


def expressoes():
    prefixo = "targets/expression/units/asian"
    return (
        (f"{prefixo}/mouth-corner-puller.target.gz", 1.03),
        (f"{prefixo}/eye-left-opened-up.target.gz", .86),
        (f"{prefixo}/eye-right-opened-up.target.gz", .86),
        ("targets/chin/chin-height-decr.target.gz", .46),
        ("targets/cheek/l-cheek-volume-incr.target.gz", .34),
        ("targets/cheek/r-cheek-volume-incr.target.gz", .34),
    )


@lru_cache(maxsize=2)
def deformacao_facial(sexo):
    vertices = np.zeros_like(formas(sexo))
    for nome, peso in expressoes():
        with gzip.open(fonte() / nome, "rt", encoding="utf-8") as arquivo:
            for linha in arquivo:
                itens = linha.split()
                if itens and itens[0].isdigit():
                    x,z,y=map(float,itens[1:4])
                    vertices[int(itens[0])] += .1*peso*np.asarray((x,-y,z))
    return vertices
