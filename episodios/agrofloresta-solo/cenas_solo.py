"""Personagens, serapilheira e plantio no sistema agroflorestal."""

from math import cos, pi, sin
from random import Random

from mathutils import Vector

from cenas import camera, mover_tempo, regime
from cenografia import agrupar, ceu, cesto, fio, iluminacao, madeira, mata, material, oval, pano, raio_sol, terreno, torno
from contatos import contornar_haste, levantar_mao, trajeto
from paisagem import bananeira, cacaueiro, vento
from personagens import Braco, Mao, Pessoa, transformar
from solo import chuva, decompor, folha_seca, folíolo_jovem, muda, semente_andiroba


def andirobeira(local,escala=1):
    r=agrupar("Andirobeira adulta",local)
    r.scale=(escala,)*3
    casco=material("Casca da andirobeira","594538","9c8161",25,.038,.88)
    folha=material("Verde do dossel de andiroba","36543c","6c9460",18,.022,.58)
    veio=material("Nervura do dossel","66734b","9bab71",36,.009)
    sombra=material("Copa da andirobeira","2d4f3a","6b8553",21,.025)
    torno("Tronco retilíneo",[(0,.242),(.17,.188),(.52,.147),(1.36,.134),
          (2.03,.112),(2.54,.091),(3.18,.062),(3.49,.024)],casco,r,ondulacao=.031)
    copa=[]
    for i in range(7):
        a=i*2*pi/7
        g=agrupar("Ramo superior",(0,0,2.28+i*.102),r)
        g.rotation_euler.z=a
        fico=.47+.13*(i%4)
        fio("Garfo da copa",[(0,0,0),(.019,.40,fico*.41),(.027,.79,fico*.78),(.088,1.29,fico)],
            .062-.005*i,casco,g)
        for j in range(3):
            x=(-1)**j*(.22+.11*j)
            y=.63+j*.34
            z=fico+.106*j
            oval("Copa ao fundo",(x,y,z),(.41+.08*j,.54,.25+.016*j),
                 sombra,g,1)
        for j in range(3):
            f=agrupar("Folha composta da andirobeira",(.055,.58+j*.29,fico+.069*j),g)
            f.rotation_euler=(.16-.14*j,(-1)**i*.12,(-1)**j*(.39+.12*j))
            fio("Raque de andiroba",[(0,0,0),(0,.27,.076),(0,.66,.028),(0,.88,-.082)],.008,veio,f)
            for k in range(4):
                for lado in (-1,1):
                    o=folíolo_jovem(f,folha,veio)
                    o.location=(0,.18+k*.196,.05+.026*sin(k*1.45)-.026*k)
                    o.rotation_euler=(.09-.073*k,lado*.21,lado*(1.10-.11*k))
                    o.scale=(1.26-.133*k,)*3
            copa.append((f,f.rotation_euler.copy()))
    return copa


def palha(nivel,area,semente=41,excluir=(),quantidade=24):
    rng=Random(semente)
    x0,x1,y0,y1=area
    partes=[]
    for i in range(quantidade):
        x,y=rng.uniform(x0,x1),rng.uniform(y0,y1)
        if any((x-a)**2+(y-b)**2<c*c for a,b,c in excluir):
            continue
        r=folha_seca((x,y,nivel(x,y)+.017+.011*(i%3)),escala=rng.uniform(.42,.89),
                      angulo=rng.uniform(-pi,pi),cor=i,curva=.55+.19*(i%3),detalhe=i%4==0)
        partes.append(r)
    return partes


def bosque():
    iluminacao("dia",(.02,.24,1.23))
    raio_sol("Sol filtrado pelas copas",(-2.36,-.41,4.43),(0,.11,.42),326,(1,.84,.57),2.88)
    ceu(False)
    nivel=terreno(y_fundo=16,limpar=((-0.60,.2,.54),(.64,.33,.54),(0,-.24,.35)))
    arvore=andirobeira((-1.46,2.81,nivel(-1.46,2.81)),1.09)
    bananas=bananeira((1.53,2.48,nivel(1.53,2.48)),1.15)
    cacaueiro_1=cacaueiro((1.04,1.61,nivel(1.04,1.61)),.80)
    cacaueiro_2=cacaueiro((-.99,1.06,nivel(-.99,1.06)),.69,2)
    mata()
    palha(nivel,(-1.8,1.58,-1.9,2.1),excluir=((-0.60,.2,.47),(.64,.33,.49)),quantidade=47)
    cesto((-1.16,.65,nivel(-1.16,.65)+.014),.48,alca=True)
    return nivel,arvore,bananas,cacaueiro_1+cacaueiro_2


