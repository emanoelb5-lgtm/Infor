"""Planos e coreografias da produção A Lua e o tempo da roça."""

from math import atan2, cos, pi, sin
from random import Random

import bpy
from mathutils import Vector

from cenografia import (
    agrupar, anel, banco, braço, brilho, caderno, caixa, caixa_barro, casa, cesto,
    ceu, cor, estrelas, feijao, fio, folha, gravar, iluminacao, lampada, lampiao,
    lapis, lua_materia, madeira, malha, mata, material, mesa, oval, pano, raio_sol,
    tablado, tecido_verde, terreno, torno, vagem, vegetacao,
)
from personagens import Mao, Pessoa


def limitar(x):
    return min(1.0, max(0.0, x))


def suave(x):
    s = limitar(x)
    return s*s*(3-2*s)


def regime(u, a, b):
    return suave((u-a)/(b-a))


def mover_tempo(u, chaves):
    """Transições entre poses com repouso nos contatos."""
    if u <= chaves[0][0]:
        return Vector(chaves[0][1])
    for (a, p), (b, q) in zip(chaves, chaves[1:]):
        if u <= b:
            return Vector(p).lerp(Vector(q), regime(u,a,b))
    return Vector(chaves[-1][1])


def camera(diafragma=0):
    dados = bpy.data.cameras.new("Objetiva")
    dados.sensor_fit = "VERTICAL"
    dados.sensor_height = 32
    dados.clip_end = 150
    dados.dof.use_dof = bool(diafragma)
    dados.dof.aperture_fstop = max(diafragma, 0.8)
    obj = bpy.data.objects.new("Câmera de filmagem", dados)
    bpy.context.collection.objects.link(obj)
    bpy.context.scene.camera = obj

    def olhar(origem, alvo, altura, foco=None):
        obj.location = origem
        d = Vector(alvo) - Vector(origem)
        obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        dados.lens = 32*d.length/altura
        dados.dof.focus_distance = d.length if foco is None else (Vector(foco)-Vector(origem)).length
    return olhar


def noite_aberta():
    iluminacao("noite")
    ceu(True)
    estrelas()
    terreno(noite=True)
    plantas = mata(True)
    tablado(1.0,0.13,5.9,3.9)
    casa(3.80,-2.0,completa=True)
    lampada("Luz da janela",(-.57,3.96,2.16),200,(1,.53,.27),.6)
    raio_sol("Reflexo do terreiro",(.57,-2.64,1.64),(-.60,-.3,1.7),
             64,(1,.77,.49),2.6)
    mulher = Pessoa("Dona Luzia",(-0.60,-0.32,0.04),velha=True)
    mat,_ = lua_materia("Lua crescente do prólogo",(.96,-.51,-.38))
    moon = oval("Lua sobre a roça",(1.16,11.1,6.33),(1.11,)*3,mat)
    vaga = []
    for i in range(11):
        m = brilho("Vaga-lumes", "e4d68b", 3.3)
        vaga.append(oval("Vaga-lume", (0,0,0), (.015,)*3,m,detalhe=1))
    cam = camera()
    def animar(t,u):
        inicio = regime(u,0.07,0.30)
        alto = regime(u,.31,.64)
        fim = regime(u,.78,1)
        canto = .30+.41*alto-.14*fim
        mulher.pose(t,giro=.31+.26*alto,olhar=(canto,-.10-.37*inicio+.04*sin(t*.8)),
                     direita=(.47+.14*alto,-.28,.18+.74*alto-.27*fim),
                     esquerda=(-.39,-.095,-.21),aperto=(.34,.46-.31*alto),apontar=alto*.91)
        moon.rotation_euler = (0,t*.011,.03)
        for i,p in enumerate(plantas):
            p.rotation_euler.x = .026*sin(t*1.51+i)
        for i,p in enumerate(vaga):
            k = i*2.39996
            p.location = (2.66*cos(k+t*.39),1.30+1.37*sin(k+t*.43),
                          .38+.25*(i%5)+.19*sin(t*1.62+k))
            p.scale = (.011+.008*max(0,sin(k+t*2.9)),)*3
        cam((.68-.20*u,-7.05+.28*u,2.36+.11*u),(.11,.24,2.65),5.1)
    return animar


