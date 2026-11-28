"""Abertura e retorno à muda com passadas firmes dos mesmos personagens."""

from functools import partial
from pathlib import Path
import sys

EPISODIO = Path(__file__).resolve().parent
sys.path.insert(0, str(EPISODIO))
from render_retratos import argumentos, renderizar, abertura, retorno
from caminhada import AtorEmMarcha, Caminhada
from movimento import progressao


def elenco(nivel, retorno):
    maria, joao = AtorEmMarcha("female", 1.235), AtorEmMarcha("male", 1.220)
    if retorno:
        m = Caminhada((-.59,1.51,0),(-.66,.67,0),.050,.290,-.071,.192,1)
        j = Caminhada((.78,1.64,0),(.61,.70,0),.094,.349,-.181,-.237,-1)
    else:
        m = Caminhada((-.57,1.35,0),(-.66,.43,0),.064,.363,-.092,.211,1)
        j = Caminhada((.79,1.40,0),(.63,.49,0),.122,.432,-.172,-.258,-1)

    def posar(t,u):
        atenção = progressao(u,.35,.66)
        if retorno:
            chamar = progressao(u,.439,.660)*(1-progressao(u,.815,.981))
        else:
            chamar = progressao(u,.394,.576)*(1-progressao(u,.728,.929))
        responde = .38*progressao(u,.453,.665)*(1-.52*progressao(u,.827,1))
        maria.pose(t,u,m,nivel,.21,(.18-.06*atenção,.019+.24*atenção),
                   ("Left",(.346,-.348,1.06 if retorno else 1.115),chamar*.89),
                   .023+.084*atenção)
        joao.pose(t+.31,u,j,nivel,-.25,(-.162+.052*atenção,.025+.23*atenção),
                  ("Right",(-.344,-.29,1.11),responde),.019+.071*atenção)
    return posar


PLANOS = {"copa": partial(abertura, elenco), "ciclo": partial(retorno, elenco)}

if __name__ == "__main__":
    renderizar(argumentos(PLANOS), PLANOS)
