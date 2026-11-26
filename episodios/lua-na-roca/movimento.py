"""Anima corpos, mãos e objetos dentro do quadro, em coordenadas da arte."""

from functools import lru_cache
import json
from math import cos, pi, radians, sin
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


CAMADAS = Path(__file__).resolve().parent / "assets" / "movimento"
PIVOS = json.loads((CAMADAS / "pivos.json").read_text(encoding="utf-8"))


def progressao(u, inicio, fim):
    p = max(0., min(1., (u - inicio) / (fim - inicio)))
    return p * p * (3 - 2 * p)


def ataque(u, entrada, alto, saida, ate):
    return progressao(u, entrada, alto) * (1 - progressao(u, saida, ate))


@lru_cache(maxsize=16)
def placa(nome):
    with Image.open(CAMADAS / f"{nome}.jpg") as imagem:
        return imagem.convert("RGB")


@lru_cache(maxsize=16)
def recorte(nome):
    with Image.open(CAMADAS / f"{nome}.webp") as imagem:
        return imagem.convert("RGBA")


def colar_pivo(fundo, imagem, pivo, posicao, escala=1.0, angulo=0.0):
    """Aplica escala e rotação em torno de um ponto de contato do recorte."""
    w, h = imagem.size
    tamanho = (max(2, round(w * escala)), max(2, round(h * escala)))
    if tamanho != imagem.size:
        imagem = imagem.resize(tamanho, Image.Resampling.BILINEAR)
    px = (pivo[0] / w - .5) * tamanho[0]
    py = (pivo[1] / h - .5) * tamanho[1]
    if abs(angulo) > .05:
        imagem = imagem.rotate(angulo, Image.Resampling.BILINEAR, expand=True)
        giro = radians(angulo)
        px, py = px * cos(giro) + py * sin(giro), -px * sin(giro) + py * cos(giro)
    x = round(posicao[0] - px - imagem.width / 2)
    y = round(posicao[1] - py - imagem.height / 2)
    fundo.paste(imagem, (x, y), imagem)


def colar(fundo, nome, posicao, escala=1.0, angulo=0.0):
    colar_pivo(fundo, recorte(nome), PIVOS[nome], posicao, escala, angulo)


@lru_cache(maxsize=8)
def grade(tamanho):
    w, h = tamanho
    xs = np.append(np.arange(0, w, 23), w)
    ys = np.append(np.arange(0, h, 23), h)
    y, x = np.meshgrid(ys, xs, indexing="ij")
    coordenadas = np.stack([x, y], axis=-1).astype(np.float32)
    caixas = [(int(xs[i]), int(ys[j]), int(xs[i + 1]), int(ys[j + 1]))
              for j in range(len(ys)-1) for i in range(len(xs)-1)]
    return coordenadas, caixas


@lru_cache(maxsize=128)
def influencia(tamanho, x, y, raio_x, raio_y):
    g, _ = grade(tamanho)
    distancia = ((g[:, :, 0] - x) / raio_x)**2 + ((g[:, :, 1] - y) / raio_y)**2
    return np.maximum(0, 1 - distancia)**1.6


def deformar(imagem, controles):
    """Deforma uma malha local com os controles de cada parte articulada."""
    g, caixas = grade(imagem.size)
    malha = g.copy()
    for x, y, rx, ry, dx, dy, giro in controles:
        peso = influencia(imagem.size, x, y, rx, ry)
        malha[:, :, 0] -= (dx - (g[:, :, 1] - y) * giro) * peso
        malha[:, :, 1] -= (dy + (g[:, :, 0] - x) * giro) * peso
    np.clip(malha[:, :, 0], 0, imagem.width, out=malha[:, :, 0])
    np.clip(malha[:, :, 1], 0, imagem.height, out=malha[:, :, 1])
    esquinas = np.concatenate(
        [malha[:-1,:-1], malha[1:,:-1], malha[1:,1:], malha[:-1,1:]], axis=-1
    ).reshape(-1, 8).tolist()
    return imagem.transform(imagem.size, Image.Transform.MESH,
                            list(zip(caixas, esquinas)), Image.Resampling.BILINEAR)