def varanda():
    iluminacao("varanda",(0,0,1.65))
    ceu(False)
    plantas = mata()
    terreno(z=-.2)
    tablado(-1.85,0,5.8,5.2)
    casa(2.52,.17,completa=True)
    banco((-.66,.10,.07),.91)
    banco((.62,.23,.07),.87)
    a = Pessoa("Dona Luzia",(-.70,.08,.075),velha=True,sentada=True)
    b = Pessoa("Rafael",(.68,.30,.075),sentada=True,escala=.94)
    mesa((.28,-.93,.07),2.05,1.04,.60)
    cesto((-.40,-.86,.745),.46)
    caixa_barro((.18,-1.01,.742),.58)
    chama,luz = lampiao((1.07,-.80,.74),.72)
    mat = material("Pote verde escuro","324438","7f8461",22,.02)
    torno("Pote de água",[(0,.13),(.051,.18),(.24,.25),(.367,.138),(.422,.127),(.433,.141)],mat,
          local=(-1.29,1.03,.08))
    cam = camera()
    def animar(t,u):
        contar = mover_tempo(u,[(0,(.44,-.35,.15)),(.22,(.42,-.41,.78)),
                             (.42,(.51,-.53,.49)),(.58,(.35,-.54,.42)),
                             (.76,(.49,-.59,.57)),(1,(.44,-.36,.19))])
        ouvir = sin(u*pi)**2
        a.pose(t,giro=.22,olhar=(.30,-.035+.09*sin(t*2.0)),direita=contar,
               esquerda=(-.27,-.47,.075),aperto=(.49,.31),falar=ouvir*.85)
        b.pose(t+.45,giro=-.28,olhar=(-.44,-.09+.08*sin(t*1.88)),esquerda=(-.41,-.44,.25*ouvir+.09),
               direita=(.29,-.34,.16),aperto=(.37,.7),inclinacao=.13+.085*ouvir)
        chama.scale.z = .128+.018*sin(10.2*t)+.013*cos(15.31*t)
        chama.rotation_euler.y = .16*sin(t*6.9)
        luz.data.energy = 108+10*sin(t*9.9)+7*cos(t*7.6)
        plantas[1].rotation_euler.y = .038*sin(t*2.49)
        cam((.40-u*.58,-6.05+.40*u,2.06+.09*u),(.04,-.04,1.72),3.76)
    return animar


def sementes():
    iluminacao("varanda",(0,0,1.10))
    ceu(False)
    casa(4)
    tablado(1.2,-.02,7,5.7)
    mesa((0,0,0),4.0,3.1,.75)
    caixa_barro((-.05,-.20,.817),1.2)
    cesto((-1.50,.30,.815),.64)
    lampiao((1.15,.84,.82),.78)
    juta = material("Juta do saco","8b7152","cfb58a",115,.023,.86)
    costura = material("Costura rústica", "9e794f", "c39c6d",52,.009)
    movel = agrupar("Saco de semente")
    oval("Volume de tecido", (0,0,-.2),(.44,.29,.47),juta,movel)
    torno("Boca aberta", [(-.18,.33),(.09,.305),(.26,.335),(.30,.36),
          (.303,.32),(.15,.267),(-.05,.22)],juta,movel,ondulacao=.065)
    anel("Costura da boca", .34,.28,costura,movel,.018,.021)
    fio("Costura do saco",[(.12,-.14,-.58),(.33,-.109,-.42),(.43,-.099,-.14),
         (.30,-.06,.19)],.01,costura,movel)
    pele = material("Pele e luz","754331","b87752",31,.018)
    braco = oval("Antebraço", (0,0,0), (1,1,1),pele)
    mao = Mao("Mão virando o saco",pele,escala=1.13)
    cam = camera(4.5)
    rng = Random(52)
    legumes = []
    for i in range(42):
        quando = .36 + i*.0069 + rng.uniform(-.008,.006)
        dur = rng.uniform(.15,.185)
        a, r = rng.uniform(-pi,pi), rng.uniform(.05,.39)
        fim = Vector((-.065+r*cos(a),-.2+r*sin(a),.954+.17*r+rng.uniform(-.013,.032)))
        obj = feijao("Grão em queda",(0,0,0),rng.uniform(.065,.088),i)
        legumes.append((obj,quando,dur,fim,rng.uniform(-pi,pi),rng.uniform(-pi,pi)))
    def animar(t,u):
        ang = .62+2.37*regime(u,.10,.34)-1.91*regime(u,.72,.96)
        movel.rotation_euler = (.19*sin(pi*u),ang,.22)
        movel.location = mover_tempo(u, [(0,(.76,.17,1.78)),(.27,(.36,.16,2.16)),
                                          (.69,(.33,.20,2.13)),(1,(.91,.30,2.24))])
        pulso = movel.location + Vector((.30,.075,-.05))
        braço(braco,(2.89,.41,2.83),pulso,.114,.125)
        mao.pose(pulso,(-.89,-.28,.06),.75,giro=.45)
        for i,(obj,partida,queda,fim,rx,rz) in enumerate(legumes):
            p = (u-partida)/queda
            obj.hide_render = p < 0
            if p < 0:
                continue
            s = limitar(p)
            origem = Vector((.21 + .06*sin(i*.78),.13+.09*cos(i*.84),1.85+.06*sin(i)))
            obj.location = (origem.x+(fim.x-origem.x)*s,origem.y+(fim.y-origem.y)*s,
                            origem.z+(fim.z-origem.z)*s*s)
            if p > 1:
                salto = max(0,1-(p-1)/.58)
                obj.location.z += .12*salto*abs(sin((p-1)*pi*2.8))
            obj.rotation_euler = (rx+s*(3.2+i%3),s*2.7,rz+s*5)
        cam((.10-u*.36,-3.46+.2*u,2.61),(.075,-.065,1.57),2.70,foco=(0,0,1.65))
    return animar


