"""Bonecos articulados e alvos de contato da animação."""

from math import atan2, cos, pi, sin, sqrt
from random import Random

from mathutils import Vector

from cenografia import agrupar, anel, braço, caixa, fio, material, oval, pano, torno


class Mao:
    """Punho, palma e cinco dedos com eixos de flexão independentes."""

    def __init__(self, nome, mat, pai=None, lado=1, escala=1):
        self.raiz = agrupar(nome, pai=pai)
        self.raiz.scale = (escala,) * 3
        oval("Palma", (0,0,0.116), (0.103,0.054,0.132), mat, self.raiz)
        self.dedos = []
        for i, (x, altura) in enumerate(zip((-0.073,-0.027,0.022,0.068), (0.142,0.181,0.180,0.142))):
            p = agrupar("Base do dedo", (x,-0.008,0.197-abs(x)*0.30), self.raiz)
            p.rotation_euler.y = x*1.2
            oval("Falange proximal", (0,0,altura*0.27), (0.026-i*.001,0.029,altura*0.45),mat,p,1)
            j = agrupar("Articulação do dedo", (0,0,altura*.56), p)
            oval("Falange distal", (0,0,altura*0.23), (0.022-i*.001,0.026,altura*0.32),mat,j,1)
            self.dedos.append((p,j))
        self.polegar = agrupar("Polegar", (lado*0.072,-0.025,0.087), self.raiz)
        self.polegar.rotation_euler.y = lado*0.67
        oval("Polegar articulado",(0,0,0.072),(0.037,0.032,0.101),mat,self.polegar,1)
        self.giro = 0

    def pose(self, posicao, direcao, fechar=0.3, indicar=0, giro=0):
        self.raiz.location = posicao
        self.raiz.rotation_mode = "XYZ"
        direcao = Vector(direcao)
        if direcao.length < 0.01:
            direcao = Vector((0,0,1))
        rotacao = direcao.to_track_quat("Z", "Y")
        if giro:
            from mathutils import Quaternion
            rotacao = rotacao @ Quaternion((0,0,1), giro)
        self.raiz.rotation_euler = rotacao.to_euler()
        for i,(p,j) in enumerate(self.dedos):
            quantidade = fechar*(1.0+0.08*abs(i-1.5))
            if i == 1:
                quantidade *= 1-indicar
            p.rotation_euler.x = quantidade*1.08
            j.rotation_euler.x = quantidade*1.04
        self.polegar.rotation_euler.x = fechar*0.85


