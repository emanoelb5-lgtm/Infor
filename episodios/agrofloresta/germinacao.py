"""Corte animado da germinação epígea de um feijoeiro-comum."""

from math import cos, pi, sin
from random import Random

from mathutils import Vector

from cenas import camera, mover_tempo, regime
from cenografia import agrupar, brilho, fio, iluminacao, malha, material, oval, raio_sol
from personagens import coordenadas


def rama(nome, pontos, espessura, mat, pai=None):
    obj=fio(nome,pontos,espessura,mat,pai)
    obj.data.use_fill_caps=True
    return obj


def atualizar(obj, valores):
    pontos=obj.data.splines[0].bezier_points
    for p,co in zip(pontos,valores,strict=True):
        p.co=co


def solo_exposto():
    rng=Random(39)
    blocos=[
        (0,-.148,"382a20","704a31"),
        (-.148,-.63,"573522","a46a44"),
        (-.63,-1.57,"523729","896148"),
    ]
    n=46
    def altura(x,z):
        onda=.013*sin(7*x+1.1)+.018*sin(15*x-2.3)
        return z+onda*(1 if z==0 else .68)
    for ordem,(cima,baixo,c1,c2) in enumerate(blocos):
        mat=material("Camada de solo "+str(ordem+1),c1,c2,26+ordem*6,.051,.87)
        vs=[]
        for i in range(n+1):
            x=-1.18+i*2.36/n
            topo=altura(x,cima)
            fundo=altura(x,baixo)
            frente=-.006+.014*sin(7.1*x)+.009*cos(16.9*x)
            vs.extend(((x,frente,topo),(x,frente,fundo),(x,1.24,topo),(x,1.24,fundo)))
        faces=[(0,2,3,1),(n*4,n*4+1,n*4+3,n*4+2)]
        for i in range(n):
            j=i*4
            faces.extend(((j,j+4,j+5,j+1),(j,j+2,j+6,j+4),
                (j+1,j+5,j+7,j+3),(j+2,j+3,j+7,j+6)))
        malha("Torrão em corte",vs,faces,mat)
    minerais=[
        material("Arestas do solo","684836","95755a",36,.035,.80),
        material("Argila mais clara","72503b","aa7e58",36,.033,.85),
        material("Partículas de húmus","4b382d","7f6551",30,.031,.84),
    ]
    for i in range(109):
        x,z=rng.uniform(-1.12,1.12),rng.uniform(-1.51,-.055)
        if abs(x+.03)<.29 and -.44<z<-.21:
            continue
        r=rng.uniform(.008,.039)*(1.32 if i%8==0 else 1)
        p=oval("Agregado exposto",(x,-.019+r*.09,z),(r,r*.54,r*.69),minerais[i%3],detalhe=1)
        p.rotation_euler.y=rng.uniform(-pi,pi)
    for i in range(31):
        x,y=rng.uniform(-1.13,1.13),rng.uniform(.10,1.2)
        r=rng.uniform(.014,.036)
        oval("Grânulo da superfície",(x,y,altura(x,0)+r*.28),(r,r*.77,r*.54),minerais[i%3],detalhe=1)
    return altura,minerais


def meio_grao(nome,lado,mat,pai,casca):
    """Forma reniforme. As duas partes compartilham o contorno de contato."""
    n,m=28,24
    vs=[]
    for i in range(n+1):
        s=i/n
        x=-.275+.538*s
        f=max(.022,sin(pi*s)**.63)
        h=.142*f*(1-.30*regime(s,.48,.70)*(1-regime(s,.76,.96)))
        c=.023*sin(pi*s)-.029*s
        for j in range(m+1):
            a=-pi/2+j*pi/m
            y=lado*.144*f*cos(a)
            z=c+h*sin(a)
            vs.append((x,y,z))
    faces=[]
    for i in range(n):
        for j in range(m):
            k=i*(m+1)+j
            faces.append((k,k+1,k+m+2,k+m+1))
    faces.extend((tuple(range(m+1)),tuple(range(n*(m+1),(n+1)*(m+1)))))
    if not casca:
        faces.append(tuple([i*(m+1) for i in range(n+1)]
                     +[i*(m+1)+m for i in range(n,-1,-1)]))
    if lado<0:
        faces=[tuple(reversed(a)) for a in faces]
    obj=malha(nome,vs,faces,mat,pai,True)
    if casca:
        obj.modifiers.new("Espessura do tegumento","SOLIDIFY").thickness=.007
    return obj