def chegada_folha(f,t,u,nivel,centro_x=.06,centro_y=-.35):
    g=regime(u,.024,.67)
    alto=1-g
    x=centro_x-.58*alto+.148*sin(g*pi*3.5)*alto
    y=centro_y+alto*1.63-.14*sin(pi*g)*alto
    z=nivel(x,y)+.045+3.23*alto
    f.location=(x,y,z)
    f.rotation_euler=(.63*sin(g*pi*6)*alto,.73*sin(g*pi*3.5)*alto,-.71+1.2*alto-.39*sin(4*pi*g)*alto)


def abertura(elenco=None):
    nivel,arvores,bananas,cacau=bosque()
    if elenco:
        posar_elenco = elenco(nivel, retorno=False)
    else:
        d=Pessoa("Dona Luzia",(-.65,.45,.057),velha=True,escala=.95)
        r=Pessoa("Rafael",(.63,.47,.052),escala=.93)
    folha=folha_seca((0,0,0),escala=1.0,curva=.72,cor=0)
    folha2=folha_seca((0,0,0),escala=.70,curva=.86,cor=2,detalhe=False)
    cam=camera(9)
    def animar(t,u):
        chegada_folha(folha,t,u,nivel)
        g=regime(u,.19,.85)
        folha2.location=(.99-.47*g,.93-.79*g,nivel(.52,.14)+.041+2.67*(1-g))
        folha2.rotation_euler=(.69*sin(14*g)*(1-g),-.6*sin(9*g)*(1-g),.58+1.9*g)
        if elenco:
            posar_elenco(t,u)
        else:
            gesto=regime(u,.23,.77)
            d.pose(t,giro=.25,olhar=(.36,.03+.27*gesto),direita=(.43,-.27,.23-.10*gesto),
                   esquerda=(-.33,-.15,.10),rumos=(None,(.20,-.64,-.71)),aperto=(.39,.12),apoio=nivel)
            r.pose(t+.39,giro=-.26,olhar=(-.20,.11+.24*gesto),esquerda=(-.34,-.21,.31-.13*gesto),
                   direita=(.37,-.14,.058),rumos=((-.50,-.65,-.49),None),aperto=(.29,.34),apoio=nivel)
        vento(arvores,t,.029)
        vento(bananas,t,.052)
        vento(cacau,t,.039)
        cam((.48-.33*u,-6.19+.58*u,2.64-.32*u),(0,.29,1.92-.28*u),
            4.56-.46*u,foco=(.01,.36,1.52))
    return animar


