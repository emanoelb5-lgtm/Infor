"""Sobrepõe recortes rígidos e objetos animados a cenários imóveis."""

from functools import lru_cache
import json
from math import cos, pi, radians, sin
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


CAMADAS = Path(__file__).resolve().parent / "assets" / "movimento"
PIVOS = json.loads((CAMADAS / "pivos.json").read_text(encoding="utf-8"))
CURVAS = {nome: np.array(pontos) for nome,pontos in
          json.loads((CAMADAS / "curvas.json").read_text(encoding="utf-8")).items()}


def progressao(u, inicio, fim):
    p = max(0., min(1., (u - inicio) / (fim - inicio)))
    return p * p * (3 - 2 * p)


def pose(nome, tempo):
    pontos = CURVAS[nome]
    posicao = min(1.,max(0.,tempo))*(len(pontos)-1)
    i = int(posicao)
    peso = posicao-i
    return pontos[i]*(1-peso)+pontos[min(i+1,len(pontos)-1)]*peso


@lru_cache(maxsize=12)
def placa(nome):
    with Image.open(CAMADAS / f"{nome}.jpg") as imagem:
        return imagem.convert("RGB")


@lru_cache(maxsize=12)
def recorte(nome):
    with Image.open(CAMADAS / f"{nome}.webp") as imagem:
        return imagem.convert("RGBA")


def colar_pivo(fundo, imagem, pivo, posicao, escala=1.0, angulo=0.0):
    """Aplica a pose em torno do ponto de contato do recorte."""
    w, h = imagem.size
    tamanho = (max(2, round(w * escala)), max(2, round(h * escala)))
    if tamanho != imagem.size:
        imagem = imagem.resize(tamanho, Image.Resampling.LANCZOS)
    px = (pivo[0] / w - .5) * tamanho[0]
    py = (pivo[1] / h - .5) * tamanho[1]
    if abs(angulo) > .05:
        imagem = imagem.rotate(angulo, Image.Resampling.BICUBIC, expand=True)
        giro = radians(angulo)
        px, py = px * cos(giro) + py * sin(giro), -px * sin(giro) + py * cos(giro)
    x = round(posicao[0] - px - imagem.width / 2)
    y = round(posicao[1] - py - imagem.height / 2)
    fundo.paste(imagem, (x, y), imagem)


def colar(fundo, nome, posicao, escala=1.0, angulo=0.0):
    colar_pivo(fundo, recorte(nome), PIVOS[nome], posicao, escala, angulo)


def recorte_animado(nome, tempo):
    quadro = placa(f"{nome}-base").copy()
    x, y, s, giro = pose(nome,tempo)
    colar(quadro,nome,(x,y),s,giro)
    return quadro


