"""Locomoção dos retratos com marcas de pisada e apoio medido na sola."""

from dataclasses import dataclass
from math import cos, pi, sin, sqrt

import bpy
from mathutils import Matrix, Quaternion, Vector

from modelar import criar_retrato
from movimento import Ator, LADOS, progressao
from modelos import suave

EIXO_X = Vector((1, 0, 0))
EIXO_Y = Vector((0, 1, 0))
EIXO_Z = Vector((0, 0, 1))
PASSADAS = (
    (.060, .265, .340),
    (.302, .506, .708),
    (.551, .755, 1.000),
    (.801, .960, 1.000),
)
PASSO_LATERAL = ((.073, .423, 1.000), (.516, .926, 1.000))


@dataclass(frozen=True)
class Apoio:
    centro: Vector
    rumo: float
    inclinacao: float = 0
    altura: float = 0


class Caminhada:
    """Trajeto curto com saída, avanço alternado e o último passo de chegada."""

    def __init__(self, inicio, fim, u0, u1, rumo_inicio, rumo_final, primeiro=1, lateral=False):
        self.inicio, self.fim = Vector(inicio), Vector(fim)
        self.u0, self.u1 = u0, u1
        self.rumo_inicio, self.rumo_final = rumo_inicio, rumo_final
        self.primeiro = primeiro
        self.lateral = lateral
        self.passos = PASSO_LATERAL if lateral else PASSADAS

    def fracao(self, u):
        return min(1., max(0., (u-self.u0)/(self.u1-self.u0)))

    def rumo(self, f):
        return self.rumo_inicio + (self.rumo_final-self.rumo_inicio)*progressao(f,.47,.96)

    def origem(self, f):
        arranque, freio = .20, .23
        distancia_total = 1-(arranque+freio)*.5
        if f< arranque:
            x=f/arranque
            d=arranque*(x**3-.5*x**4)
        elif f>1-freio:
            x=(1-f)/freio
            d=distancia_total-freio*(x**3-.5*x**4)
        else:
            d=f-arranque*.5
        return self.inicio.lerp(self.fim,d/distancia_total)

    def solo(self, f, lado):
        ultimo=Apoio(self.inicio,self.rumo_inicio)
        impacto=.060 if self.lateral else .17
        descarga=.082 if self.lateral else .22
        fim_anterior=None
        for i,(saida,chegada,avanco) in enumerate(self.passos):
            if self.primeiro*(-1)**i!=lado:
                continue
            novo=Apoio(self.inicio.lerp(self.fim,avanco),self.rumo(chegada))
            if f < saida:
                giro=descarga*progressao(f,saida-.047,saida)
                if fim_anterior is not None:
                    giro-=impacto*(1-progressao(f,fim_anterior,fim_anterior+.055))
                return Apoio(ultimo.centro,ultimo.rumo,giro)
            if f < chegada:
                fase=(f-saida)/(chegada-saida)
                mistura=suave(fase)
                passo_curto=i==len(self.passos)-1
                ganho=(.023 if passo_curto else .038)*(1-.20*self.lateral)
                return Apoio(
                    ultimo.centro.lerp(novo.centro,mistura),
                    ultimo.rumo+(novo.rumo-ultimo.rumo)*mistura,
                    descarga*(1-progressao(fase,0,.37))-impacto*progressao(fase,.69,1),
                    ganho*sin(pi*fase)**1.45,
                )
            ultimo,fim_anterior=novo,chegada
        incl=0 if fim_anterior is None else -impacto*(1-progressao(f,fim_anterior,fim_anterior+.047))
        return Apoio(ultimo.centro,ultimo.rumo,incl)

    def apoio_corpo(self, f):
        """Transfere peso para a perna que está imóvel durante o balanço da outra."""
        for i,(a,b,_) in enumerate(self.passos):
            if a<=f<=b:
                s=self.primeiro*(-1)**i
                fase=(f-a)/(b-a)
                carga=sin(pi*fase)**1.25
                return -s*carga, carga
        return 0.,0.


