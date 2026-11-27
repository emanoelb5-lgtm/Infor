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
from contatos import contornar_haste, levantar_mao, nivel_tigela, orla_saco, trajeto
from personagens import Braco, Mao, Pessoa, matriz, transformar


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
    nivel = terreno(noite=True,limpar=((-0.60,-0.42,.42),))
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
                     esquerda=(-.39,-.095,-.21),aperto=(.34,.46-.31*alto),apontar=alto*.91,apoio=nivel)
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
               esquerda=(-.35,-.39,.18),aperto=(.49,.31),falar=ouvir*.85)
        b.pose(t+.45,giro=-.28,olhar=(-.44,-.09+.08*sin(t*1.88)),esquerda=(-.41,-.44,.25*ouvir+.09),
               direita=(.34,-.31,.18),aperto=(.37,.53),inclinacao=.11+.069*ouvir)
        chama.scale.z = .128+.018*sin(10.2*t)+.013*cos(15.31*t)
        chama.rotation_euler.y = .16*sin(t*6.9)
        luz.data.energy = 108+10*sin(t*9.9)+7*cos(t*7.6)
        plantas[1].rotation_euler.y = .038*sin(t*2.49)
        cam((.40-u*.58,-6.05+.40*u,2.06+.09*u),(.04,-.04,1.72),3.76)
    return animar


def sementes():
    iluminacao("varanda",(0,0,1.16))
    ceu(False)
    casa(4)
    tablado(1.2,-.02,7,5.7)
    mesa((0,0,0),4.0,3.1,.75)
    centro=(-.05,-.20,.817)
    fator=1.20
    caixa_barro(centro,fator)
    cesto((-1.50,.30,.815),.64)
    lampiao((1.18,.83,.82),.76)
    saco=agrupar("Saco de feijão")
    orla_saco(saco)
    pele=material("Pele de Luzia","865139","bd8768",34,.006,.66)
    braco=Braco(pele,pano("285752","63867a"),pano("335f56","749085"),None)
    mao=Mao("Mão que inclina o saco",pele,escala=1.11)
    cam=camera(4.5)

    def bolsa(u):
        saco.rotation_euler=(.12*sin(pi*u),.42+2.34*regime(u,.08,.34)-1.82*regime(u,.73,.99),.15)
        saco.location=mover_tempo(u,[(0,(.73,.13,1.83)),(.29,(.015,-.16,2.13)),
                                      (.70,(.030,-.17,2.17)),(1,(.77,.15,2.31))])

    rng=Random(43)
    grade=[]
    for j in range(-3,4):
        for i in range(-3,4):
            x,y=.111*i+.055*(j%2),.097*j
            if x*x+y*y<.338**2:
                grade.append((centro[0]+x,centro[1]+y))
    rng.shuffle(grade)
    feijoes=[]
    # A sequência ocupa o fundo da tigela da frente para trás.
    alvos=sorted(grade[:25],key=lambda p:p[1])
    for i,(x,y) in enumerate(alvos):
        instante=.354+.0147*i
        bolsa(instante)
        d=(i%3-1)*.047
        origem=transformar(saco,(d,(-1)**i*.052,.286))
        tamanho=.048+rng.random()*.006
        apoio=Vector((x,y,nivel_tigela(x,y,centro,fator)+tamanho*.51))
        v=feijao("Grão de feijão",origem,tamanho,i)
        feijoes.append((v,origem,apoio,instante,.090+rng.random()*.009,rng.uniform(-pi,pi)))

    def animar(t,u):
        bolsa(u)
        apoio=transformar(saco,(-.406,-.099,-.14))
        rumo=Vector((-.67,-.43,-.23))
        pulso=mao.punho(apoio,rumo,.38)
        mao.pose(pulso,rumo,.47,giro=.38)
        braco.pose(Vector((2.91,.60,2.96)),Vector((1.52,.36,2.68)),pulso)
        for v,origem,chao,instante,d,angulo in feijoes:
            v.hide_render=u<instante
            if v.hide_render:
                continue
            v.location,s=trajeto(u,instante,d,origem,chao,.038)
            v.rotation_euler=(.77*sin(pi*s),-.54*sin(pi*2*s),angulo+1.42*s)
        cam((.14-u*.37,-3.57+.20*u,2.58),(.05,-.12,1.57),2.70,foco=(-.04,-.20,1.73))
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
    plantas=mata()
    altura=terreno(canteiro=True,limpar=((-.07,-.28,.48),))
    pele=material("Pele de Luzia","865139","bd8768",34,.006,.66)
    braco=Braco(pele,pano("285752","63867a"),pano("335f56","749085"),None)
    mao=Mao("Mão medindo a umidade",pele,escala=1.21)
    cam=camera(3.8)
    terra=material("Terra úmida","4b2a19","855838",36,.027)
    torrões=[]
    rng=Random(13)
    for j in range(3):
        for i in range(4):
            x,y=-.26+.11*i,-.58+.065*j
            r=rng.uniform(.014,.022)
            p=(x,y,altura(x,y)+r*.57)
            obj=oval("Torrão úmido",p,(r,r*.73,r*.59),terra,detalhe=1)
            torrões.append((obj,Vector(p),r))
    for i in range(9):
        x,y=-1.48+(i%3)*1.45,.95+i//3*1.18
        vegetacao((x,y,altura(x,y)),i*19,.37+.07*(i%4),5)
    def animar(t,u):
        pulso=mover_tempo(u,[(0,(.86,-.10,1.12)),(.34,(.22,-.22,.47)),
                             (.46,(.20,-.24,.07)),(.59,(.17,-.18,.10)),
                             (.82,(.32,-.04,.80)),(1,(.38,0,.90))])
        toque=regime(u,.25,.46)-regime(u,.61,.83)
        rumo=Vector((-.78,-.08,-.52+.54*regime(u,.56,.85)))
        mao.pose(pulso,rumo,.59-.44*toque,indicar=.73*toque,giro=-.38)
        pulso=levantar_mao(mao,altura,.0015)
        braco.pose(Vector((2.70,.46,1.72)),Vector((1.53,.21,1.27)),pulso)
        for i,(p,origem,r) in enumerate(torrões):
            a=regime(u,.47+i*.002,.62+i*.004)
            x=origem.x+a*(-.036-.026*(i%3))
            y=origem.y-a*.064
            p.location=(x,y,altura(x,y)+r*.60+.055*sin(pi*a))
            p.rotation_euler=(a*1.5,.5*a,i*.33)
        plantas[0].rotation_euler.x=.025*sin(t*2.3)
        cam((-.80+.42*u,-3.42,1.60),(.02,-.10,.51),2.38,foco=(.06,-.27,.25))
    return animar


