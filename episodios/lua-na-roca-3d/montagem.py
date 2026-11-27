"""Monta a animação do Infor, com locução em português e gravações do AgroHere."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import numpy as np

EPISODIO = Path(__file__).resolve().parent
ORIGINAL = EPISODIO.parent / "lua-na-roca"
sys.path.insert(0, str(ORIGINAL))
from som import TAXA, colocar, escrever_wav, locucao, ruido, tempo, trilha

FPS = 30
FPS_3D = 15
TITULO = "A Lua e o tempo da roça"
ARQUIVO = "A_Lua_e_o_Tempo_da_Roca_Reel.mp4"

DECUPAGEM = (
    (("noite", 1),),
    (("varanda", 1),),
    (("fases", .49), ("sementes", .51)),
    (("ciclo", 1),),
    (("terra", .52), ("canteiro", .48)),
    (("observacao", 1),),
    (("semear", .39), ("dados", .61)),
    (("broto", .40), ("balanca", .60)),
    (("memoria", .53), ("caderno-final", .47)),
    (("calendario", 1),),
    (("diario", 1),),
)

APP = {
    "calendario": ("calendario.mp4", 0.22, 1.55),
    "diario": ("diario.mp4", 0, 1),
}


def linha_do_tempo():
    roteiro = json.loads((ORIGINAL / "roteiro.json").read_text(encoding="utf-8"))
    cursor = 0
    falas = []
    planos = []
    faixas = [np.zeros(6*TAXA//FPS, dtype=np.float32)]
    assert len(roteiro) == len(DECUPAGEM)
    for i, (fala, tomadas) in enumerate(zip(roteiro, DECUPAGEM, strict=True)):
        sinal = locucao(ORIGINAL / "assets" / "voz" / f'{fala["id"]}.mp3')
        intro = 6 if i == 0 else 0
        frames_fala = round((len(sinal)/TAXA + fala["pausa"]) * FPS)
        total = frames_fala + intro
        inicio = (cursor+intro)/FPS
        falas.append((inicio, inicio+len(sinal)/TAXA, fala["texto"]))
        faixas.extend([sinal, np.zeros(frames_fala*TAXA//FPS-len(sinal),dtype=np.float32)])
        parcial = 0
        peso_total = 0
        for j,(nome,peso) in enumerate(tomadas):
            peso_total += peso
            limite = total if j==len(tomadas)-1 else round(total*peso_total)
            planos.append({"nome":nome,"inicio":cursor+parcial,"frames":limite-parcial})
            parcial = limite
        cursor += total
    voz = np.concatenate(faixas)
    if len(voz) != cursor*TAXA//FPS or cursor > 120*FPS:
        raise ValueError("Duração incompatível com a faixa de narração.")
    return planos, falas, voz, cursor


def foley(voz, planos):
    sinais = [{"imagem":p["nome"] if p["nome"]=="noite" else
               "prosa" if p["nome"]=="varanda" else "ambiente",
               "inicio":p["inicio"],"frames":p["frames"]} for p in planos]
    mix = trilha(voz, sinais, FPS)
    rng = np.random.default_rng(522)
    for p in planos:
        nome = p["nome"]
        inicio = p["inicio"]/FPS
        d = p["frames"]/FPS
        if nome in ("observacao","dados","caderno-final"):
            dur = d*.55
            t = tempo(dur)
            faixa = ruido(rng,dur,2350)
            faixa *= (0.004+.0035*np.sin(16*t)**2)*np.minimum(1,t/.06)*np.minimum(1,(dur-t)/.12)
            colocar(mix,faixa,inicio+d*.14,.24)
        if nome in ("sementes","terra","semear","balanca","memoria"):
            instantes, freq, volume = {
                "sementes": (tuple(.534+i*.0068 for i in range(42)), 710, .014),
                "semear": (tuple(.563+i*.034 for i in range(6)), 275, .012),
                "terra": ((.48,.58,.70), 210, .009),
                "balanca": ((.49,.52,.58,.64,.68), 645, .015),
                "memoria": ((.61,.73), 187, .014),
            }[nome]
            for f in instantes:
                t = tempo(.086)
                h = freq*rng.uniform(.79,1.24)
                onda = .30*np.sin(2*np.pi*h*t)+.70*ruido(rng,.086,3000)
                colocar(mix,volume*onda*np.exp(-t*64),inicio+f*d,rng.uniform(-.20,.20))
    return mix


def stamp(s, ass=False):
    n = round(s*(100 if ass else 1000))
    if ass:
        return f"{n//360000}:{n//6000%60:02d}:{n//100%60:02d}.{n%100:02d}"
    return f"{n//3600000:02d}:{n//60000%60:02d}:{n//1000%60:02d},{n%1000:03d}"


CABECALHO_ASS = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Titulo,DejaVu Serif,96,&H00DFEEFF,&H00000000,&H9914130F,&H8014120A,0,0,0,0,100,100,-1.5,0,1,1.4,0,8,60,60,0,1
Style: Fase,DejaVu Sans,52,&H00DFEEFF,&H00000000,&H6614130F,&H0014120A,0,0,0,0,100,100,.1,0,1,1.2,0,8,60,60,0,1
Style: Apoio,DejaVu Sans,36,&H009ED3F9,&H00000000,&H9914130F,&H8014120A,0,0,0,0,100,100,3,0,1,1.0,0,8,60,60,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""


def letreiros(plano, arquivo):
    duracao = plano["frames"]/FPS
    linhas = []
    def evento(estilo, texto, x, y, entrada=0.12, saida=None, opcao=""):
        if saida is None:
            saida = duracao
        tags = r"{\an8\pos(" + f"{x},{y}" + r")\fad(360,230)" + opcao + "}"
        linhas.append(f"Dialogue: 0,{stamp(entrada,True)},{stamp(saida,True)},{estilo},,0,0,0,,{tags}{texto}")
    nome = plano["nome"]
    if nome == "noite":
        evento("Apoio","INFOR",540,124,.43,4.89)
        evento("Titulo",r"A Lua e o\Ntempo da roça",540,185,.59,4.89)
    if nome == "fases":
        evento("Apoio","AS FASES DA LUA",540,238)
        for palavra,x,y,i in (("Nova",246,786,0),("Crescente",834,786,1),
                              ("Cheia",246,1435,2),("Minguante",834,1435,3)):
            evento("Fase",palavra,x,y,0.15+i*.18)
    if nome == "ciclo":
        evento("Titulo","29,5 dias",540,1356,1.08)
        evento("Apoio","DE LUA NOVA A LUA NOVA",540,1492,1.36)
    if nome == "canteiro":
        evento("Fase",r"Umidade, chuva\Ne época de plantio",540,1380,.19,opcao=r"\fs50")
    if nome == "broto":
        evento("Apoio","GERMINAÇÃO DO FEIJÃO",540,327)
    if not linhas:
        return False
    arquivo.write_text(CABECALHO_ASS + "\n".join(linhas) + "\n",encoding="utf-8")
    return True


def ffmpeg(args):
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",*args],check=True)


def codificar(plano, pasta_frames, destino):
    filtro = []
    app = plano["nome"] in APP
    if app:
        video, corte, velocidade = APP[plano["nome"]]
        arquivo = ORIGINAL/"assets"/"capturas"/video
        entrada = ["-ss",str(corte),"-i",str(arquivo)]
        filtro.append(f"setpts=(PTS-STARTPTS)/{velocidade}")
    else:
        entrada = ["-framerate",str(FPS_3D),"-i",str((pasta_frames/"%04d.jpg").resolve())]
        filtro.append("hqdn3d=1.45:1.0:1.8:1.2")
    filtro.extend([
        f"fps={FPS}", "scale=1080:1920:flags=lanczos:out_color_matrix=bt709",
        "setsar=1", "tpad=stop_mode=clone:stop_duration=7", "format=yuv420p",
    ])
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="infor-tipos-",dir="/tmp") as pasta:
        arquivo = Path(pasta)/"texto.ass"
        if letreiros(plano,arquivo):
            filtro.append(f"ass={arquivo}")
        ffmpeg([*entrada, "-an","-filter_threads","2","-vf",",".join(filtro),
            "-frames:v",str(plano["frames"]),"-c:v","libx264","-preset","veryfast","-crf","19",
            "-threads","2","-pix_fmt","yuv420p","-color_primaries","bt709","-color_trc","bt709",
            "-colorspace","bt709","-video_track_timescale","30000",str(destino)])


def renderizar(nome, quadros, clipes, blender, amostras, largura, altura, threads, denoise):
    planos, _, _, _ = linha_do_tempo()
    p = next(p for p in planos if p["nome"] == nome)
    destino = clipes/f"{nome}.mp4"
    if nome in APP:
        codificar(p, quadros, destino)
        return
    quadros = quadros/nome
    n = (p["frames"]*FPS_3D+FPS-1)//FPS
    comando = [blender,"-b","-t",str(threads),"--factory-startup","--python-exit-code","1",
        "--python",str(EPISODIO/"render.py"),"--","--plano",nome,"--pasta",str(quadros),
        "--quadros",str(n),"--duracao",str(p["frames"]/FPS),"--fps",str(FPS_3D),
        "--largura",str(largura),"--altura",str(altura),"--amostras",str(amostras),
        "--threads",str(threads)]
    if denoise:
        comando.append("--denoise")
    subprocess.run(comando,check=True)
    codificar(p,quadros,destino)


def normalizar(wav):
    alvo = "loudnorm=I=-15:LRA=9:TP=-1.5"
    log = subprocess.run(["ffmpeg","-hide_banner","-i",str(wav),"-af",alvo+":print_format=json",
        "-f","null","-"],check=True,stderr=subprocess.PIPE,text=True).stderr
    n = json.loads(log[log.rfind("{"):log.rfind("}")+1])
    medidos = ("I", "LRA", "TP", "thresh")
    filtro = ":".join(f"measured_{k}={n['input_'+k.lower()]}" for k in medidos)
    return f"{alvo}:linear=true:{filtro}:offset={n['target_offset']}"


def legendas(falas, caminho):
    textos = []
    for inicio, fim, fala in falas:
        pedacos = re.split(r"(?<=[.!?])\s+",fala)
        if len(pedacos) == 1 and len(fala)>86:
            pos = fala.rfind(" ",0,len(fala)//2+10)
            pedacos = [fala[:pos],fala[pos+1:]]
        peso = sum(len(p) for p in pedacos)
        t = inicio
        for parte in pedacos:
            fim_bloco = t+(fim-inicio)*len(parte)/peso
            textos.append(f"{len(textos)+1}\n{stamp(t)} --> {stamp(fim_bloco)}\n{parte}\n")
            t = fim_bloco
    caminho.write_text("\n".join(textos),encoding="utf-8")


def conferencia(destino, n):
    p = subprocess.run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",
        str(destino)],check=True,capture_output=True,text=True)
    resultado = json.loads(p.stdout)
    video = next(s for s in resultado["streams"] if s["codec_type"]=="video")
    audio = next(s for s in resultado["streams"] if s["codec_type"]=="audio")
    alteracao = abs(n/FPS-float(resultado["format"]["duration"]))
    if (video["width"],video["height"],video["codec_name"],video["r_frame_rate"]) != (1080,1920,"h264","30/1"):
        raise RuntimeError("Dimensões ou codificação de vídeo incorretas.")
    if int(video["nb_frames"]) != n or alteracao > 2/FPS or audio["codec_name"]!="aac":
        raise RuntimeError("Duração ou formato de áudio incorretos.")
    subprocess.run(["ffmpeg","-v","error","-xerror","-threads","2","-i",str(destino),"-map","0:v",
        "-map","0:a","-f","null","-"],check=True)
    print(f"{n/FPS:.2f}s | 1080 × 1920 | {n} quadros | H264/AAC",flush=True)


def montar(clipes, destino):
    planos, falas, voz, n = linha_do_tempo()
    destino = destino.resolve()
    destino.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="infor-montagem-") as tmp:
        pasta = Path(tmp)
        wav = pasta/"mix.wav"
        escrever_wav(wav, foley(voz,planos))
        srt = pasta/"fala.srt"
        legendas(falas,srt)
        lista = pasta/"cortes.txt"
        ordenados = []
        for p in planos:
            arq = clipes/f'{p["nome"]}.mp4'
            if p["nome"] in APP and not arq.is_file():
                arq = pasta/arq.name
                codificar(p, pasta, arq)
            if not arq.is_file():
                raise FileNotFoundError(arq)
            ordenados.append(arq)
        lista.write_text("".join(f"file '{arq.resolve()}'\n" for arq in ordenados),encoding="utf-8")
        temporario = destino.with_name(f".{destino.name}.montando.mp4")
        ffmpeg(["-f","concat","-safe","0","-i",str(lista),"-i",str(wav),"-i",str(srt),
            "-map","0:v","-map","1:a","-map","2:s","-c:v","copy",
            "-af",normalizar(wav),"-c:a","aac","-b:a","192k","-ar",str(TAXA),"-c:s","mov_text",
            "-disposition:s:0","0","-metadata",f"title={TITULO}",
            "-metadata:s:a:0","language=por","-metadata:s:s:0","language=por",
            "-movflags","+faststart",str(temporario)])
        conferencia(temporario,n)
        temporario.replace(destino)


def argumentos():
    parser = argparse.ArgumentParser(description=__doc__)
    comandos = parser.add_subparsers(dest="acao",required=True)
    comandos.add_parser("planos")
    p = comandos.add_parser("render")
    p.add_argument("nome")
    p.add_argument("--quadros",type=Path,default=EPISODIO/".build"/"quadros")
    p.add_argument("--clipes",type=Path,default=EPISODIO/".build"/"clipes")
    p.add_argument("--blender",default="blender")
    p.add_argument("--amostras",type=int,default=11)
    p.add_argument("--largura",type=int,default=540)
    p.add_argument("--altura",type=int,default=960)
    p.add_argument("--threads",type=int,default=4)
    p.add_argument("--denoise",action="store_true")
    p = comandos.add_parser("montar")
    p.add_argument("--clipes",type=Path,default=EPISODIO/".build"/"clipes")
    p.add_argument("--saida",type=Path,default=EPISODIO/"dist"/ARQUIVO)
    return parser.parse_args()


if __name__ == "__main__":
    args = argumentos()
    if args.acao == "planos":
        print(json.dumps([p["nome"] for p in linha_do_tempo()[0] if p["nome"] not in APP]))
    elif args.acao == "render":
        renderizar(args.nome,args.quadros,args.clipes,args.blender,args.amostras,args.largura,args.altura,
              args.threads,args.denoise)
    elif args.acao == "montar":
        montar(args.clipes,args.saida)