def fases():
    ceu(True,horizonte=-12)
    estrelas(y=10,largura=8.2,altura=7.9,base=-7.9)
    cam = camera()
    fase = [(-.95,1.32,(0,1,0)),(.95,1.32,(1,-.03,-.36)),
            (-.95,-.83,(0,-1,0)),(.95,-.83,(-1,-.03,.36))]
    faces = []
    ouro = brilho("Traçado astronômico", "a88d68",0.64)
    base = brilho("Bronze escuro", "46577b",0.84)
    for i,(x,z,d) in enumerate(fase):
        mat,luz = lua_materia(f"Modelo lunar {i}",d)
        obj = oval("Esfera lunar", (x,0,z), (.627,)*3,mat)
        r = .702
        guia = fio("Círculo de referência",[(x+r*cos(a),.07,z+r*sin(a))
                   for a in (2*pi*j/48 for j in range(48))],.0065,base,fechado=True)
        ponteiro = oval("Marcador orbital", (x,0,z+.705),(.021,)*3,ouro,detalhe=1)
        faces.append((obj,ponteiro,x,z))
    for x in (-.15,.15):
        fio("Divisor de latão",[(x,-.2,-.18),(x*.52,-.2,.10),(x,-.2,.39)],.004,base)
    def animar(t,u):
        cam((0,-9,0),(0,0,0),6.18)
        for i,(obj,p,x,z) in enumerate(faces):
            obj.rotation_euler = (.07*cos(t*.77+i), .29*sin(t*.31+i), i*.77+.18*t)
            a = 1.57 - .88*t + i*.4
            p.location = (x+.706*cos(a),-.02,z+.706*sin(a))
    return animar


