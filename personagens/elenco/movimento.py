"""Poses, deslocamento e contato dos pés do elenco Infor."""

from math import cos, pi, sin, sqrt
from mathutils import Matrix, Quaternion, Vector

from modelos import criar, suave

LADOS = (("Left", 1), ("Right", -1))


def progressao(u, a, b):
    return suave((u-a)/(b-a))


def calcular_dobra(a, c, r1, r2, polo):
    eixo = c - a
    d = max(.001, eixo.length)
    eixo.normalize()
    alcance = min(d, r1+r2-.00025)
    arco = min(r1-.0001,max(-r1+.0001,(r1*r1-r2*r2+alcance*alcance)/(2*alcance)))
    lado = Vector(polo) - eixo * eixo.dot(Vector(polo))
    lado.normalize()
    meio = a + eixo * arco + lado * sqrt(max(0,r1*r1-arco*arco))
    return meio, a + eixo*alcance


class Marcha:
    """Cada apoio tem uma posição no chão. O pé só se desloca durante a passada."""

    def __init__(self, começo, fim, u0, u1, passos, primeiro=1, altura=.085):
        self.começo, self.fim = Vector(começo), Vector(fim)
        self.u0, self.u1 = u0, u1
        self.passos, self.primeiro, self.altura = passos, primeiro, altura

    def posição(self, u):
        return self.começo.lerp(self.fim,progressao(u,self.u0,self.u1))

    def apoio(self, u, s):
        t = min(1,max(0,(u-self.u0)/(self.u1-self.u0)))
        perna = [i for i in range(self.passos) if self.primeiro*(-1)**i==s]
        anterior = self.começo
        for i in perna:
            pouso = min(1,(i+2)/self.passos)
            destino = self.começo.lerp(self.fim, suave(pouso))
            f = min(1,max(0, (t*self.passos-i-.08)/.80))
            if f < 1:
                return anterior.lerp(destino,suave(f)), self.altura*sin(pi*f)**1.25, -.10*sin(2*pi*f)
            anterior = destino
        return anterior, 0, 0

    def balanço(self, u):
        t = min(1,max(0,(u-self.u0)/(self.u1-self.u0)))
        ativo = suave(t/.13)*suave((1-t)/.16)
        angulo = 2*pi*t*self.passos/2
        return ativo*sin(angulo), ativo*cos(angulo*2)


