"""Exporta o Reel vertical em H.264 e AAC com as artes e a narração do episódio."""

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np

from som import TAXA, escrever_wav, locucao, trilha
from visuais import quadro

EPISODIO = Path(__file__).resolve().parent
FPS = 30
TITULO = "A Lua e o tempo da roça"
ARQUIVO = "A_Lua_e_o_Tempo_da_Roca_Reel.mp4"
CAPTURAS = EPISODIO / "assets" / "capturas"


def carregar(arquivo):
    return json.loads((EPISODIO / arquivo).read_text(encoding="utf-8"))


def linha_do_tempo(origem_voz):
    roteiro, cenas = carregar("roteiro.json"), carregar("planos.json")
    quadros, planos, falas = 0, [], []
    faixa = [np.zeros(TAXA // FPS * 6, dtype=np.float32)]
    for i, fala in enumerate(roteiro):
        voz = locucao(origem_voz / f'{fala["id"]}.mp3')
        abertura = 6 if i == 0 else 0
        segundos = len(voz) / TAXA + fala["pausa"]
        frames = round(segundos * FPS)
        pausa_amostras = frames * TAXA // FPS - len(voz)
        if pausa_amostras < 0:
            raise ValueError(f'Pausa inválida em {fala["id"]}')
        faixa.extend([voz, np.zeros(pausa_amostras, dtype=np.float32)])
        limite = quadros + abertura + frames
        falas.append({"id": fala["id"], "texto": fala["texto"],
                      "inicio_s": round((quadros + abertura) / FPS, 3),
                      "fim_fala_s": round((quadros + abertura) / FPS + len(voz) / TAXA, 3)})
        tomadas = cenas[fala["id"]]
        soma, cursor = 0.0, quadros
        for j, plano in enumerate(tomadas):
            soma += plano["peso"]
            fim = limite if j == len(tomadas) - 1 else quadros + round((frames + abertura) * soma)
            planos.append(dict(plano, inicio=cursor, frames=fim - cursor, abertura=not planos))
            cursor = fim
        quadros = limite
    if quadros > FPS * 120:
        raise ValueError(f"Reel com {quadros / FPS:.2f}s. O limite é 120s.")
    voz = np.concatenate(faixa)
    if len(voz) != quadros * TAXA // FPS:
        raise RuntimeError("A duração da voz não coincide com a das cenas.")
    return planos, falas, voz, quadros


def codificacao(previa, destino):
    return [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22" if previa else "18", "-threads", "2",
        "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-video_track_timescale", "30000", str(destino),
    ]


def renderizar_plano(tarefa):
    plano, destino, previa = tarefa
    w, h = (360, 640) if previa else (720, 1280)
    dw, dh = (w, h) if previa else (1080, 1920)
    escala = f"scale={dw}:{dh}:flags=bicubic:out_color_matrix=bt709,setsar=1"
    comando = ["ffmpeg", "-v", "error", "-y"]
    if "video" in plano:
        entrada = CAPTURAS / plano["video"]
        filtro = (f"setpts=(PTS-STARTPTS)/{plano.get('velocidade', 1)},fps={FPS},"
                  f"{escala},tpad=stop_mode=clone:stop_duration=8")
        subprocess.run([
            *comando, "-ss", str(plano.get("entrada_s", 0)), "-i", str(entrada),
            "-an", "-filter_threads", "1", "-vf", filtro, "-frames:v", str(plano["frames"]),
            *codificacao(previa, destino),
        ], check=True)
        return destino
    comando.extend([
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{w}x{h}", "-framerate", str(FPS),
        "-i", "pipe:0", "-an", "-filter_threads", "1", "-vf", escala, *codificacao(previa, destino),
    ])
    with subprocess.Popen(comando, stdin=subprocess.PIPE) as encoder:
        assert encoder.stdin is not None
        for frame in range(plano["frames"]):
            imagem = quadro(plano, frame, plano["frames"], FPS, w, h)
            encoder.stdin.write(imagem.tobytes())
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError(f"Falha ao exportar {destino.name}")
    return destino


def normalizacao(wav):
    alvo = "loudnorm=I=-15:LRA=9:TP=-1.5"
    medida = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(wav), "-af", f"{alvo}:print_format=json", "-f", "null", "-"],
        check=True, stderr=subprocess.PIPE, text=True,
    ).stderr
    dados = json.loads(medida[medida.rfind("{"):medida.rfind("}") + 1])
    return (f"{alvo}:linear=true:measured_I={dados['input_i']}:measured_LRA={dados['input_lra']}"
            f":measured_TP={dados['input_tp']}:measured_thresh={dados['input_thresh']}"
            f":offset={dados['target_offset']}")


def montar(destino, origem_voz, previa, trabalhadores):
    planos, falas, voz, total = linha_do_tempo(origem_voz)
    destino = destino.resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    print(f"{len(planos)} planos, {len(falas)} trechos de fala, {total / FPS:.2f} segundos", flush=True)
    with tempfile.TemporaryDirectory(prefix="infor-lua-") as tmp:
        pasta = Path(tmp)
        wav = pasta / "mix.wav"
        escrever_wav(wav, trilha(voz, planos, FPS))
        tarefas = [(plano, pasta / f"plano-{i:02d}.mp4", previa) for i, plano in enumerate(planos, 1)]
        with ProcessPoolExecutor(max_workers=trabalhadores) as executor:
            arquivos = []
            for i, caminho in enumerate(executor.map(renderizar_plano, tarefas), 1):
                arquivos.append(caminho)
                print(f"Plano {i:02d}/{len(planos):02d}  {planos[i - 1]['imagem']}", flush=True)
        lista = pasta / "cortes.txt"
        lista.write_text("\n".join(f"file {f.name}" for f in arquivos) + "\n", encoding="utf-8")
        saida = destino.with_name(destino.stem + ".tmp.mp4")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "1", "-i", str(lista),
             "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
             "-af", normalizacao(wav), "-c:a", "aac", "-b:a", "192k", "-ar", str(TAXA),
             "-metadata", f"title={TITULO}", "-metadata:s:a:0", "language=por",
             "-movflags", "+faststart", str(saida)],
            check=True,
        )
        saida.replace(destino)
    metadados = {
        "titulo": TITULO, "duracao_s": round(total / FPS, 3), "quadros_por_segundo": FPS,
        "locucao": "pt-BR-ThalitaMultilingualNeural", "legendas_embutidas": False,
        "cenas": [{**p, "inicio_s": round(p["inicio"] / FPS, 3), "duracao_s": round(p["frames"] / FPS, 3)}
                  for p in planos], "falas": falas,
    }
    destino.with_suffix(".json").write_text(json.dumps(metadados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(destino, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=EPISODIO / "dist" / ARQUIVO)
    parser.add_argument("--voz", type=Path, default=EPISODIO / "assets" / "voz")
    parser.add_argument("--previa", action="store_true")
    parser.add_argument("--trabalhadores", type=int, default=min(4, max(1, (os.cpu_count() or 2) // 2)))
    args = parser.parse_args()
    montar(args.saida, args.voz, args.previa, args.trabalhadores)
