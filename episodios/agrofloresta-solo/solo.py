"""Cortes animados do chão e da plântula de Carapa guianensis."""

from math import cos, pi, sin
from random import Random

from mathutils import Vector

from cenas import camera, regime
from cenografia import agrupar, brilho, fio, iluminacao, malha, material, oval, raio_sol
from germinacao import atualizar, rama
from personagens import superficie


PALETA_FOLHAS = (
    ("7d5534", "b88b50"),
    ("624327", "9d6640"),
    ("835c39", "cf9e57"),
    ("544734", "967249"),
)


def pos_folha(u,v,c):
    w=.155*max(.012,sin(u*pi)**.79)*(1-.27*u)
    return (w*v,.586*u,
            c*(.096*sin(u*pi)+.050*u*u+.043*abs(v)**1.5*sin(u*5.4))
            +.009*v*sin(u*21))


def parte_folha(pai,mat,a,b,curva):
    vs=[pos_folha(a+(b-a)*j/6,2*i/6-1,curva) for j in range(7) for i in range(7)]
    fs=[]
    for j in range(6):
        for i in range(6):
            q=j*7+i
            fs.append((q,q+1,q+8,q+7))
    m=malha("Lâmina da folha",vs,fs,mat,pai,True)
    m.modifiers.new("Espessura","SOLIDIFY").thickness=.003
    return m


def folha_seca(local,*,escala=1,angulo=0,cor=0,curva=1,detalhe=True):
    r=agrupar("Folha de serapilheira",local)
    r.scale=(escala,)*3
    r.rotation_euler.z=angulo
    a,b=PALETA_FOLHAS[cor%len(PALETA_FOLHAS)]
    mat=material("Folha seca "+a,a,b,45,.018,.83)
    parte_folha(r,mat,0,1,curva)
    if detalhe:
        nervura=material("Veios da folha seca","90714b","c6a273",30,.009)
        fio("Veio seco",[(x,y,z+.005) for x,y,z in
            (pos_folha(i/9,0,curva) for i in range(10))],.004,nervura,r)
        for i in range(3):
            p=.20+i*.19
            for lado in (-1,1):
                fio("Ramificação do veio",[(x,y,z+.004) for x,y,z in
                     (pos_folha(p+.14*j/3,lado*j*.30,curva) for j in range(4))],
                     .0018,nervura,r)
    return r


def semente_andiroba(local=(0,0,0),escala=1):
    raiz=agrupar("Semente de andiroba",local)
    raiz.scale=(escala,)*3
    mat=material("Tegumento da andiroba","352723","795138",35,.012,.48)
    # Facetas do tegumento e duas extremidades arredondadas da semente.
    vs=[(-.274,-.064,.008),(-.144,-.136,-.102),(.125,-.107,-.122),(.254,-.041,-.038),
        (.231,.057,.092),(.081,.121,.166),(-.120,.110,.136),(-.248,.066,.060),
        (-.084,-.115,.122),(.114,-.103,.141),(.076,.102,-.101),(-.137,.089,-.093)]
    faces=[(0,1,2,3,9,8),(3,4,5,9),(8,9,5,6),(0,8,6,7),
           (3,2,10,4),(4,10,11,7,6,5),(7,11,1,0),(1,11,10,2)]
    m=superficie("Semente angular arredondada",vs,faces,mat,raiz,0)
    b=m.modifiers.new("Cantos arredondados","BEVEL")
    b.width=.024
    b.segments=3
    m.modifiers.new("Normais da casca","WEIGHTED_NORMAL")
    oval("Marca do hilo",(.212,-.056,-.018),(.032,.009,.022),
         material("Cicatriz da andiroba","684632","91694c",29,.007),raiz,1)
    return raiz


def solo_altura(x):
    return .017*sin(9*x+.8)+.016*sin(15*x-1.9)


