"""Recoloca as cenas de caminhada na última edição do filme."""
from montagem_retratos import EPISODIO, main

APROVADO="e086f7923eb3e4c34ecd0ed46bb0939f9651f72654e6a127ac06cafa9b1019d0"

if __name__ == "__main__":
    main(fonte=APROVADO,script=EPISODIO/"render_caminhada.py")
