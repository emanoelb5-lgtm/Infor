"""Superfícies de apoio, pontos de pegada e trajetórias dos objetos."""

from math import cos, pi, sin

from mathutils import Vector

from cenografia import fio, malha, material
from personagens import coordenadas, matriz


def levantar_mao(mao, altura, distancia=0.004, exato=False):
    m = matriz(mao.raiz)
    pontos = [m @ Vector(ponto) for ponto in mao.vertices]
    folga = min(p.z-altura(p.x,p.y) for p in pontos)
    ajuste = distancia-folga
    if exato or ajuste>0:
        mao.raiz.location.z += ajuste
    return mao.raiz.location.copy()


def contornar_haste(mao, base, eixo, raio, comprimento, folga=.004):
    """Ajusta as superfícies da pegada ao contorno de uma alça ou lápis."""
    m=matriz(mao.raiz)
    volta=m.inverted()
    origem=Vector(base)
    d=Vector(eixo).normalized()
    for i,co in enumerate(mao.vertices):
        ponto=m@Vector(co)
        deslocamento=ponto-origem
        s=deslocamento.dot(d)
        if not 0<s<comprimento:
            continue
        radial=deslocamento-s*d
        limite=raio+folga
        if .00001<radial.length<limite:
            mao.vertices[i]=tuple(volta@(origem+s*d+radial.normalized()*limite))
    coordenadas(mao.obj,mao.vertices)


def trajeto(u, instante, duracao, origem, apoio, ressalto=.02):
    """A saliência de queda termina acima do apoio e amortiza o impacto."""
    q=(u-instante)/duracao
    s=max(0,min(1,q))
    p=Vector(origem).lerp(Vector(apoio),s)
    p.z=origem[2]+(apoio[2]-origem[2])*(.36*s+.64*s*s)
    if 1<q<1.36:
        p.z+=ressalto*sin(pi*(q-1)/.36)
    return p,s


def nivel_tigela(x,y,centro,fator):
    r=((x-centro[0])**2+(y-centro[1])**2)**.5/fator
    curva=((0,.085),(.25,.092),(.41,.19),(.49,.33),(.52,.35))
    for (a,z),(b,w) in zip(curva,curva[1:]):
        if r<=b:
            return centro[2]+fator*(z+(w-z)*max(0,(r-a)/(b-a)))
    return centro[2]+fator*.35


def orla_saco(pai):
    """Aba, paredes externa e interna formam o mesmo tecido."""
    juta=material("Juta do saco","897351","c6ad83",122,.019,.84)
    linha=material("Trama costurada","ad8a5a","d7b990",93,.009,.84)
    secoes=(
        (-.620,.050,.032),(-.594,.205,.155),(-.521,.303,.228),(-.410,.362,.269),
        (-.258,.396,.296),(-.108,.382,.278),(.036,.310,.224),(.133,.296,.215),
        (.198,.332,.250),(.241,.335,.260),(.260,.326,.250),
        (.258,.301,.226),(.236,.306,.228),(.195,.304,.219),(.116,.274,.189),
        (.019,.290,.198),(-.124,.353,.251),(-.264,.369,.269),(-.383,.330,.240),
        (-.493,.280,.200),(-.554,.178,.128),(-.573,.040,.027),
    )
    def ponto(a,z,rx,ry):
        dr=1+.034*cos(9*a-z*8)+.019*sin(15*a+z*4)
        return (rx*dr*cos(a),ry*dr*sin(a),z+.009*cos(3*a)*min(1,(z+.63)/.89))
    n=48
    vertices=[ponto(2*pi*i/n,*s) for s in secoes for i in range(n)]
    faces=[]
    for j in range(len(secoes)-1):
        for i in range(n):
            a,b=j*n+i,j*n+(i+1)%n
            faces.append((a,b,b+n,a+n))
    faces.append(tuple(reversed(range(n))))
    faces.append(tuple(range(len(vertices)-n,len(vertices))))
    obj=malha("Juta externa e forro do saco",vertices,faces,juta,pai,True)
    obj.modifiers.new("Curvatura do tecido","SUBSURF").levels=1
    fio("Borda de juta costurada",[ponto(i*2*pi/48,.251,.335,.258) for i in range(48)],
        .010,linha,pai,fechado=True)
    fio("Costura lateral", [ponto(-.48,z,x+.003,y+.003) for z,x,y in secoes[1:9]],
        .0055,linha,pai)