def cobertura(elenco_mao=None):
    iluminacao("dia",(-.07,-.13,.75))
    ceu(False)
    nivel=terreno(limpar=((.19,-.20,.45),))
    mata()
    veg=bananeira((1.81,1.55,nivel(1.81,1.55)),.72)
    cacau=cacaueiro((-1.48,.86,nivel(-1.48,.86)),.71)
    palha(nivel,(-1.58,1.47,-1.32,1.58),excluir=((.03,-.37,.28),),quantidade=54)
    calda=folha_seca((-.27,-.61,nivel(-.27,-.61)+.035),escala=1.06,angulo=-.47,cor=2)
    ramo=agrupar("Ramo fino da poda")
    galho=material("Fibra do ramo podado","61452e","a4875f",35,.026)
    fio("Ramo podado",[(-.49,.052,-.019),(-.25,.002,0),(0,.02,.014),(.28,-.043,.025),
                      (.49,-.083,.073)],.020,galho,ramo)
    for x,y,z,a in ((-.38,.05,0,-.49),(-.28,0,.019,.47),(-.09,.014,.012,-.64),
                    (.15,-.02,.025,.59),(.31,-.04,.039,-.37)):
        fio("Raminho",[ (x,y,z),(x+.086,y+.116,z+.018),(x+.13,y+.126,z+.033)],
            .007,galho,ramo)
        folha_seca((x+.107,y+.11,z+.028),escala=.54,angulo=a+.4,cor=int((x+.5)*12),curva=.44,detalhe=False).parent=ramo
    if elenco_mao:
        mao,braco=elenco_mao("female",1.05)
    else:
        pele=material("Pele de Luzia","865139","bd8768",34,.006,.66)
        mao=Mao("Mão de Dona Luzia",pele,escala=1.05)
        braco=Braco(pele,pano("285752","63867a"),pano("335f56","749085"),None)
    cam=camera(6.35)
    def animar(t,u):
        baixa=regime(u,.15,.66)
        solta=regime(u,.69,.98)
        ramo.location=(.22-.36*baixa,-.13-.11*baixa,nivel(-.14,-.24)+.105+.66*(1-baixa))
        ramo.rotation_euler=(.09*(1-baixa),-.16*(1-baixa),-.22+.39*baixa)
        pegada=transformar(ramo,(.249,-.037,.032))+Vector((.61*solta,-.09*solta,.43*solta))
        rumo=(-.84,-.19,-.39)
        p=mao.punho(pegada,rumo,.62)
        mao.pose(p,rumo,.68-.57*solta,giro=.62)
        contornar_haste(mao,transformar(ramo,(-.08,.01,.016)),(.93,.30,.042),.020,.46,.005)
        p=levantar_mao(mao,nivel,.009)
        braco.pose(Vector((2.68,.42,1.88)),Vector((1.42,.17,1.26)),p)
        calda.rotation_euler.x=.027*sin(t*2.3)
        vento(veg,t,.036)
        vento(cacau,t,.028)
        cam((-.51+.27*u,-3.53+.27*u,1.84-.27*u),(-.08,-.18,.32-.15*u),
            2.22,foco=(-.09,-.24,.16))
    return animar


def plantio(elenco_mao=None):
    iluminacao("dia",(-.05,-.06,.82))
    ceu(False)
    nivel=terreno(limpar=((-.16,-.23,.41),))
    mata()
    cacau=cacaueiro((-1.04,.84,nivel(-1.04,.84)),.79)
    bal=bananeira((1.65,2.21,nivel(1.65,2.21)),.87)
    palha(nivel,(-1.76,1.42,-1.22,1.49),excluir=((-.16,-.25,.42),),quantidade=51)
    folhagem=[]
    formas=[(.12,-.13,1.10),(-.38,-.038,-.51),(.15,-.40,1.02),(-.41,-.37,-1.89)]
    for i,(x,y,a) in enumerate(formas):
        o=folha_seca((x,y,nivel(x,y)+.027),escala=.47+.05*i,
                     angulo=a,cor=i,curva=.39,detalhe=True)
        folhagem.append((o,Vector((x,y,0)),Vector(((-1)**i*(.19+.026*i),.03*(i%3-1),0)),a))
    if elenco_mao:
        mao,braco=elenco_mao("male",1.23)
    else:
        pele=material("Pele de Rafael","815039","c1885c",34,.006,.66)
        mao=Mao("Rafael com a semente",pele,escala=1.23)
        braco=Braco(pele,pano("966735","c39758"),pano("ad7545","daa766"),None)
    s=semente_andiroba((0,0,0),.38)
    cam=camera(6.26)

    def gesto(u):
        p=mover_tempo(u,[(0,(.65,.13,1.32)),(.33,(.23,-.069,.66)),(.44,(.23,-.086,.536)),
                          (.57,(.45,-.029,.64)),(.72,(.53,-.084,.456)),(.91,(.26,-.066,.351)),
                          (1,(.50,.03,.74))])
        solta=regime(u,.36,.54)
        mao.pose(p,(-.79,-.37,-.42),.69-.54*solta,giro=.53+.41*solta)
        return levantar_mao(mao,nivel,.008)
    inicio=.444
    gesto(inicio)
    encaixe=(.012,-.107,.177)
    origem=transformar(mao.raiz,encaixe)
    fim=(-.158,-.21,nivel(-.158,-.21)+.051)

    def animar(t,u):
        p=gesto(u)
        braco.pose(Vector((2.54,.60,2.16)),Vector((1.48,.15,1.38)),p)
        if u<inicio:
            s.location=transformar(mao.raiz,encaixe)
            f=0
        else:
            s.location,f=trajeto(u,inicio,.146,origem,fim,.019)
        s.rotation_euler=(.32*sin(pi*f),.54*sin(pi*f),.22+.96*f)
        for i,(o,piso,d,a) in enumerate(folhagem):
            abrir=regime(u,.06+.022*i,.28+.026*i)
            voltar=regime(u,.68+.016*i,.90+.013*i)
            m=abrir*(1-voltar)
            loc=piso+d*m
            o.location=(loc.x,loc.y,nivel(loc.x,loc.y)+.024+.03*sin(pi*m))
            o.rotation_euler=(.16*sin(pi*m),-.11*sin(pi*m),a-.23*m)
        vento(cacau,t,.031)
        vento(bal,t,.039)
        cam((-.48+.31*u,-3.47+.27*u,1.89),(-.07,-.20,.43),2.34,foco=(-.14,-.23,.20))
    return animar