class Pessoa:
    """Proporções de boneco de barro e tecido. IK analítica nos braços."""

    def __init__(self, nome, local, velha=False, sentada=False, escala=1):
        self.velha = velha
        self.sentada = sentada
        self.raiz = agrupar(nome, local)
        self.raiz.scale = (escala,)*3
        self.base = Vector(local)
        cor_pele = ("633528","af6b4a") if velha else ("6e3d2a","b8794f")
        self.pele = material("Barro moldado " + cor_pele[0], *cor_pele, 31, 0.017, 0.64)
        self.roupa = pano("254b48","47796b") if velha else pano("8c592c","cf9c54")
        self.detalhe = pano("37695e","639888") if velha else pano("ba8142","e2b36b")
        self.calca = pano("42493a","677257") if velha else pano("34485e","576779")
        self.sapato = material("Couro do calçado", "443026", "775640", 28, 0.015)
        self.hip = 0.88 if sentada else 1.00
        self.tronco = agrupar("Eixo do corpo", (0,0,self.hip), self.raiz)
        oval("Quadril",(0,0,-0.03),(0.31,0.23,0.22),self.calca,self.tronco)
        oval("Camisa",(0,0,0.39),(0.378,0.245,0.505),self.roupa,self.tronco)
        oval("Bainha da camisa",(0,0,0.115),(0.339,0.229,0.124),self.roupa,self.tronco)
        oval("Gola",(0,-0.017,0.79),(0.175,0.16,0.063),self.detalhe,self.tronco)
        oval("Pescoço",(0,0,0.85),(0.13,0.133,0.167),self.pele,self.tronco)
        caixa("Bolso", (-0.147,-0.222,0.453), (0.164,0.042,0.164),self.detalhe,0.036,self.tronco)
        fio("Costura do bolso",[(-0.222,-0.247,0.52),(-0.221,-0.253,0.39),
             (-0.076,-0.253,0.39),(-0.072,-0.247,0.51)], .005,self.roupa,self.tronco)
        botao = material("Botão de osso", "ceab7c", "edd6af", 20, .007)
        for h in (0.31,0.47,0.63):
            oval("Botão",(0.017,-0.249+max(0,h-.56)*.29,h),(.021,.010,.021),botao,self.tronco,1)
        if velha:
            agulha = material("Bordado da camisa","b5b582","d8d0a4",22,.010)
            for j in range(5):
                x = -0.214+j*0.029
                fio("Ponto do bordado", [(x,-0.253,.475),(x+.008,-.256,.461),(x+.017,-.253,.478)],
                    .004,agulha,self.tronco)
        self.cabeca = agrupar("Eixo da cabeça",(0,-0.01,1.13),self.tronco)
        self.rosto()
        self.bracos = []
        self.pernas = []
        for lado in (-1,1):
            manga = oval("Manga", (0,0,0), (1,1,1), self.roupa, self.tronco)
            acima = oval("Braço", (0,0,0), (1,1,1), self.pele, self.tronco)
            cotovelo = oval("Cotovelo", (0,0,0), (.094,.097,.094), self.pele,self.tronco)
            baixo = oval("Antebraço", (0,0,0), (1,1,1), self.pele, self.tronco)
            mao = Mao("Mão articulada",self.pele,self.tronco,lado=-lado,escala=0.78)
            self.bracos.append((lado,manga,acima,cotovelo,baixo,mao))
            coxa = oval("Coxa", (0,0,0), (1,1,1), self.calca, self.raiz)
            canela = oval("Perna da calça", (0,0,0), (1,1,1), self.calca, self.raiz)
            bota = agrupar("Botina", pai=self.raiz)
            oval("Ponta da botina",(0,-0.119,0.108),(0.119,0.233,0.115),self.sapato,bota)
            oval("Sola da botina",(0,-0.123,0.031),(0.123,0.233,0.032),
                 material("Sola da botina","312721","644a3e",26,.012),bota,1)
            fio("Cadarço",[(-0.06,-0.094,0.19),(0,-0.115,0.215),(0.066,-0.099,0.19)],.011,
                material("Cadarço","967959"),bota)
            self.pernas.append((lado,coxa,canela,bota))

    def rosto(self):
        n = self.cabeca
        pele = self.pele
        oval("Crânio",(0,0,0),(0.265,0.230,0.308),pele,n)
        oval("Mandíbula",(0,-0.049,-0.126),(0.221,0.194,0.175),pele,n)
        cheek = material("Rosto acobreado", "945b42" if self.velha else "ab7050",
                         "b77553",35,.008)
        cabelo = material("Cabelo", "333136" if self.velha else "291f22",
                          "84756d" if self.velha else "5f4538",42,.02)
        oval("Cabelo como volume",(0,0.060,0.127),(0.264,0.218,0.220),cabelo,n)
        rng = Random(14 if self.velha else 29)
        for i in range(19):
            a = i*2*pi/19
            x,y = 0.231*cos(a), 0.041+0.175*sin(a)
            if y < 0.01:
                continue
            z = 0.06 + rng.uniform(-0.04,0.07)
            oval("Mecha esculpida",(x,y,z),(.048,.055,.141),cabelo,n,1)
        if self.velha:
            oval("Coque grisalho",(0.023,0.251,-0.018),(.126,.107,.128),cabelo,n)
            chap = agrupar("Chapéu de palha", (0,0,0.157), n)
            chap.rotation_euler = (0.12,-0.055,-0.12)
            palha = material("Palha trançada do chapéu", "946b38", "dac387", 61, .016)
            sombra = material("Palha dourada", "a67c46", "ddc086", 45, .018)
            torno("Aba e copa do chapéu",[(-.068,.46),(-.056,.49),(-.026,.493),
                  (-.011,.46),(.009,.301),(.060,.283),(.199,.23),(.229,.12),(.229,.008)],
                  palha,chap,ondulacao=.012)
            for k in range(7):
                anel("Volta de palha", .294+k*.025, .008-k*.0048,sombra,chap,.0075,.006)
            for k in range(3):
                anel("Costura da copa", .275-k*.019,.076+k*.037,sombra,chap,.007,.004)
            torno("Fita do chapéu",[(.01,.301),(.034,.304),(.062,.281),(.063,.270)],
                  pano("4a4431","8b7452"),chap)
        else:
            for i in range(6):
                x = -.18+i*.072
                oval("Franja curta",(x,-.143-.046*cos(x*5),.171+i*.012),(.063,.065,.100),cabelo,n,1)
        self.olhos = []
        esclerotica = material("Marfim dos olhos","d9c2a6")
        iris = material("Íris escura","472d24")
        pupila = material("Pupila","1a2021")
        brilho_olho = material("Reflexo dos olhos","eee5ca",rugoso=.3)
        orelha_fundo = material("Interior da orelha","905039")
        for lado in (-1,1):
            x = lado*0.103
            oval("Maçã do rosto",(lado*.151,-.171,-.091),(.099,.072,.079),cheek,n)
            oval("Orelha",(lado*.248,-.009,-.029),(.057,.061,.092),pele,n)
            oval("Relevo da orelha",(lado*.268,-.060,-.027),(.021,.011,.053),orelha_fundo,n,1)
            if self.velha:
                oval("Brinco de cobre",(lado*.273,-.056,-.098),(.021,.020,.027),
                     material("Cobre do brinco","d1a566",rugoso=.35),n)
            olho = agrupar("Pálpebras e olho",(x,-.205,0.034),n)
            oval("Sombra da pálpebra",(0,-.002,0),(.073,.027,.048),orelha_fundo,olho)
            oval("Globo ocular",(0,-.014,-.002),(.058,.024,.034),esclerotica,olho)
            olhar = agrupar("Eixo do olhar",(0,-.034,0),olho)
            oval("Íris",(0,0,0),(.029,.015,.028),iris,olhar,1)
            oval("Pupila",(.001,-.013,0),(.016,.006,.018),pupila,olhar,1)
            oval("Ponto de luz",(-.008,-.018,.009),(.007,.004,.007),brilho_olho,olhar,1)
            self.olhos.append((olho,olhar))
            fio("Sobrancelha",[(x-.063,-.179,.100),(x-.027,-.210,.122),(x+.028,-.213,.121),
                 (x+.059,-.176,.105)],.014,cabelo,n)
            if self.velha:
                for j in range(2):
                    fio("Vincos de expressão",[(lado*.150,-.233,-.034-j*.016),
                         (lado*.187,-.204,-.038-j*.022),(lado*.211,-.185,-.059-j*.021)],
                        .0036,orelha_fundo,n)
        oval("Ponte do nariz",(0,-.219,-.046),(.057,.061,.083),pele,n)
        oval("Ponta do nariz",(0,-.269,-.079),(.068,.053,.046),cheek,n)
        for e in (-1,1):
            oval("Asa do nariz",(e*.044,-.248,-.093),(.034,.032,.027),pele,n)
            oval("Narina",(e*.038,-.273,-.106),(.016,.013,.008),orelha_fundo,n,1)
        tom_boca = material("Lábio", "713b34", "a76151", 34, .010)
        self.boca = agrupar("Expressão da boca",(0,-.217,-.163),n)
        fio("Linha do sorriso",[(-.082,.012,.012),(-.039,-.014,-.008),(0,-.024,-.011),
             (.044,-.012,-.004),(.080,.011,.017)],.013,tom_boca,self.boca)
        fio("Lábio inferior",[(-.060,-.001,-.009),(0,-.024,-.023),(.06,-.002,-.006)],
            .009,cheek,self.boca)
        oval("Queixo",(0,-.166,-.224),(.112,.073,.063),pele,n)

    def pose(self, tempo, *, giro=0, olhar=(0,0), inclinacao=0, esquerda=None, direita=None,
             aperto=(0.27,0.27), apontar=0, respirar=1, passo=0, falar=0):
        t = tempo
        peso = sin(t*1.7)*.012*respirar
        self.raiz.rotation_euler.z = giro
        self.tronco.location.z = self.hip + peso
        self.tronco.rotation_euler = (inclinacao,0.022*sin(t*1.7),0.035*sin(t*1.1))
        self.cabeca.rotation_euler = (olhar[1]+.017*sin(t*2.1),.027*sin(t*1.6+.5),olhar[0])
        piscar = min(abs((t+0.66)%3.37-1.68), abs((t+0.08)%5.27-4.81))
        abre = .12+.88*min(1,piscar/.082)
        for olho,mira in self.olhos:
            olho.scale.z = abre
            mira.location.x = max(-.019,min(.019,olhar[0]*.026))
        self.boca.scale.z = 1+falar*(.58+.37*sin(t*16))
        for lado, coxa, canela, bota in self.pernas:
            fase = (passo+int(lado==1)*.5)*2*pi
            onda = sin(fase) if passo else 0
            levante = max(0,cos(fase))*.10 if passo else 0
            a = (lado*.164,0,self.hip-.055+peso)
            b = (lado*.224,-.54,.45) if self.sentada else (lado*.181,-.023+.13*onda,.55+levante*.32)
            c = (lado*.247,-.61,.16) if self.sentada else (lado*.184,-.13+.20*onda,.162+levante)
            braço(coxa,a,b,.143,.137,.085)
            braço(canela,b,c,.109,.113,.063)
            bota.location = (c[0],c[1],c[2]-.155)
            bota.rotation_euler.z = lado*.095
        for i,(lado,manga,acima,articulacao,baixo,mao) in enumerate(self.bracos):
            a = Vector((lado*.294,-.002,.673))
            alvo = (esquerda,direita)[i]
            b = Vector(alvo or (lado*.39, -.25 if self.sentada else -.058,
                       .03 if self.sentada else -.22)) - Vector((0,0,.038*sin(t*1.67+lado)))
            vetor = b-a
            d = min(0.906, max(0.15,vetor.length))
            eixo = vetor.normalized()
            b = a+eixo*d
            pino = Vector((lado*.4,.39,-.65))
            dobra = (pino-eixo*pino.dot(eixo)).normalized()
            l1,l2 = .485,.455
            adj = (l1*l1-l2*l2+d*d)/(2*d)
            meio = a+eixo*adj+dobra*sqrt(max(0,l1*l1-adj*adj))
            braço(acima,a,meio,.091,.099)
            braço(manga,a,a+(meio-a)*.45,.147,.133,.095)
            articulacao.location = meio
            braço(baixo,meio,b,.079,.091,.049)
            rumo = (b-meio).normalized()
            if apontar and lado == 1:
                rumo = (rumo*.25+Vector((.21,-.1,.89))*apontar).normalized()
            mao.pose(b,rumo,aperto[i],apontar if lado==1 else 0,giro=lado*.21)
