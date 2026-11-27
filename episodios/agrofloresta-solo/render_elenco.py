"""Refaz somente os planos do filme que mostram o elenco."""

from functools import partial
from math import sin
from pathlib import Path
import sys

EPISODIO = Path(__file__).resolve().parent
RAIZ = EPISODIO.parents[1]
sys.path[:0] = [str(EPISODIO), str(RAIZ / "personagens/elenco"), str(EPISODIO.parent / "agrofloresta"),
                str(EPISODIO.parent / "lua-na-roca-3d")]

from cenas_solo import abertura, cobertura, plantio, retorno
from cenografia import material, pano
from modelos import NOMES, TONS
from movimento import Ator, Marcha, progressao
from personagens import Braco, Mao
from render import argumentos, renderizar


def elenco(nivel, retorno):
    maria = Ator("female", 1.235)
    joao = Ator("male", 1.220)
    if retorno:
        m = Marcha((-.53,1.19,0),(-.66,.67,0),.04,.39,3,1,.075)
        j = Marcha((.79,1.24,0),(.61,.70,0),.13,.52,3,-1,.076)
    else:
        m = Marcha((-.51,1.02,0),(-.66,.43,0),.025,.42,4,1,.077)
        j = Marcha((.94,.94,0),(.63,.49,0),.11,.55,4,-1,.088)

    def posar(t,u):
        chamar=progressao(u,.31,.58)*(1-progressao(u,.74,.94))
        atenção=progressao(u,.38,.69)
        if retorno:
            chamar=progressao(u,.43,.67)*(1-progressao(u,.81,.98))
        maria.pose(t,u,m,nivel,.227,(.31-.17*atenção,.075+.21*atenção),
                   ("Left",(.36,-.36,1.051 if retorno else 1.12),chamar*.96),
                   .038+.075*atenção)
        joao.pose(t+.3,u,j,nivel,-.268,(-.24+.10*atenção,.042+.23*atenção),
                  ("Right",(-.36,-.30,1.12),.40*atenção*(1-.52*progressao(u,.83,1))),
                  .025+.077*atenção)
    return posar


def mão_e_manga(sexo, escala):
    s1,s2,c1,c2,*_ = TONS[sexo]
    pele = material(f"Pele do detalhe de {NOMES[sexo]}",s1,s2,31,.0012,.54)
    p = pele.node_tree.nodes.get("Principled BSDF")
    p.inputs["Subsurface Weight"].default_value = .09
    p.inputs["Subsurface Scale"].default_value = .010
    mao = Mao("Mão de " + NOMES[sexo],pele,escala=escala)
    mao.obj.modifiers[0].levels = mao.obj.modifiers[0].render_levels = 3
    braço = Braco(pele,pano(c1,c2),pano(c2,c1),None)
    braço.obj.modifiers[0].levels = braço.obj.modifiers[0].render_levels = 2
    return mao,braço


PLANOS_ELENCO = {
    "copa": partial(abertura, elenco),
    "palhada": partial(cobertura, mão_e_manga),
    "plantio": partial(plantio, mão_e_manga),
    "ciclo": partial(retorno, elenco),
}

if __name__ == "__main__":
    renderizar(argumentos(PLANOS_ELENCO), PLANOS_ELENCO)