def ciclo():
    ceu(True,horizonte=-12)
    estrelas(y=13,largura=8,altura=9,base=-9)
    cam = camera()
    c = Vector((0,.04,.12))
    orbe = material("Planeta Terra","153657","427798",4.2,.029,.65)
    seu = orbe.node_tree.nodes
    no = next(n for n in seu if n.type=="VALTORGB")
    no.color_ramp.elements[0].position = .29
    no.color_ramp.elements[1].position = .47
    e = no.color_ramp.elements.new(.482)
    e.color = (*cor("71915d"),1)
    e = no.color_ramp.elements.new(.76)
    e.color = (*cor("c1b180"),1)
    terra = oval("Planeta Terra", c, (.65,)*3,orbe)
    terra.rotation_euler.y = .28
    lua_mat,_ = lua_materia("Lua em órbita",(-1,-.12,.15))
    fase_mat,direcao = lua_materia("Fase vista da Terra",(0,1,.03))
    lua = oval("Lua orbitando a Terra",(0,0,0),(.273,)*3,lua_mat)
    fita = brilho("Órbita projetada", "6181a2", .85)
    traço = brilho("Posições do ciclo", "bd9d68",1)
    xy = 1.54
    z = .97
    def pos(a, delta=0):
        return (xy*cos(a),.31*sin(a),.18+z*sin(a)+delta)
    fio("Órbita", [pos(2*pi*i/65) for i in range(65)], .010, fita, fechado=True)
    for i in range(8):
        ponto = pos(2*pi*i/8)
        oval("Marca orbital",ponto,(.025,)*3,traço,detalhe=1)
    raio_sol("Luz solar lateral",(-3.0,-1.5,1.7),c,510,(1,.79,.45),1.5)
    raio_sol("Luz fria refletida",(2,0,0),c,38,(.36,.59,1),4.5)
    mat = brilho("Sol fora de quadro", "ffc87c",2.15)
    oval("Borda solar",(-3.6,.30,.45),(1.68,)*3,mat)
    for j in range(3):
        d = j*.25
        fio("Incidência de luz", [(-2.05,.21,.48-d),(-1.55,.28,.48-d)],.006,traço)
    lupa = oval("Lua vista da Terra",(.07,1.02,2.41),(.585,)*3,fase_mat)
    def animar(t,u):
        a = pi+2*pi*(.95*u+.05*suave(u))
        lua.location = pos(a)
        lua.rotation_euler = (.04,t*.11,t*.41)
        lupa.rotation_euler = (.08-u*.07,t*.09,t*.23)
        terra.rotation_euler.z = t*.29
        direcao.default_value = (sin(a)*.97, cos(a)*-.97, .19)
        cam((0,-9,0),(0,0,.26),6.30)
    return animar


def terra_mao():
    iluminacao("dia",(0,0,.6))
    ceu(False)
    plantas = mata()
    altura = terreno(canteiro=True)
    rng = Random(4)
    piel = material("Pele e luz","754331","b87752",31,.018)
    manga = oval("Manga verde",(0,0,0),(1,1,1),pano("254b48","47796b"))
    pele_braco = oval("Antebraço",(0,0,0),(1,1,1),piel)
    mao = Mao("Indicador pressiona a terra",piel,escala=1.23)
    cam = camera(3.3)
    terra = material("Terra úmida", "442714", "915535", 20,.053)
    bolas=[]
    for i in range(34):
        r = rng.uniform(.012,.036)
        obj=oval("Grumo de terra solto",(0,0,0),(r,r*.81,r*.67),terra,detalhe=1)
        bolas.append((obj,rng.uniform(-.27,.28),rng.uniform(-.20,.23),rng.uniform(0,.22)))
    for i in range(9):
        x = -1.48+(i%3)*1.45
        y = .95+i//3*1.18
        vegetacao((x,y,altura(x,y)),i*19, .37+.07*(i%4),5)
    def animar(t,u):
        p = mover_tempo(u,[(0,(.82,-.11,1.20)),(.34,(.17,-.26,.54)),
                         (.48,(.13,-.23,.34)),(.60,(.13,-.20,.44)),
                         (.81,(.25,-.03,.95)),(1,(.34,-.01,.84))])
        toque = regime(u,.15,.49)-regime(u,.66,.81)
        entao = regime(u,.56,.82)
        d = Vector((-.67,-.12,-.62+.70*entao))
        braço(manga,(2.55,.41,1.67),(1.70,.39,1.32),.225,.20)
        braço(pele_braco,(1.91,.33,1.42),p,.10,.13)
        mao.pose(p,d,.73*(1-toque)+.14,indicar=.73*toque,giro=-.64)
        for i,(obj,x,y,z) in enumerate(bolas):
            v = limitar((u-.47-z*.60)/.36)
            h = max(0,.51*(1-(v/.66-1)**2))*(.19+z)
            obj.location = (p.x-.10+x*(.52+v),-.25+y*(.62+v),altura(.1+x,-.25+y)+h)
            if v>0.01:
                obj.location.x = .11+x*(.52+v)
            obj.rotation_euler = (v*6+i,v*3,2*v)
        plantas[0].rotation_euler.x = .031*sin(t*2.3)
        cam((-.86+.45*u,-3.68,1.69),(.02,-.02,.54),2.48,foco=(.10,-.15,.39))
    return animar


