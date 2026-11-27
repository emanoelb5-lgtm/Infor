"""Exporta a edição centrada na serapilheira e no solo da agrofloresta."""

import json
from pathlib import Path
import sys

import numpy as np

EPISODIO=Path(__file__).resolve().parent
sys.path.insert(0,str(EPISODIO.parent/"agrofloresta"))
from montagem_agrofloresta import (CABECALHO_ASS, FPS, argumentos, exportar, linha_do_tempo,
                                    lotes, mixar, renderizar, stamp)
from som import colocar, ruido, tempo

TITULO="Agrofloresta da folha ao solo"


def planos_e_locucao(caminho):
    planos,falas,voz,total=linha_do_tempo(caminho,arquivo_roteiro=EPISODIO/"roteiro.json",planos_fluidos=("muda",))
    for p in planos:
        p["peso_render"]={"copa":1.32,"ciclo":1.30,"muda":.83,
                          "decomposicao":.90,"chuva":.86}.get(p["nome"],1)
    return planos,falas,voz,total


def letreiros(plano,destino):
    nome=plano["nome"]
    dur=plano["frames"]/FPS
    linhas=[]
    def mostrar(texto,x,y,comeco,fim,estilo="Fase",opts=""):
        tags=r"{\an8\pos("+f"{x},{y}"+r")\fad(265,225)"+opts+"}"
        linhas.append(f"Dialogue: 0,{stamp(comeco,True)},{stamp(fim,True)},{estilo},,0,0,0,,{tags}{texto}")
    if nome=="copa":
        d=min(5.8,dur-.30)
        mostrar("INFOR",540,135,.29,d,"Apoio")
        mostrar("Agrofloresta",540,195,.42,d,"Titulo",r"\fs90\bord2.9")
        mostrar("Da folha ao solo",540,311,.54,d,"Fase",r"\fs53\bord2.5")
    elif nome=="palhada":
        mostrar("Serapilheira",540,232,dur*.49,dur-.23,"Fase",r"\fs55\bord2")
    elif nome=="chuva":
        mostrar("Solo exposto",269,320,.30,dur*.59,"Fase",r"\fs43\bord2")
        mostrar("Com cobertura",811,320,.30,dur*.59,"Fase",r"\fs43\bord2")
        mostrar("Umidade sob as folhas",540,240,dur*.64,dur-.18,"Fase",r"\fs47")
    elif nome=="decomposicao":
        mostrar("CORTE AMPLIADO DO SOLO",540,162,.18,dur-.12,"Apoio")
        mostrar("Decomposição",540,290,.29,dur*.39,"Fase",r"\fs51")
        mostrar("Matéria orgânica",540,290,dur*.405,dur*.735,"Fase",r"\fs50")
        mostrar("Nutrientes para as raízes",540,290,dur*.75,dur-.17,"Fase",r"\fs48")
    elif nome=="plantio":
        mostrar("Semente de andiroba",540,255,.35,dur-.29,"Fase",r"\fs51\bord2")
    elif nome=="muda":
        mostrar("GERMINAÇÃO DA ANDIROBA",540,159,.21,dur-.12,"Apoio")
        mostrar("Os cotilédones ficam sob o solo",540,240,dur*.69,dur-.16,"Fase",r"\fs44\bord1.9")
    if linhas:
        destino.write_text(CABECALHO_ASS+"\n".join(linhas)+"\n",encoding="utf-8")
    return bool(linhas)


def mixagem(voz,planos):
    mix=mixar(voz,planos)
    rng=np.random.default_rng(935)
    for p in planos:
        nome=p["nome"]
        d=p["frames"]/FPS
        inicio=p["inicio"]/FPS
        if nome=="chuva":
            t=tempo(d)
            envoltorio=np.minimum(1,t/.5)*np.minimum(1,(d-t)/.72)
            camada=ruido(rng,d,2200)*(.0044+.0015*np.sin(t*8.6)**2)
            colocar(mix,camada*envoltorio,inicio,0)
        elif nome in ("copa","palhada","plantio","ciclo"):
            ponto={"copa":.657,"palhada":.649,"plantio":.589,"ciclo":.662}[nome]
            t=tempo(.20)
            camada=.010*ruido(rng,.20,1600)*np.exp(-23*t)
            colocar(mix,camada,inicio+ponto*d,-.08)
    return mix


if __name__=="__main__":
    args=argumentos()
    ps,fs,voz,n=planos_e_locucao(args.voz)
    if args.acao=="lotes":
        print(json.dumps(list(range(len(lotes(ps))))))
    elif args.acao=="roteiro":
        print(json.dumps({"quadros":n,"fps":FPS,"planos":ps,"falas":fs},ensure_ascii=False,indent=2))
    elif args.acao=="render":
        renderizar(ps,args.lote,args.blender,args.saida,script=EPISODIO/"render_solo.py",amostras=11)
    elif args.acao=="montar":
        exportar(ps,fs,voz,n,args.pacotes,args.saida,
                 titulo=TITULO,texto_dos_planos=letreiros,som=mixagem)
