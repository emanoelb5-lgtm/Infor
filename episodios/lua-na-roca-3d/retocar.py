"""Renderiza os letreiros revisados e atualiza a montagem a partir do MP4 já exportado."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile

from montagem import EPISODIO, FPS, FPS_3D, codificar, conferencia, ffmpeg, linha_do_tempo

REVISAO = ("noite", "observacao")
QUADROS_POR_TAREFA = 18


def planos_e_total():
    plano, _, _, total = linha_do_tempo()
    return {p["nome"]:p for p in plano if p["nome"] in REVISAO}, total


def poses(plano):
    return (plano["frames"]*FPS_3D + FPS-1)//FPS


def tarefas(planos):
    return [{"plano":p["nome"],"inicio":k,"fim":min(k+QUADROS_POR_TAREFA,poses(p))}
            for p in planos.values() for k in range(0,poses(p),QUADROS_POR_TAREFA)]


def parte(args, plano):
    with tempfile.TemporaryDirectory(prefix="infor-parte-") as tmp:
        quadros = Path(tmp)
        subprocess.run([args.blender,"-b","-t","4","--factory-startup","--python-exit-code","1",
            "--python",str(EPISODIO/"render.py"),"--","--plano",args.plano,"--pasta",tmp,
            "--quadros",str(poses(plano)),"--duracao",str(plano["frames"]/FPS),
            "--fps",str(FPS_3D),"--amostras","13","--threads","4","--denoise",
            "--primeiro",str(args.inicio),"--ultimo",str(args.fim)],check=True)
        with ZipFile(args.saida, "w") as pacote:
            for n in range(args.inicio,args.fim):
                nome=f"{n:04d}.jpg"
                pacote.write(quadros/nome,arcname=nome)


def numero_frames(arquivo):
    resultado=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=nb_frames","-of","csv=p=0",str(arquivo)],text=True)
    return int(resultado.strip())


def regularizar(base, destino, total):
    destino.parent.mkdir(parents=True,exist_ok=True)
    ffmpeg(["-threads","4","-i",str(base),"-map","0:v:0","-map","0:a:0","-map","0:s:0",
        "-map_metadata","0","-vf","settb=expr=1/30000,setpts=N*1000","-r",str(FPS),
        "-fps_mode","passthrough","-c:v","libx264","-preset","veryfast","-crf","17",
        "-threads","4","-c:a","copy","-c:s","copy","-pix_fmt","yuv420p",
        "-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709",
        "-video_track_timescale","30000","-disposition:s:0","0","-movflags","+faststart",
        str(destino)])
    conferencia(destino,total)


def montar(base, pacotes, destino, planos, total):
    destino.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="infor-letreiros-") as tmp:
        pasta=Path(tmp)
        for plano in planos.values():
            nome=plano["nome"]
            quadros=pasta/nome
            quadros.mkdir()
            for tarefa in tarefas({nome:plano}):
                arquivo=pacotes/f'{nome}-{tarefa["inicio"]}.zip'
                with ZipFile(arquivo) as pacote:
                    for i in range(tarefa["inicio"],tarefa["fim"]):
                        img=f"{i:04d}.jpg"
                        (quadros/img).write_bytes(pacote.read(img))
            codificar(plano,quadros,pasta/f"{nome}.mp4")

        caderno=planos["observacao"]
        cortes=(planos["noite"]["frames"],caderno["inicio"],caderno["inicio"]+caderno["frames"])
        tempos=",".join(f"{n/FPS-.008:.6f}" for n in cortes)
        ffmpeg(["-i",str(base),"-map","0:v:0","-c:v","copy","-f","segment",
            "-segment_times",tempos,"-reset_timestamps","1",str(pasta/"base-%d.mp4")])
        limites=(0,*cortes,total)
        for i, (inicio,fim) in enumerate(zip(limites,limites[1:])):
            if numero_frames(pasta/f"base-{i}.mp4") != fim-inicio:
                raise RuntimeError(f"Corte fora do ponto de montagem no trecho {i}.")
        lista=pasta/"cortes.txt"
        lista.write_text("file noite.mp4\nfile base-1.mp4\nfile observacao.mp4\nfile base-3.mp4\n",
                         encoding="utf-8")
        intermediario=pasta/"intermediario.mp4"
        ffmpeg(["-f","concat","-safe","1","-i",str(lista),"-i",str(base),
            "-map","0:v:0","-map","1:a:0","-map","1:s:0","-map_metadata","1","-c","copy",
            "-disposition:s:0","0",str(intermediario)])
        regularizar(intermediario,destino,total)


def argumentos():
    p=argparse.ArgumentParser(description=__doc__)
    comandos=p.add_subparsers(dest="acao",required=True)
    comandos.add_parser("tarefas")
    r=comandos.add_parser("parte")
    r.add_argument("plano",choices=REVISAO)
    r.add_argument("inicio",type=int)
    r.add_argument("fim",type=int)
    r.add_argument("--blender",required=True)
    r.add_argument("--saida",required=True,type=Path)
    m=comandos.add_parser("montar")
    m.add_argument("--base",required=True,type=Path)
    m.add_argument("--pacotes",required=True,type=Path)
    m.add_argument("--saida",required=True,type=Path)
    c=comandos.add_parser("relogio")
    c.add_argument("--base",required=True,type=Path)
    c.add_argument("--saida",required=True,type=Path)
    return p.parse_args()


if __name__=="__main__":
    args=argumentos()
    planos,total=planos_e_total()
    if args.acao=="tarefas":
        print(json.dumps(tarefas(planos)))
    elif args.acao=="parte":
        parte(args,planos[args.plano])
    elif args.acao=="montar":
        montar(args.base,args.pacotes,args.saida,planos,total)
    elif args.acao=="relogio":
        regularizar(args.base,args.saida,total)