class Lamina:
    """A lâmina e as nervuras usam a mesma superfície ao se desenrolarem."""

    def __init__(self,nome,pai,mat,veio):
        self.raiz=agrupar(nome,pai=pai)
        self.n,self.m=20,10
        self.vers=[(0,0,0)]*((self.n+1)*(self.m+1))
        faces=[]
        for j in range(self.n):
            for i in range(self.m):
                c=j*(self.m+1)+i
                faces.append((c,c+1,c+self.m+2,c+self.m+1))
        self.lamina=malha("Folha simples",self.vers,faces,mat,self.raiz,True)
        self.lamina.modifiers.new("Cutícula","SOLIDIFY").thickness=.0028
        self.nervura=rama("Nervura principal",[(0,i*.02,0) for i in range(9)],.0046,veio,self.raiz)
        self.laterais=[]
        for lado in (-1,1):
            for i in range(1,6):
                par=.14+i*.11
                linha=rama("Nervura lateral",[(0,0,0)]*5,.0019,veio,self.raiz)
                self.laterais.append((lado,par,linha))

    def forma(self,fracao):
        f=max(.009,fracao)
        abrir=regime(f,.13,.88)
        dobra=1-abrir
        def co(u,v):
            r=.241*max(.007,sin(pi*u)**.77)*(1-.27*u)
            largura=f*(.20+.80*abrir)
            lado=v*r*largura
            y=f*(.59*u-.21*dobra*u*u)
            z=f*(.098*sin(pi*u)+.30*dobra*u*u-.069*u**3)
            z+=abs(v)**1.76*r*largura*(.92*dobra-.19)
            z+=.011*f*abs(v)*sin(29*u)*u
            return (lado,y,z)
        self.vers=[co(j/self.n,2*i/self.m-1) for j in range(self.n+1) for i in range(self.m+1)]
        coordenadas(self.lamina,self.vers)
        atualizar(self.nervura,[(x,y,z+.003) for x,y,z in
                  (co(i/8,0) for i in range(9))])
        for lado,par,linha in self.laterais:
            ps=[]
            for i in range(5):
                s=i/4
                x,y,z=co(par+.16*s,lado*.91*s)
                ps.append((x,y,z+.0032))
            atualizar(linha,ps)
        self.raiz.hide_render=fracao<.012