def perfil_solo():
    rng=Random(71)
    limites=(0,-.145,-.65,-1.47)
    mats=(
        material("Horizonte dos resíduos decompostos","59402d","866445",25,.049,.89),
        material("Solo sob a serapilheira","69422e","a66e4b",35,.054,.87),
        material("Camada mais profunda","694d3c","967354",33,.040,.89),
    )
    n=44
    for k,mat in enumerate(mats):
        vs=[]
        for i in range(n+1):
            x=-1.27+i*2.54/n
            y=.012*sin(13*x)+.009*cos(8*x)
            b=limites[k]+solo_altura(x)*(.72 if k else 1)
            c=limites[k+1]+solo_altura(x)*.72
            vs.extend(((x,y,b),(x,y,c),(x,1.24,b),(x,1.24,c)))
        fs=[(0,2,3,1),(4*n,4*n+1,4*n+3,4*n+2)]
        for i in range(n):
            q=i*4
            fs.extend(((q,q+4,q+5,q+1),(q,q+2,q+6,q+4),
                (q+1,q+5,q+7,q+3),(q+2,q+3,q+7,q+6)))
        malha("Camada de solo exposta",vs,fs,mat)
    cores=[material("Agregado de argila","76543c","aa7f5c",26,.021),
           material("Fragmento escuro","4d3928","836147",42,.016)]
    for i in range(89):
        x,z=rng.uniform(-1.19,1.19),rng.uniform(-1.40,-.036)
        r=rng.uniform(.009,.049)
        p=oval("Agregado na face do solo",(x,-.012,z),(r,r*.48,r*.61),cores[i%2],detalhe=1)
        p.rotation_euler.y=rng.uniform(-pi,pi)
    return mats


def solo_umedecido(mat):
    """A cor muda somente no volume de terra umedecido."""
    nos=mat.node_tree.nodes
    link=mat.node_tree.links.new
    cor=nos["Principled BSDF"].inputs["Base Color"]
    textura=cor.links[0].from_socket
    geom=nos.new("ShaderNodeNewGeometry")
    separar=nos.new("ShaderNodeSeparateXYZ")
    link(geom.outputs["Position"],separar.inputs[0])
    limites=[]
    for eixo,a,b in (("X",-.12,.49),("Z",-.312,.058)):
        r=nos.new("ShaderNodeMapRange")
        r.interpolation_type="SMOOTHSTEP"
        r.inputs["From Min"].default_value=a
        r.inputs["From Max"].default_value=b
        link(separar.outputs[eixo],r.inputs["Value"])
        limites.append(r.outputs["Result"])
    regiao=nos.new("ShaderNodeMath")
    regiao.operation="MULTIPLY"
    link(limites[0],regiao.inputs[0])
    link(limites[1],regiao.inputs[1])
    intensidade=nos.new("ShaderNodeMath")
    intensidade.operation="MULTIPLY"
    link(regiao.outputs[0],intensidade.inputs[0])
    m=nos.new("ShaderNodeMixRGB")
    m.blend_type="MULTIPLY"
    m.inputs[2].default_value=(.43,.52,.46,1)
    link(intensidade.outputs[0],m.inputs[0])
    link(textura,m.inputs[1])
    link(m.outputs[0],cor)
    return intensidade.inputs[1]


def fundo_macro(ambiente="33504a"):
    mat=brilho("Fundo da seção do solo",ambiente,.61)
    malha("Fundo do corte", [(-10,3,-5),(10,3,-5),(10,3,6),(-10,3,6)],
          [(0,1,2,3)],mat)


def camada_folhas(*,direita=False):
    rng=Random(63)
    folhagem=[]
    n=15 if direita else 25
    for i in range(n):
        x=rng.uniform(.12 if direita else -1.12,1.10)
        y=rng.uniform(.023,.92)
        e=rng.uniform(.36,.82)
        o=folha_seca((x,y,solo_altura(x)+.015+.015*(i%4)),escala=e,
                     angulo=rng.uniform(-pi,pi),cor=i,curva=.41+.14*(i%4),detalhe=(i%3==0))
        folhagem.append((o,o.rotation_euler.copy(),o.location.copy()))
    return folhagem