@lru_cache(maxsize=7)
def feijao(indice):
    rng = np.random.default_rng(indice + 67)
    z, x = np.mgrid[-1:1:44j, -1:1:34j].astype(np.float32)
    f = (x + (1 - z*z) * .095)**2 / .72**2 + z*z / .92**2
    alfa = np.clip((1 - f) * 20, 0, 1)
    volume = .57 + .51 * np.sqrt(np.maximum(0, 1 - f))
    volume *= .91 - .12*x - .09*z
    rgb = np.array([170, 102, 64]) if indice % 2 else np.array([203, 150, 97])
    manchas = np.zeros_like(x)
    for _ in range(22):
        cx, cy = rng.uniform(-.77, .77, 2)
        manchas += rng.uniform(.16, .48) * np.exp(
            -((x-cx)/rng.uniform(.04, .115))**2 - ((z-cy)/rng.uniform(.036, .12))**2
        )
    manchas += .29 * np.exp(-((x+.17)/.13)**2 - ((z+.06)/.24)**2)
    c = volume[:, :, None] * rgb - manchas[:, :, None] * np.array([105, 75, 34])
    return Image.fromarray(np.uint8(np.clip(np.dstack([c, alfa * 255]), 0, 255)), "RGBA")


def grao(imagem, x, y, tamanho, giro, indice=0):
    sprite = feijao(indice % 7)
    colar_pivo(imagem, sprite, (17,22), (x,y), tamanho / 44, giro)


def plantar(u, t):
    cena = placa("sulco").copy()
    descer = progressao(u, .02, .46)
    subir = progressao(u, .56, .91)
    x = 261 + 95 * (1 - descer) + 137 * subir
    y = 480 - 542 * (1 - descer) - 534 * subir
    quadro = ImageDraw.Draw(cena, "RGBA")
    queda = max(0, min(1, (u - .54) / .13))
    gx, gy = (x + 4, y + 13) if u < .54 else (264 + 12*queda, 493 + 48*queda**2)
    if u > .11:
        sombra = int(38 * descer * (1 - .64 * subir))
        quadro.ellipse((213, 524, 321, 553), fill=(31, 13, 6, sombra))
        grao(cena, gx, gy, 36, 17 + 52*queda + 4*sin(u*28)*queda, 3)
    if u < .94:
        colar(cena, "muda-semente", (x,y), .91, -12 + 17*descer - 14*subir)
    if .64 < u < .85:
        q = (u-.64) / .21
        for j in range(10):
            sx = 277 + (j - 4.5)*8*q
            sy = 539 - sin(q*pi)*(.8 + j%3)*10
            r = 2 + j%3
            quadro.ellipse((sx-r,sy-r,sx+r,sy+r),fill=(106,61,32,round(188*(1-q))))
    return cena


@lru_cache(maxsize=1)
def destinos_graos():
    rng = np.random.default_rng(86)
    destinos = []
    for j in range(37):
        ang = rng.uniform(0, 2*pi)
        rad = np.sqrt(rng.uniform(0,1))
        destinos.append((247+rad*143*cos(ang), 506+rad*43*sin(ang), rng.uniform(-132,132), rng.uniform(18,33)))
    return destinos


def servir_sementes(u, t):
    cena = placa("tigela").copy()
    retirar = progressao(u, .73, .99)
    baixar = progressao(u, .0, .29)
    tombar = progressao(u, .23, .52)
    pos = (271 - 125*(1-baixar) - 164*retirar, 346 - 350*(1-baixar) - 315*retirar)
    quadro = ImageDraw.Draw(cena, "RGBA")
    quadro.ellipse((122, 480, 348, 556), fill=(44, 24, 14, int(20*tombar)))
    for i, (final_x, final_y, giro, tam) in enumerate(destinos_graos()):
        partida = .32 + i * .0095
        p = (u - partida) / (.15 + (i % 4) * .009)
        if p < 0:
            continue
        arco = max(0, min(1, p))
        x = 269 + (final_x - 269)*arco
        y = 350 + (final_y - 350)*arco**1.72
        quique = max(0, min(1, (p - 1)*1.7))
        y -= sin(quique*pi) * (9 + i%6) * (1-quique)
        if p > .79:
            sombra = max(0, min(1, (p - .79) * 5))
            quadro.ellipse((x-tam*.38,y-1,x+tam*.39,y+tam*.35),
                           fill=(70,31,19,round(77*sombra)))
        grao(cena, x, y, tam, giro + (1-arco)*133, i)
    if u < .99:
        colar(cena, "saco", pos, .74, 15 - 41*tombar + 22*retirar)
    return cena


