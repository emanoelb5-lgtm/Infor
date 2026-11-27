"""Tomadas da agrofloresta, com a equipe de personagens do primeiro episódio."""

from math import cos, exp, pi, sin
from random import Random

from mathutils import Vector

from cenas import camera, mover_tempo, regime
from cenografia import (agrupar, caixa, ceu, cesto, feijao, fio, folha, gravar, iluminacao,
                        madeira, malha, mata, material, mesa, oval, pano, raio_sol, terreno)
from contatos import levantar_mao, trajeto
from germinacao import corte
from paisagem import bananeira, cacaueiro, feijoeiro, ingazeiro, vento
from personagens import Braco, Mao, Pessoa, coordenadas, transformar


def campo(*, pessoas=False, denso=False):
    ceu(False)
    solo=terreno(y_fundo=20,canteiro=True,limpar=((-0.65,-.21,.43),(.65,-.20,.43)))
    borda=mata()
    if pessoas:
        pos_banana=(1.42,2.66,1.08)
        pos_cacau=(1.10,1.45,.83)
        pos_inga=(-1.91,4.58,1.05)
    else:
        pos_banana=(.86,3.18,1.16)
        pos_cacau=(1.03,1.81,1.0)
        pos_inga=(-1.22,5.19,1.27)
    def colocar(funcao,pos):
        x,y,e=pos
        return funcao((x,y,solo(x,y)),e)
    banana=colocar(bananeira,pos_banana)
    cacau=colocar(cacaueiro,pos_cacau)
    inga=colocar(ingazeiro,pos_inga)
    if denso:
        banana+=colocar(bananeira,(2.79,5.36,.91))
        cacau+=colocar(cacaueiro,(-.03,4.75,1.10))
    feijoes=[]
    for i in range(19):
        x=-1.28+(i%3)*.62
        y=-.93+(i//3)*.81
        if pessoas and i in (1,2,4,5,7,8):
            continue
        feijoes+=feijoeiro((x,y,solo(x,y)),.52+.12*(i%4),i*13+2)
    return solo,borda,banana,cacau,inga,feijoes


def entrada():
    iluminacao("dia",(0,.16,1.23))
    raio_sol("Luz quente no canteiro",(2.4,-2.96,3.81),(0,.75,1.32),190,(1,.87,.67),3.3)
    nivel,borda,banana,cacau,inga,feijoes=campo(pessoas=True)
    a=Pessoa("Dona Luzia",(-.68,.48,.056),velha=True,escala=.96)
    b=Pessoa("Rafael",(.58,.52,.044),escala=.94)
    cesto((-1.3,.96,nivel(-1.3,.96)+.012),.52,alca=True)
    g=feijao("Feijão que Rafael carrega",(0,0,0),.059,2)
    cam=camera(9)

    def animar(t,u):
        passo=regime(u,.015,.44)
        a.raiz.location=(-.68+.058*passo,.61-.185*passo,.056)
        b.raiz.location=(.62-.029*passo,.70-.262*passo,.049)
        aponta=regime(u,.26,.66)
        a.pose(t,giro=.18,olhar=(.34+.26*aponta,-.10-.15*aponta),
               esquerda=(-.32,-.29,.078),direita=(.43,-.31,.28+.36*aponta),
               aperto=(.36,.26),apontar=.69*aponta,
               passo=passo*.86 if u<.44 else 0,apoio=nivel)
        b.pose(t+.38,giro=-.34,olhar=(-.37,.14-.23*regime(u,.34,.82)),
               esquerda=(-.34,-.34,.35+.22*regime(u,.20,.48)),direita=(.42,-.14,.026),
               aperto=(.18,.48),rumos=((-.31,-.86,.55),None),
               passo=passo*.76 if u<.44 else 0,apoio=nivel)
        mao=b.bracos[0][2]
        g.location=transformar(mao.raiz,(.006,-.057,.174))
        g.rotation_euler=(.03,-.14,-.12)
        vento(banana,t,.045)
        vento(cacau,t,.036)
        vento(inga,t,.025)
        vento(feijoes,t,.038)
        borda[1].rotation_euler.x=.025*sin(t*1.8)
        cam((.69-.49*u,-6.15+.54*u,2.43+.081*u),(0.03,.30,2.02),4.46,foco=(0,.43,1.85))
    return animar


def desenho():
    iluminacao("varanda",(0,0,1.02))
    mesa((0,0,0),8.75,9.30,.78)
    base=.845
    t=material("Solo da maquete","5e3f2d","9b7151",28,.025,.86)
    margem=material("Madeira clara da maquete","795837","c19763",15,.018,veio=True)
    caixa("Maquete de madeira",(0,0,base+.078),(2.46,2.94,.151),margem,.058)
    caixa("Terra da maquete",(0,0,base+.172),(2.31,2.79,.116),t,.054)
    caminho=material("Caminho de pedrisco","ad8c68","d4b28b",39,.014,.84)
    fio("Caminho da maquete",[(.43,-1.15,1.078),(.32,-.60,1.078),(.32,.05,1.078),
        (.25,.54,1.078),(.41,1.10,1.078)],.051,caminho)
    banana=bananeira((.69,.21,1.077),.19,9)
    cacao=cacaueiro((.83,-.31,1.077),.28,2)
    inga=ingazeiro((-.48,.81,1.077),.18,12)
    campos=[]
    for i in range(12):
        x=-.91+(i%3)*.28
        y=-.95+(i//3)*.29
        campos+=feijoeiro((x,y,1.079),.208,i*5+3)
    art=material("Madeira das placas","d1b27a","e8d2a4",32,.01)
    letras=material("Marcação verde","3d5241","64735a",32,.007)
    for mensagem,x,y in (("FEIJÃO",-.88,-1.20),("CACAU",.56,-.71),("INGÁ",-.83,1.08)):
        caixa("Placa da maquete",(x+.16,y+.043,1.084),(.39,.134,.019),art,.012)
        gravar("Nome da faixa",mensagem,(x,y+.015,1.097),letras,tamanho=.069)
    poste=agrupar("Marcador da faixa de plantio")
    caixa("Haste do marcador",(0,0,.15),(.039,.037,.30),madeira(),.008,poste)
    pano_m=material("Marcador verde esmeralda","376b4b","729758",29,.012)
    malha("Sinal do marcador",[(0,.001,.221),(.174,.001,.22),(.16,.001,.306),(0,.001,.318)],
          [(0,1,2,3)],pano_m,poste).modifiers.new("Espessura","SOLIDIFY").thickness=.005
    pele=material("Pele de Rafael","815039","c1885c",34,.006,.66)
    mao=Mao("Mão que posiciona o marcador",pele,escala=.87)
    braco=Braco(pele,pano("966735","c39758"),pano("ad7545","daa766"),None)
    cam=camera(7.4)

    def animar(t,u):
        descida=regime(u,.20,.61)
        fim=regime(u,.65,.98)
        poste.location=(.26-.52*descida,-.54-.27*descida,1.079+.34*(1-descida))
        poste.rotation_euler.y=.33*(1-descida)
        pega=transformar(poste,(0,-.017,.235))
        alvo=pega+Vector((.56*fim,-.32*fim,.37*fim))
        rumo=(-.76,.52,-.40)
        p=mao.punho(alvo,rumo,.31)
        mao.pose(p,rumo,.53-.42*fim,giro=.31)
        braco.pose(Vector((2.37,-1.76,2.4)),Vector((1.31,-1.29,1.86)),p)
        vento(banana,t,.033)
        vento(cacao,t,.027)
        vento(inga,t,.021)
        vento(campos,t,.031)
        cam((.13-.28*u,-2.87+.36*u,4.73),(-.08,-.02,1.19),3.98,foco=(0,-.02,1.3))
    return animar


def faixas():
    iluminacao("dia",(0,1.1,1.08))
    nivel,borda,banana,cacau,inga,feijoes=campo(denso=True)
    raio_sol("Faixa aberta ao sol",(-3.8,-3,4.3),(-.72,.4,.22),464,(1,.87,.52),2.8)
    cam=camera(8.5)
    def animar(t,u):
        vento(banana,t,.066)
        vento(cacau,t,.045)
        vento(inga,t,.038)
        vento(feijoes,t,.045)
        borda[1].rotation_euler.x=.045*sin(t*1.9)
        c=regime(u,.04,.94)
        cam((1.46-2.44*c,-6.65+.63*c,2.63+.35*c),
            (-.23+.43*c,2.01,1.64+.27*c),4.96,foco=(.30,1.94,1.2))
    return animar


def semeadura():
    iluminacao("dia",(-.03,0,.84))
    ceu(False)
    mata()
    mat=material("Solo de semeadura","4d3020","a56b49",34,.043,.86)
    agregado=material("Torrões da semeadura","67452f","b07a52",35,.037)
    pel=material("Pele de Rafael","815039","c1885c",34,.006,.66)
    mao=Mao("Rafael semeando",pel,escala=1.18)
    braco=Braco(pel,pano("966735","c39758"),pano("ad7545","daa766"),None)
    pos=Vector((-.19,-.22,0))
    n=84
    amostra=[(-4.2+8.4*i/n,-4.6+12.1*j/n) for j in range(n+1) for i in range(n+1)]
    faces=[]
    for j in range(n):
        for i in range(n):
            q=j*(n+1)+i
            faces.extend(((q,q+1,q+n+2),(q,q+n+2,q+n+1)))
    def altura(x,y,tampa=0):
        ruido=.025*cos(4.29*x+1.18*y)+.018*sin(5.61*x-4.32*y)
        k=((x-pos.x)/.37)**2+((y-pos.y)/.25)**2
        return ruido-(.165-.157*tampa)*exp(-2.05*k)
    malha_solo=malha("Cova aberta em solo fofo",[(x,y,altura(x,y)) for x,y in amostra],faces,mat,suave=True)
    cesto((.96,.41,altura(.96,.41)+.022),.57)
    rng=Random(47)
    pedriscos=[]
    for i in range(84):
        x,y=rng.uniform(-1.92,1.9),rng.uniform(-2.8,2.9)
        r=rng.uniform(.012,.059)
        if i<24:
            x=pos.x+rng.uniform(.31,.63)
            y=pos.y+rng.uniform(-.27,.29)
        if abs(x-pos.x)<.135 and abs(y-pos.y)<.122:
            continue
        o=oval("Terra solta",(0,0,0),(r,r*.77,r*.59),agregado,detalhe=1)
        o.rotation_euler=(i*.23,i*.14,i*.11)
        pedriscos.append((o,x,y,r,i<24))
    gr=feijao("Semente da agrofloresta",(0,0,0),.090,1)
    cam=camera(5.8)

    def gesto(u):
        p=mover_tempo(u,[(0,(.70,.20,1.19)),(.28,(.27,-.03,.56)),(.395,(.09,-.069,.458)),
                         (.54,(.31,-.05,.69)),(.65,(.61,-.035,.47)),(.85,(.10,-.071,.36)),
                         (1,(.38,.10,.65))])
        abre=regime(u,.333,.47)
        mao.pose(p,(-.80,-.36,-.42),.69-.55*abre,giro=.46+.40*abre)
        return p

    solta=.412
    gesto(solta)
    local=(.014,-.098,.158)
    largada=transformar(mao.raiz,local)
    aterra=Vector((pos.x,pos.y,altura(pos.x,pos.y)+.047))
    ult_tampa=0

    def animar(t,u):
        nonlocal ult_tampa
        p=gesto(u)
        fecha=regime(u,.648,.89)
        if u<solta:
            gr.location=transformar(mao.raiz,local)
            q=0
        else:
            gr.location,q=trajeto(u,solta,.144,largada,aterra,.025)
        gr.rotation_euler=(.59*sin(pi*q),.51*sin(pi*q),.57+2.1*q)
        p=levantar_mao(mao,lambda x,y:altura(x,y,fecha),.008)
        braco.pose(Vector((2.8,.51,2.22)),Vector((1.51,.281,1.40)),p)
        if fecha!=ult_tampa:
            coordenadas(malha_solo,[(x,y,altura(x,y,fecha)) for x,y in amostra])
            ult_tampa=fecha
        for o,x,y,r,solto in pedriscos:
            s=fecha if solto else 0
            xx=x-.494*s
            yy=y-(y-pos.y)*.41*s
            o.location=(xx,yy,altura(xx,yy,fecha)+.51*r+.105*sin(pi*s))
        cam((-.51+.38*u,-3.66+.19*u,1.98),(-.11,-.17,.39),2.25,foco=(pos.x,pos.y,.17))
    return animar


def manejo():
    iluminacao("dia",(0,0,1.08))
    raio_sol("Luz do fim da manhã",(-1.95,-.05,3.4),(0,.04,.28),296,(1,.78,.51),3)
    nivel,borda,banana,cacau,inga,feijoes=campo(pessoas=True,denso=True)
    a=Pessoa("Dona Luzia",(-.66,.79,.05),velha=True,escala=.96)
    b=Pessoa("Rafael",(.66,.44,.05),escala=.94)
    verde=material("Marcador de plantio","3e714b","749459",25,.016)
    estaca=agrupar("Estaca da fileira")
    caixa("Madeira da estaca",(0,0,0.28),(.059,.048,.56),madeira(),.012,estaca)
    caixa("Placa do canteiro",(0,-.018,.478),(.23,.057,.123),verde,.026,estaca)
    cam=camera(7)
    def animar(t,u):
        aponta=regime(u,.31,.75)
        a.pose(t,giro=.31,olhar=(.26,-.09+.25*regime(u,.60,.92)),direita=(.47,-.37,.27+.12*aponta),
               esquerda=(-.40,-.16,.07),aperto=(.40,.21),apontar=.42*aponta,apoio=nivel)
        niv=nivel(.38,-.18)
        pouso=regime(u,.23,.61)
        recolhe=regime(u,.63,.92)
        estaca.location=(.38+.239*(1-pouso),-.18+.155*(1-pouso),niv+.43*(1-pouso))
        estaca.rotation_euler.y=.27*(1-pouso)
        pegar=transformar(estaca,(0,-.033,.51))+Vector((.37*recolhe,.1*recolhe,.286*recolhe))
        b.pose(t+.4,giro=-.25,olhar=(-.34,.15+.18*sin(pi*u)),inclinacao=.23*(1-.75*recolhe),
               direita=(.33,-.125,.046),contatos=((pegar,(-.61,-.54,-.48)),None),
               aperto=(.62-.49*recolhe,.35),apoio=nivel)
        vento(banana,t,.052)
        vento(cacau,t,.037)
        vento(inga,t,.031)
        vento(feijoes,t,.046)
        borda[1].rotation_euler.x=.023*sin(t*1.6)
        cam((.95-.84*u,-5.71+.51*u,2.32+.034*u),(.06,.35,1.46),3.65,
            foco=(.11,.25,1.46))
    return animar


PLANOS={
    "abertura":entrada,
    "desenho":desenho,
    "estratos":faixas,
    "semeadura":semeadura,
    "raiz":lambda:corte("raiz"),
    "emergencia":lambda:corte("emergencia"),
    "folhas":lambda:corte("folhas"),
    "manejo":manejo,
}