def canteiro():
    ceu(False)
    iluminacao("dia",(0,0,1.08))
    nivel = terreno(canteiro=True,limpar=((-0.55,.22,.55),))
    mata()
    a = Pessoa("Rafael",(-.5,.32,.08))
    casa(7.2,1.7,completa=True)
    cesto((-1.03,.93,nivel(-1.03,.93)+.015),.69,alca=True)
    mocas = []
    for i in range(23):
        x = (-1.75,-.55,.58,1.72)[i%4]
        y = -.52+(i//4)*.72
        if i in (1,5,6):
            continue
        mocas.append(vegetacao((x,y,nivel(x,y)-.003),i*73+7,.34+.05*(i%5),5))
    cam = camera(8)
    def animar(t,u):
        pulso = mover_tempo(u,[(0,(.43,-.26,.02)),(.23,(.47,-.40,.11)),
            (.54,(.50,-.48,.40)),(.81,(.39,-.51,.29)),(1,(.36,-.43,.13))])
        a.raiz.location = (-.62+.13*u,.37,.045-.025*sin(pi*u))
        a.pose(t,giro=.17,olhar=(.18,-.25+.35*suave(u)),inclinacao=.23-.16*regime(u,.35,.87),
               esquerda=(-.29,-.53,.11),direita=pulso,aperto=(.44,.32),apontar=.14,apoio=nivel)
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
        nomes = [("Caderno de campo", -.99,.66,.103),("Observações",-.99,.38,.118),
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
    rng=Random(25)
    for i in range(9):
        x=-1.32+(i%5)*.137+rng.uniform(-.008,.008)
        y=-1.18-(i//5)*.126+rng.uniform(-.009,.009)
        r=rng.uniform(.043,.057)
        v=feijao("Feijão sobre a mesa",(x,y,.845+r*.46),r,i)
        v.rotation_euler.z=rng.uniform(-pi,pi)
    lampiao((1.44,1.07,.848),.67)
    pele=material("Pele de Luzia","865139","bd8768",34,.006,.66)
    braco=Braco(pele,pano("285752","63867a"),pano("335f56","749085"),None)
    lap=lapis((0,0,0),raiz)
    mao=Mao("Pegada do lápis",pele,pai=raiz,escala=1.06)
    xy=[(.24,-.041),(.30,-.077),(.37,.011),(.414,.061),(.44,.053)]
    if tipo!="observacao":
        xy=[(x,y-.21) for x,y in xy]
    pontos=[Vector((x,y,.114-.013*(x-.586))) for x,y in xy]
    curva=[]
    for i,(b,c) in enumerate(zip(pontos,pontos[1:])):
        a=pontos[max(0,i-1)]
        d=pontos[min(len(pontos)-1,i+2)]
        for j in range(8):
            t=j/8
            curva.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t**3))
    curva.append(pontos[-1])
    dist=[0.0]
    for a,b in zip(curva,curva[1:]):
        dist.append(dist[-1]+(b-a).length)
    linha=fio("Marca de grafite rente à página",curva,.0033,tinta,raiz,suave=False)
    linha.data.bevel_factor_mapping_end="SPLINE"
    cam=camera(8)
    def animar(t,u):
        avancar=regime(u,.17,.67)
        linha.data.bevel_factor_end=avancar
        alvo_d=avancar*dist[-1]
        i=next((i for i,v in enumerate(dist[1:]) if alvo_d<=v),len(dist)-2)
        alvo=curva[i].lerp(curva[i+1],(alvo_d-dist[i])/(dist[i+1]-dist[i]))
        descanso=regime(u,.69,.94)
        alvo.z+=.094*descanso+.066*(1-regime(u,0,.17))
        alvo.x+=.14*descanso
        lap.location=alvo
        eixo=Vector((.58,-.33,.74+.11*descanso)).normalized()
        lap.rotation_euler=eixo.to_track_quat("Z","Y").to_euler()
        apoio=alvo+eixo*.25
        rumo=Vector((-.62,.41,-.59))
        pulso=mao.punho(apoio,rumo,.62)
        mao.pose(pulso,rumo,.53,giro=.62)
        m=matriz(raiz)
        contornar_haste(mao,m@(alvo+eixo*.095),m.to_3x3()@eixo,.043,.735,.007)
        braco.pose(Vector((3.17,-1.69,1.61)),Vector((2.08,-.93,1.54)),m@pulso)
        cam((.34-.39*u,-2.13+.42*u,4.68),(.01,-.13,.89),3.76,foco=(.18,0,1.0))
    return animar


def semear():
    iluminacao("dia",(0,0,.65))
    ceu(False)
    nivel=terreno(canteiro=True,limpar=((0,-.42,.77),))
    mata()
    vegetacao((-1.75,.62,nivel(-1.75,.62)),53,1.04,5)
    vegetacao((1.58,1.40,nivel(1.58,1.40)),61,.95,6)
    cesto((.98,.30,nivel(.98,.30)+.018),.68)
    pele=material("Pele de Luzia","865139","bd8768",34,.006,.66)
    braco=Braco(pele,pano("285752","63867a"),pano("335f56","749085"),None)
    mao=Mao("Mão em concha",pele,escala=1.22)
    cam=camera(4.0)

    def gesto(u):
        p=mover_tempo(u,[(0,(.72,.24,1.43)),(.30,(.40,.02,.94)),
                         (.58,(.55,.09,.88)),(1,(1.02,.39,1.30))])
        abrir=regime(u,.30,.63)
        mao.pose(p,(-.90,-.34,.23-.73*abrir),.70-.65*abrir,giro=.21+.97*abrir)
        return p

    grãos=[]
    localizacoes=((-0.051,-.097,.189),(.043,-.099,.193),(.003,-.169,.241))
    gesto(.40)
    # Solta primeiro o grão mais próximo do chão.
    locais=sorted(localizacoes,key=lambda xyz:transformar(mao.raiz,xyz).z)
    for i,((x,y),local) in enumerate(zip(((-.24,-.55),(.076,-.46),(.36,-.50)),locais,strict=True)):
        r=.051+(i%3)*.003
        part=.405+.069*i
        gesto(part)
        origem=transformar(mao.raiz,local)
        fim=(x,y,nivel(x,y)+r*.48)
        g=feijao("Semente lançada",origem,r,i)
        grãos.append((g,local,origem,fim,part,r))
    def animar(t,u):
        p=gesto(u)
        braco.pose(Vector((2.65,.77,1.91)),Vector((1.69,.54,1.44)),p)
        for i,(g,local,origem,fim,part,r) in enumerate(grãos):
            if u<part:
                g.location=transformar(mao.raiz,local)
                q=0
            else:
                g.location,q=trajeto(u,part,.123,origem,fim,.022)
            g.rotation_euler=(.65*sin(pi*q),.95*sin(pi*q),i*.61+q*3.7)
            # As seed tilts and bounces, leave the elliptical shell above the terrain.
            floor=nivel(g.location.x,g.location.y)
            g.location.z=max(g.location.z,floor+r*(.46+.33*sin(pi*q)))
        cam((-.43+.25*u,-3.48,1.80),(.17,-.09,.63),2.63,foco=(.02,-.15,.48))
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
    inicio = nivel(0,-.13)+.013
    g=agrupar("Planta do feijão",(0,-.13,inicio))
    mat = tecido_verde()
    caule = fio("Caule contínuo", [(0,0,.08*i) for i in range(8)],.039,mat,g)
    pontos_caule = caule.data.splines[0].bezier_points
    for i,ponto in enumerate(pontos_caule):
        ponto.radius = 1.02-.052*i
    feijao("Casca deixada no solo",(.175,-.22,nivel(.175,-.22)+.033),.073,0)
    cot = []
    folha_mat = material("Folhas do primeiro par","356539","a5b751",19,.02,.46)
    verde = material("Cotilédones espessos","54763d","aab65c",21,.016,.55)
    for lado in (-1,1):
        u = agrupar("Articulação do cotilédone",pai=g)
        oval("Cotilédone",(0,.115,.016),(.079,.143,.040),verde,u)
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
            pontos.append((.08*sin(p*pi)+dobra*p**2*alonga,.037*sin(p*2.6)+.028*sin(t*2.1)*p,
                           altura*p-dobra*.52*p**3*alonga))
        for ponto,pos in zip(pontos_caule,pontos,strict=True):
            ponto.co = pos
        for i,(lado,c,f) in enumerate(cot):
            c.location=Vector(pontos[6])+Vector((lado*.021,0,0))
            c.rotation_euler=(.80-(.79*regime(u,.28,.64))+.16*sin(t*2),.16*lado,lado*1.37)
            c.scale=(.05+.95*regime(u,.10+i*.04,.49+i*.04),)*3
            f.location=Vector(pontos[7])+Vector((lado*.015,0,.021))
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
    pele=material("Pele de Luzia","865139","bd8768",34,.006,.66)
    braco=Braco(pele,pano("285752","63867a"),pano("335f56","749085"),None)
    mao=Mao("Mão que coloca as vagens",pele,escala=1.08)
    cam=camera(7)

    def gesto(u):
        punho=mover_tempo(u,[(0,(1.34,.33,2.83)),(.29,(.58,.16,2.65)),
                            (.58,(.54,.19,2.60)),(1,(1.57,.41,2.88))])
        abre=regime(u,.40,.62)
        mao.pose(punho,(-.77,-.33,-.29),.66-.61*abre,giro=.65+.21*abre)
        return punho

    disposicoes=(
        ((-.095,-.29,.085),.08),((.079,-.135,.087),.14),((-.123,.025,.088),-.12),
        ((.066,.192,.087),.10),((-.095,.35,.092),-.13),
    )
    def na_mao(i):
        corpo=transformar(mao.raiz,(0,-.113,.176))
        coluna=(i%3-1)*.098
        return corpo+Vector((i%2*.04,coluna,(i//3)*.094))

    vagens=[]
    for i,(fim,angulo) in enumerate(disposicoes):
        instante=.413+.043*i
        gesto(instante)
        origem=na_mao(i)
        v=vagem(bandeja,fim,angulo)
        vagens.append((v,Vector(fim),origem,instante,angulo))
    def animar(t,u):
        p=gesto(u)
        braco.pose(Vector((2.92,.49,3.33)),Vector((1.76,.43,2.98)),p)
        peso=sum(regime(u,v[3]+.115,v[3]+.164) for v in vagens)/len(vagens)
        mola=sin((u-.529)*61)*max(0,1-(u-.529)*3.8) if u>.529 else 0
        ponteiro.rotation_euler.y=-1.27+(peso+.13*mola)*1.58
        bandeja.location.z=1.78-.052*peso+.007*mola
        for i,(v,fim,origem,instante,a) in enumerate(vagens):
            if u<instante:
                mundo=na_mao(i)
                q=0
            else:
                mundo,q=trajeto(u,instante,.117,origem,bandeja.location+fim,.018)
            v.location=mundo-bandeja.location
            v.rotation_euler=(.40*sin(pi*q),.25*sin(pi*q),.20+(a-.20)*q)
        cam((.68-.91*u,-4.53+.32*u,2.63),(.04,0,1.84),3.06,foco=(0,0,1.94))
    return animar


def memoria():
    iluminacao("varanda",(0,0,1.3))
    ceu(False)
    mata()
    terreno(z=-.23)
    casa(3.2,-.4,completa=True)
    tablado(-2.2,.02,6,5.9)
    mesa((0,-.23,.12),2.73,1.40,.81)
    lume,luz=lampiao((1.12,.36,.997),.70)
    caderno((-.46,-.40,.997),.58,.74)
    saco=cesto((.47,.19,1.32),.69,alca=True)
    posicoes=(((-.10,-.22,.34),.24),((.055,-.07,.359),-.13),((-.085,.107,.365),.18),
              ((.06,.26,.35),-.11),((-.011,.01,.44),1.28))
    for loc,giro in posicoes:
        vagem(saco,loc,giro)
    a=Pessoa("Dona Luzia",(-.44,.95,.095),velha=True)
    cam=camera(7)
    def animar(t,u):
        baixar=regime(u,.18,.60)
        soltar=regime(u,.62,.91)
        chegar=regime(u,0,.29)
        a.raiz.location=(-.396+.136*chegar,.897-.179*chegar,.095)
        saco.location=(.37+.22*baixar,.28-.186*baixar,.998+.316*(1-baixar))
        saco.rotation_euler=(.070*(1-baixar),-.051*(1-baixar),.12*(1-baixar))
        pegada=transformar(saco,(0,-.010,.953))
        alvo=pegada+Vector((-.12*soltar,.23*soltar,.158*sin(pi*soltar/2)))
        a.pose(t,giro=-.07,olhar=(.18,.06+.20*baixar-.27*soltar),
            inclinacao=.12*baixar-.087*soltar,esquerda=(-.35,-.27,.06+.20*baixar),
            aperto=(.24,.61-.53*soltar),passo=(.74*chegar+.02) if u<.27 else 0,
            contatos=(None,(alvo,(-.79,-.55,-.18+.28*soltar))),apoio=lambda x,y:.096)
        if soltar<.74:
            mao=a.bracos[1][2]
            contornar_haste(mao,pegada+Vector((-.134,0,0)),(1,0,0),.034,.268,.004)
        lume.scale.z=.124+.018*sin(t*8.3)+.011*cos(t*14.1)
        luz.data.energy=116+8*cos(t*8.1)
        cam((.63-.87*u,-4.76+.39*u,2.07+.14*u),(-.02,.13,1.69),3.55,foco=(.06,.25,1.64))
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
