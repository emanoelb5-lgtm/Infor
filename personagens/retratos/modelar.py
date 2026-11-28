"""Reconstrução texturizada e armadura do elenco Infor."""

from functools import lru_cache
from pathlib import Path

import bpy
from mathutils import Vector
import numpy as np

from modelos import NOMES, deformar, sub, suave

PASTA = Path(__file__).resolve().parent
ARQUIVO = {"female": "maria", "male": "joao"}
# Marcos medidos na imagem frontal. As profundidades saem da malha reconstruída.
MEDIDAS = {
    "female": {
        "torso": (843, 771, 657, 529, 423, 370, 167),
        "braco": ((674,473),(764,649),(848,798),(873,851)),
        "perna": ((611,858),(618,1183),(628,1415)),
        "limite_braco": ((440,535,613,678,740,840,953),(137,166,181,173,203,249,274)),
        "limites_perna": (1122,1184,1412),
        "dedos": {
            "Thumb": ((849,834),(846,860),(850,880),(849,901)),
            "Index": ((870,847),(881,872),(880,898),(881,925)),
            "Middle": ((879,847),(894,877),(895,915),(891,954)),
            "Ring": ((885,842),(902,869),(907,909),(904,946)),
            "Pinky": ((892,840),(913,867),(918,900),(915,930)),
        },
        "olho": (558,234),
    },
    "male": {
        "torso": (936,838,704,544,429,379,113),
        "braco": ((691,492),(783,685),(870,859),(900,918)),
        "perna": ((622,960),(632,1190),(658,1414)),
        "limite_braco": ((448,550,622,696,770,874,1057),(147,183,207,224,230,238,254)),
        "limites_perna": (948,1190,1409),
        "dedos": {
            "Thumb": ((867,899),(858,928),(855,956),(850,993)),
            "Index": ((893,919),(898,955),(894,985),(897,1020)),
            "Middle": ((907,924),(916,961),(917,1004),(904,1054)),
            "Ring": ((921,920),(931,955),(930,993),(919,1040)),
            "Pinky": ((930,910),(944,947),(943,977),(931,1017)),
        },
        "olho": (555,231),
    },
}


@lru_cache(maxsize=2)
def carregar(sexo):
    with np.load(PASTA / "assets" / (ARQUIVO[sexo] + ".npz"), allow_pickle=False) as dados:
        return {nome: dados[nome] for nome in dados.files}


