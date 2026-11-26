"""Trilha instrumental e sons ambientes sintetizados localmente."""

from math import pi
from pathlib import Path
import subprocess
import wave

import numpy as np

TAXA = 48000


def locucao(caminho: Path):
    resultado = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(caminho), "-af", "highpass=f=74",
         "-ar", str(TAXA), "-ac", "1", "-f", "f32le", "pipe:1"],
        check=True, stdout=subprocess.PIPE,
    )
    sinal = np.frombuffer(resultado.stdout, dtype=np.float32)
    janela = TAXA // 100
    rms = np.sqrt(np.mean(sinal[:len(sinal) // janela * janela].reshape(-1, janela)**2, axis=1))
    indices = np.flatnonzero(rms > 0.007)
    if not len(indices):
        raise ValueError(f"Locução vazia em {caminho.name}")
    inicio = max(0, int(indices[0] - 6) * janela)
    fim = min(len(sinal), int(indices[-1] + 14) * janela)
    trecho = sinal[inicio:fim].copy()
    borda = TAXA // 120
    trecho[:borda] *= np.linspace(0, 1, borda, endpoint=False)
    trecho[-borda:] *= np.linspace(1, 0, borda)
    return trecho


def tempo(segundos):
    return np.arange(round(TAXA * segundos), dtype="float32") / TAXA


def freq(nota):
    return 440 * 2**((nota - 69) / 12)


def corda(nota, duracao, suavidade):
    t = tempo(duracao)
    a = t * (2 * pi * freq(nota))
    ataque = np.minimum(1, t / 0.014)
    saida = np.minimum(1, (duracao - t) / 0.16)
    fundamental = np.sin(a) * np.exp(-t * 0.69)
    harmonia = 0.35 * np.sin(2.002 * a + 0.2) * np.exp(-t * 1.9)
    detalhe = 0.13 * np.sin(3.006 * a - 0.7) * np.exp(-t * 3.8)
    madeira = 0.045 * np.sin(4.012 * a) * np.exp(-t * 13)
    return ((fundamental + harmonia + detalhe + madeira) * ataque * saida * suavidade).astype(np.float32)


def colocar(destino, sinal, segundos, pan):
    inicio = max(0, round(segundos * TAXA))
    tamanho = min(len(sinal), len(destino) - inicio)
    if tamanho <= 0:
        return
    destino[inicio:inicio + tamanho, 0] += sinal[:tamanho] * np.cos((pan + 1) * pi / 4)
    destino[inicio:inicio + tamanho, 1] += sinal[:tamanho] * np.sin((pan + 1) * pi / 4)


def ruido(rng, duracao, taxa):
    n = round(duracao * TAXA)
    pontos = max(2, round(duracao * taxa))
    return np.interp(np.arange(n), np.linspace(0, n - 1, pontos), rng.normal(0, 1, pontos)).astype(np.float32)


def trilha(voz, planos, fps):
    """Mistura a voz à trilha, com o ambiente ligado aos planos."""
    rng = np.random.default_rng(29)
    n = len(voz)
    duracao = n / TAXA
    musica = np.zeros((n, 2), dtype=np.float32)
    acordes = [(45, 57, 60, 64, 71), (41, 53, 57, 60, 64),
               (48, 55, 60, 64, 69), (43, 55, 57, 62, 67)]
    padroes = ((0.0, 0), (0.52, 2), (1.23, 3), (2.13, 4), (2.89, 2))
    compasso = 3.25
    for b in range(int(duracao / compasso) + 1):
        acorde = acordes[b % len(acordes)]
        for deslocamento, i in padroes:
            if b % 4 == 1 and i == 4:
                continue
            volume = (0.042 if i == 0 else 0.025) * (0.87 + rng.random() * 0.25)
            instante = 0.14 + b * compasso + deslocamento + rng.uniform(-0.032, 0.032)
            pan = -0.22 if i % 2 == 0 else 0.27
            nota = corda(acorde[i], 2.62 if i == 0 else 1.93, volume)
            colocar(musica, nota, instante, pan)
            colocar(musica, nota * 0.18, instante + 0.108, -pan)
        if b % 4 == 3:
            ping = corda(acorde[3] + 12, 2.0, 0.012)
            colocar(musica, ping, b * compasso + 1.76, 0.52)
        t = tempo(3.37)
        envelope = np.sin(np.minimum(1, t / 3.37) * pi)**1.6
        f = freq(acorde[0] + 12)
        corpo = (np.sin(2 * pi * f * t) + 0.46 * np.sin(2 * pi * f * 1.499 * t)) * envelope
        colocar(musica, corpo * 0.0095, b * compasso, -0.3)

    ambiente = np.zeros_like(musica)
    for plano in planos:
        efeito = plano.get("efeito", "")
        imagem = plano["imagem"]
        inicio = plano["inicio"] / fps
        d = plano["frames"] / fps
        if efeito == "chuva":
            t = tempo(d)
            chuva = (ruido(rng, d, 7600) * 0.0046 + ruido(rng, d, 1750) * 0.004)
            chuva *= np.minimum(1, t / 0.34) * np.minimum(1, (d - t) / 0.25)
            colocar(ambiente, chuva, inicio, -0.29)
            colocar(ambiente, chuva * 0.33, inicio + 0.013, 0.61)
        elif imagem in ("noite", "prosa"):
            for k in range(max(1, round(d * 1.4))):
                t = tempo(0.155)
                batida = np.sin(2 * pi * (2940 + rng.uniform(-420, 360)) * t)
                envelope = np.sin(pi * t / 0.155)**2 * (0.55 + 0.45 * np.sin(t * 2 * pi * 38)**2)
                colocar(ambiente, batida * envelope * 0.007, inicio + k * 0.68 + 0.2, rng.uniform(-0.55, 0.55))
        elif imagem in ("sementes", "balanca", "anotar"):
            duracao_toque = 0.28 if imagem == "anotar" else 0.13
            t = tempo(duracao_toque)
            for k in range(3):
                tom = np.sin(2 * pi * (380 + k * 82) * t)
                toque = (tom * 0.005 + ruido(rng, duracao_toque, 2400) * 0.006) * np.exp(-t * 30)
                colocar(ambiente, toque, inicio + 0.33 + k * 0.13, 0.16)
        elif imagem == "amanhecer":
            t = tempo(0.31)
            envoltoria = np.sin(pi * t / 0.31)**2
            canto = np.sin(2 * pi * (1346 * t + 2280 * t**2)) * envoltoria * 0.009
            colocar(ambiente, canto, inicio + 0.26, -0.56)
            colocar(ambiente, canto * 0.63, inicio + 0.52, -0.47)

    tamanho = TAXA // 10
    envelope = np.sqrt(np.mean(voz[:n // tamanho * tamanho].reshape(-1, tamanho)**2, axis=1))
    reducao = np.clip(envelope * 7, 0, 0.42)
    trilha_final = musica * (1 - np.interp(np.arange(n), np.arange(len(reducao)) * tamanho, reducao))[:, None]
    trilha_final += ambiente
    rampa = min(n // 2, round(TAXA * 1.45))
    trilha_final[-rampa:] *= np.linspace(1, 0, rampa)[:, None]**1.6
    trilha_final[:TAXA // 8] *= np.linspace(0, 1, TAXA // 8)[:, None]
    trilha_final += voz[:, None] * 0.82
    return trilha_final


def escrever_wav(caminho, mix):
    with wave.open(str(caminho), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(TAXA)
        wav.writeframes((np.clip(mix, -0.999, 0.999) * 32767).astype("<i2").tobytes())