@lru_cache(maxsize=1)
def vagem():
    w,h = 126,52
    y,x = np.mgrid[0:h, 0:w].astype(np.float32)
    ponto = np.clip((x-6)/(w-11), 0, 1)
    meio = 26 + 11*sin(pi*.1) - 12*np.sin(pi*ponto)
    b = 2.4 + 11*np.maximum(0, np.sin(pi*ponto))**.82
    d = (y-meio)/b
    alfa = np.clip((1 - np.abs(d))*7, 0, 1) * np.clip((x-3)*.5,0,1) * np.clip((w-3-x)*.5,0,1)
    luz = .51 + .53*np.sqrt(np.maximum(0, 1-d*d)) - .18*d
    luz += .055*np.cos(ponto*2*pi*3.2) + np.random.default_rng(441).normal(0,.028,d.shape)
    veia = np.exp(-((d-.31)*10)**2)*.14
    c = np.stack([(luz + veia)*112, (luz+veia)*162, (luz+veia)*48, alfa*255], axis=-1)
    return Image.fromarray(np.uint8(np.clip(c,0,255)),"RGBA")


def pesar(u, t):
    entrada = progressao(u, .02, .37)
    soltar = progressao(u, .46, .67)
    retirar = progressao(u, .53, .94)
    impulso = max(0,u-.65)
    tremor = 4.9 * sin(impulso*43)*np.exp(-impulso*9) if impulso else 0
    cena = deformar(placa("balanca-vazia"),[(252,333,240,130,0,tremor,.007*tremor)])
    sprite = vagem()
    pos = (296+158*(1-entrada)+230*retirar, 192-343*(1-entrada)-292*retirar)
    for i,(x,y,giro,tam) in enumerate([(202,315,-10,1.15),(278,316,12,1.01),(250,302,36,1.08),
                                        (316,304,-5,.92),(180,303,8,.94)]):
        salto = 0 if i < 2 else (1-soltar)
        sx = x if i < 2 else x + (pos[0]-x-25)*salto
        sy = y + tremor if i < 2 else y + tremor + (pos[1]-y+56)*salto
        colar_pivo(cena,sprite,(64,21),(sx,sy),tam,giro+salto*(69-i*3))
    if u < .98:
        colar(cena, "mao-colheita", pos, .76, -10 + 17*entrada - 20*retirar)
    return cena