@lru_cache(maxsize=8)
def feijao(indice):
    imagem = recorte("graos-blender")
    lado = imagem.height // 2
    x, y = (indice % 4)*lado, (indice // 4)*lado
    return imagem.crop((x,y,x+lado,y+lado))


def grao(cena, x, y, tamanho, giro, indice=0):
    sprite = feijao(indice % 8)
    centro = sprite.width / 2
    colar_pivo(cena,sprite,(centro,centro),(x,y),tamanho/sprite.width,giro)


def sombra(cena, x, y, rx, ry, forca):
    if forca <= 0:
        return
    ImageDraw.Draw(cena,"RGBA").ellipse(
        (x-rx,y-ry,x+rx,y+ry), fill=(39,18,10,min(255,round(forca)))
    )


def plantar(u, solo=False):
    cena = placa("sulco").copy()
    x,y,s,giro = pose("tocar-solo" if solo else "plantar",u)
    if solo:
        contato = progressao(u,.35,.43)*(1-progressao(u,.64,.78))
        sombra(cena,252,518,45,10,34*contato)
        if .58 < u < .79:
            p=(u-.58)/.21
            pincel=ImageDraw.Draw(cena,"RGBA")
            for j in range(7):
                px=250+(j-3)*6*p
                py=505+22*p**2-sin(p*pi)*(10+j%3*3)
                r=1+j%3
                pincel.ellipse((px-r,py-r,px+r,py+r),fill=(132-j*4,69-j*3,42-j*2,145))
    else:
        solta = .53
        queda = min(1.,max(0.,(u-solta)/.155))
        if u < solta:
            px,py=x+2,y+11
        else:
            px,py=262+12*queda,486+48*queda**2
        sombra(cena,274,537,17,5,70*queda)
        grao(cena,px,py,36,10+35*queda,round(queda*3))
    colar(cena,"muda-semente",(x,y),s,giro)
    return cena


@lru_cache(maxsize=1)
def destinos_graos():
    rng = np.random.default_rng(86)
    destinos=[]
    for j in range(33):
        angulo = rng.uniform(0,2*pi)
        raio = np.sqrt(rng.uniform(0,1))
        destinos.append((241+raio*111*cos(angulo),512+raio*37*sin(angulo),
                         rng.integers(8),rng.uniform(-125,125),rng.uniform(22,38)))
    return destinos


def servir_sementes(u):
    cena = placa("tigela").copy()
    sementes=[]
    for i,(x,y,vista,giro,tam) in enumerate(destinos_graos()):
        solta=.365+i*.0089
        if u < solta:
            continue
        origem_x,origem_y,_,_=pose("saco",solta)
        origem_x+=2
        origem_y+=13
        queda = (u-solta)/(.154+.014*(i % 4))
        p=min(1.,queda)
        quique=max(0.,min(1.,(queda-1)*3))
        altura_quique=sin(pi*quique)*(7+i%3)*(1-quique)
        px=origem_x+(x-origem_x)*p
        py=origem_y+(y-origem_y)*p*p-altura_quique
        sementes.append((py,px,tam,giro+210*(1-p),vista+int(queda*4 if queda < 1 else 4),p))
    for py,px,tam,giro,vista,p in sorted(sementes):
        sombra(cena,px+1,py+tam*.13,tam*.27,tam*.15,47*progressao(p,.8,1.))
        grao(cena,px,py,tam,giro,vista)
    x,y,s,giro=pose("saco",u)
    colar(cena,"saco",(x,y),s,giro)
    return cena


@lru_cache(maxsize=1)
def vagem():
    w,h=126,52
    y,x=np.mgrid[0:h,0:w].astype(np.float32)
    ponto=np.clip((x-6)/(w-11),0,1)
    meio=29-13*np.sin(pi*ponto)
    b=1.8+11*np.maximum(0,np.sin(pi*ponto))**.82
    d=(y-meio)/b
    alfa=np.clip((1-np.abs(d))*7,0,1)*np.clip((x-3)*.5,0,1)*np.clip((w-3-x)*.5,0,1)
    luz=.52+.5*np.sqrt(np.maximum(0,1-d*d))-.23*d
    luz+=.057*np.cos(ponto*2*pi*3.2)+np.random.default_rng(441).normal(0,.022,d.shape)
    veia=np.exp(-((d-.42)*13)**2)*.09
    c=np.stack([(luz+veia)*112,(luz+veia)*150,(luz+veia)*52,alfa*255],axis=-1)
    return Image.fromarray(np.uint8(np.clip(c,0,255)),"RGBA")


def pesar(u):
    cena = placa("balanca-vazia").copy()
    x_mao,y_mao,s_mao,giro_mao = pose("vagens",u)
    solta = .46
    x_solto,y_solto,_,_ = pose("vagens",solta)
    sprite=vagem()
    for i,(x,y,giro,s) in enumerate([(201,315,-13,1.06),(286,318,19,.98),
                                      (248,303,44,1.04),(305,303,-7,.85),(186,306,8,.89)]):
        deslocamento = -18 + (i-3)*7
        angulo_inicial = 52 + (i-3)*20
        if i < 2:
            sx,sy,angulo,contato=x,y,giro,1
        elif u < solta:
            sx,sy,angulo,contato=x_mao+deslocamento,y_mao+38,angulo_inicial,0
        else:
            p=max(0.,(u-solta)/(.19 + (i-2)*.016))
            contato=min(1.,p)
            q=max(0.,min(1.,(p-1)*4.2))
            origem_x=x_solto+deslocamento
            sx=origem_x+(x-origem_x)*contato
            sy=y_solto+38+(y-y_solto-38)*contato**2 - 6*sin(q*pi)*(1-q)
            angulo=angulo_inicial+(giro-angulo_inicial)*contato
        sombra(cena,sx,sy+5,45*s,4,45*progressao(contato,.8,1.))
        colar_pivo(cena,sprite,(64,21),(sx,sy),s,angulo)
    colar(cena,"mao-colheita",(x_mao,y_mao),s_mao,giro_mao)
    return cena


def brotar(u):
    cena=placa("sulco").copy()
    x,y,fase,giro=pose("broto",u)
    altura=218*fase
    inclinar=24*sin(radians(giro))
    quadro=ImageDraw.Draw(cena,"RGBA")
    sombra(cena,x+7,y+4,12+fase*10,3,52*fase)
    linhas=[(x+inclinar*(i/26)**2,y-altura*i/26) for i in range(27)]
    esp=round(12*fase**.55)
    quadro.line(linhas,fill=(66,85,25,255),width=max(2,esp),joint="curve")
    quadro.line([(px-esp*.23,py) for px,py in linhas],fill=(150,162,67,210),
                width=max(1,esp//4),joint="curve")
    folha=progressao(fase,.19,1.)
    if folha > .003:
        ponta=linhas[-1]
        colar(cena,"folha-esquerda",(ponta[0]-1,ponta[1]-5),.79*folha,-61*(1-folha)+giro)
        colar(cena,"folha-direita",(ponta[0]+2,ponta[1]+4),.74*folha,47*(1-folha)-giro*.65)
    if fase < .44:
        px,py=linhas[-1]
        r=4+9*fase
        quadro.ellipse((px-r,py-r,px+r,py+r),fill=(119,151,53,250))
    return cena


def riscar(cena, efeito, u):
    ajuste_y={"nota-lunar":-34,"ficha":0,"ficha-pronta":29}[efeito]
    contato_inicio, contato_fim=.19,.775
    x,y,s,giro=pose("lapis",u)
    if u > contato_inicio:
        quantidade=max(2,int((min(u,contato_fim)-contato_inicio)*110))
        pontos=[tuple(pose("lapis",t)[:2]) for t in np.linspace(contato_inicio,min(u,contato_fim),quantidade)]
        desenho=ImageDraw.Draw(cena,"RGBA")
        desenho.line([(px,py+ajuste_y) for px,py in pontos],width=2,fill=(70,62,43,171))
    colar(cena,"lapis",(x,y+ajuste_y),s,giro)
