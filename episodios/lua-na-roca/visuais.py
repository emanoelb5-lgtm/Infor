"""Composição das cenas animadas em um tempo determinado pela montagem."""

from functools import lru_cache
from math import cos, pi, sin
from pathlib import Path
import random

import numpy as np
from PIL import Image, ImageDraw

ARTES = Path(__file__).resolve().parent / "assets" / "imagens"


def limitar(valor, minimo=0, maximo=1):
    return max(minimo, min(maximo, valor))


def suave(valor):
    n = limitar(valor)
    return n * n * (3 - 2 * n)


@lru_cache(maxsize=16)
def arte(nome):
    with Image.open(ARTES / f"{nome}.jpg") as imagem:
        return imagem.convert("RGB")


@lru_cache(maxsize=1)
def esfera():
    """Textura sintética de relevo e normais da face visível da Lua."""
    lado = 384
    y, x = np.mgrid[-1:1:complex(lado), -1:1:complex(lado)].astype(np.float32)
    raio = np.hypot(x, y)
    z = np.sqrt(np.maximum(0, 1 - raio**2))
    rng = np.random.default_rng(371)
    textura = np.full_like(x, 0.69)
    for resolucao, ganho in ((7, 0.30), (20, 0.18), (58, 0.12), (132, 0.10)):
        areia = Image.fromarray(rng.integers(0, 256, (resolucao, resolucao), dtype=np.uint8))
        camada = np.asarray(areia.resize((lado, lado), Image.Resampling.BICUBIC))
        textura += ganho * (camada / 255 - 0.5)
    for cx, cy, r, forca in (
        (-0.31, -0.35, 0.27, 0.18), (0.23, -0.31, 0.21, 0.16),
        (0.44, -0.12, 0.26, 0.16), (0.17, 0.22, 0.20, 0.13),
        (-0.43, 0.10, 0.24, 0.15), (-0.28, 0.38, 0.16, 0.12),
    ):
        textura -= forca * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / r**2)
    for _ in range(110):
        cx, cy = rng.uniform(-0.98, 0.98, 2)
        r = rng.uniform(0.014, 0.11)
        d = np.hypot((x - cx) * (1 + abs(cx) * 0.5), y - cy) / r
        textura += 0.115 * np.exp(-((d - 1) / 0.11) ** 2)
        textura -= rng.uniform(0.025, 0.13) * np.exp(-d**3)
    textura += rng.normal(0, 0.012, x.shape)
    alfa = np.clip((1.001 - raio) * lado * 0.55, 0, 1)
    return x, y, z, np.maximum(textura, 0.1), alfa


@lru_cache(maxsize=96)
def lua(passo):
    """Ilumina a esfera, da Lua nova à próxima nova, em 360 passos."""
    x, y, z, albedo, alfa = esfera()
    angulo = passo / 360 * 2 * pi
    lado = -sin(angulo)
    sol = np.maximum(0, lado * (0.94 * x - 0.342 * y) - cos(angulo) * z)
    escuro = albedo * (19 + 14 * z)
    luz = albedo * 307 * sol**0.39
    canais = np.stack(
        [escuro * 0.73 + luz, escuro * 0.94 + luz * 0.863, escuro * 1.26 + luz * 0.694, alfa * 255],
        axis=-1,
    )
    return Image.fromarray(np.uint8(np.clip(canais, 0, 255)), "RGBA")


@lru_cache(maxsize=96)
def disco(passo, diametro):
    return lua(passo).resize((diametro, diametro), Image.Resampling.LANCZOS)


@lru_cache(maxsize=20)
def halo(diametro, forca):
    y, x = np.mgrid[-1:1:complex(diametro), -1:1:complex(diametro)].astype(np.float32)
    intensidade = np.exp(-(x * x + y * y) * 4.8) * forca
    pixels = np.zeros((diametro, diametro, 4), dtype=np.uint8)
    pixels[:, :, :3] = (225, 193, 140)
    pixels[:, :, 3] = intensidade
    return Image.fromarray(pixels, "RGBA")


def inserir(imagem, camada, x, y):
    xy = (round(x - camada.width / 2), round(y - camada.height / 2))
    imagem.paste(camada, xy, camada)


