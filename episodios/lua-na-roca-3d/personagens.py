"""Modelagem e poses de Dona Luzia e Rafael."""

from math import cos, exp, pi, sin, sqrt
from random import Random

import bmesh
from mathutils import Matrix, Quaternion, Vector

from cenografia import agrupar, anel, fio, malha, material, oval, pano, torno


def matriz(objeto):
    """Compõe a hierarquia sem esperar a atualização do quadro."""
    transformacao = Matrix.Identity(4)
    while objeto is not None:
        rotacao = (objeto.rotation_quaternion if objeto.rotation_mode == "QUATERNION"
                   else objeto.rotation_euler.to_quaternion())
        transformacao = Matrix.LocRotScale(objeto.location, rotacao, objeto.scale) @ transformacao
        objeto = objeto.parent
    return transformacao


def transformar(objeto,ponto):
    return matriz(objeto) @ Vector(ponto)


def orientar(direcao,giro=0):
    eixo=Vector(direcao)
    if eixo.length<.001:
        eixo=Vector((0,0,1))
    return eixo.to_track_quat("Z","Y") @ Quaternion((0,0,1),giro)


def superficie(nome, vertices, faces, mat, pai, divisao=1):
    obj = malha(nome, vertices, faces, mat, pai, True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    if divisao:
        obj.modifiers.new("Suavização da superfície", "SUBSURF").levels = divisao
    return obj


def perfil(nome, chaves, mat, pai, lados=32, divisao=1):
    """Seções elípticas de largura, profundidade e avanço independentes."""
    vertices = []
    faces = []
    for z, rx, ry, y in chaves:
        for i in range(lados):
            a = i*2*pi/lados
            vertices.append((rx*sin(a), y-ry*cos(a), z))
    for j in range(len(chaves)-1):
        for i in range(lados):
            q = j*lados+i
            r = j*lados+(i+1)%lados
            faces.append((q,r,r+lados,q+lados))
    faces.extend((tuple(reversed(range(lados))),tuple(range(len(vertices)-lados,len(vertices)))))
    return superficie(nome, vertices, faces, mat, pai, divisao)


def coordenadas(obj, vertices):
    obj.data.vertices.foreach_set("co", [v for ponto in vertices for v in ponto])
    obj.data.update()


class Mao:
    """Palma, dedos e polegar compartilham uma superfície fechada."""

    ENCAIXE=(0,-.074,.174)

    def __init__(self, nome, mat, pai=None, lado=1, escala=1):
        self.raiz = agrupar(nome, pai=pai)
        self.raiz.scale = (escala,)*3
        self.lado = lado
        self.escala = escala
        self.vertices = []
        self.falanges = []
        faces = []
        bordas = (-.086, -.045, -.002, .041, .080)
        secoes = ((0,.060,.042),(.050,.081,.045),(.108,.095,.044),
                  (.166,.092,.036),(.192,.080,.027))
        grade = {}
        for j,(z,w,d) in enumerate(secoes):
            for i,x in enumerate(bordas):
                for frente in (-1,1):
                    grade[j,i,frente] = len(self.vertices)
                    ry = d*(1-.26*abs(x/.086)**1.8)
                    self.vertices.append((x/.086*w,frente*ry,z-.015*abs(x/.086)**1.8))
        for j in range(4):
            for i in range(4):
                for lado_y in (-1,1):
                    faces.append(tuple(grade[k,l,lado_y] for k,l in
                                       ((j,i),(j,i+1),(j+1,i+1),(j+1,i))))
            for i in (0,4):
                base = [grade[k,i,l] for k,l in ((j,-1),(j,1),(j+1,1),(j+1,-1))]
                if j==1 and (i==4)==(lado==1):
                    self.digito(base, .123, .039, .032, lado*.63, faces, True)
                else:
                    faces.append(tuple(base))
        tamanhos=(.120,.154,.162,.135)
        for i in range(4):
            n = i if lado==1 else 3-i
            abertura = [grade[4,j,s] for j,s in ((i,-1),(i+1,-1),(i+1,1),(i,1))]
            self.digito(abertura,tamanhos[n],.0195,.024,(i-1.5)*.098,faces,False)
            faces.append(tuple(grade[0,j,s] for j,s in ((i,-1),(i+1,-1),(i+1,1),(i,1))))
        self.obj = superficie("Pele contínua da mão",self.vertices,faces,mat,self.raiz,2)
        self.neutra = self.vertices.copy()
        self.pontas = []
        self.pose((0,0,0),(0,0,1))

    def digito(self, base, comprimento, rx, ry, abertura, faces, polegar):
        centro = sum((Vector(self.vertices[i]) for i in base),Vector((0,0,0)))/4
        # A orientação de cada anel segue a ordem do contorno que sai da palma.
        lados = ((-1,-1),(1,-1),(1,1),(-1,1))
        if polegar:
            lados = ((1,-1),(1,1),(-1,1),(-1,-1)) if self.lado == 1 else (
                (-1,-1),(-1,1),(1,1),(1,-1))
        anel_anterior = base
        aneis = []
        for pos, estreito in zip((.24,.47,.65,.86,.966,1),(.95,.93,.79,.75,.50,.21)):
            indices = list(range(len(self.vertices),len(self.vertices)+4))
            aneis.append((pos,estreito,indices))
            for _ in indices:
                self.vertices.append(tuple(centro+Vector((0,0,pos*comprimento))))
            for i in range(4):
                q=(i+1)%4
                faces.append((anel_anterior[i],anel_anterior[q],indices[q],indices[i]))
            anel_anterior = indices
        faces.append(tuple(anel_anterior))
        self.falanges.append((centro,comprimento,rx,ry,abertura,lados,aneis,polegar))

    def pose(self, posicao, direcao, fechar=.30, indicar=0, giro=0):
        self.raiz.location = posicao
        self.raiz.rotation_mode = "QUATERNION"
        self.raiz.rotation_quaternion = orientar(direcao,giro)
        self.vertices[:] = self.neutra
        self.pontas = []
        for i,(base,l,rx,ry,abr,lados,aneis,polegar) in enumerate(self.falanges):
            indice = i == (4 if self.lado == 1 else 1)
            flexao = min(1,max(0,fechar))*(1-indicar if indice else 1)
            anterior = 0
            centro = base.copy()
            for u,fino,anel in aneis:
                dobra = flexao*((.14+.73*u) if polegar else (.28+1.34*u))
                abertura = abr*(1-.24*flexao if polegar else 1-.69*flexao)
                ult = Vector((sin(abertura)*cos(dobra),-sin(dobra),cos(abertura)*cos(dobra)))
                centro += (u-anterior)*l*ult
                anterior = u
                horizontal = Vector((cos(abertura),0,-sin(abertura)))
                normal = ult.cross(horizontal)
                for j,(a,b) in zip(anel,lados,strict=True):
                    self.vertices[j] = tuple(centro+horizontal*rx*a*fino+normal*ry*b*fino)
            self.pontas.append(centro.copy())
        coordenadas(self.obj,self.vertices)

    def ponta(self, indice):
        return transformar(self.raiz,self.pontas[indice])

    def pega(self):
        return transformar(self.raiz,self.ENCAIXE)

    def punho(self,pos,direcao,giro=0):
        return Vector(pos)-orientar(direcao,giro)@(Vector(self.ENCAIXE)*self.escala)


class Braco:
    """A curva do cotovelo dobra pele e tecido sem peças salientes."""

    def __init__(self, mat, roupa, detalhe, pai):
        self.n, self.m = 14, 12
        vertices = [(0,0,0)]*(self.n*self.m)
        faces = [(j*self.m+i,j*self.m+(i+1)%self.m,(j+1)*self.m+(i+1)%self.m,(j+1)*self.m+i)
                 for j in range(self.n-1) for i in range(self.m)]
        faces.append(tuple(reversed(range(self.m))))
        faces.append(tuple(range((self.n-1)*self.m,self.n*self.m)))
        self.obj = malha("Braço e manga ajustada",vertices,faces,mat,pai,True)
        self.obj.data.materials.append(roupa)
        self.obj.data.materials.append(detalhe)
        for p in self.obj.data.polygons:
            anel=p.index//self.m
            if anel<4 or p.index==len(faces)-2:
                p.material_index=1
            if anel==4:
                p.material_index=2
        self.obj.modifiers.new("Suavização do braço", "SUBSURF").levels = 1

    def pose(self, ombro, cotovelo, punho):
        acima=(cotovelo-ombro).normalized()
        abaixo=(punho-cotovelo).normalized()
        pontos = [ombro-acima*extra for extra in (.12,.075)]
        pontos += [ombro.lerp(cotovelo,k) for k in (.14,.30,.44,.51,.55,.68,.85)]
        pontos += [cotovelo,punho.lerp(cotovelo,.74),punho.lerp(cotovelo,.43),
                   punho-abaixo*.068,punho+abaixo*.017]
        raios=(.112,.139,.145,.142,.131,.127,.102,.093,.091,.093,.084,.077,.065,.056)
        vertices=[]
        for j,p in enumerate(pontos):
            d=(pontos[min(j+1,self.n-1)]-pontos[max(j-1,0)]).normalized()
            lateral=Vector((0,1,0)).cross(d)
            if lateral.length < .06:
                lateral=Vector((1,0,0)).cross(d)
            lateral.normalize()
            transversal=d.cross(lateral)
            r=raios[j]
            vertices.extend(tuple(p + r*(cos(a)*lateral + .88*sin(a)*transversal))
                            for a in (2*pi*i/self.m for i in range(self.m)))
        coordenadas(self.obj,vertices)


def gauss(x,z,cx,cz,wx,wz):
    return exp(-((x-cx)/wx)**2-((z-cz)/wz)**2)


class Rosto:
    """A forma do rosto inclui bochechas, órbitas, nariz, boca e maxilar."""

    def __init__(self, pai, pele, velha):
        self.pai=pai
        self.velha=velha
        self.perfil=(
            (-.303,.026,.043,-.066),(-.291,.083,.083,-.064),
            (-.265,.143,.122,-.042),(-.222,.186,.155,-.025),
            (-.155,.210,.180,-.014),(-.081,.239,.205,0),
            (.028,.248,.209,.011),(.106,.238,.207,.018),
            (.180,.225,.203,.030),(.246,.187,.175,.037),
            (.309,.128,.125,.047),(.332,.016,.024,.053),
        )
        self.palpebras=[]
        self.iris=[]
        sangue=material("Lábios de Luzia" if velha else "Lábios de Rafael",
                        "7d4639" if velha else "874d34","9f6050",40,.005,.72)
        dobra=material("Traços em argila","64392c","835342",45,.004,.80)
        cabelo=material("Fios grisalhos" if velha else "Cabelos castanhos",
                         "484348" if velha else "2d2326","a39187" if velha else "5a4140",36,.011,.79)
        self.mesh(pele)
        self.cabelo(cabelo,pele)
        for lado in (-1,1):
            x=lado*.102
            e=oval("Orelha", (lado*.229,.006,-.026),(.047,.057,.071),pele,pai)
            e.rotation_euler.y=lado*.15
            fio("Relevo interno da orelha",[(lado*.264,-.024,.008),(lado*.273,-.040,-.023),
                (lado*.256,-.046,-.052)],.006,dobra,pai)
            if velha:
                cobre=material("Brinco de cobre","987349","d6b288",24,.003,.34)
                fio("Brinco",[(lado*.268+.018*cos(i*pi/10),-.037-.011*sin(i*pi/10),-.09-.018*sin(i*pi/10))
                              for i in range(20)],.0052,cobre,pai,fechado=True)
            self.olho(x, .019 if velha else .026, lado, pele, cabelo, dobra)
            retas=((-0.045,.078),(-.019,.103),(.016,.105),(.048,.090))
            fio("Sobrancelha", [(x+lado*a,self.y(x+lado*a,z)-.004,z) for a,z in retas],
                .0085 if velha else .0094,cabelo,pai)
            if velha:
                for j in range(2):
                    trilha=[(lado*xx,z) for xx,z in ((.151,-.018-j*.016),(.173,-.032-j*.014),
                            (.195,-.047-j*.012))]
                    fio("Vincos delicados",[(xx,self.y(xx,z)-.002,z) for xx,z in trilha],.0025,dobra,pai)
        for lado in (-1,1):
            x=.041*lado
            z=-.096
            oval("Sombra na base do nariz",(x,self.y(x,z)-.001,z),(.011,.005,.005),dobra,pai,1)
        sorriso=[(-.073,-.151),(-.043,-.161),(0,-.168),(.036,-.162),(.071,-.149)]
        fio("Canto e linha dos lábios",[(x,self.y(x,z)-.006,z) for x,z in sorriso],.0063,sangue,pai)
        fio("Lábio inferior",[(x,self.y(x,z-.010)-.003,z-.010) for x,z in sorriso[1:-1]],
            .0066,sangue,pai)

    def secao(self,z):
        for (za,xa,ya,ca),(zb,xb,yb,cb) in zip(self.perfil,self.perfil[1:]):
            if z<=zb:
                f=max(0,(z-za)/(zb-za))
                return xa+f*(xb-xa), ya+f*(yb-ya), ca+f*(cb-ca)
        _,x,y,c=self.perfil[-1]
        return x,y,c

    def detalhes(self,x,z):
        sinais = -.022*gauss(abs(x),z,.142,-.064,.068,.057)
        sinais += .028*gauss(abs(x),z,.105,.029,.058,.060)
        sinais -= .036*gauss(x,z,0,.003,.041,.12)
        sinais -= .079*gauss(x,z,0,-.064,.044,.040)
        sinais -= .029*gauss(abs(x),z,.044,-.073,.026,.025)
        sinais -= .018*gauss(x,z,0,-.143,.112,.038)
        sinais -= .014*gauss(x,z,0,-.238,.094,.033)
        return sinais

    def y(self,x,z):
        rx, ry, centro = self.secao(z)
        c = sqrt(max(0,1-(x/rx)**2))
        return centro-ry*c+self.detalhes(x,z)*c**.45

    def mesh(self,mat):
        lados=76
        h=60
        ver,faces=[],[]
        z0,z1=self.perfil[0][0],self.perfil[-1][0]
        for j in range(h+1):
            z=z0+(z1-z0)*j/h
            rx,ry,c=self.secao(z)
            for i in range(lados):
                a=i*2*pi/lados
                x=rx*sin(a)
                y=c-ry*cos(a)+self.detalhes(x,z)*max(0,cos(a))**.45
                ver.append((x,y,z))
        for j in range(h):
            for i in range(lados):
                a=j*lados+i
                b=j*lados+(i+1)%lados
                faces.append((a,b,b+lados,a+lados))
        faces.append(tuple(reversed(range(lados))))
        faces.append(tuple(range(h*lados,(h+1)*lados)))
        superficie("Cabeça modelada em uma só peça",ver,faces,mat,self.pai,0)

    def olho(self,x,z,lado,pele,cabelo,dobra):
        branco=material("Marfim dos olhos","aa947e","d7bfa6",18,.003,.61)
        iris_mat=material("Íris castanha","42312b","62483b",56,.002,.49)
        pupila_mat=material("Pupila","272020",rugoso=.41)
        reflexo=material("Ponto luminoso","e7d6b5",rugoso=.50)
        ver=[]
        faces=[]
        w=.052
        for i in range(19):
            s=(i-9)/9
            meia=sqrt(max(.001,1-s*s))
            xx=x+s*w
            for j in range(5):
                d=(j-2)/2
                zz=z+lado*s*.004+meia*d*.021
                y=self.y(xx,zz)-.002-.018*meia*(1-.63*d*d)
                ver.append((xx,y,zz))
        for i in range(18):
            for j in range(4):
                q=i*5+j
                faces.append((q,q+1,q+6,q+5))
        grupo=agrupar("Abertura dos olhos",(x,self.y(x,z),z),self.pai)
        verts=[(X-x,Y-grupo.location.y,Z-z) for X,Y,Z in ver]
        malha("Olho amendoado",verts,faces,branco,grupo,True)
        mira=agrupar("Centro do olhar",(0,-.021,.001),grupo)
        oval("Íris", (0,0,0),(.023,.006,.019),iris_mat,mira,1)
        oval("Pupila",(0,-.004,0),(.014,.0035,.014),pupila_mat,mira,1)
        oval("Reflexo",(-.006,-.007,.008),(.004,.0025,.004),reflexo,mira,1)
        p=[]
        q=[]
        for i in range(11):
            s=(i-5)/5
            xx=x+w*s
            meia=sqrt(max(.001,1-s*s))
            cima=z+lado*s*.004+.022*meia
            baixo=z+lado*s*.004-.021*meia
            p.append((xx-x,self.y(xx,cima)-grupo.location.y-.013*meia-.002,cima-z))
            q.append((xx-x,self.y(xx,baixo)-grupo.location.y-.013*meia-.001,baixo-z))
        fio("Linha da pálpebra superior",p,.0042,dobra,grupo)
        fio("Pálpebra inferior",q,.0048,pele,grupo)
        fio("Pálpebra fechada",[(xx,y+.005,0) for xx,y,zz in p],.0032,dobra,grupo)
        self.palpebras.append(grupo)
        self.iris.append(mira)

    def cabelo(self, mat, pele):
        pai=self.pai
        velha=self.velha
        couro=perfil("Cabelo esculpido",[(.039,.191,.167,.092),(.101,.240,.180,.068),
             (.188,.249,.212,.043),(.261,.204,.184,.037),(.324,.159,.142,.045),
             (.363 if not velha else .344,.079,.089,.067),(.373 if not velha else .349,.007,.022,.075)],mat,pai)
        rng=Random(24 if velha else 48)
        if velha:
            coque=oval("Coque baixo",(.030,.222,-.021),(.110,.107,.103),mat,pai)
            for i in range(7):
                x=-.160+i*.049
                fio("Mechas penteadas",[(x,-.144,.183+.021*sin(i)),(x+.032,-.128,.246),
                      (x+.052,-.055,.299),(x+.044,.060,.329)],.012,mat,pai)
            self.chapeu()
        else:
            for ramo in range(4):
                n=9-min(2,ramo)
                for i in range(n):
                    x=(i-(n-1)/2)*.045+.018*ramo+.008*rng.random()
                    y=-.155+ramo*.059+.23*abs(x)
                    z=.237+.022*ramo+.040*cos(x/.224*pi)+.012*sin(i*1.6+ramo)
                    m=oval("Cacho penteado", (x,y,z),(.051,.053,.047+rng.random()*.011),mat,pai,1)
                    m.rotation_euler.y=.27+(i%4)*.12
            for e in (-1,1):
                oval("Acabamento da costeleta",(e*.218,-.065,.077),(.025,.030,.067),mat,pai)

    def chapeu(self):
        p=agrupar("Chapéu de palha",(0,.025,.257),self.pai)
        p.rotation_euler=(.045,-.075,-.10)
        palha=material("Palha da aba","926c42","d1b37d",78,.009,.84)
        costura=material("Pesponto na palha","aa8352","e0c18a",59,.011)
        aba=torno("Aba e copa modeladas", [(-.035,.327),(-.035,.395),(-.025,.402),
            (-.013,.393),(.012,.296),(.031,.251),(.119,.238),(.202,.193),(.216,.100),
            (.215,.014)],palha,p,ondulacao=.009)
        for v in aba.data.vertices:
            x,y,z=v.co
            r=sqrt(x*x+y*y)
            v.co.z+=max(0,r-.263)*max(0,-y)*1.4
        for j in range(7):
            r=.281+j*.016
            ps=[]
            for i in range(46):
                a=i*2*pi/46
                x,y=r*cos(a),r*sin(a)
                z=.019-j*.0052+max(0,r-.263)*max(0,-y)*1.4
                ps.append((x,y,z))
            fio("Costura em espiral",ps,.0048,costura,p,fechado=True)
        torno("Faixa verde de tecido",[(.036,.254),(.045,.258),(.083,.247),(.088,.241)],
              pano("454e3f","716c52"),p)
        for j in range(3):
            anel("Trama da copa",.233-.018*j,.109+.026*j,costura,p,.0041)

    def pose(self,tempo,yaw):
        piscar=min(abs((tempo+.66)%3.57-1.68),abs((tempo+.08)%5.47-4.81))
        aberto=.075+.925*min(1,piscar/.081)
        for e,mira in zip(self.palpebras,self.iris,strict=True):
            e.scale.z=aberto
            mira.location.x=max(-.012,min(.012,yaw*.022))


class Pessoa:
    """Boneco inteiro com cinemática inversa e roupa construída em torno do corpo."""

    def __init__(self,nome,local,velha=False,sentada=False,escala=1):
        self.raiz=agrupar(nome,local)
        self.raiz.scale=(escala,)*3
        self.sentada=sentada
        self.hip=.88 if sentada else 1.00
        cores=("865139","bd8768") if velha else ("815039","c1885c")
        self.pele=material("Pele de Luzia" if velha else "Pele de Rafael",*cores,34,.006,.66)
        self.roupa=pano("285752","63867a") if velha else pano("966735","c39758")
        self.detalhe=pano("335f56","749085") if velha else pano("ad7545","daa766")
        self.calca=pano("454c3d","727662") if velha else pano("394f5a","637989")
        solado=material("Borracha da sola","422e28","65513e",24,.008)
        sapato=material("Couro da botina","573829","967858",37,.010)
        botao=material("Botão de osso","bd9a71","e0c59b",43,.008,.65)
        self.tronco=agrupar("Eixo do corpo",(0,0,self.hip),self.raiz)
        perfil("Camisa ajustada", [(.055,.23,.152,-.004),(.084,.275,.180,0),
             (.192,.272,.187,0),(.345,.265,.199,-.011),(.487,.297,.203,-.019),
             (.596,.325,.198,-.006),(.689,.318,.179,.003),(.773,.218,.143,-.013),
             (.812,.119,.109,-.027)],self.roupa,self.tronco)
        oval("Quadril coberto pela calça",(0,.015,-.036),(.275,.192,.177),self.calca,self.tronco)
        perfil("Pescoço",[(.760,.105,.106,-.004),(.834,.093,.099,-.002),
                (.902,.098,.091,-.014),(.954,.121,.094,-.006)],self.pele,self.tronco)
        gola_esq=[(-.12,-.068,.793),(-.108,-.144,.784),(-.063,-.180,.733),(0,-.164,.771)]
        gola_dir=[(-x,y,z) for x,y,z in gola_esq]
        for lado in (gola_esq,gola_dir):
            f=malha("Gola dobrada",lado,[(0,1,2,3)],self.detalhe,self.tronco)
            f.modifiers.new("Espessura da gola","SOLIDIFY").thickness=.012
        fio("Costura da abertura",[(0,-.203,.215),(.0,-.219,.492),(.0,-.201,.668)],.008,
            self.detalhe,self.tronco)
        for z,y in ((.327,-.211),(.475,-.224),(.631,-.206)):
            oval("Botão",(0,y,z),(.014,.007,.014),botao,self.tronco,1)
        bol=[(-.229,-.145,.553),(-.121,-.205,.554),(-.118,-.197,.436),(-.170,-.187,.417),(-.221,-.156,.441)]
        fio("Pesponto do bolso",bol,.0056,self.detalhe,self.tronco,fechado=True)
        if velha:
            mat_linha=material("Linha de bordado","aeaa73","c8bd90",47,.007)
            for j in range(4):
                x=-.217+.026*j
                y=-.154-.017*j
                fio("Ponto de bordado",[(x,y,.519),(x+.008,y-.002,.504),(x+.020,y-.007,.520)],
                    .0038,mat_linha,self.tronco)
        self.cabeca=agrupar("Pivô da cabeça",(0,-.012,1.13),self.tronco)
        self.rosto=Rosto(self.cabeca,self.pele,velha)
        self.bracos=[]
        self.pernas=[]
        for lado in (-1,1):
            braço=Braco(self.pele,self.roupa,self.detalhe,self.tronco)
            mao=Mao("Mão de "+nome,self.pele,self.tronco,lado=-lado,escala=.76)
            self.bracos.append((lado,braço,mao))
            calca=Braco(self.calca,self.calca,self.calca,self.raiz)
            bota=agrupar("Botina",pai=self.raiz)
            oval("Couro da botina",(0,-.085,.103),(.106,.184,.100),sapato,bota)
            oval("Sola",(0,-.085,.033),(.108,.184,.026),solado,bota)
            for j in range(2):
                y=-.077-.033*j
                fio("Cadarço",[(-.041,y,.174),(0,y-.011,.187),(.041,y,.176)],.0077,botao,bota)
            self.pernas.append((lado,calca,bota))

    def pose(self,tempo,*,giro=0,olhar=(0,0),inclinacao=0,esquerda=None,direita=None,
             aperto=(.27,.27),apontar=0,respirar=1,passo=0,falar=0,rumos=(None,None),
             apoio=None,contatos=(None,None)):
        peso=sin(tempo*1.7)*.010*respirar
        self.raiz.rotation_euler.z=giro
        self.tronco.location.z=self.hip+peso
        self.tronco.rotation_euler=(inclinacao,.022*sin(tempo*1.7),.026*sin(tempo*1.1))
        balanco=falar*.025*sin(tempo*13)
        self.cabeca.rotation_euler=(olhar[1]+.016*sin(tempo*2.1)+balanco,
                                    .022*sin(tempo*1.6+.5),olhar[0])
        self.rosto.pose(tempo,olhar[0])
        for lado,calca,bota in self.pernas:
            fase=(passo+(lado==1)*.5)*2*pi
            andar=sin(fase) if passo else 0
            levante=max(0,cos(fase))*.087 if passo else 0
            a=Vector((lado*.154,.016,self.hip-.068+peso))
            b=Vector((lado*.191,-.46,.45) if self.sentada else (lado*.156,-.024+.12*andar,.55))
            c=Vector((lado*.194,-.51,.155) if self.sentada else (lado*.160,-.105+.192*andar,.159+levante))
            if apoio:
                m=matriz(self.raiz)
                pontos=(m@Vector((c.x+x,c.y+y,0)) for x,y in
                        ((0,-.22),(-.077,-.12),(.077,-.12),(0,.066),(0,-.064)))
                chao=max(apoio(p.x,p.y) for p in pontos)
                c.z=.157+levante+(chao-self.raiz.location.z)/self.raiz.scale.z
            calca.pose(a,b,c)
            bota.location=(c.x,c.y,c.z-.159)
            bota.rotation_euler.z=lado*.078
        for j,(lado,braço,mao) in enumerate(self.bracos):
            ombro=Vector((lado*.265,0,.658))
            alvo=(esquerda,direita)[j]
            p=Vector(alvo if alvo is not None else (lado*.37,-.25 if self.sentada else -.048,
                            .029 if self.sentada else -.20))
            rumo=rumos[j]
            if contatos[j]:
                ponto,rotacao=contatos[j]
                inv=matriz(self.tronco).inverted()
                rumo=inv.to_3x3() @ Vector(rotacao)
                p=mao.punho(inv @ Vector(ponto),rumo,lado*.23)
            eixo=(p-ombro).normalized()
            dist=min(.877,max(.15,(p-ombro).length))
            punho=ombro+eixo*dist
            ajuste=Vector((lado*.40,.31,-.66))
            dobra=(ajuste-eixo*ajuste.dot(eixo)).normalized()
            superior,inferior=.475,.431
            cateto=(superior**2-inferior**2+dist**2)/(2*dist)
            cotovelo=ombro+eixo*cateto+dobra*sqrt(max(0,superior**2-cateto**2))
            braço.pose(ombro,cotovelo,punho)
            rumo=Vector(rumo) if rumo is not None else (punho-cotovelo).normalized()
            if lado==1 and apontar:
                rumo=(rumo*(1-apontar*.75)+Vector((.19,-.09,.98))*apontar).normalized()
            mao.pose(punho,rumo,aperto[j],apontar if lado==1 else 0,giro=lado*.23)
