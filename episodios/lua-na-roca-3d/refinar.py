"""Renderiza a edição refinada em lotes e monta o MP4 verificável."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile

from montagem import APP, EPISODIO, FPS, FPS_3D, codificar, ffmpeg, linha_do_tempo, montar

REAPROVEITAR = ("fases", "ciclo")
TRABALHADORES = 20
QUADROS_POR_FATIA = 18


def distribuicao():
    lotes=[[] for _ in range(TRABALHADORES)]
    cargas=[0.0]*TRABALHADORES
    dados=[]
    for plano in linha_do_tempo()[0]:
        nome=plano["nome"]
        if nome in APP or nome in REAPROVEITAR:
            continue
        poses=(plano["frames"]*FPS_3D+FPS-1)//FPS
        duracao=plano["frames"]/FPS
        fator=1.17 if nome in ("varanda","canteiro","memoria","terra") else 1.0
        for inicio in range(0,poses,QUADROS_POR_FATIA):
            fim=min(poses,inicio+QUADROS_POR_FATIA)
            dados.append((fator*(fim-inicio),nome,inicio,fim,poses,duracao))
    for carga,*fatia in sorted(dados,reverse=True):
        i=cargas.index(min(cargas))
        lotes[i].append(fatia)
        cargas[i]+=carga+2.5
    return lotes


def renderizar(i,blender,destino):
    lote=distribuicao()[i]
    with tempfile.TemporaryDirectory(prefix="infor-quadros-") as tmp, ZipFile(destino,"w") as zipado:
        pasta=Path(tmp)
        for nome,inicio,fim,poses,duracao in lote:
            local=pasta/nome
            subprocess.run([blender,"-b","-t","4","--factory-startup","--python-exit-code","1",
                "--python",str(EPISODIO/"render.py"),"--","--plano",nome,"--pasta",str(local),
                "--quadros",str(poses),"--duracao",str(duracao),"--fps",str(FPS_3D),
                "--amostras","12","--threads","4","--primeiro",str(inicio),
                "--ultimo",str(fim),"--denoise"],check=True)
            for k in range(inicio,fim):
                imagem=f"{k:04d}.jpg"
                zipado.write(local/imagem,arcname=f"{nome}/{imagem}")


def recorte(p, base, destino):
    inicio,fim=p["inicio"],p["inicio"]+p["frames"]
    ffmpeg(["-threads","2","-i",str(base),"-map","0:v:0","-an",
        "-vf",f"trim=start_frame={inicio}:end_frame={fim},settb=expr=1/30000,setpts=N*1000,setsar=1",
        "-c:v","libx264","-crf","19","-preset","veryfast","-threads","2","-r",str(FPS),
        "-pix_fmt","yuv420p","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709",
        "-video_track_timescale","30000",str(destino)])


def exportar(pacotes,base,destino):
    planos=linha_do_tempo()[0]
    lotes=distribuicao()
    with tempfile.TemporaryDirectory(prefix="infor-edicao-") as tmp:
        pasta=Path(tmp)
        quadros=pasta/"quadros"
        clipes=pasta/"clipes"
        clipes.mkdir()
        for i,lote in enumerate(lotes):
            with ZipFile(pacotes/f"lote-{i}.zip") as pacote:
                for nome,inicio,fim,_,_ in lote:
                    pasta_plano=quadros/nome
                    pasta_plano.mkdir(exist_ok=True,parents=True)
                    for k in range(inicio,fim):
                        imagem=f"{k:04d}.jpg"
                        (pasta_plano/imagem).write_bytes(pacote.read(f"{nome}/{imagem}"))
        def codificar_plano(p):
            nome=p["nome"]
            arquivo=clipes/f"{nome}.mp4"
            if nome in REAPROVEITAR:
                recorte(p,base,arquivo)
            else:
                codificar(p,quadros/nome,arquivo)
            print(f"Plano exportado: {nome}",flush=True)
        with ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(codificar_plano,planos))
        montar(clipes,destino)


def argumentos():
    parser=argparse.ArgumentParser(description=__doc__)
    comando=parser.add_subparsers(dest="acao",required=True)
    comando.add_parser("lotes")
    p=comando.add_parser("render")
    p.add_argument("lote",type=int)
    p.add_argument("--blender",required=True)
    p.add_argument("--saida",required=True,type=Path)
    p=comando.add_parser("montar")
    p.add_argument("--pacotes",required=True,type=Path)
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--saida",required=True,type=Path)
    return parser.parse_args()


if __name__=="__main__":
    args=argumentos()
    if args.acao=="lotes":
        print(json.dumps(list(range(len(distribuicao())))))
    elif args.acao=="render":
        renderizar(args.lote,args.blender,args.saida)
    elif args.acao=="montar":
        exportar(args.pacotes,args.base,args.saida)
