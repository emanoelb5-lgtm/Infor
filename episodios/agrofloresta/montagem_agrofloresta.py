"""Decupa, renderiza e finaliza o curta vertical do episódio de agrofloresta."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile

import numpy as np

EPISODIO=Path(__file__).resolve().parent
sys.path.insert(0,str(EPISODIO.parent/"lua-na-roca-3d"))
from montagem import CABECALHO_ASS, FPS, codificar, conferencia, ffmpeg, legendas, normalizar, stamp
from som import TAXA, colocar, escrever_wav, locucao, ruido, tempo, trilha

TITULO="Agrofloresta da semente à sombra"
VIDEO="Agrofloresta_Da_Semente_a_Sombra_Reel.mp4"
GERMINACAO=("raiz","emergencia","folhas")
EXECUTORES=20
QUADROS_POR_FATIA=22


def linha_do_tempo(narracao):
    roteiro=json.loads((EPISODIO/"roteiro.json").read_text(encoding="utf-8"))
    faixa=[]
    cenas=[]
    falas=[]
    cursor=0
    for i,p in enumerate(roteiro):
        nome=p["id"]
        audio=locucao(narracao/f"{nome}.mp3")
        intro=7 if i==0 else 0
        quadros=round((len(audio)/TAXA+p["pausa"])*FPS)
        inicio=(cursor+intro)/FPS
        falas.append((inicio,inicio+len(audio)/TAXA,p["texto"]))
        pausa=quadros*TAXA//FPS-len(audio)
        if pausa<0:
            raise ValueError(f"Pausa insuficiente para a locução de {nome}.")
        faixa.extend((np.zeros(intro*TAXA//FPS,dtype=np.float32),audio,
                      np.zeros(pausa,dtype=np.float32)))
        orig=30 if nome in GERMINACAO else 15
        cenas.append({"nome":nome,"inicio":cursor,"frames":quadros+intro,"fps_3d":orig,
                      "titulo":p["titulo"],"texto":p["texto"],"acao":p["acao"]})
        cursor+=quadros+intro
    voz=np.concatenate(faixa)
    if len(voz)!=cursor*TAXA//FPS or cursor>120*FPS:
        raise ValueError("A duração da linha do tempo não confere.")
    return cenas,falas,voz,cursor


def lotes(planos):
    grupos=[[] for _ in range(EXECUTORES)]
    cargas=[0.0]*EXECUTORES
    fatias=[]
    for p in planos:
        nome=p["nome"]
        if nome=="diario":
            continue
        fps=p["fps_3d"]
        n=(p["frames"]*fps+FPS-1)//FPS
        peso=.84 if nome in GERMINACAO else 1.24 if nome in ("abertura","manejo","estratos") else 1.0
        for i in range(0,n,QUADROS_POR_FATIA):
            fim=min(n,i+QUADROS_POR_FATIA)
            fatias.append((peso*(fim-i),nome,i,fim,n,p["frames"]/FPS,fps))
    for carga,*s in sorted(fatias,reverse=True):
        k=cargas.index(min(cargas))
        grupos[k].append(s)
        cargas[k]+=carga+2.7
    return grupos


def renderizar(planos,indice,blender,destino):
    with tempfile.TemporaryDirectory(prefix="agro-poses-") as temp, ZipFile(destino,"w") as z:
        base=Path(temp)
        for p,a,b,n,dt,fps in lotes(planos)[indice]:
            pasta=base/p
            subprocess.run([blender,"-b","-t","4","--factory-startup","--python-exit-code","1",
                "--python",str(EPISODIO/"render_agrofloresta.py"),"--","--plano",p,"--pasta",str(pasta),
                "--quadros",str(n),"--duracao",str(dt),"--fps",str(fps),
                "--amostras","12","--threads","4","--primeiro",str(a),"--ultimo",str(b),
                "--denoise"],check=True)
            for i in range(a,b):
                img=f"{i:04d}.jpg"
                z.write(pasta/img,arcname=f"{p}/{img}")


def letreiros(plano,salvar):
    nome=plano["nome"]
    duracao=plano["frames"]/FPS
    linhas=[]
    def por(texto,x,y,comeco,fim,estilo="Fase",opts=""):
        tags=r"{\an8\pos("+f"{x},{y}"+r")\fad(285,225)"+opts+"}"
        linhas.append(f"Dialogue: 0,{stamp(comeco,True)},{stamp(fim,True)},{estilo},,0,0,0,,{tags}{texto}")
    if nome=="abertura":
        d=min(5.8,duracao-.30)
        por("INFOR",540,141,.29,d,"Apoio")
        por("Agrofloresta",540,221,.44,d,"Titulo",r"\fs91\bord2.8")
        por("Da semente à sombra",540,337,.55,d,"Fase",r"\fs50\bord2.1")
    elif nome=="desenho":
        por("Espaço, luz e tempo",540,213,.47,duracao-.30,"Fase",r"\fs53\bord2")
    elif nome=="estratos":
        por("Feijão na faixa aberta",540,257,.20,duracao*.32,"Fase",r"\fs47\bord2")
        por(r"Banana\NSombra temporária para o cacau",540,247,duracao*.33,duracao*.72,"Fase",r"\fs43\bord2")
        por("Ingá na copa mais alta",540,257,duracao*.73,duracao-.22,"Fase",r"\fs47\bord2")
    elif nome=="raiz":
        por("CORTE DO SOLO",540,162,.17,duracao-.08,"Apoio")
        por("Radícula",274,1481,duracao*.44,duracao-.17,"Fase",r"\fs48\bord2")
    elif nome=="emergencia":
        por("Curva do hipocótilo",540,232,.34,duracao*.63,"Fase",r"\fs48")
        por("Cotilédones",540,232,duracao*.64,duracao-.25,"Fase",r"\fs49")
    elif nome=="folhas":
        por("Primeiras folhas simples",540,207,duracao*.39,duracao-.18,"Fase",r"\fs50")
    if linhas:
        salvar.write_text(CABECALHO_ASS+"\n".join(linhas)+"\n",encoding="utf-8")
    return bool(linhas)


def mixar(voz,planos):
    dados=[{"imagem":"prosa" if p["nome"] in ("abertura","manejo") else "ambiente",
            "inicio":p["inicio"],"frames":p["frames"]} for p in planos]
    mix=trilha(voz,dados,FPS)
    gerador=np.random.default_rng(104)
    efeitos={"desenho":(.612,.10,246,.013),"semeadura":(.553,.18,313,.020),
             "emergencia":(.463,.36,543,.007),"manejo":(.601,.11,203,.014)}
    for p in planos:
        if p["nome"] not in efeitos:
            continue
        parte,d,f,vol=efeitos[p["nome"]]
        t=tempo(d)
        amostra=(.37*np.sin(2*np.pi*f*t)+.63*ruido(gerador,d,2650))*np.exp(-24*t)
        instante=(p["inicio"]+p["frames"]*parte)/FPS
        colocar(mix,amostra*vol,instante,.15)
    return mix


def exportar(planos,falas,voz,total,entrega,destino):
    destino=destino.resolve()
    destino.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="agrofloresta-edicao-") as tmp:
        p=Path(tmp)
        clipes,frames=p/"clipes",p/"quadros"
        clipes.mkdir()
        for i,lote in enumerate(lotes(planos)):
            with ZipFile(entrega/f"lote-{i}.zip") as z:
                for nome,a,b,_,_,_ in lote:
                    pasta=frames/nome
                    pasta.mkdir(exist_ok=True,parents=True)
                    for k in range(a,b):
                        arq=f"{k:04d}.jpg"
                        (pasta/arq).write_bytes(z.read(f"{nome}/{arq}"))
        def codificar_plano(plano):
            nome=plano["nome"]
            codificar(plano,frames/nome,clipes/f"{nome}.mp4",fps_3d=plano["fps_3d"],
                      escrever_letreiros=letreiros)
            print(f"Plano exportado: {nome}",flush=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(codificar_plano,planos))
        wav,srt=p/"mix.wav",p/"fala.srt"
        escrever_wav(wav,mixar(voz,planos))
        legendas(falas,srt)
        lista=clipes/"cortes.txt"
        lista.write_text("".join(f"file {x['nome']}.mp4\n" for x in planos),encoding="utf-8")
        nome_temp=destino.with_name(f".{destino.name}.montando.mp4")
        ffmpeg(["-f","concat","-safe","1","-i",str(lista),"-i",str(wav),"-i",str(srt),
              "-map","0:v","-map","1:a","-map","2:s","-c:v","copy",
              "-af",normalizar(wav),"-c:a","aac","-b:a","192k","-ar",str(TAXA),"-c:s","mov_text",
              "-disposition:s:0","0","-metadata",f"title={TITULO}","-metadata:s:a:0","language=por",
              "-metadata:s:s:0","language=por","-movflags","+faststart",str(nome_temp)])
        conferencia(nome_temp,total)
        nome_temp.replace(destino)


def argumentos():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--voz",type=Path,required=True)
    sub=p.add_subparsers(dest="acao",required=True)
    sub.add_parser("lotes")
    sub.add_parser("roteiro")
    r=sub.add_parser("render")
    r.add_argument("lote",type=int)
    r.add_argument("--blender",required=True)
    r.add_argument("--saida",required=True,type=Path)
    r=sub.add_parser("montar")
    r.add_argument("--pacotes",required=True,type=Path)
    r.add_argument("--saida",required=True,type=Path)
    return p.parse_args()


if __name__=="__main__":
    args=argumentos()
    ps,fs,voz,n=linha_do_tempo(args.voz)
    if args.acao=="lotes":
        print(json.dumps(list(range(len(lotes(ps))))))
    elif args.acao=="roteiro":
        print(json.dumps({"quadros":n,"fps":FPS,"planos":ps,"falas":fs},ensure_ascii=False,indent=2))
    elif args.acao=="render":
        renderizar(ps,args.lote,args.blender,args.saida)
    elif args.acao=="montar":
        exportar(ps,fs,voz,n,args.pacotes,args.saida)
