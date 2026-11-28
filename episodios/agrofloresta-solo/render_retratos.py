"""Dirige os dois modelos da referência nos planos de corpo inteiro do filme."""

from functools import partial
from pathlib import Path
import sys

EPISODIO = Path(__file__).resolve().parent
RAIZ = EPISODIO.parents[1]
sys.path[:0] = [str(EPISODIO), str(RAIZ/"personagens/retratos")]
from render_elenco import elenco
from render import argumentos, renderizar
from cenas_solo import abertura, retorno
from modelar import criar_retrato
from movimento import Ator

atores = partial(elenco, fabricar=partial(Ator, construir=criar_retrato))
PLANOS = {"copa": partial(abertura, atores), "ciclo": partial(retorno, atores)}

if __name__ == "__main__":
    renderizar(argumentos(PLANOS), PLANOS)
