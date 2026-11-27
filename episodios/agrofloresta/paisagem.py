"""Espécies e faixas de cultivo da agrofloresta."""

from math import cos, pi, sin
from random import Random

from cenografia import agrupar, fio, folha, material, oval, torno


def lamina(nome,pai,mat,nervura,origem,comprimento,largura,curva,rotacao):
    f=agrupar(nome,origem,pai)
    f.rotation_euler=rotacao
    folha("Lâmina",mat,f,comprimento,largura,curva)
    trilha=[]
    for i in range(9):
        u=i/8
        z=curva*(.78*sin(u*pi*.92)-.46*u*u)+.005
        trilha.append((0,u*comprimento,z))
    fio("Nervura central",trilha,.0045,nervura,f)
    return f


def bananeira(local,escala=1,semente=1):
    raiz=agrupar("Bananeira",local)
    raiz.scale=(escala,)*3
    verde=material("Folha de bananeira","507a35","a3a94c",12,.018,.55)
    nervura=material("Nervura de bananeira","638c42","bdbe70",21,.010)
    caule=material("Pseudocaule de bananeira","637740","ad9d60",26,.033)
    bainha=material("Bainha seca","735843","a78f56",26,.029)
    torno("Pseudocaule",[(0,.164),(.048,.165),(.26,.127),(1.13,.112),
                        (1.64,.107),(1.90,.074),(2.13,.048)],caule,raiz,ondulacao=.023)
    for i in range(5):
        a=i*2*pi/5
        f=agrupar("Tira do pseudocaule",(0,0,0),raiz)
        f.rotation_euler.z=a
        fio("Fibra do pseudocaule",[(.146,-.024,.17),(.13,0,.56),(.117,.024,1.13),
             (.104,.042,1.55)],.009,bainha,f)
    folhas=[]
    rng=Random(semente)
    for i in range(8):
        a=i*2*pi/8+rng.uniform(-.17,.17)
        p=agrupar("Pecíolo da banana",(.0,.0,1.78+.059*(i%5)),raiz)
        p.rotation_euler=(.11+.12*(i%4),0,a)
        curv=.30+.07*(i%3)
        fio("Pecíolo",[(0,0,0),(0,.21,.18),(0,.44,.19)],.030,nervura,p)
        f=lamina("Folha larga",p,verde,nervura,(0,.398,.187),1.19+.13*(i%4),.27+.033*(i%3),
                   curv,(.11,0,.0))
        folhas.append((p,p.rotation_euler.copy()))
    return folhas


def cacaueiro(local,escala=1,semente=3):
    raiz=agrupar("Cacaueiro jovem",local)
    raiz.scale=(escala,)*3
    tronco=material("Ramo de cacau","684d37","967346",18,.019)
    verde=material("Folha de cacau","365d38","6e9b4e",20,.014,.53)
    rubra=material("Brotação de cacau","804937","b77a51",21,.009,.50)
    veio=material("Nervura do cacau","8d9b56","a6a968",25,.008)
    fio("Caule de cacau",[(0,0,0),(.013,.037,.24),(-.016,.003,.56),(.037,.016,.94)],.034,tronco,raiz)
    rng=Random(semente)
    folhas=[]
    for i in range(7):
        a=(i*2.39996)%(2*pi)
        p=agrupar("Ramo com folhas",(0,0,.34+i*.083),raiz)
        p.rotation_euler.z=a
        fio("Ramo fino",[(0,0,0),(0,.15,.028),(0,.36,.10)],.012,tronco,p)
        for j in range(3):
            z=.024+.031*j
            f=lamina("Folha elíptica de cacau",p,rubra if i==6 else verde,veio,
                (0,.105+j*.10,z),rng.uniform(.24,.42),rng.uniform(.047,.080),.073,
                (-.36-rng.random()*.24, rng.uniform(-.38,.29),(-1)**j*(.55+.18*j)))
            folhas.append((f,f.rotation_euler.copy()))
    return folhas


def ingazeiro(local,escala=1,semente=5):
    raiz=agrupar("Ingazeiro",local)
    raiz.scale=(escala,)*3
    castanho=material("Casca do ingazeiro","594a38","97866b",18,.039)
    folhas_mats=[material("Copa de ingá verde escura","294d33","63834b",13,.031),
                 material("Copa de ingá verde nova","426742","8caa6a",14,.024)]
    veio=material("Pecíolo de ingá","68854c","a6ad68",27,.018)
    torno("Tronco do ingazeiro",[(0,.20),(.16,.176),(.63,.125),(1.31,.108),
            (2.09,.091),(2.48,.07),(3.06,.035),(3.25,.014)],castanho,raiz,ondulacao=.042)
    rng=Random(semente)
    folhagem=[]
    for i in range(9):
        a=i*2*pi/9+.12*sin(i)
        g=agrupar("Ramo da copa",(0,0,1.71+i*.112),raiz)
        g.rotation_euler.z=a
        z=.53+.12*(i%4)
        fio("Forquilha",[(0,0,0),(0,.48,z*.40),(.053,.93,z),(.081,1.22,z+.13)],
            .072-.004*i,castanho,g)
        for k in range(5):
            b=(-1)**k*(.51+.15*(k%3))
            q=agrupar("Raque do ingá",(.055,.46+.19*k,.22+k*.142),g)
            q.rotation_euler=(.21,.08,b)
            fio("Eixo da folha composta",[(0,0,0),(0,.24,.12),(0,.54,.13)],.007,veio,q)
            for j in range(3):
                for lado in (-1,1):
                    f=lamina("Folíolo do ingá",q,folhas_mats[(i+j)%2],veio,
                        (0,.12+j*.16,.05+j*.037),.24+.026*j,.063+.009*j,.089,
                        (.04,lado*.11,lado*(1.14-.06*j)))
                    if k==4:
                        folhagem.append((f,f.rotation_euler.copy()))
        for k in range(4):
            x=rng.uniform(-.40,.43)
            y=.67+k*.21+rng.uniform(-.09,.11)
            dia=rng.uniform(.35,.52)
            oval("Massa de folhas ao fundo",(x,y,z-.08+.08*k),(dia,dia*1.0,dia*.39),
                 folhas_mats[(i+k)%2],g,1)
    return folhagem


def feijoeiro(local,escala=1,semente=1):
    raiz=agrupar("Feijoeiro na faixa aberta",local)
    raiz.scale=(escala,)*3
    raiz.rotation_euler.z=(semente*2.39996)%(2*pi)
    f=material("Folhas do feijão no campo","3d6e39","8ba851",21,.012,.52)
    n=material("Veios do feijão no campo","789347","b0c17c",18,.009)
    fio("Haste do feijão",[(0,0,0),(.018,-.013,.16),(-.022,0,.37)],.018,n,raiz)
    partes=[]
    for i in range(3):
        z=.226+i*.051
        a=2*pi*i/3
        obj=lamina("Folha do feijoeiro",raiz,f,n,(-.008,.005,z),.29+.023*(i%2),.126,.084,
                   (.087,.17*(-1)**i,a))
        partes.append((obj,obj.rotation_euler.copy()))
    return partes


def vento(partes,t,forca=.06):
    for i,(obj,r) in enumerate(partes):
        obj.rotation_euler.x=r.x+forca*sin(t*1.72+i*.63)+.29*forca*cos(t*2.41+i*.29)
        obj.rotation_euler.y=r.y+.52*forca*sin(t*1.91+i*.61)