def chuva():
    iluminacao("dia",(0,0,.26))
    raio_sol("Luz fria da chuva",(1.27,-1.0,4.9),(0,0,-.02),235,(.67,.84,1),3.4)
    fundo_macro("344e4f")
    horizonte=perfil_solo()
    umidade=[solo_umedecido(m) for m in horizonte[:2]]
    folhas=camada_folhas(direita=True)
    terra=material("Terra atingida pela chuva","5b3a29","98724c",32,.024)
    agua=material("Gotas de chuva","4b767c","b7d1c6",42,.004,.20)
    aclara=material("Brilho das gotas","77a09e","c4dad0",44,.002,.17)
    rng=Random(81)
    gotas=[]
    for i in range(24):
        x=rng.uniform(-1.10,1.10)
        y=rng.uniform(.021,.66)
        r=rng.uniform(.011,.020)
        ob=oval("Gota em queda",(0,0,0),(r,r*.86,r*2.2),agua if i%3 else aclara,detalhe=1)
        gotas.append((ob,x,y,r,rng.random(),rng.uniform(.82,1.62)))
    particulas=[]
    for i in range(24):
        o=oval("Agregado lançado pelo impacto",(0,0,0),(.014,.012,.011),terra,detalhe=1)
        particulas.append((o,rng.uniform(-1.08,-.20),rng.uniform(.045,.36),rng.random(),rng.uniform(-.26,.26)))
    cam=camera(8.8)

    def animar(t,u):
        for o,x,y,r,defas,vel in gotas:
            f=(t*.73+defas)%1
            nivel=solo_altura(x)+(.062 if x>.07 else .017)
            o.location=(x+.068*(1-f),y,nivel+(1.10+.42*vel)*(1-f*f))
            o.rotation_euler.y=-.10
            o.hide_render=f>.987
        for o,x,y,defas,m in particulas:
            q=((t*.94+defas)%1)/.27
            o.hide_render=q>1
            z=solo_altura(x)+.1*sin(pi*min(1,q))
            o.location=(x+m*min(1,q),y+.08*min(1,q),z+.017)
            o.rotation_euler=(q*.76,q*.51,defas)
        for i,(o,base,p) in enumerate(folhas):
            g=(t*.80+i*.216)%1
            incl=.052*sin(g*pi*5)*(1-g)**2
            o.rotation_euler=(base.x+incl,base.y,base.z)
            o.location=p
        for intensidade in umidade:
            intensidade.default_value=.85*regime(u,.27,.94)
        cam((.30-.17*u,-5.96,2.42-.29*u),(-.02,.13,-.07-.18*u),2.97,
            foco=(0,.09,-.102))
    return animar