def inserir_lua(imagem, fase, x, y, diametro, brilho=True):
    passo = round((fase % 1) * 360) % 360
    diametro = max(12, int(diametro) // 2 * 2)
    if brilho:
        forca = 7 + round(22 * (1 - cos(fase * 2 * pi)) / 2)
        inserir(imagem, halo(diametro * 2, forca), x, y)
    inserir(imagem, disco(passo, diametro), x, y)


@lru_cache(maxsize=4)
def fundo_ceu(w, h):
    y, x = np.mgrid[0:1:complex(h), 0:1:complex(w)].astype(np.float32)
    azul = np.exp(-((x - 0.38) ** 2 * 5 + (y - 0.62) ** 2 * 10))
    bruma = np.exp(-((y - 0.76 + x * 0.18) * 9) ** 2) * 0.65
    pixels = np.stack([4 + azul * 7 + bruma * 7, 10 + azul * 16 + bruma * 8, 20 + azul * 20 + bruma * 11], axis=-1)
    pixels += np.random.default_rng(87).uniform(0, 1.4, (h, w, 1))
    return Image.fromarray(np.uint8(np.clip(pixels, 0, 255)), "RGB")


@lru_cache(maxsize=8)
def pontos(semente, quantidade):
    gerador = random.Random(semente)
    return [(gerador.random(), gerador.random(), gerador.random(), gerador.random()) for _ in range(quantidade)]


def pintar_ceu(plano, u, t, w, h):
    imagem = fundo_ceu(w, h).copy()
    pincel = ImageDraw.Draw(imagem, "RGBA")
    for x, y, luz, vel in pontos(330, 190):
        px = ((x + t * (0.0015 + vel * 0.0018)) % 1) * w
        py = ((y + t * 0.0019) % 1) * h
        r = 0.55 + 0.85 * luz**3
        alfa = int(26 + 168 * luz * (0.78 + 0.22 * sin(t * (2 + vel) + luz * 45)))
        pincel.ellipse((px - r, py - r, px + r, py + r), fill=(208, 227, 224, alfa))
    if plano == "quatro-fases":
        fases = (0, 0.25, 0.5, 0.75)
        for i, fase in enumerate(fases):
            foco = suave((u - i * 0.157) * 11)
            x = (0.19 + 0.206 * i) * w
            y = (0.48 + sin(i * 1.05) * 0.033 + (1 - foco) * 0.07) * h
            d = w * (0.095 + foco * 0.06)
            inserir_lua(imagem, fase * foco, x, y, d)
            if i == 0:
                raio = d / 2
                pincel.ellipse((x - raio, y - raio, x + raio, y + raio), outline=(120, 147, 159, round(110 * foco)), width=max(1, w // 400))
        pincel.arc((w * 0.16, h * 0.42, w * 0.84, h * 0.68), 14, 163, fill=(115, 153, 156, 57), width=max(1, w // 320))
    else:
        fase = suave(u)
        cx, cy = w * 0.5, h * 0.46
        d = w * (0.54 + 0.07 * sin(u * pi))
        rx, ry = w * 0.367, h * 0.227
        caixa = (cx - rx, cy - ry, cx + rx, cy + ry)
        pincel.ellipse(caixa, outline=(158, 188, 188, 48), width=max(1, w // 370))
        for i in range(28):
            theta = -pi / 2 + i * 2 * pi / 28
            px, py = cx + rx * cos(theta), cy + ry * sin(theta)
            tam = 2.5 if i % 7 == 0 else 1.1
            pincel.ellipse((px - tam, py - tam, px + tam, py + tam), fill=(219, 204, 155, 143 if i % 7 == 0 else 71))
        angulo = -pi / 2 + fase * 2 * pi
        px, py = cx + rx * cos(angulo), cy + ry * sin(angulo)
        inserir(imagem, halo(max(18, w // 16), 92), px, py)
        r = max(3, w / 170)
        pincel.ellipse((px - r, py - r, px + r, py + r), fill=(255, 215, 162, 240))
        inserir_lua(imagem, fase, cx, cy, d)
    return imagem


def tela_camera(imagem, camera, u, w, h):
    zo, xo, yo, zf, xf, yf = camera
    passo = u + sin(u * pi * 2) * 0.038
    z = zo + (zf - zo) * passo
    cw = min(imagem.width, imagem.height * w / h) / z
    ch = cw * h / w
    x = limitar((xo + (xf - xo) * passo) * imagem.width - cw / 2, 0, imagem.width - cw)
    y = limitar((yo + (yf - yo) * passo) * imagem.height - ch / 2, 0, imagem.height - ch)
    return imagem.transform((w, h), Image.Transform.AFFINE, (cw / w, 0, x, 0, ch / h, y), Image.Resampling.BILINEAR)


def pintar_ficha(imagem, efeito, u):
    pincel = ImageDraw.Draw(imagem, "RGBA")
    simbolos = [(107, 293, "data"), (181, 293, "lua"), (107, 381, "feijao"),
                (181, 381, "canteiro"), (327, 309, "chuva"), (397, 309, "manejo")]
    if efeito == "nota-lunar":
        simbolos = [(154, 339, "lua")]
    for i, (x, y, simbolo) in enumerate(simbolos):
        força = 1 if efeito == "ficha-pronta" else suave((u - i * 0.118 - 0.03) * 8)
        if força == 0:
            continue
        tinta = (51, 65, 53, round(214 * força))
        pincel.ellipse((x - 30, y - 30, x + 30, y + 30), outline=(*tinta[:3], round(86 * força)), width=1)
        if simbolo == "lua":
            pincel.arc((x - 14, y - 14, x + 14, y + 14), 0, 360, fill=tinta, width=2)
            pincel.pieslice((x - 12, y - 12, x + 12, y + 12), 90, 270, fill=tinta)
        elif simbolo == "data":
            pincel.rounded_rectangle((x - 14, y - 12, x + 14, y + 13), radius=3, outline=tinta, width=2)
            pincel.line((x - 12, y - 5, x + 13, y - 5), fill=tinta, width=2)
            for dx in (-6, 5):
                pincel.line((x + dx, y - 16, x + dx, y - 9), fill=tinta, width=2)
                pyn = y + 2
                pincel.ellipse((x + dx - 1, pyn - 1, x + dx + 1, pyn + 1), fill=tinta)
        elif simbolo == "feijao":
            pincel.ellipse((x - 15, y - 9, x - 1, y + 11), outline=tinta, width=2)
            pincel.ellipse((x + 1, y - 13, x + 14, y + 6), outline=tinta, width=2)
            pincel.arc((x - 13, y - 6, x - 4, y + 7), 65, 259, fill=tinta, width=2)
            pincel.arc((x + 4, y - 10, x + 11, y + 4), 65, 259, fill=tinta, width=2)
        elif simbolo == "canteiro":
            pincel.line((x - 16, y + 10, x + 11, y + 10, x + 16, y - 11, x - 10, y - 11, x - 16, y + 10), fill=tinta, width=2)
            pincel.line((x - 8, y + 8, x - 2, y - 9), fill=tinta, width=2)
            pincel.line((x + 2, y + 8, x + 8, y - 9), fill=tinta, width=2)
        elif simbolo == "chuva":
            pincel.arc((x - 9, y - 15, x + 9, y + 1), 178, 343, fill=tinta, width=2)
            pincel.arc((x - 16, y - 7, x + 1, y + 5), 30, 255, fill=tinta, width=2)
            pincel.arc((x + 1, y - 7, x + 16, y + 5), 280, 510, fill=tinta, width=2)
            for dx in (-10, 0, 10):
                pincel.line((x + dx + 2, y + 7, x + dx - 2, y + 13), fill=tinta, width=2)
        else:
            pincel.line((x - 14, y + 12, x + 6, y - 8), fill=tinta, width=3)
            pincel.line((x - 3, y - 14, x + 14, y + 3), fill=tinta, width=3)


@lru_cache(maxsize=1)
def marca():
    with Image.open(ARTES / "agrohere.png") as arquivo:
        imagem = arquivo.convert("RGBA").resize((107, 107), Image.Resampling.LANCZOS)
    mascara = Image.new("L", imagem.size)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, 106, 106), radius=23, fill=255)
    imagem.putalpha(mascara)
    return imagem.rotate(-6, Image.Resampling.BICUBIC, expand=True)


def tela_celular(imagem, efeito, u):
    y = 327
    if efeito == "marca":
        icone = marca()
        alfa = suave(u * 4 + 0.15)
        if alfa < 1:
            icone = icone.copy()
            icone.putalpha(icone.getchannel("A").point(lambda p: round(p * alfa)))
        inserir(imagem, halo(186, 21), 268, y)
        inserir(imagem, icone, 268, y)
        return
    for i, (dx, dy) in enumerate(((-29, -33), (24, -29), (-32, 24), (21, 28))):
        avanço = suave((u - i * 0.12) * 5 + 0.22)
        inserir_lua(imagem, avanço * i / 4, 268 + dx, y + dy, 33, brilho=False)


@lru_cache(maxsize=4)
def atmosfera(w, h):
    y, x = np.mgrid[-1:1:complex(h // 4), -1:1:complex(w // 4)]
    densidade = np.exp(-(y * (2 + 0.45 * cos(pi / 8))) ** 2 - (x * 1.65) ** 2)
    pixels = np.zeros((*densidade.shape, 4), dtype=np.uint8)
    pixels[:, :, :3] = (252, 204, 157)
    pixels[:, :, 3] = np.uint8(densidade * 29)
    return Image.fromarray(pixels, "RGBA").resize((w, h), Image.Resampling.BILINEAR)


def ambiente(imagem, efeito, t, u, w, h):
    pincel = ImageDraw.Draw(imagem, "RGBA")
    if efeito in ("chuva", "poeira", "sementes", "lampiao", "luar", "luar-final"):
        chuva = efeito == "chuva"
        dia = efeito == "poeira"
        for x, y, s, v in pontos(71 if chuva else 91, 76 if chuva else 23):
            px = (x + sin(t * 0.48 + y * 8) * 0.02 - (0.10 * t if chuva else 0)) % 1 * w
            py = (y + t * ((0.41 + v * 0.73) if chuva else (0.036 + 0.026 * v))) % 1 * h
            if chuva:
                comprimento = (9 + s * 29) * h / 1280
                pincel.line((px + comprimento * 0.19, py, px, py + comprimento), fill=(211, 232, 217, int(16 + 50 * s)), width=1 if s < 0.84 else 2)
            elif (dia and py > h * 0.69) or (not dia and py < h * 0.77):
                raio = (0.7 + s * 2.5) * w / 720
                brilho = round((19 + 79 * s) * (0.56 + 0.44 * sin(v * 72 + t * 2.7) ** 2))
                pincel.ellipse((px - raio, py - raio, px + raio, py + raio), fill=(246, 194, 121, brilho))
    if efeito == "neblina":
        for i in range(2):
            camada = atmosfera(w, h // (5 + i))
            inserir(imagem, camada, w * (0.31 + 0.35 * i + 0.11 * sin(t * 0.33 + i)), h * (0.48 + 0.13 * i))
    if efeito == "sombra":
        sombra = atmosfera(w, h // 2).getchannel("A")
        camada = Image.new("RGBA", sombra.size, (38, 64, 47))
        camada.putalpha(sombra)
        inserir(imagem, camada, w * (0.42 + u * 0.06), h * 0.48)


def quadro(plano, frame, total, fps, w, h):
    u = frame / max(1, total - 1)
    t = frame / fps
    efeito = plano.get("efeito", "")
    nome = plano["imagem"]
    if nome == "ceu":
        imagem = pintar_ceu(efeito, u, t, w, h)
    else:
        base = arte(nome)
        if nome in ("noite", "caderno", "celular"):
            base = base.copy()
            if nome == "noite":
                inserir_lua(base, 0.43 + 0.012 * sin(t * 0.45), 342 - t, 155 + t * 0.55, 105)
            elif nome == "caderno":
                pintar_ficha(base, efeito, u)
            else:
                tela_celular(base, efeito, u)
        camera = plano.get("camera", [1, 0.5, 0.5, 1.08, 0.5, 0.5])
        imagem = tela_camera(base, camera, u, w, h)
        ambiente(imagem, efeito, t, u, w, h)
    intensidade = 1.0
    if plano.get("abertura"):
        intensidade = 0.78 + 0.22 * suave(t / 0.44)
    if efeito == "luar-final":
        intensidade = suave((total - 1 - frame) / (fps * 0.90))
    if intensidade < 1:
        imagem = Image.blend(Image.new("RGB", (w, h), (4, 10, 15)), imagem, intensidade)
    return imagem