def retorno(elenco=None):
    nivel,arvores,bananas,cacau=bosque()
    if elenco:
        posar_elenco = elenco(nivel, retorno=True)
    else:
        d=Pessoa("Dona Luzia",(-.68,.88,.061),velha=True,escala=.95)
        r=Pessoa("Rafael",(.57,.89,.050),escala=.93)
    x,y=-.04,-.52
    broto=agrupar("Muda plantada", (x,y,nivel(x,y)))
    folha_mat=material("Folhas jovens de andiroba","3f6a43","9bad60",21,.012,.49)
    veio=material("Eixo de andiroba","617f46","b1b875",24,.008)
    fio("Tronco fino da andiroba",[(0,0,0),(.032,-.012,.23),(.008,.018,.46),(.05,0,.752)],
        .026,veio,broto)
    eixos=[]
    for i,(x,y,z,t) in enumerate(((.016,0,.401,2.41),(.019,.012,.584,-.80),(.046,.001,.725,1.61))):
        g=agrupar("Folha alterna da muda",(x,y,z),broto)
        g.rotation_euler=(.23+.08*i,0,t)
        fio("Raque",[(0,0,0),(0,.18,.048),(0,.382,.064)],.008,veio,g)
        for k in range(3):
            for lado in (-1,1):
                f=folíolo_jovem(g,folha_mat,veio)
                f.location=(0,.085+k*.118,.022+k*.017)
                f.rotation_euler=(.18+.028*k,lado*.17,lado*(1.09-.13*k))
                f.scale=(.62-.06*k,)*3
        eixos.append((g,g.rotation_euler.copy()))
    f=folha_seca((0,0,0),escala=.93,curva=.69,cor=0)
    cam=camera(8)
    def animar(t,u):
        chegada_folha(f,t,u,nivel,.32,-.76)
        if elenco:
            posar_elenco(t,u)
        else:
            g=regime(u,.18,.77)
            d.pose(t,giro=.23,olhar=(.32,.10+.22*g),direita=(.42,-.39,.19-.082*g),
                   esquerda=(-.31,-.23,.068),aperto=(.44,.14),rumos=(None,(.36,-.59,-.77)),apoio=nivel)
            r.pose(t+.18,giro=-.18,olhar=(-.22,.13+.19*g),esquerda=(-.39,-.35,.24-.16*g),
                   direita=(.35,-.18,.131),aperto=(.23,.37),rumos=((-.60,-.37,-.63),None),apoio=nivel)
        vento(arvores,t,.028)
        vento(bananas,t,.048)
        vento(cacau,t,.030)
        vento(eixos,t,.040)
        cam((.36-.32*u,-5.43+.58*u,2.32-.38*u),(0,.24,1.26-.14*u),
            3.59-.26*u,foco=(.01,-.22,.96))
    return animar


PLANOS={"copa":abertura,"palhada":cobertura,"chuva":chuva,"decomposicao":decompor,
        "plantio":plantio,"muda":muda,"ciclo":retorno}