def decompor():
    iluminacao("dia",(0,0,-.14))
    raio_sol("Interior úmido do solo",(-1.05,-2.82,1.0),(0,0,-.55),146,(.72,.84,1),2.7)
    fundo_macro("334e43")
    camada=perfil_solo()[0]
    folhas=camada_folhas()
    raiz=material("Raiz em atividade","9a7855","c4a378",23,.017)
    hifas=material("Filamentos claros","b3ad8e","d3c7a8",40,.005)
    particulas=material("Matéria orgânica fina","42352a","705440",42,.024)
    veiosa=material("Folha em decomposição","735035","b68455",31,.042)
    fluxo=brilho("Símbolo de nutrientes","d4a95a",.62)
    tecidos=[]
    amarelo=[]
    rng=Random(271)
    for i in range(5):
        x=-.62+i*.225
        pai=agrupar("Folha em fragmentação",(x,-.076,.036+.012*i))
        pai.rotation_euler.z=-1.17+i*.69
        partes=[]
        for j in range(7):
            a,b=j/7,(j+1)/7
            o=parte_folha(pai,veiosa,a+.003,b-.003,1.32)
            partes.append((o,rng.uniform(-.09,.10),rng.uniform(-.029,.074),rng.uniform(.19,.37)))
        tecidos.append(partes)
    redes=[]
    for i in range(17):
        x=rng.uniform(-.91,.77)
        z=solo_altura(x)-.02-rng.uniform(0,.15)
        ramo=rama("Filamento de decompositores",
            [(x,-.067,z),(x+.041,-.074,z-.04),(x+.083,-.082,z-.011),
             (x+.131,-.08,z-.056),(x+.178,-.072,z-.083)],.0025,hifas)
        redes.append(ramo)
    for i in range(31):
        x,z=rng.uniform(-1.07,1.04),rng.uniform(-.29,-.052)
        r=rng.uniform(.009,.026)
        p=oval("Partícula incorporada",(x,-.038,z),(r,r*.54,r*.72),particulas,detalhe=1)
        amarelo.append((p,x,z,r,i))
    pontos=[(.67,-.069,.012),(.62,-.075,-.235),(.53,-.083,-.477),(.34,-.09,-.683),
            (.25,-.085,-1.01)]
    principal=rama("Raiz vizinha",pontos,.031,raiz)
    for j,a in enumerate(principal.data.splines[0].bezier_points):
        a.radius=1-.193*j
    for i,(x,y,z) in enumerate(pontos[1:-1]):
        lado=(-1)**i
        p=rama("Ramificação da raiz vizinha",[(x,y,z),(x+lado*.07,y-.003,z-.071),
             (x+lado*.16,y-.020,z-.137),(x+lado*(.246-.038*i),y-.016,z-.226)],.012,raiz)
        for j,a in enumerate(p.data.splines[0].bezier_points):
            a.radius=.91-.248*j
    nutrientes=[]
    for i in range(11):
        x=rng.uniform(-.49,.5)
        o=oval("Traço esquemático de nutriente",(0,0,0),(.018,)*3,fluxo,detalhe=1)
        nutrientes.append((o,x,i))
    cam=camera(8.1)

    def animar(t,u):
        for i,partes in enumerate(tecidos):
            for j,(o,x,y,v) in enumerate(partes):
                f=regime(u,.26+.035*j+.020*i,.55+.043*j+.024*i)
                o.location=(x*f,y*f,-v*f)
                o.rotation_euler.y=.32*f
                o.scale=(1-.64*f,1-.66*f,1-.81*f)
                o.hide_render=f>.96
        for i,r in enumerate(redes):
            f=regime(u,.056+.014*i,.33+i*.014)
            r.hide_render=f<.012
            r.data.bevel_factor_end=f
        for p,x,z,r,i in amarelo:
            f=regime(u,.21+.011*i,.55+.009*i)
            p.hide_render=f<.012
            p.location=(x,-.045,z+.12*(1-f))
            p.scale=(r*f,r*.57*f,r*.70*f)
        for i,(obj,r,p) in enumerate(folhas):
            f=regime(u,.52+.012*(i%7),.88)
            obj.location=p+Vector((0,0,-.023*f))
            obj.scale=(obj["escala"]*(1-.16*f),)*3
        cores=camada.node_tree.nodes
        rampa=next(n for n in cores if n.type=="VALTORGB")
        f=regime(u,.32,.86)
        rampa.color_ramp.elements[0].color=(.10-.065*f,.056-.036*f,.032-.020*f,1)
        rampa.color_ramp.elements[1].color=(.19-.095*f,.133-.070*f,.083-.051*f,1)
        for i,(o,x,ind) in enumerate(nutrientes):
            q=(u-.59-i*.016)/.23
            o.hide_render=not 0<q<1
            if not o.hide_render:
                o.location=(x+(.40-x)*q*.40,-.117,-.105-(.40+.043*(i%4))*q)
                o.scale=(.008+.010*sin(pi*q),)*3
        cam((.30-.30*u,-5.71,1.88-.45*u),(.02,.045,-.324+.03*u),2.63,
            foco=(0,-.087,-.39))

    for obj,_,_ in folhas:
        obj["escala"]=obj.scale.x
    return animar


def folíolo_jovem(pai,mat,veio):
    r=agrupar("Folíolo jovem",pai=pai)
    vs=[]
    faces=[]
    n,c=15,6
    for j in range(n+1):
        u=j/n
        w=.086*max(.012,sin(pi*u)**.83)*(1-.31*u)
        for i in range(c+1):
            p=2*i/c-1
            vs.append((w*p,.372*u,.052*sin(pi*u)-.071*u*u-abs(p)*w*.25))
    for j in range(n):
        for i in range(c):
            k=j*(c+1)+i
            faces.append((k,k+1,k+c+2,k+c+1))
    m=malha("Folíolo lanceolado",vs,faces,mat,r,True)
    m.modifiers.new("Cutícula","SOLIDIFY").thickness=.002
    fio("Nervura do folíolo",[(0,.372*i/8,.052*sin(pi*i/8)-.071*(i/8)**2+.003)
                              for i in range(9)],.0031,veio,r)
    return r