def brotar(u, t, crescimento):
    cena = placa("solo-broto").copy()
    fase = progressao(u, .03, .76) if crescimento else .8 + .15*progressao(u, .03, .92)
    origem = (253,508)
    altura = 230*fase
    curva = 12*sin(t*2.4)*fase
    ponta = (origem[0]+curva, origem[1]-altura)
    quadro = ImageDraw.Draw(cena,"RGBA")
    if fase > .003:
        linhas = [(origem[0]+curva*(p/20)**2, origem[1]-altura*p/20) for p in range(21)]
        esp = round(19*max(.16,fase)**.46)
        quadro.line(linhas, fill=(71, 92, 27,255), width=max(3,esp), joint="curve")
        quadro.line([(x-esp*.18,y) for x,y in linhas], fill=(159,173,67,200), width=max(2,esp//4), joint="curve")
        folhas = progressao(fase, .13, .93)
        if folhas > .004:
            vento = sin(t*2.5)
            colar(cena, "folha-esquerda", (ponta[0]-4,ponta[1]-5), .88*folhas, -44*(1-folhas)+10*vento)
            colar(cena, "folha-direita", (ponta[0]+1,ponta[1]+4), .78*folhas, 43*(1-folhas)-8*vento)
        if fase < .49:
            raio = 7 + fase*9
            quadro.ellipse((ponta[0]-raio,ponta[1]-raio,ponta[0]+raio,ponta[1]+raio),fill=(146,172,52,245))
    return cena


def riscar(cena, efeito, u):
    inicio, y = (118,402) if efeito == "nota-lunar" else (126,441)
    progresso = progressao(u,.13,.76)
    fim = inicio + 93 + (21 if efeito == "ficha-pronta" else 0)
    pos_x = inicio + (fim-inicio)*progresso
    y_lapis = y - 88*(1-progressao(u,.04,.18)) - 136*progressao(u,.83,1)
    if progresso > 0:
        partes = max(2, round(38*progresso))
        pontos = [(inicio+(pos_x-inicio)*j/(partes-1),
                   y + 2.6*sin((pos_x-inicio)*j/(partes-1)*.26)
                   + 1.1*cos((pos_x-inicio)*j/(partes-1)*.43)) for j in range(partes)]
        pincel = ImageDraw.Draw(cena, "RGBA")
        pincel.line(pontos, fill=(65,65,47,170),width=2)
        if .18 < u < .83:
            y_lapis = pontos[-1][1]
    corre = 57*(1-progressao(u,.03,.13)) + 87*progressao(u,.83,1)
    colar(cena, "lapis", (pos_x-corre,y_lapis), .84, -11 + 4*sin(14*u))


def gesto(imagem, nome, u, t):
    f = ataque(u,.04,.40,.57,.93)
    onda = sin(t*2.1)
    curvar = sin(t*2.9)
    if nome == "prosa":
        controles = [(187,462,137,123,26*f,-52*f,-.20*f),
                     (128,307,148,154,7*f,-9*onda,.10*f),
                     (401,322,106,139,-7*onda,17*f,-.09*f),
                     (124,373,41,33,3*curvar,5*curvar,0)]
    elif nome == "noite":
        controles = [(166,347,132,137,13*f,-23*f,-.11*f),
                     (161,524,178,173,6*f,-12*sin(t*1.8),.035*f),
                     (392,381,129,121,13*onda,6*curvar,.07*onda)]
    elif nome == "colheita":
        controles = [(391,516,171,186,-25*f,-42*f,-.09*f),
                     (214,285,146,152,8*curvar,13*f,.085*f),
                     (207,434,152,137,-12*f,-14*f,.03*onda)]
    elif nome == "anotar":
        controles = [(177,499,128,114,21*onda,6*curvar,-.115*onda),
                     (282,321,156,161,9*f,13*f,.075*f)]
    else:
        controles = [
            (x,y,rx,ry,13*sin(t*2.2 + p),6*sin(t*3.7+p),.072*sin(t*2+p))
            for x,y,rx,ry,p in ((119,250,130,146,.1),(317,275,131,186,1.9),
                               (436,454,104,143,.6),(104,539,103,131,2.9))
        ]
    return deformar(imagem,controles)


def vida_no_campo(imagem, u, t, aves):
    pincel = ImageDraw.Draw(imagem,"RGBA")
    if aves:
        for i in range(4):
            x = -23 + u*465-i*38
            y = 93 + 17*i + sin(u*pi+i)*31
            asa = sin(t*2*pi*3.8+i*1.1) * (7+i)
            pincel.polygon([(x-11,y+asa),(x-3,y-2),(x,y-1),(x+9,y+asa-2),
                            (x+3,y+2),(x,y+5),(x-3,y+2)], fill=(32,40,34,185-i*12))
    else:
        x, y = 97 + 280*u, 540 - 209*u + 33*sin(u*pi*4.2)
        asa = 3.2+8.5*abs(sin(t*2*pi*6.3))
        pincel.ellipse((x-asa,y-8,x+1,y+6),fill=(215,132,49,217))
        pincel.ellipse((x-1,y-6,x+asa,y+7),fill=(237,170,76,226))
        pincel.line((x-1,y+5,x+2,y-6), fill=(45,31,22,255),width=2)


def cena_atuada(nome, efeito, imagem, u, t):
    if nome == "plantio":
        return plantar(u,t)
    if nome == "sementes":
        return servir_sementes(u,t)
    if nome == "balanca":
        return pesar(u,t)
    if nome == "broto":
        return brotar(u,t,efeito == "brotacao")
    if nome in ("noite","prosa","colheita","anotar","canteiros","amanhecer"):
        nova = gesto(imagem,nome,u,t)
        if nome in ("canteiros","amanhecer"):
            vida_no_campo(nova,u,t,aves=nome=="amanhecer")
        return nova
    return imagem