def canteiro():
    ceu(False)
    iluminacao("dia",(0,0,1.08))
    nivel = terreno(canteiro=True)
    mata()
    a = Pessoa("Rafael",(-.5,.32,.08))
    casa(7.2,1.7,completa=True)
    cesto((-.85,.81,.15),.76,alca=True)
    mocas = []
    for i in range(23):
        x = (-1.75,-.55,.58,1.72)[i%4]
        y = -.52+(i//4)*.72
        if i in (1,5,6):
            continue
        mocas.append(vegetacao((x,y,nivel(x,y)+.085),i*73+7,.34+.05*(i%5),5))
    cam = camera(8)
    def animar(t,u):
        pulso = mover_tempo(u,[(0,(.43,-.26,.02)),(.23,(.47,-.40,.11)),
            (.54,(.50,-.48,.40)),(.81,(.39,-.51,.29)),(1,(.36,-.43,.13))])
        a.raiz.location = (-.62+.13*u,.37,.09-.095*sin(pi*u))
        a.pose(t,giro=.17,olhar=(.18,-.25+.35*suave(u)),inclinacao=.23-.16*regime(u,.35,.87),
               esquerda=(-.29,-.53,.11),direita=pulso,aperto=(.44,.32),apontar=.14)
        for i,p in enumerate(mocas):
            p.rotation_euler.x = .10*sin(t*1.88+i*.63)
            p.rotation_euler.y = .074*sin(t*2.15+i*.74)
        cam((2.13-.67*u,-6.1+.61*u,3.2),(-.06,.15,1.23),3.43,foco=(-.7,.4,1.4))
    return animar


def anotacoes(tipo):
    iluminacao("varanda",(0,0,1))
    ceu(False)
    mesa((0,0,0),5.2,4.8,.78)
    raiz = caderno((0,0,.852),1.15,1.86)
    raiz.rotation_euler.z = -.10
    tinta = material("Lápis no papel","5c4538")
    tit = material("Letra em verde escuro","354a3f")
    if tipo == "observacao":
        nomes = [("Caderno de campo", -.99,.66,.144),("Observações",-.99,.38,.118),
                 ("Fase da Lua",.16,.665,.137),("Lua crescente",.17,.425,.108),
                 ("Umidade do solo",.17,.135,.096)]
    elif tipo == "dados":
        nomes = [("Feijão", -.98,.67,.173),("Data do plantio",-.99,.40,.116),
                 ("Variedade",-.99,.12,.116),("Canteiro",-.99,-.16,.116),
                 ("Chuva",.19,.67,.146),("Manejo",.19,.24,.146)]
    elif tipo == "memoria":
        nomes = [("Safra anterior",-.99,.66,.128),("Germinação",-.99,.38,.110),
                 ("Colheita",-.99,.11,.117),("Próxima safra",.15,.66,.133),
                 ("O que observar?",.15,.38,.102)]
    else:
        raise ValueError(tipo)
    for i,(palavra,x,y,s) in enumerate(nomes):
        gravar("Anotação",palavra,(x,y,.125),tit if i in (0,2,3,4) else tinta,raiz,tamanho=s)
    caixa_barro((-1.59,.81,.846),.62)
    for i in range(15):
        r = Random(25+i)
        v = feijao("Feijão sobre a mesa",(-1.03+r.uniform(-.44,.38),-1.15+r.uniform(-.20,.15),.874),
                   r.uniform(.044,.068),i)
        v.rotation_euler.z = r.uniform(-pi,pi)
    lampiao((1.44,1.07,.848),.67)
    pele = material("Pele e luz","754331","b87752",31,.018)
    braco = oval("Antebraço sobre a mesa",(0,0,0),(1,1,1),pele)
    lap = lapis((0,0,0),raiz)
    mao = Mao("Mão segurando o lápis",pele,pai=raiz,escala=1.06)
    traçado = [(0.25,.013,.132),(0.32,-.023,.132),(0.41,.066,.132),
               (.43,.054,.132),(.56,.066,.132),(.72,.057,.132),(.84,.073,.132)]
    if tipo in ("dados","memoria"):
        traçado = [(x,y-.23,.132) for x,y,z in traçado]
    linha = fio("Grafite surgindo no papel",traçado,.009,tinta,raiz)
    linha.data.bevel_factor_end = 0
    cam = camera(8)
    def animar(t,u):
        marca = regime(u,.13,.71)
        linha.data.bevel_factor_end = marca
        x = marca*(len(traçado)-1)
        i = min(len(traçado)-2,int(x))
        alvo = Vector(traçado[i]).lerp(Vector(traçado[i+1]),x-i)
        descanso = regime(u,.72,.99)
        alvo.z += .058*descanso+.07*(1-regime(u,0,.16))
        alvo.x += .20*descanso
        lap.location = alvo
        inclinacao = Vector((.54,-.36,.69+.10*descanso)).normalized()
        lap.rotation_euler = inclinacao.to_track_quat("Z","Y").to_euler()
        pulso = alvo + inclinacao*.43+Vector((.100,-.08,-.04))
        mao.pose(pulso,(-.62,.30,-.27),.78,giro=.8)
        v = Vector((cos(.10)*pulso.x+sin(.10)*pulso.y,-sin(.10)*pulso.x+cos(.10)*pulso.y,
                    .852+pulso.z))
        braço(braco,(3.26,-1.61,1.36),v,.108,.128)
        cam((.34-.39*u,-2.13+.42*u,4.68),(.01,-.13,.89),3.76,foco=(.18,0,1.0))
    return animar


def semear():
    iluminacao("dia",(0,0,.65))
    ceu(False)
    nivel = terreno(canteiro=True)
    mata()
    vegetacao((-1.75,.62,.15),53,1.04,5)
    vegetacao((1.58,1.40,.12),61,.95,6)
    cesto((.85,.12,.14),.75)
    pele = material("Pele e luz","754331","b87752",31,.018)
    manga = oval("Manga verde",(0,0,0),(1,1,1),pano("254b48","47796b"))
    braco = oval("Braço semeando",(0,0,0),(1,1,1),pele)
    mao = Mao("Mão em concha",pele,escala=1.26)
    rng=Random(8)
    grãos=[]
    for i in range(6):
        x = -.20+.12*i
        fim=Vector((x,-.48+rng.uniform(-.093,.24),nivel(x,-.44)+.066))
        g=feijao("Semente lançada",(0,0,0),.075+rng.uniform(-.014,.01),i)
        grãos.append((g,fim,rng.uniform(-pi,pi)))
    cam=camera(3.8)
    def animar(t,u):
        p = mover_tempo(u,[(0,(.63,.24,1.44)),(.31,(.43,.005,.89)),
                         (.64,(.65,.12,.92)),(1,(1.09,.39,1.29))])
        abrir = regime(u,.31,.55)
        mao.pose(p,(-.87,-.36,-.17-.24*abrir),.89-.69*abrir,giro=-.19-.37*abrir)
        braço(manga,(2.65,.77,1.91),(1.65,.58,1.39),.18,.191)
        braço(braco,(1.93,.62,1.50),p,.114,.122)
        for i,(g,fim,a) in enumerate(grãos):
            v = (u-.39-i*.034)/.17
            g.hide_render = v < 0
            origem = p+Vector((-.27-.023*i,-.128,-.137))
            s=limitar(v)
            g.location = origem.lerp(fim,s)
            g.location.z = origem.z+(fim.z-origem.z)*s*s
            if v > 1:
                g.location.z += .035*max(0,1-(v-1)/.5)*abs(sin((v-1)*pi*4))
            g.rotation_euler=(a+s*5.3,s*1.6,a-s*3.8)
        cam((-.43+.25*u,-3.48,1.80),(.14,-.09,.60),2.65,foco=(.02,-.10,.39))
    return animar


def broto():
    iluminacao("dia",(0,0,.7))
    ceu(False)
    sol = raio_sol("Recorte da manhã",(0,4,2.7),(0,0,.45),620,(1,.67,.33),2.8)
    nivel = terreno(canteiro=True)
    matas=mata()
    for i in range(6):
        x, y = -1.7+.68*i, 1.5+i*.135
        vegetacao((x,y,nivel(x,y)),68+i*12,.54+(i%2)*.3,7)
    inicio = nivel(0,0)+.052
    g=agrupar("Planta do feijão",(0,-.13,inicio))
    mat = tecido_verde()
    caule = fio("Caule contínuo", [(0,0,.08*i) for i in range(8)],.058,mat,g)
    pontos_caule = caule.data.splines[0].bezier_points
    for i,ponto in enumerate(pontos_caule):
        ponto.radius = 1.02-.052*i
    feijao("Casca deixada no solo",(.094,-.15,inicio-.020),.095,0)
    cot = []
    folha_mat = material("Folhas do primeiro par","356539","a5b751",19,.02,.46)
    verde = material("Cotilédones espessos","54763d","aab65c",21,.016,.55)
    for lado in (-1,1):
        u = agrupar("Articulação do cotilédone",pai=g)
        vo = oval("Cotilédone",(0,.14,.025),(.110,.183,.055),verde,u)
        v = agrupar("Folha em abertura",pai=g)
        folha("Primeira folha verdadeira",folha_mat,v,.72,.226,.26)
        fio("Nervura principal",[(0,0,0),(0,.20,.141),(0,.41,.152),(0,.68,-.037)],
            .006,mat,v)
        cot.append((lado,u,v))
    cam=camera(3.2)
    def animar(t,u):
        alonga = .016+.984*regime(u,.03,.73)
        dobra = .28*(1-regime(u,.43,.88))
        altura=1.34*alonga
        pontos=[]
        for j in range(8):
            p = j/7
            pontos.append((.08*sin(p*pi)+dobra*p**2,.037*sin(p*2.6)+.028*sin(t*2.1)*p,
                           altura*p-dobra*.61*p**3))
        for ponto,pos in zip(pontos_caule,pontos,strict=True):
            ponto.co = pos
        for i,(lado,c,f) in enumerate(cot):
            c.location=pontos[6]
            c.rotation_euler=(.80-(.79*regime(u,.28,.64))+.16*sin(t*2),.16*lado,lado*1.37)
            c.scale=(.05+.95*regime(u,.10+i*.04,.49+i*.04),)*3
            f.location=pontos[7]
            f.rotation_euler=(1.17-(1.13*regime(u,.56+i*.04,.965))+.10*sin(t*2.3),
                              lado*.25,lado*1.59-.14)
            f.scale=(.002+.998*regime(u,.35+i*.025,.88+i*.04),)*3
        for i,p in enumerate(matas):
            p.rotation_euler.x=.034*sin(t*1.9+i)
        sol.data.energy = 480+390*suave(u)
        cam((.16+.31*u,-3.02,1.63+.16*u),(.055,0,.68),2.63,foco=(.03,-.13,.56))
    return animar


def balanca():
    iluminacao("varanda",(0,0,1.2))
    ceu(False)
    casa(4.3,1.71)
    tablado(1.2,-.02,7,5.7)
    mesa((0,0,0),4.0,2.95,.76)
    cesto((-1.21,.11,.828),.89)
    lampiao((1.3,.64,.828),.70)
    verde = material("Esmalte da balança","355b52","789280",33,.017,.51)
    branco = material("Mostrador envelhecido","c89562","ead2a7",39,.015)
    escuro = material("Marcas da balança","453c36")
    ponteira = material("Agulha vermelha","a04435",rugoso=.46)
    base=.831
    caixa("Base da balança",(0,0,base+.05),(1.24,.80,.10),verde,.081)
    oval("Carcaça",(0,.034,1.237),(.50,.31,.416),verde)
    oval("Mostrador",(0,-.241,1.238),(.352,.060,.352),branco)
    fio("Contorno do mostrador",[(.355*cos(a),-.263,1.238+.355*sin(a))
        for a in (2*pi*j/40 for j in range(40))],.024,verde,fechado=True)
    for j in range(21):
        a=-.83+3.82*j/20
        ri=.231 if j%5==0 else .263
        fio("Escala graduada",[(ri*cos(a),-.306,1.238+ri*sin(a)),
               (.296*cos(a),-.300,1.238+.296*sin(a))],.008,escuro)
    ponteiro=agrupar("Pivô da agulha",(0,-.313,1.238))
    fio("Agulha",( (0,0,-.059),(0,0,0),(0,0,.267) ),.012,ponteira,ponteiro)
    oval("Cubinho do ponteiro",(0,-.005,0),(.035,.016,.035),verde,ponteiro)
    caixa("Haste da bandeja",(0,.066,1.66),(.19,.23,.24),verde,.04)
    bandeja = agrupar("Prato da balança",(0,.066,1.78))
    torno("Prato do peso",[(0,.15),(0,.47),(.028,.66),(.071,.72),(.106,.719),
          (.108,.68),(.065,.58),(.047,.12)],verde,bandeja,ondulacao=.013)
    pele=material("Pele e luz","754331","b87752",31,.018)
    braco=oval("Braço que deposita a colheita",(0,0,0),(1,1,1),pele)
    mão=Mao("Mão larga as vagens",pele,escala=1.03)
    rng=Random(72)
    urdidas=[]
    for i in range(14):
        fim=(rng.uniform(-.37,.37),rng.uniform(-.32,.28),.104+i*.008)
        v=vagem(bandeja,fim,rng.uniform(-pi,pi))
        urdidas.append((v,Vector(fim),v.rotation_euler.z))
    cam=camera(7)
    def animar(t,u):
        p=mover_tempo(u,[(0,(1.20,.34,2.80)),(.27,(.49,.28,2.68)),
                         (.57,(.57,.23,2.45)),(1,(1.57,.32,2.83))])
        braço(braco,(2.93,.53,3.37),p,.107,.117)
        braço_abre=regime(u,.37,.64)
        mão.pose(p,(-.75,-.32,-.34-.2*braço_abre),.81-.63*braço_abre,giro=.53)
        peso=regime(u,.50,.71)
        mola=sin((u-.50)*46)*max(0,1-(u-.50)*3.1) if u>.50 else 0
        ponteiro.rotation_euler.y=-1.27+(peso+.32*mola)*1.58
        bandeja.location.z=1.78-.056*peso+.01*mola
        for i,(v,fim,a) in enumerate(urdidas):
            s=limitar((u-.31-i*.018)/.17)
            v.hide_render = u < .24+i*.018
            captura=Vector((p.x-.39,.13+(i%3)*.052,p.z-bandeja.location.z-.18-(i%4)*.035))
            v.location = captura.lerp(fim,s)
            v.location.z = captura.z+(fim.z-captura.z)*s*s
            v.rotation_euler=(sin(s*pi)*(i%4),sin(s*pi*.9)*.39,a+(1-s)*2.0)
        cam((.68-.91*u,-4.53+.32*u,2.63),(.04,0,1.78),3.11,foco=(0,0,1.89))
    return animar


def memoria():
    iluminacao("varanda",(0,0,1.3))
    ceu(False)
    mata()
    terreno(z=-.23)
    casa(3.2,-.4,completa=True)
    tablado(-2.2,.02,6,5.9)
    mesa((0,-.18,.12),2.69,1.51,.81)
    lume,luz=lampiao((.95,.03,1.0),.80)
    caderno((-.41,-.43,1.00),.61,.77)
    saco=cesto((.23,-.06,1.17),.73,alca=True)
    for i in range(7):
        vagem(saco,(-.34+.065*i,-.13+.036*i,.36+(i%3)*.039),.26+i*.38)
    a=Pessoa("Dona Luzia",(-.34,.88,.123),velha=True)
    cam=camera(8)
    def animar(t,u):
        baixar = regime(u,.19,.62)
        repouso = regime(u,.65,.92)
        a.raiz.location = (-.58+.23*regime(u,0,.27),1.21-.36*regime(u,0,.32),.12)
        a.pose(t,giro=-.09,olhar=(.11,-.19+.19*repouso),inclinacao=.16*baixar-.10*repouso,
               direita=(.41,-.57,.48-.29*baixar+.23*repouso),esquerda=(-.33,-.55,.17+.08*baixar),
               aperto=(.47,.78-.49*repouso),passo=(.92*u+.015) if u<.26 else 0)
        saco.location=(.09+.11*baixar,-.16+.062*baixar,1.37-.371*baixar)
        saco.rotation_euler=(.14*(1-baixar)+.023*sin(t*3),-.09*(1-baixar),.16-.11*baixar)
        lume.scale.z = .128+.020*sin(t*8.3)+.012*cos(t*14.1)
        luz.data.energy = 129+8*cos(t*8.1)
        cam((.68-.92*u,-4.79+.39*u,2.07+.14*u),(-.03,.13,1.69),3.54,foco=(-.2,.24,1.55))
    return animar


PLANOS = {
    "noite": noite_aberta,
    "varanda": varanda,
    "fases": fases,
    "sementes": sementes,
    "ciclo": ciclo,
    "terra": terra_mao,
    "canteiro": canteiro,
    "observacao": lambda: anotacoes("observacao"),
    "semear": semear,
    "dados": lambda: anotacoes("dados"),
    "broto": broto,
    "balanca": balanca,
    "memoria": memoria,
    "caderno-final": lambda: anotacoes("memoria"),
}