def muda():
    iluminacao("dia",(0,0,.32))
    raio_sol("Luz sobre o broto",(1.69,1.18,3.7),(-.02,.01,.51),255,(1,.85,.62),2.83)
    fundo_macro("304e43")
    perfil_solo()
    folhas_secas=camada_folhas()
    for o,_,p in folhas_secas:
        if abs(p.x)<.17:
            o.location.x+=.32 if p.x>0 else -.32
    semente=semente_andiroba((-.182,-.186,-.218),1.11)
    semente.rotation_euler=(.02,-.12,.04)
    raiz=material("Raiz primária da andiroba","8a634b","b7946e",35,.011)
    lateral=material("Raízes secundárias claras","aa885f","c9a985",41,.007)
    verde=material("Epicótilo de andiroba","4b6644","89a164",30,.012,.52)
    folha_mat=material("Folhas da andirobeira jovem","386044","799851",28,.013,.46)
    nerv=material("Nervuras jovens de andiroba","729253","a5b880",38,.007)
    b=Vector((.082,-.222,-.256))

    def rp(q):
        return b+Vector((.064*sin(q*3.7)-.080*q*q,-.017-.021*sin(q*2.8),-.996*q))

    prim=rama("Primeira raiz",[rp(i/10) for i in range(11)],.030,raiz)
    for i,p in enumerate(prim.data.splines[0].bezier_points):
        p.radius=1-.089*i
    raizes=[]
    for i,x in enumerate((.17,.229,.321,.403,.491,.566,.657,.744,.80)):
        a=rp(x)
        lado=(-1)**i
        compr=.147+.049*(i%4)
        pontos=[a+Vector((lado*compr*j/5,-.013*sin(j*pi/5),-.15*(j/5)**1.60)) for j in range(6)]
        q=rama("Raiz lateral fina",pontos,.010,lateral)
        for j,p in enumerate(q.data.splines[0].bezier_points):
            p.radius=.91-.17*j
        raizes.append(q)
    caule=rama("Epicótilo nascente",[(0,0,.05*i) for i in range(8)],.034,verde)
    for i,p in enumerate(caule.data.splines[0].bezier_points):
        p.radius=1.03-.079*i
    catáfilos=[]
    for i in range(4):
        cat=oval("Catáfilo", (0,0,0),(.029,.020,.064),verde)
        catáfilos.append(cat)
    ramal=[]
    for lado in (1,-1):
        co=agrupar("Folha alterna composta")
        pec=rama("Raque da folha",[(0,0,0)]*7,.008,nerv,co)
        c=[]
        for j in range(3):
            for i in (-1,1):
                f=folíolo_jovem(co,folha_mat,nerv)
                c.append((j,i,f))
        ramal.append((lado,co,pec,c))
    cam=camera(8.75)

    def animar(t,u):
        f=regime(u,.072,.60)
        prim.data.bevel_factor_end=f
        prim.hide_render=f<.012
        for i,o in enumerate(raizes):
            g=regime(u,.25+.035*i,.58+.033*i)
            o.data.bevel_factor_end=g
            o.hide_render=g<.015
        grow=regime(u,.243,.858)
        altura=1.57*grow
        def ponto(p):
            curva=.11*sin(p*pi*.91)+.048*p*p*(1-grow)
            return b+Vector((curva, .020*sin(p*pi)+.061*p*p*grow,
                altura*p-.065*p*p*(1-grow)))
        atualizar(caule,[ponto(j/7) for j in range(8)])
        caule.hide_render=grow<.017
        for i,cat in enumerate(catáfilos):
            f=regime(u,.38+i*.072,.49+i*.062)
            cat.hide_render=f<.018
            cat.location=ponto(.325+i*.115)+Vector((-.021 if i%2 else .021,-.007,0))
            cat.rotation_euler=(.18,.38*(-1)**i,.03)
            cat.scale=(.028*f,.014*f,.045*f)
        for i,(lado,co,pec,ramos) in enumerate(ramal):
            e=regime(u,.669+i*.054,.989+i*.007)
            co.hide_render=e<.009
            co.location=ponto(1-.143*i)
            co.rotation_euler=(.12,.11*lado,-lado*(1.30+.10*sin(t*1.4)*e))
            atualizar(pec,[(0,.50*e*j/6,.15*e*sin(j*pi*.81/6)) for j in range(7)])
            for j,sinal,r in ramos:
                g=regime(e,.17+j*.122,.78+j*.061)
                a=.111+.149*j
                r.location=(0,a*e,.15*e*sin(pi*.81*a/.50))
                r.rotation_euler=(.22-.44*(1-g),sinal*.40,sinal*(.93-.12*j))
                r.scale=(g*(.92-.108*j),)*3
                r.hide_render=g<.009
        c=regime(u,.32,.87)
        cam((.26-.18*u,-5.77,1.16+1.30*c),(-.035,-.038,-.42+.955*c),
            2.27+.43*c,foco=(.04,-.195,-.14+.64*c))
    return animar
