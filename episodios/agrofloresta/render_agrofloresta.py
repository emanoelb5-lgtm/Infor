"""Renderiza os planos da agrofloresta com a mesma câmera e o mesmo motor do Infor."""

from pathlib import Path
import sys

EPISODIO=Path(__file__).resolve().parent
sys.path[:0]=[str(EPISODIO),str(EPISODIO.parent/"lua-na-roca-3d")]
from cenas_agrofloresta import PLANOS
from render import argumentos, renderizar

if __name__=="__main__":
    renderizar(argumentos(PLANOS),PLANOS)