@lru_cache(maxsize=2)
def material(sexo):
    mat = bpy.data.materials.new("Texturas de " + NOMES[sexo])
    mat.use_nodes = True
    tr = mat.node_tree
    p = tr.nodes.get("Principled BSDF")
    p.inputs["Roughness"].default_value = .70
    p.inputs["Specular IOR Level"].default_value = .27
    tex = tr.nodes.new("ShaderNodeTexImage")
    tex.label = "Textura frontal registrada na referência"
    tex.image = bpy.data.images.load(str(PASTA / "assets" / (ARQUIVO[sexo] + ".jpg")), check_existing=True)
    tex.image.pack()
    tex.extension = "EXTEND"
    uv = tr.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "Frente da referência"
    tr.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    neural = tr.nodes.new("ShaderNodeVertexColor")
    neural.layer_name = "Textura de volume"
    mascara = tr.nodes.new("ShaderNodeAttribute")
    mascara.attribute_name = "Projeção frontal"
    cores = tr.nodes.new("ShaderNodeMixRGB")
    tr.links.new(mascara.outputs["Fac"], cores.inputs[0])
    tr.links.new(neural.outputs["Color"], cores.inputs[1])
    tr.links.new(tex.outputs["Color"], cores.inputs[2])
    tr.links.new(cores.outputs[0], p.inputs["Base Color"])
    tr.links.new(cores.outputs[0], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = .24
    return mat


class Referencia:
    def __init__(self, sexo):
        self.dados = carregar(sexo)
        self.medidas = MEDIDAS[sexo]
        self.sexo = sexo
        self.centro = float(self.dados["centro"])
        self.base = float(self.dados["base"])
        self.unit = float(self.dados["unidade"])
        self.pos = self.dados["pos"].astype(np.float32) / 10000
        x, _, z = self.pos.T
        self.pixels = np.column_stack((x/self.unit+self.centro,self.base-(z-.007)/self.unit))
        self.uv = np.column_stack((self.pixels[:,0]/1024,1-self.pixels[:,1]/1536))
        self.ossos = {}

    def ponto(self, x, y, s=1):
        x = self.centro + s * (x - self.centro)
        raio = (self.pixels[:, 0] - x) ** 2 + (self.pixels[:, 1] - y) ** 2
        perto = np.argpartition(raio, 46)[:46]
        frente, costas = np.quantile(self.pos[perto, 1], (.14, .86))
        return Vector(((x - self.centro) * self.unit, (frente + costas) * .5, (self.base - y) * self.unit + .007))

    def osso(self, nome, a, b, pai=None, deforma=True):
        self.ossos[nome] = (a, b, pai, deforma)

    def armar(self):
        nomes = ("Hips", "Spine", "Spine1", "Spine2", "Neck", "Head")
        p = [self.ponto(self.centro, y) for y in self.medidas["torso"]]
        self.osso("Root", Vector(), Vector((0, 0, .14)), deforma=False)
        for i, nome in enumerate(nomes):
            self.osso(nome, p[i], p[i + 1], nomes[i - 1] if i else "Root")

        for lado, s in (("Left", 1), ("Right", -1)):
            b1, b2, b3, b4 = [self.ponto(x, y, s) for x, y in self.medidas["braco"]]
            m0, m1, m2 = [self.ponto(x, y, s) for x, y in self.medidas["perna"]]
            self.osso(lado + "Shoulder", p[3].lerp(b1, .23), b1, "Spine2")
            for sufixo, a, b, pai in (
                ("Arm", b1, b2, "Shoulder"), ("ForeArm", b2, b3, "Arm"), ("Hand", b3, b4, "ForeArm"),
            ):
                self.osso(lado + sufixo, a, b, lado + pai)
            pe = m2 + Vector((0, -.120, -.078))
            self.osso(lado + "UpLeg", m0, m1, "Hips")
            self.osso(lado + "Leg", m1, m2, lado + "UpLeg")
            self.osso(lado + "Foot", m2, pe, lado + "Leg")
            self.osso(lado + "ToeBase", pe, pe + Vector((0, -.052, -.008)), lado + "Foot")
            for dedo, coords in self.medidas["dedos"].items():
                pts = [self.ponto(x, y, s) for x, y in coords]
                prefixo = lado + "Hand" + dedo
                for i in range(3):
                    pai = prefixo + str(i) if i else lado + "Hand"
                    self.osso(prefixo + str(i + 1), pts[i], pts[i + 1], pai)
            olho = self.ponto(*self.medidas["olho"], s)
            self.osso(lado + "Eye", olho, olho + Vector((0, -.027, 0)), "Head", deforma=False)

        arm = bpy.data.armatures.new("Esqueleto — " + NOMES[self.sexo])
        rig = bpy.data.objects.new("Rig — " + NOMES[self.sexo], arm)
        bpy.context.collection.objects.link(rig)
        bpy.context.view_layer.objects.active = rig
        rig.show_in_front = True
        arm.display_type = "STICK"
        bpy.ops.object.mode_set(mode="EDIT")
        for nome, (a, b, pai, deforma) in self.ossos.items():
            bone = arm.edit_bones.new(nome)
            bone.head, bone.tail = a, b
            bone.use_deform = deforma
            if pai:
                bone.parent = arm.edit_bones[pai]
                bone.use_connect = (bone.head - bone.parent.tail).length < .00001
        bpy.ops.object.mode_set(mode="OBJECT")
        rig["personagem"] = NOMES[self.sexo]
        rig["descida_quadril"] = .009
        rig["origem"] = "TripoSR e textura UV da referência frontal"
        return rig

    def pesos_braco(self, x, z, lado, valor):
        cotovelo = self.medidas["braco"][1][1]
        punho = self.medidas["braco"][2][1]
        ante = suave((z - cotovelo + 64) / 128)
        palma = suave((z - punho + 27) / 74)
        pesos = {
            lado + "Arm": valor * (1 - ante) * (1 - palma),
            lado + "ForeArm": valor * ante * (1 - palma),
            lado + "Hand": valor * palma,
        }
        dedos = suave((z - punho - 43) / 57) * .77
        if dedos:
            osso = self.osso_dedo(x, z, lado)
            pesos[osso] = pesos[lado + "Hand"] * dedos
            pesos[lado + "Hand"] *= 1 - dedos
        return pesos

    def transicao(self, x, z, lado, cor):
        quadril, lombar, torax, ombros, pescoco, queixo, _ = self.medidas["torso"]
        separa, joelho, torno = self.medidas["limites_perna"]
        margem = np.interp(z, *self.medidas["limite_braco"])
        fim = 1091 if self.sexo == "male" else 1002
        longe = abs(x-self.centro)
        braco = suave((longe - margem + 20) / 57) * suave((z - 419) / 108)
        if z >= fim:
            braco = 0
        elif z > 716 and longe > (279 if self.sexo == "male" else 283):
            braco = 1
        cabeca = suave((queixo + 28 - z) / 72)
        pescoco = suave((pescoco + 52 - z) / 95) * (1 - cabeca)
        pernas = suave((z - separa + 22) / 69)
        if self.sexo == "female":
            # A barra acompanha o quadril. As pernas só puxam o trecho sob o tecido.
            vermelho, _, azul = (float(c) for c in cor)
            tecido = suave((azul-vermelho+16)/37)*(1-suave((z-1273)/53))
            barra = .15*suave((z-1067)/131)
            abaixo = suave((z-1218)/57)
            pernas = barra + (1-barra)*abaixo*(1-.92*tecido)
        resto = 1 - cabeca - pescoco
        base = {"Head": cabeca, "Neck": pescoco}
        coluna = (("Spine2", ombros), ("Spine1", torax), ("Spine", lombar), ("Hips", quadril))
        peso_coluna = resto * (1 - pernas)
        for i, (nome, y) in enumerate(coluna):
            if z <= y:
                if i == 0:
                    base[nome] = peso_coluna
                else:
                    anterior, y0 = coluna[i - 1]
                    p = suave((z - y0) / (y - y0))
                    base[nome] = p * peso_coluna
                    base[anterior] = (1 - p) * peso_coluna
                break
        else:
            base["Hips"] = peso_coluna
        pe = suave((z - torno + 27) / 64)
        perna = suave((z - joelho + 67) / 134)
        base[lado + "Foot"] = resto * pernas * pe
        base[lado + "Leg"] = resto * pernas * (1 - pe) * perna
        base[lado + "UpLeg"] = resto * pernas * (1 - pe) * (1 - perna)
        if braco:
            base = {k: p * (1 - braco) for k, p in base.items()}
            base.update(self.pesos_braco(x, z, lado, braco))
        return base

    def osso_dedo(self, x, z, lado):
        origem = np.asarray((x, z))
        sinal = 1 if lado == "Left" else -1
        melhor = (float("inf"), None)
        for dedo, coords in self.medidas["dedos"].items():
            pts = np.asarray([(self.centro + sinal * (u - self.centro), v) for u, v in coords])
            for i, (a, b) in enumerate(zip(pts[:-1], pts[1:], strict=True)):
                linha = b - a
                t = max(0, min(1, np.dot(origem - a, linha) / np.dot(linha, linha)))
                d = np.linalg.norm(a + t * linha - origem)
                if d < melhor[0]:
                    melhor = (d, lado + "Hand" + dedo + str(i + 1))
        return melhor[1]

    def malha(self, rig):
        malha = bpy.data.meshes.new("Malha reconstruída de " + NOMES[self.sexo])
        faces = self.dados["faces"]
        malha.from_pydata(self.pos.tolist(), [], faces.tolist())
        malha.update()
        obj = bpy.data.objects.new(NOMES[self.sexo], malha)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(material(self.sexo))
        uv = malha.uv_layers.new(name="Frente da referência")
        uv.data.foreach_set("uv", self.uv[faces.ravel()].ravel())
        pol = malha.polygons
        pol.foreach_set("use_smooth", [True] * len(pol))
        cor = malha.color_attributes.new(name="Textura de volume", type="BYTE_COLOR", domain="POINT")
        rgb = self.dados["cor"].astype(np.float32) / 255
        cor.data.foreach_set("color_srgb", np.column_stack((rgb, np.ones(len(rgb), dtype=np.float32))).ravel())
        frontal = malha.attributes.new("Projeção frontal", "FLOAT", "POINT")
        frontal.data.foreach_set("value", self.dados["projeção"].astype(np.float32) / 255)

        nomes = list(self.ossos)
        colunas = {nome: j for j,nome in enumerate(nomes)}
        pesos = np.zeros((len(self.pos),len(nomes)),dtype=np.float32)
        for i, (x, z) in enumerate(self.pixels):
            lado = "Left" if x >= self.centro else "Right"
            for nome, p in self.transicao(x,z,lado,self.dados["cor"][i]).items():
                pesos[i,colunas[nome]]=p
        arestas = np.asarray([tuple(e.vertices) for e in malha.edges],dtype=np.int32)
        origem,destino=np.concatenate((arestas,arestas[:,::-1]),axis=0).T
        graus=np.bincount(origem,minlength=len(pesos))[:,None]
        for _ in range(2):
            soma=np.zeros_like(pesos)
            np.add.at(soma,origem,pesos[destino])
            pesos=.72*pesos+.28*soma/np.maximum(graus,1)
        pesos[pesos<.0001]=0
        total=pesos.sum(axis=1,keepdims=True)
        if np.any(total==0):
            raise RuntimeError("Um vértice ficou sem peso no esqueleto.")
        pesos/=total
        registro={}
        for j,nome in enumerate(nomes):
            indices=np.flatnonzero(pesos[:,j])
            if len(indices):
                registro[nome]=[(int(i),float(pesos[i,j])) for i in indices]
        deformar(obj, rig, registro)
        sub(obj)
        return obj


def criar_retrato(sexo):
    forma = Referencia(sexo)
    rig = forma.armar()
    return rig, forma.malha(rig)