class Ator:
    """Aplica cinemática à armadura ponderada e aos acessórios do personagem."""

    def __init__(self, sexo, escala=1, *, construir=criar):
        self.obj, self.pele = construir(sexo)
        self.obj.scale = (escala,)*3
        self.escala = escala
        self.ossos = self.obj.pose.bones
        self.repouso = {b.name: b.matrix_local.copy() for b in self.obj.data.bones}
        self.poses = {}

    def matriz(self, nome):
        if nome in self.poses:
            return self.poses[nome]
        pai = self.ossos[nome].parent
        local = self.repouso[nome]
        if pai:
            return self.matriz(pai.name) @ self.repouso[pai.name].inverted() @ local
        return local

    def posicionar(self, nome, rotacao=None, ponto=None):
        """Usa a posição da junta ponderada e uma rotação no espaço do personagem."""
        pose = self.matriz(nome)
        if rotacao is None:
            m = pose.copy()
        else:
            m = (rotacao @ self.repouso[nome].to_quaternion()).to_matrix().to_4x4()
        m.translation = pose.translation if ponto is None else ponto
        pai = self.ossos[nome].parent
        esperada = self.repouso[nome] if pai is None else (
            self.matriz(pai.name) @ self.repouso[pai.name].inverted() @ self.repouso[nome])
        self.ossos[nome].matrix_basis = esperada.inverted() @ m
        self.poses[nome] = m
        return m

    def membros(self, nomes, alvo, polo, mao_ou_pe):
        primeiro, segundo, extremidade = nomes
        a = self.matriz(primeiro).translation
        b, c = calcular_dobra(a,alvo,self.ossos[primeiro].length,self.ossos[segundo].length,polo)
        for nome, de, para in ((primeiro,a,b),(segundo,b,c)):
            n = (self.repouso[nome].to_quaternion() @ Vector((0,1,0))).normalized()
            q = n.rotation_difference((para-de).normalized())
            self.posicionar(nome,q,de)
        q = q if mao_ou_pe is None else mao_ou_pe
        self.posicionar(extremidade,q,c)
        return c

    def dedos(self,lado,sinal,fechar,indicar):
        for dedo, força in (("Thumb",.48),("Index",1-indicar),("Middle",1),
                            ("Ring",1.11),("Pinky",1.24)):
            for i in range(1,4):
                nome=f"{lado}Hand{dedo}{i}"
                osso=self.ossos[nome]
                flexao=fechar * força * (.93,.99,.70)[i-1]
                eixo=self.repouso[nome].to_quaternion().inverted() @ Vector((0,sinal,0))
                osso.rotation_mode="QUATERNION"
                osso.rotation_quaternion=Quaternion(eixo,flexao)

    def pose(self,t,u,marcha,altura,giro,olhar=(0,0),gesto=None,inclinacao=0):
        self.poses.clear()
        for b in self.ossos:
            b.matrix_basis=Matrix.Identity(4)
        root = marcha.posição(u)
        root.z += altura(root.x,root.y)
        self.obj.location = root
        # O rumo dos pés é estável durante o apoio. A rotação do tórax vem do esqueleto.
        self.obj.rotation_euler = (0,0,giro)
        mover,gait = marcha.balanço(u)
        quadril = self.repouso["Hips"].translation.copy()
        quadril.z += -self.obj.get("descida_quadril",.028) + .014*gait + .006*sin(t*2.05)
        quadril.x += .024*mover
        quadril.y -= .12*inclinacao
        self.posicionar("Hips",Quaternion((0,0,1),.09*mover),quadril)
        self.posicionar("Spine",Quaternion((1,0,0),inclinacao*.65+.015*sin(t*2.1)))
        self.posicionar("Spine2",Quaternion((1,0,0),inclinacao) @ Quaternion((0,0,1),-.10*mover))
        pescoço = Quaternion((0,0,1),olhar[0]*.47) @ Quaternion((1,0,0),olhar[1]*.54)
        self.posicionar("Neck",pescoço)
        olhar_q = Quaternion((0,0,1),olhar[0]) @ Quaternion((1,0,0),olhar[1]+.019*sin(t*2.8))
        self.posicionar("Head",olhar_q)
        for lado,v in LADOS:
            self.posicionar(lado+"Eye",olhar_q @ Quaternion((0,0,1),.038*sin(t*1.49+v*.25)))

        orientar = Quaternion((0,0,1),giro)
        for lado,s in LADOS:
            apoio,subida,ponta=marcha.apoio(u,s)
            pé=self.repouso[lado+"Foot"].translation.copy()
            px,py,pz=pé
            mundo=apoio+orientar @ Vector((px,py,0))*self.escala
            planta=[mundo+orientar @ Vector((a,b,0))*self.escala
                    for a,b in ((0,-.17),(-.046,-.083),(.046,-.083),(0,.035))]
            solo=max(altura(v.x,v.y) for v in planta)
            mundo.z=solo+(pz-.009+subida)*self.escala
            pé=orientar.inverted()@(mundo-root)/self.escala
            self.membros((lado+"UpLeg",lado+"Leg",lado+"Foot"),pé,(s*.09,-1,0),
                         Quaternion((1,0,0),ponta))

            braço=self.matriz(lado+"Arm").translation
            mão=braço+Vector((s*.083, .008+s*.142*mover, -.372+.071*abs(mover)))
            indicar=0
            fechar=.42
            if gesto and gesto[0]==lado:
                _, alvo, força = gesto
                mão=mão.lerp(Vector(alvo),força)
                fechar+=.12*força
                indicar=força*.86
            self.membros((lado+"Arm",lado+"ForeArm",lado+"Hand"),mão,(s*.34,.54,-.46),None)
            self.dedos(lado,s,fechar,indicar)
        return self.obj

    def registrar(self,frame):
        self.obj.keyframe_insert(data_path="location",frame=frame,group="Deslocamento")
        self.obj.keyframe_insert(data_path="rotation_euler",frame=frame,group="Deslocamento")
        for b in self.ossos:
            if b.name=="Root":
                continue
            b.rotation_mode="QUATERNION"
            b.keyframe_insert(data_path="rotation_quaternion",frame=frame,group=b.name)
            if b.name=="Hips":
                b.keyframe_insert(data_path="location",frame=frame,group=b.name)