def corte(etapa):
    inicio,fim={"raiz":(0,.33),"emergencia":(.33,.69),"folhas":(.69,1)}[etapa]
    iluminacao("dia",(0,0,.0))
    raio_sol("Recorte alto da folha",(1.92,1.90,3.2),(0,0,.36),280,(1,.84,.56),2.85)
    luz=raio_sol("Luz do corte frontal",(-1.3,-3.7,.11),(0,0,-.54),190,(.62,.79,1),2.8)
    fundo=brilho("Fundo oliva","273f38",.50)
    malha("Fundo da bancada", [(-15,3,-5),(15,3,-5),(15,3,8),(-15,3,8)],[(0,1,2,3)],fundo)
    alt,minerais=solo_exposto()
    rng=Random(21)
    clastos=[]
    for i in range(12):
        lado=(-1)**i
        x=lado*(.058+.016*i)
        y=.026+rng.random()*.105
        r=.013+.006*(i%4)
        p=oval("Partícula deslocada pelo hipocótilo",(0,0,0),(r,r*.77,r*.69),minerais[0],detalhe=1)
        clastos.append((p,x,y,lado*(.090+i*.016),r))
    gotas=[]
    agua=material("Umidade em poros do solo","618681","abc9a9",48,.002,.21)
    for i in range(4):
        o=oval("Gota de umidade",(0,0,0),(.016,.017,.021),agua,detalhe=1)
        gotas.append((o,i))

    tegumento=material("Tegumento do feijão rajado","452b23","996c52",39,.017,.49)
    semente=material("Reserva dos cotilédones","a7ac66","d8d398",29,.008,.64)
    raiz_mat=material("Raiz e pelos absorventes","b9a284","e7cdb0",44,.004,.71)
    caule_mat=material("Hipocótilo","506b35","a8ac58",29,.014,.56)
    folha_mat=material("Primeiras folhas do feijão","396035","8aaf54",27,.013,.49)
    veio=material("Nervuras verdes","748e3f","b3c976",47,.005,.56)
    origem=Vector((-.15,-.237,-.307))
    colo=Vector((.088,-.218,-.356))

    sementes, cascas=[],[]
    for lado in (-1,1):
        miolo=agrupar("Cotilédone")
        meio_grao("Tecido do cotilédone",lado,semente,miolo,False)
        sementes.append((lado,miolo))
        ovo=agrupar("Casca que se desprende")
        meio_grao("Tegumento externo",lado,tegumento,ovo,True)
        if lado==-1:
            x,z=-.153,-.023
            oval("Hilo", (x,-.113,z),(.044,.012,.025),
                 material("Cicatriz do hilo","957b58","c5a076",29,.004,.68),ovo)
        cascas.append((lado,ovo))

    def raiz_pos(q):
        return colo+Vector((.072*sin(pi*q*1.1)-.093*q*q,
                             -.027+.014*sin(5.2*q),-1.081*q-.027*sin(pi*q)))

    prim=rama("Radícula", [raiz_pos(i/9) for i in range(10)],.027,raiz_mat)
    for i,p in enumerate(prim.data.splines[0].bezier_points):
        p.radius=1.04-.87*i/9
    redes=[]
    for i,n in enumerate((.159,.24,.34,.44,.54,.67,.77)):
        lado=(-1)**i
        base=raiz_pos(n)
        l=.23+(i%3)*.07
        def ramo(q,base=base,lado=lado,l=l,i=i):
            return base+Vector((lado*l*q,-.016*sin(q*pi),-.095*q-.093*q*q+.021*sin(i+q*4)*q))
        a=rama("Raiz lateral",[ramo(k/5) for k in range(6)],.012,raiz_mat)
        for k,p in enumerate(a.data.splines[0].bezier_points):
            p.radius=.88-.76*k/5
        pelos=[]
        for j in range(4):
            q=.29+j*.16
            x,y,z=ramo(q)
            cabelo=rama("Pelo radicular",[(x,y,z),(x+lado*.026,y-.003,z-.031),
                (x+lado*.059,y-.003,z-.041)],.0024,raiz_mat)
            for k,p in enumerate(cabelo.data.splines[0].bezier_points):
                p.radius=1-.43*k
            pelos.append(cabelo)
        redes.append((i,n,a,pelos))

    broto=rama("Curva do hipocótilo",[(0,0,.1*i) for i in range(6)],.038,caule_mat)
    for i,p in enumerate(broto.data.splines[0].bezier_points):
        p.radius=1.06-.40*i/5
    epicotilo=rama("Epicótilo",[(0,0,.02*i) for i in range(4)],.025,caule_mat)
    folhas=[]
    for lado in (-1,1):
        peciolo=rama("Pecíolo",[(0,0,0)]*3,.012,caule_mat)
        folha=Lamina("Folha primária",None,folha_mat,veio)
        conector=rama("Inserção do cotilédone",[(0,0,0)]*3,.014,caule_mat)
        folhas.append((lado,peciolo,folha,conector))
    cam=camera(7.5)

    def posicao(g):
        return mover_tempo(g,[(0,origem),(.27,origem),(.39,(-.175,-.235,-.259)),
          (.47,(-.206,-.234,-.159)),(.54,(-.217,-.237,-.018)),(.62,(-.139,-.228,.199)),
          (.70,(-.069,-.208,.423)),(.85,(-.022,-.182,.685)),(1,(-.014,-.165,.806))])

    desprende=.716
    ponto_casca=posicao(desprende)

    def marcar(g,t):
        expande=regime(g,.016,.107)
        fissura=regime(g,.096,.18)
        crescimento=regime(g,.089,.395)
        luz.data.energy=190-69*regime(g,.52,.90)
        prim.data.bevel_factor_end=crescimento
        prim.hide_render=crescimento<.006
        for i,no,a,capilares in redes:
            v=regime(g,.134+no*.44,.26+no*.51)
            a.hide_render=v<.006
            a.data.bevel_factor_end=v
            for k,pelo in enumerate(capilares):
                s=regime(v,.36+.12*k,.66+.08*k)
                pelo.hide_render=s<.006
                pelo.data.bevel_factor_end=s

        c=posicao(g)
        cot=regime(g,.719,.903)
        gancho=regime(g,.301,.471)*(1-regime(g,.586,.838))
        alonga=regime(g,.27,.59)
        eixo=c+Vector((.179*(1-cot),.006,-.019))
        j=colo+Vector((.01,.0,-.007))
        atualizar(broto,[j,j+Vector((.063*(1-cot),.008,.083*alonga)),
            j.lerp(eixo,.57)+Vector((.156*gancho,.029,.101*gancho)),
            eixo+Vector((.084*gancho,.022,.166*gancho)),
            eixo+Vector((-.037*gancho,.01,.222*gancho)),
            eixo])
        broto.hide_render=g<.274

        for lado,m in sementes:
            abre=.198*cot
            m.location=c+Vector((lado*abre, lado*(.003+.047*cot), .022*cot))
            m.rotation_euler=(lado*.83*cot, lado*.28*cot, lado*.38*cot)
            escala=(.895+.088*expande)*(1-.41*cot)
            m.scale=(escala,)*3
        for lado,obj in cascas:
            if g<desprende:
                obj.location=c+Vector((lado*.007*fissura,lado*.016*fissura,0))
                obj.rotation_euler=(lado*.106*fissura,lado*.082*fissura,-.10*fissura)
                obj.scale=(1+.098*expande,)*3
            else:
                f=min(1,max(0,(g-desprende)/.104))
                pos=ponto_casca+Vector((lado*.007,lado*.016,0))
                final=Vector((lado*(.415+.060*(lado==1)),-.017,.076))
                obj.location=pos.lerp(final,f)
                obj.location.z=pos.z+(final.z-pos.z)*(.21*f+.79*f*f)
                obj.rotation_euler=(lado*(.106+1.01*f),lado*(.082+.081*f),-.10+lado*.522*f)
                obj.scale=(1.098,)*3

        exposta=regime(g,.733,.996)
        ponta=c+Vector((.005,.01,.305*exposta))
        atualizar(epicotilo,[eixo,eixo.lerp(ponta,.41),eixo.lerp(ponta,.73),ponta])
        epicotilo.hide_render=exposta<.02
        for lado,peciolo,folha,cot_ramo in folhas:
            a=regime(g,.754+.014*(lado==1),.987+.006*(lado==1))
            x=ponta+Vector((lado*.116*a,.013*a,.047*a))
            atualizar(peciolo,[ponta,ponta.lerp(x,.54)+Vector((0,0,.027*a)),x])
            peciolo.hide_render=a<.014
            folha.raiz.location=x
            folha.raiz.rotation_euler=(.17+.060*sin(t*2.3+lado)*a,lado*(.19+.61*a),
                                         -lado*(1.28+.25*a))
            folha.forma(a)
            ramo_c=c+Vector((lado*.133*cot,lado*.028*cot,.024*cot))
            atualizar(cot_ramo,[eixo,eixo.lerp(ramo_c,.5)+Vector((0,0,.008)),ramo_c])
            cot_ramo.hide_render=cot<.075

        for o,i in gotas:
            u=(g-.011-i*.012)/.089
            o.hide_render=not 0<u<1
            if not o.hide_render:
                o.location=(-.34+.095*i+.016*sin(pi*u),-.143,-.016-(.17+.048*i)*u)
                o.scale=(.013*(1-u*.44),.012*(1-u*.4),.023*(1-u*.51))
        for i,(p,x,y,d,r) in enumerate(clastos):
            v=regime(g,.447+.002*(i%4),.537+.007*(i%4))
            xf=x+d*v
            p.location=(xf,y+.03*v,alt(xf,0)+r*.57+.115*sin(pi*v))
            p.rotation_euler=(v*.43,v*(i%4)*.62,.21*i)

    def animar(t,u):
        g=inicio+(fim-inicio)*u
        # Mantém o vento na mesma fase entre as três tomadas do corte.
        marcar(g,g*19.6)
        if etapa=="raiz":
            cam((.36-.15*u,-5.05,1.03),(-.05,-.043,-.476-.02*u),2.22-.11*u,
                foco=(-.02,-.24,-.55))
        elif etapa=="emergencia":
            cam((.22+.27*u,-5.38,1.46+.20*u),(-.04,0,-.257+.49*u),2.58,
                foco=(-.04,-.21,.12+.30*u))
        else:
            cam((.42-.35*u,-4.78,1.88+.85*u),(-.03,-.015,.42+.23*u),2.20+.82*regime(u,.28,.95),
                foco=(0,-.16,.45+.42*u))
    return animar