class AtorEmMarcha(Ator):
    def __init__(self, sexo, escala=1):
        super().__init__(sexo,escala,construir=criar_retrato)
        self.solas={}
        self.pivos={}
        bpy.context.view_layer.update()
        malha=self.pele.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
        for lado,s in LADOS:
            tornozelo=self.repouso[lado+"Foot"].translation
            pontos=[v.co.copy() for v in malha.vertices if s*v.co.x>0 and v.co.z<.048]
            if not pontos:
                raise ValueError(f"A sola {lado} não foi localizada em {self.obj.name}.")
            y_min,y_max=min(p.y for p in pontos),max(p.y for p in pontos)
            x_min,x_max=min(p.x for p in pontos),max(p.x for p in pontos)
            amostras={}
            for p in pontos:
                chave=(
                    min(3,int(4*(p.x-x_min)/max(x_max-x_min,.001))),
                    min(6,int(7*(p.y-y_min)/max(y_max-y_min,.001))),
                )
                if chave not in amostras or p.z < amostras[chave].z:
                    amostras[chave]=p
            sola=tuple(p-tornozelo for p in amostras.values())
            self.solas[lado]=sola
            frente=min(sola,key=lambda p:p.y)
            costas=max(sola,key=lambda p:p.y)
            self.pivos[lado]=(frente,costas)

    def pé(self, lado, sinal, marca, terreno, corpo, rumo):
        """Aplica a rotação em torno da ponta ou calcanhar da pisada."""
        base=self.repouso[lado+"Foot"].translation.copy()
        apoio=Quaternion(EIXO_Z,marca.rumo)
        volta=Quaternion(EIXO_Z,marca.rumo+.050*sinal)
        rot=volta@Quaternion(EIXO_X,marca.inclinacao)
        frente, calcanhar = self.pivos[lado]
        pv = calcanhar if marca.inclinacao < 0 else frente
        pos=marca.centro+apoio@Vector((base.x*.88,base.y,0))*self.escala
        recuo=volta@pv-rot@pv
        pos.x+=recuo.x*self.escala
        pos.y+=recuo.y*self.escala
        alturas=[]
        for ponto in self.solas[lado]:
            p=rot@ponto*self.escala
            alturas.append(terreno(pos.x+p.x,pos.y+p.y)-p.z)
        pos.z=max(alturas)+.0015+marca.altura
        return rumo.inverted()@(pos-corpo)/self.escala,rumo.inverted()@rot

    def quadril(self, pes, balanço, carga, t):
        neutro=self.repouso["Hips"].translation.copy()
        q=Quaternion(EIXO_Z,.048*balanço) @ Quaternion(EIXO_Y,.032*balanço)
        neutro.x += .018*balanço
        neutro.z += -.005 + .010*carga + .003*sin(t*1.8)
        limite=neutro.z
        for lado,_ in LADOS:
            deslocamento=q@(self.repouso[lado+"UpLeg"].translation-self.repouso["Hips"].translation)
            c=pes[lado]
            d=(c.x-neutro.x-deslocamento.x)**2+(c.y-neutro.y-deslocamento.y)**2
            alcance=self.ossos[lado+"UpLeg"].length+self.ossos[lado+"Leg"].length-.0018
            teto=c.z-deslocamento.z+sqrt(max(.001,alcance**2-d))
            # Um mínimo suave evita um ressalto quando o apoio troca de perna.
            limite=min(limite,teto)-max(0.,.010-abs(limite-teto))**2/.040
        neutro.z=limite
        self.posicionar("Hips",q,neutro)

    def pose(self,t,u,marcha,altura,giro,olhar=(0,0),gesto=None,inclinacao=0):
        self.poses.clear()
        for b in self.ossos:
            b.matrix_basis=Matrix.Identity(4)
        f=marcha.fracao(u)
        direcao=marcha.rumo(f)
        corpo=marcha.origem(f)
        corpo.z+=altura(corpo.x,corpo.y)
        self.obj.location=corpo
        self.obj.rotation_euler=(0,0,direcao)
        rumo=Quaternion(EIXO_Z,direcao)
        balance,carga=marcha.apoio_corpo(f)
        marcas={lado:marcha.solo(f,s) for lado,s in LADOS}
        apoios={lado:self.pé(lado,s,marcas[lado],altura,corpo,rumo) for lado,s in LADOS}
        self.quadril({l:p for l,(p,_) in apoios.items()},balance,carga,t)

        flexao=inclinacao*.68+.052*carga
        self.posicionar("Spine",Quaternion(EIXO_X,flexao*.55))
        tronco=Quaternion(EIXO_X,flexao)@Quaternion(EIXO_Z,-.069*balance)
        self.posicionar("Spine2",tronco)
        giro_cabeca=olhar[0]+.37*(giro-direcao)
        pescoço=Quaternion(EIXO_Z,.52*giro_cabeca)@Quaternion(EIXO_X,.52*olhar[1])
        self.posicionar("Neck",pescoço)
        cabeca=Quaternion(EIXO_Z,giro_cabeca)@Quaternion(EIXO_X,olhar[1]+.009*sin(t*2.28))
        self.posicionar("Head",cabeca)
        for lado,s in LADOS:
            self.posicionar(lado+"Eye",cabeca)
            pé,rotação=apoios[lado]
            polo=Quaternion(EIXO_Z,marcas[lado].rumo-direcao)@Vector((s*.035,-1,0))
            self.membros((lado+"UpLeg",lado+"Leg",lado+"Foot"),pé,polo,rotação)

            outro="Right" if lado=="Left" else "Left"
            avanco=apoios[outro][0].y-self.repouso[outro+"Foot"].translation.y
            balanco_braco=min(.094,max(-.105,.42*avanco))
            ativar=progressao(f,.01,.135)*(1-progressao(f,.85,1))
            frente=.009+balanco_braco*ativar*(.30 if marcha.lateral else 1)
            ombro=self.matriz(lado+"Arm").translation
            compr=self.ossos[lado+"Arm"].length+self.ossos[lado+"ForeArm"].length
            punho=ombro+Vector((s*.087,frente,-.91*compr+.16*abs(frente)))
            indicar,fechar=0.,.27
            if gesto and gesto[0]==lado:
                _,alvo,forca=gesto
                punho=punho.lerp(Vector(alvo),forca)
                indicar,fechar=.80*forca,.27+.092*forca
            self.membros((lado+"Arm",lado+"ForeArm",lado+"Hand"),punho,(s*.24,.57,-.38),None)
            self.dedos(lado,s,fechar,indicar)
        return self.obj
