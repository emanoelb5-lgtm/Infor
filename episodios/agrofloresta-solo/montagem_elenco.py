"""Reedita a cópia aprovada com o elenco Infor preservando a linha do tempo."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile

from montagem_solo import EPISODIO, FPS, letreiros
from montagem import codificar, conferencia, ffmpeg

ORIGINAL = "7b044c9ca0440ed491a272423016f60a6880aee2f1f177b3124cb69762f28759"
QUADROS = (
    ("copa",230,24), ("palhada",314,15), ("chuva",320,None),
    ("decomposicao",390,None), ("plantio",252,15), ("muda",386,None),
    ("ciclo",279,24), ("diario",216,None),
)
LOTES = 20
FPS_FINAL = FPS


def lotes():
    lotes = [[] for _ in range(LOTES)]
    pesos = [0] * LOTES
    fatias = []
    for plano, frames, fps in QUADROS:
        if not fps:
            continue
        n = (frames*fps + FPS_FINAL-1)//FPS_FINAL
        for i in range(0,n,16):
            fim=min(i+16,n)
            carga = (fim-i) * (1.2 if plano in ("copa","ciclo") else 1)
            fatias.append((carga, plano, i, fim, n, frames/FPS_FINAL, fps))
    for carga, *fatia in sorted(fatias, reverse=True):
        i=pesos.index(min(pesos))
        lotes[i].append(fatia)
        pesos[i]+=carga+2
    return lotes


def renderizar(blender, numero_lote, saida):
    with tempfile.TemporaryDirectory(prefix="infor-elenco-") as tmp, ZipFile(saida,"w") as z:
        for plano, inicio, fim, n, duração, fps in lotes()[numero_lote]:
            pasta=Path(tmp)/plano
            subprocess.run([
                str(blender),"-b","-t","4","--factory-startup","--python-exit-code","1",
                "--python",str(EPISODIO/"render_elenco.py"),"--","--plano",plano,
                "--pasta",str(pasta),"--quadros",str(n),"--duracao",str(duração),
                "--fps",str(fps),"--amostras","11","--threads","4",
                "--primeiro",str(inicio),"--ultimo",str(fim),"--denoise",
            ],check=True)
            for í in range(inicio,fim):
                fonte=f"{í:04d}.jpg"
                z.write(pasta/fonte,arcname=f"{plano}/{fonte}")


def trilha_hash(video, mapa):
    saida = subprocess.check_output([
        "ffmpeg","-v","error","-i",str(video),"-map",mapa,"-c","copy","-f","hash","-hash","SHA256","-",
    ])
    return saida.strip()


def detalhes(video):
    p = subprocess.check_output(["ffprobe","-v","error","-show_streams","-of","json",str(video)])
    return json.loads(p)["streams"]


def extrair(origem,pasta):
    total=0
    marcadores=[]
    for _,n,_ in QUADROS[:-1]:
        total+=n
        marcadores.append(str(total))
    ffmpeg(["-i",str(origem),"-map","0:v:0","-c:v","copy","-f","segment",
            "-segment_frames",",".join(marcadores),"-reset_timestamps","1",str(pasta/"original-%d.mp4")])
    for i,(_,n,_) in enumerate(QUADROS):
        v=detalhes(pasta/f"original-{i}.mp4")[0]
        if int(v["nb_frames"])!=n:
            raise RuntimeError(f"O plano {i} mudou o número de quadros.")
    return marcadores


def comparar(origem, final, pasta, originais):
    if trilha_hash(origem,"0:a:0") != trilha_hash(final,"0:a:0"):
        raise RuntimeError("A trilha de áudio diverge da edição aprovada.")
    orig_srt = subprocess.check_output(["ffmpeg","-v","error","-i",str(origem),"-map","0:s:0","-f","srt","-"])
    final_srt = subprocess.check_output(["ffmpeg","-v","error","-i",str(final),"-map","0:s:0","-f","srt","-"])
    if orig_srt != final_srt:
        raise RuntimeError("As legendas divergem da edição aprovada.")
    novo=pasta/"conferencia"
    novo.mkdir()
    extrair(final,novo)
    for i in originais:
        a=pasta/f"original-{i}.mp4"
        b=novo/a.name
        vals=[subprocess.check_output([
            "ffmpeg","-v","error","-threads","2","-i",str(p),"-map","0:v:0",
            "-f","hash","-hash","SHA256","-",
        ]).strip() for p in (a,b)]
        if vals[0]!=vals[1]:
            raise RuntimeError(f"Um plano preservado foi alterado: {QUADROS[i][0]}.")
    print("Locução, trilha, legenda e quatro planos preservados conferidos por conteúdo.",flush=True)


def editar(origem, pacotes, destino):
    origem,destino=origem.resolve(),destino.resolve()
    with origem.open("rb") as arquivo:
        hash_aprovado=sha256(arquivo.read()).hexdigest()
    if hash_aprovado!=ORIGINAL:
        raise ValueError("Informe o MP4 aprovado de Agrofloresta da folha ao solo.")
    destino.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="infor-montagem-elenco-") as tmp:
        pasta=Path(tmp)
        extrair(origem,pasta)
        for i,lote in enumerate(lotes()):
            with ZipFile(pacotes/f"lote-{i}.zip") as z:
                for plano,inicio,fim,*_ in lote:
                    frames=pasta/plano
                    frames.mkdir(exist_ok=True)
                    for idx in range(inicio,fim):
                        img=f"{idx:04d}.jpg"
                        (frames/img).write_bytes(z.read(f"{plano}/{img}"))

        def preparar(item):
            i,(nome,n,fps)=item
            if fps:
                codificar({"nome":nome,"frames":n},pasta/nome,pasta/f"elenco-{i}.mp4",
                          fps_3d=fps,escrever_letreiros=letreiros)
            print(f"{nome} | {n} quadros | {'elenco' if fps else 'edição aprovada'}",flush=True)

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(preparar,enumerate(QUADROS)))

        lista=pasta/"montagem.txt"
        lista.write_text("".join(
            f"file {'elenco' if fps else 'original'}-{i}.mp4\nduration {n/FPS_FINAL:.8f}\n"
            for i,(_,n,fps) in enumerate(QUADROS)
        ),encoding="utf-8")
        temporário=destino.with_name(f".{destino.name}.parte.mp4")
        ffmpeg(["-f","concat","-safe","1","-i",str(lista),"-i",str(origem),
                "-map","0:v:0","-map","1:a:0","-map","1:s:0","-c","copy","-map_metadata","1",
                "-video_track_timescale","30000","-movflags","+faststart",str(temporário)])
        conferencia(temporário, sum(n for _,n,_ in QUADROS))
        comparar(origem,temporário,pasta,[i for i,(_,_,fps) in enumerate(QUADROS) if fps is None])
        temporário.replace(destino)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="acao",required=True)
    sub.add_parser("lotes")
    r=sub.add_parser("renderizar")
    r.add_argument("lote",type=int)
    r.add_argument("blender",type=Path)
    r.add_argument("saida",type=Path)
    e=sub.add_parser("editar")
    e.add_argument("origem",type=Path)
    e.add_argument("pacotes",type=Path)
    e.add_argument("destino",type=Path)
    a=p.parse_args()
    if a.acao=="lotes":
        print(json.dumps(list(range(len(lotes())))))
    elif a.acao=="renderizar":
        renderizar(a.blender,a.lote,a.saida)
    else:
        editar(a.origem,a.pacotes,a.destino)


if __name__=="__main__":
    main()
