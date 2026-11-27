"""Malhas e materiais do Seu João e da Dona Maria, em metros e voltados para -Y."""

from collections import defaultdict
from functools import lru_cache
from math import atan2, cos, exp, pi, sin
from random import Random

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
import numpy as np

from cenografia import cor, fio, malha, material, oval
from dados import esqueleto, formas, geometria, deformacao_facial

NOMES = {"male": "Seu João", "female": "Dona Maria"}
TONS = {
    "male": ("a35f3d", "c18157", "243754", "42587c", "30382a", "4f583d"),
    "female": ("9a5136", "b9714b", "853b2e", "b5553c", "22324d", "384b6b"),
}


def suave(x):
    v = min(1., max(0., x))
    return v * v * (3 - 2 * v)


def media(vertices, indices):
    return Vector(np.mean(vertices[list(indices)], axis=0))


def indices_do_grupo(nome):
    return {i for face in geometria()[2][nome] for i, _ in face}


@lru_cache(maxsize=2)
def anatomia(sexo):
    v = formas(sexo) + deformacao_facial(sexo)
    grupo = geometria()[2]
    centro = media(v, indices_do_grupo("joint-head"))
    nuca = centro.z - .095
    topo = max(v[i, 2] for face in grupo["body"] for i, _ in face)
    olho = media(v, indices_do_grupo("joint-l-eye"))
    for p in v:
        x, y, z = p
        cabeca = suave((z - nuca) / .105)
        p[0] = x * (1 + .55 * cabeca)
        p[0] *= 1 + .11 * exp(-((z-olho.z+.087)/.069)**2) * cabeca
        p[1] = centro.y + (y - centro.y) * (1 + .18 * cabeca)
        p[2] = z + cabeca * (.032 + .23 * (z - nuca))
        # Aumenta a leitura do olhar e arredonda as maçãs sem separar o rosto da cabeça.
        if z > olho.z - .072:
            ex = abs(x) - olho.x
            ez = z - olho.z
            orbital = exp(-(ex/.046)**2 - (ez/.043)**2)
            frente = suave((centro.y - y - .027) / .045)
            p[2] += .42 * orbital * ez * frente
            d = (ex/.024)**2 + (ez/.019)**2
            p[1] += .029 * suave((1.16-d)/.76) * frente
            p[1] -= .011 * exp(-((abs(x)-.065)/.033)**2 - ((ez+.045)/.029)**2) * frente
        # Alongamento discreto do tronco para uma silhueta adulta e estável.
        p[2] += .019 * suave((z - .68) / (topo - .68))
    return v


def sub(obj, nivel=1):
    mod = obj.modifiers.new("Suavização da malha", "SUBSURF")
    mod.levels = nivel
    mod.render_levels = nivel


def superficie(nome, coords, faces, mat):
    o = malha(nome, coords, faces, mat, suave=True)
    a = o.data.attributes.new("posicao_de_reposo", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", np.asarray(coords, dtype=np.float32).ravel())
    return o


def material_fixo(nome, escuro, claro, escala, relevo, rugoso):
    mat = material(nome, escuro, claro, escala, relevo, rugoso)
    if mat.node_tree.nodes.get("Rest"):
        return mat
    nodes = mat.node_tree.nodes
    attr = nodes.new("ShaderNodeAttribute")
    attr.name = "Rest"
    attr.attribute_name = "posicao_de_reposo"
    tex = next(n for n in nodes if n.type == "TEX_NOISE")
    mat.node_tree.links.new(attr.outputs["Vector"], tex.inputs["Vector"])
    return mat


@lru_cache(maxsize=2)
def materiais(sexo):
    nome = NOMES[sexo]
    s1, s2, c1, c2, p1, p2 = TONS[sexo]
    pele = material_fixo(f"Pele de {nome}", s1, s2, 26, .00058, .49)
    p = pele.node_tree.nodes.get("Principled BSDF")
    p.inputs["Subsurface Weight"].default_value = .10
    p.inputs["Subsurface Radius"].default_value = (1, .52, .28)
    p.inputs["Subsurface Scale"].default_value = .011
    camisa = material_fixo(f"Tecido de {nome}", c1, c2, 195, .0013, .78)
    outra = material_fixo(f"Roupa inferior de {nome}", p1, p2, 164, .0010, .79)
    return pele, camisa, outra


def armar(nome, vertices):
    definicao, _ = esqueleto()

    def ponto(item):
        if item["strategy"] == "CUBE":
            return media(vertices, indices_do_grupo(item["cube_name"]))
        return media(vertices, item["vertex_indices"])

    data = bpy.data.armatures.new(f"Esqueleto — {nome}")
    obj = bpy.data.objects.new(f"Rig — {nome}", data)
    bpy.context.collection.objects.link(obj)
    obj.show_in_front = True
    data.display_type = "STICK"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    base = data.edit_bones.new("Root")
    base.head, base.tail = (0, 0, 0), (0, 0, .16)
    base.use_deform = False
    for chave, item in definicao.items():
        bone = data.edit_bones.new(chave)
        bone.head, bone.tail = ponto(item["head"]), ponto(item["tail"])
        bone.roll = item["roll"]
    for chave, item in definicao.items():
        bone = data.edit_bones[chave]
        bone.parent = data.edit_bones[item["parent"] or "Root"]
        bone.use_connect = item["use_connect"] and (bone.head - bone.parent.tail).length < .0001
    for lado, codigo in (("Left", "l"), ("Right", "r")):
        bone = data.edit_bones.new(lado + "Eye")
        bone.head = media(vertices, indices_do_grupo(f"joint-{codigo}-eye"))
        bone.tail = bone.head + Vector((0, -.035, 0))
        bone.parent = data.edit_bones["Head"]
    bpy.ops.object.mode_set(mode="OBJECT")
    obj["personagem"] = nome
    return obj


def deformar(obj, rig, registro):
    for nome, pesos in registro.items():
        grupo = obj.vertex_groups.new(name=nome)
        cheios = [i for i, peso in pesos if peso >= .9999]
        if cheios:
            grupo.add(cheios, 1, "REPLACE")
        for i, peso in pesos:
            if 0 < peso < .9999:
                grupo.add([i], peso, "REPLACE")
    obj.parent = rig
    mod = obj.modifiers.new("Deformação pelo esqueleto", "ARMATURE")
    mod.object = rig
    mod.use_deform_preserve_volume = True


def recorte(nome, coords, uvs, faces, mat, rig, origem, folga=0, ondular=None, ajustar=None):
    mapa = {v: i for i, v in enumerate(sorted({i for f in faces for i, _ in f}))}
    if not mapa:
        raise ValueError(f"Região vazia de malha: {nome}")
    obj = superficie(nome, [coords[i] for i in mapa], [[mapa[i] for i, _ in f] for f in faces], mat)
    uv = obj.data.uv_layers.new(name="UVMap")
    for pol, face in zip(obj.data.polygons, faces, strict=True):
        for loop, (_, t) in zip(pol.loop_indices, face, strict=True):
            uv.data[loop].uv = uvs[t]
    if folga:
        espaco = []
        for p in obj.data.vertices:
            v = p.co.copy()
            ondulacao = ondular(v) if ondular else 0
            p.co += p.normal * (folga + ondulacao)
            if ajustar:
                p.co = ajustar(p.co)
            espaco.extend(p.co)
        obj.data.attributes["posicao_de_reposo"].data.foreach_set("vector", espaco)
        obj.data.update()
    _, pesos = esqueleto()
    registro = {}
    for osso, valores in pesos.items():
        anteriores = dict(valores)
        grupo = []
        for original, final in mapa.items():
            if original in origem:
                peso = sum(anteriores.get(i, 0)*w for i,w in origem[original].items())
            else:
                peso = anteriores.get(original, 0)
            if peso > 1e-5:
                grupo.append((final,peso))
        if grupo:
            registro[osso] = grupo
    cobertos = {i for vals in registro.values() for i, _ in vals}
    if len(cobertos) != len(mapa):
        raise ValueError(f"{nome}: {len(mapa) - len(cobertos)} vértices sem peso.")
    deformar(obj, rig, {n: v for n, v in registro.items() if v})
    sub(obj)
    return obj


def espessura(obj, valor, para_dentro=True):
    mod = obj.modifiers.new("Bainha", "SOLIDIFY")
    mod.thickness = valor
    mod.offset = -1 if para_dentro else 0


def nivelar_rig(rig, o, osso):
    """Fixa um acessório a um osso, mantendo sua posição de repouso."""
    m = o.matrix_basis.copy()
    o.parent = rig
    o.parent_type = "BONE"
    o.parent_bone = osso
    bone = rig.data.bones[osso]
    o.matrix_parent_inverse = (bone.matrix_local @ Matrix.Translation((0, bone.length, 0))).inverted()
    o.matrix_basis = m
    return o


@lru_cache(maxsize=1)
def olho_materia():
    olhos = material("Esclera e íris castanha", "f4e4d0", rugoso=.27)
    arvore = olhos.node_tree
    n = arvore.nodes
    tx = n.new("ShaderNodeTexCoord")
    xyz = n.new("ShaderNodeSeparateXYZ")
    arvore.links.new(tx.outputs["Generated"], xyz.inputs[0])
    uv = n.new("ShaderNodeCombineXYZ")
    arvore.links.new(xyz.outputs["X"], uv.inputs["X"])
    arvore.links.new(xyz.outputs["Z"], uv.inputs["Z"])
    dist = n.new("ShaderNodeVectorMath")
    dist.operation = "DISTANCE"
    dist.inputs[1].default_value = (.5, 0, .5)
    arvore.links.new(uv.outputs[0], dist.inputs[0])
    rampa = n.new("ShaderNodeValToRGB")
    r = rampa.color_ramp
    r.elements.remove(r.elements[1])
    r.elements[0].color = (*cor("130c07"), 1)
    for u, c in ((.17, "19100b"), (.184, "5e3620"), (.241, "885527"), (.289, "51301c"),
                 (.314, "352218"), (.326, "e2cbb3"), (.36, "fff2df")):
        r.elements.new(u).color = (*cor(c), 1)
    arvore.links.new(dist.outputs["Value"], rampa.inputs[0])
    frente = n.new("ShaderNodeMath")
    frente.operation = "LESS_THAN"
    frente.inputs[1].default_value = .51
    arvore.links.new(xyz.outputs["Y"], frente.inputs[0])
    mix = n.new("ShaderNodeMixRGB")
    mix.inputs[1].default_value = (*cor("f7e8d7"), 1)
    arvore.links.new(frente.outputs[0], mix.inputs[0])
    arvore.links.new(rampa.outputs[0], mix.inputs[2])
    p = n.get("Principled BSDF")
    arvore.links.new(mix.outputs[0], p.inputs["Base Color"])
    p.inputs["Coat Weight"].default_value = .29
    return olhos


def sapato(rig, lado, sexo, ponto_min):
    foot = rig.data.bones[lado + "Foot"]
    toe = rig.data.bones[lado + "ToeBase"]
    x, y, z = foot.head_local
    larga = .060 if sexo == "male" else .050
    topo = .153 if sexo == "male" else .104
    comprimento = max(.20, y - toe.head_local.y + .091)
    amostra = ((-.068,.14,.28),(-.056,.74,.76),(-.010,1,1),
               (.043,.96,.79),(.106,.95,.57),(.164,1,.47),
               (comprimento-.010,.79,.36),(comprimento,.24,.22))
    vertices, faces = [], []
    n = 24
    for andar, escala, altura in amostra:
        for i in range(n):
            a = i * 2*pi/n
            zz = max(.012, topo * altura * (.46+.54*cos(a)))
            vertices.append((x + larga*escala*sin(a), y-andar, ponto_min+zz))
    for j in range(len(amostra)-1):
        for i in range(n):
            a = j*n+i
            q = j*n+(i+1)%n
            faces.append((a,q,q+n,a+n))
    faces += [tuple(reversed(range(n))), tuple(range(len(vertices)-n,len(vertices)))]
    couro = material("Couro café", "432a23", "765141", 65, .0017, .48)
    sola = material("Sola de borracha", "2d221f", "503c31", 50, .0011, .62)
    for label, mat, fator, altura in (("Cabedal", couro, 1, 1), ("Solado", sola, 1.035, .21)):
        pts = [(x+(px-x)*fator, py, ponto_min+(pz-ponto_min)*altura-(.007 if label=="Solado" else 0))
               for px,py,pz in vertices]
        o = superficie(label, pts, faces, mat)
        nivelar_rig(rig, o, lado + "Foot")
        sub(o)


def saia(rig, posicao, mat, bainha, cintura):
    vertices, faces = [], []
    faixas = [
        (0,.247,.203), (.026,.248,.206), (.14,.242,.200),
        (.36,.227,.184), (.64,.221,.181), (.84,.203,.151), (.96,.183,.130),
        (1,.180,.126),
    ]
    for j,(t,rx,ry) in enumerate(faixas):
        for i in range(64):
            a = i*2*pi/64
            onda = (.016 * (1-t) * cos(7*a+.90) + .003*cos(11*a-.46))
            z=bainha+(cintura-bainha)*t
            vertices.append(((rx+onda)*sin(a),posicao-(ry+onda)*cos(a),z+.005*sin(5*a)*(1-t)))
    for j in range(len(faixas)-1):
        for i in range(64):
            a = j*64+i
            q = j*64+(i+1)%64
            faces.append((a,q,q+64,a+64))
    obj = superficie("Saia de gomos", vertices, faces, mat)
    pesos = {nome: [] for nome in ("Hips", "LeftUpLeg", "RightUpLeg")}
    for i,(x,_,z) in enumerate(vertices):
        influ = .64*suave((cintura-z)/(cintura-bainha))
        l = suave((x+.125)/.25)
        for nome,p in (("Hips",1-influ),("LeftUpLeg",influ*l),("RightUpLeg",influ*(1-l))):
            pesos[nome].append((i,p))
    deformar(obj, rig, pesos)
    sub(obj)
    espessura(obj,.006)
    return obj


class OrigemDoTecido:
    """Particiona a superfície em bordas lisas e interpola UV e pesos nas junções."""

    def __init__(self, vertices):
        self.vertices = [Vector(v) for v in vertices]
        self.uv = list(geometria()[1])
        self.pesos = {}
        self.cortes = {}

    def interpolar(self, anterior, atual, frac, canal):
        a, uv1 = anterior
        b, uv2 = atual
        chave = (canal, min(a,b), max(a,b))
        if chave not in self.cortes:
            idx=len(self.vertices)
            self.cortes[chave]=idx
            self.vertices.append(self.vertices[a].lerp(self.vertices[b],frac))
            p=defaultdict(float)
            for vert, influencia in ((a,1-frac),(b,frac)):
                for i,peso in self.pesos.get(vert,{vert:1.}).items():
                    p[i]+=influencia*peso
            self.pesos[idx]=p
        tex=tuple(x*(1-frac)+y*frac for x,y in zip(self.uv[uv1], self.uv[uv2], strict=True))
        self.uv.append(tex)
        return self.cortes[chave], len(self.uv)-1

    def dividir(self, faces, canal, dentro):
        internos, externos = [], []
        for face in faces:
            menores, maiores = [], []
            a=face[-1]
            fa=dentro(self.vertices[a[0]])
            for b in face:
                fb=dentro(self.vertices[b[0]])
                if (fa<0)!=(fb<0):
                    ponto=self.interpolar(a,b,fa/(fa-fb),canal)
                    menores.append(ponto)
                    maiores.append(ponto)
                (menores if fb<0 else maiores).append(b)
                a,fa=b,fb
            if len(menores)>2:
                internos.append(menores)
            if len(maiores)>2:
                externos.append(maiores)
        return internos,externos


def roupa_e_pele(sexo, rig, v):
    pele, camisa, parte_baixa = materiais(sexo)
    altura = rig.data.bones["Hips"].head_local.z
    barra = altura - (.124 if sexo=="female" else .095)
    ombro = rig.data.bones["LeftArm"].head_local
    ante = rig.data.bones["LeftForeArm"].head_local - ombro
    pesco = rig.data.bones["Neck"].head_local.z
    tornozelo = rig.data.bones["LeftFoot"].head_local.z
    fem=sexo=="female"
    bainha=.389

    def camisa_limite(pos):
        x,y,z=pos
        d=abs(x)
        avanco = (Vector((d,y,z))-ombro).dot(ante)/ante.length_squared
        manga = (avanco-.50)*.19 if d>ombro.x+.031 else -.12
        gola = pesco - (.057 if fem else .038) + .106*suave(d/.145) + .047*suave((y+.103)/.121)
        return max(barra-z,z-gola,manga)

    def tecido(pos):
        ruido = sin(pos.z*54+pos.x*14)*cos(pos.y*32+pos.x*23)
        return .0024*ruido

    cortes=OrigemDoTecido(v)
    faces=geometria()[2]["body"]
    # A parte abaixo do sapato é coberta pelo cabedal.
    _,rosto_e_roupa=cortes.dividir(faces,"linha-do-sapato",lambda p: p.z-(tornozelo+(.006 if fem else .026)))
    camisa_faces, resto=cortes.dividir(rosto_e_roupa,"contorno-da-camisa",camisa_limite)
    parte_baixa_faces, superiores=cortes.dividir(resto,"barra-da-camisa",lambda p: p.z-barra)
    if fem:
        inferiores,_=cortes.dividir(parte_baixa_faces,"borda-da-saia",lambda p: p.z-bainha-.015)
        superiores+=inferiores
    def caimento_da_camisa(v):
        x,y,z=v
        centro_y=-.022
        if fem:
            # O tecido da frente perde o detalhe fino da pele que existe sob a peça.
            p = suave((-.050-y)/.060)*exp(-((z-pesco+.223)/.101)**2)
            perfil=-.144-.035*cos(x/.193*pi*.52)
            v.y = y+(perfil-y)*p*.84
            y=v.y
        f = suave((barra+.124-z)/.123)
        if f:
            rx,ry = (.195,.149) if fem else (.186,.142)
            a=atan2(x/rx,(centro_y-y)/ry)
            v.x=x+(rx*sin(a)-x)*f*.91
            v.y=y+(centro_y-ry*cos(a)-y)*f*.91
            v.z+=f*.004*cos(7*a)
        return v

    args=cortes.vertices,cortes.uv
    obj=recorte("Pele em malha anatômica",*args,superiores,pele,rig,cortes.pesos)
    camiseta=recorte("Camisa com mangas integradas",*args,camisa_faces,camisa,rig,cortes.pesos,
                     .018,tecido,caimento_da_camisa)
    espessura(camiseta,.005)
    if not fem:
        calca=recorte("Calça de sarja",*args,parte_baixa_faces,parte_baixa,rig,cortes.pesos,.020,tecido)
        espessura(calca,.006)
    else:
        saia(rig,-.018,parte_baixa,bainha,barra+.027)
    for lado in ("Left","Right"):
        sapato(rig,lado,sexo,.006)
    return obj,camiseta,altura,pesco


def bvh(obj):
    return BVHTree.FromPolygons([v.co for v in obj.data.vertices], [p.vertices[:] for p in obj.data.polygons])


def superficie_frontal(arvore, x, z):
    p, _, _, _ = arvore.ray_cast((x,-.7,z),(0,1,0))
    return p


def caimento(pontos, diametro, mat, rig, osso, nome, resistir=None):
    o = fio(nome, pontos, diametro, mat)
    o.data.resolution_u = 12
    o.data.bevel_resolution = 3
    if resistir:
        for bp, r in zip(o.data.splines[0].bezier_points, resistir, strict=True):
            bp.radius = r
    return nivelar_rig(rig,o,osso)


def arcada(rig, pele, olho, sexo):
    arco = material("Sobrancelhas", "463b35" if sexo=="male" else "3d2925",
                    "8d8279" if sexo=="male" else "665049", 73, .0008, .68, True)
    arvore = bvh(pele)
    for lado in (-1,1):
        base = []
        for i in range(9):
            t = i/8
            x = lado * (max(.053,abs(olho.x)) + .064 * (t-.50))
            z = olho.z + .046 + .012*sin(pi*t) - .016*t
            frente = superficie_frontal(arvore, x, z)
            if frente:
                base.append((x,frente.y-.0035,z))
        if len(base) == 9:
            caimento(base,.0057,arco,rig,"Head","Sobrancelha",
                     (.28,.78,1,1.05,1,.90,.73,.47,.16))
        for j in range(2):
            linha = []
            for i in range(5):
                k=i/4
                x=lado*(abs(olho.x)+.038+.016*k)
                z=olho.z-.009-j*.006-(.007+.003*j)*k
                p=superficie_frontal(arvore,x,z)
                if p:
                    linha.append((x,p.y-.0005,z))
            if len(linha)==5:
                r=material("Linhas finas da pele","905842",rugoso=.57)
                caimento(linha,.0007,r,rig,"Head","Linha de sorriso",(.2,.66,.8,.5,.10))


def bigode(rig, pele, olho):
    mat = material("Prata quente do bigode", "8f8b80", "c4c1b2", 65,.0018,.64,True)
    fio_claro = material("Fios do bigode", "c2beb3", "e2ded2", 55,.0008,.66,True)
    arvore = bvh(pele)
    for signo in (-1,1):
        pontos=[]
        for i in range(9):
            t=i/8
            x=signo*(.007+.068*t)
            z=olho.z-.092+.011*sin(pi*t)-.016*t*t
            p=superficie_frontal(arvore,x,z)
            if p:
                pontos.append((x,p.y-.006,z))
        if len(pontos)!=9:
            continue
        caimento(pontos,.0115,mat,rig,"Head","Mecha do bigode",(.56,.92,1,1,.96,.81,.62,.42,.14))
        for j in range(11):
            f=(j+.5)/12
            k=min(7,int(f*8))
            u=f*8-k
            x,y,z=Vector(pontos[k]).lerp(Vector(pontos[k+1]),u)
            caimento([(x,y-.004,z+.008),(x+signo*.005,y-.010,z+.003),
                      (x+signo*.009,y-.009,z-.006)],.0009,fio_claro,rig,"Head","Fio prateado",(.18,1,.17))


def cabelo(rig, pele, v, sexo, olho):
    rng=Random(86 if sexo=="male" else 165)
    c1,c2=("625f5d","aaa59f") if sexo=="male" else ("282120","4a3f3b")
    base=material("Cabelo grisalho" if sexo=="male" else "Cabelo castanho grisalho",c1,c2,51,.002,.47,True)
    tons=[material(f"Reflexos nos fios de {NOMES[sexo]} {i}",c,c2,68,.00085,.48,True)
          for i,c in enumerate(("514847","837a76","aaa19c") if sexo=="female" else ("878380","a4a39e","bfbab1"))]
    arvore=bvh(pele)
    topo=max(p.co.z for p in pele.data.vertices)
    piv=Vector((0,rig.data.bones["Head"].head_local.y - .009, olho.z+.042))
    cortes=64

    def escalpo(a, frac):
        frente = max(0,cos(a))
        lado = abs(sin(a))
        phi = (1.97 - .93*frente + .19*lado)*frac
        dx=Vector((sin(a)*sin(phi),-cos(a)*sin(phi),cos(phi)))
        pt,_,_,_=arvore.ray_cast(piv+dx*.52,-dx)
        alvo=pt if pt is not None else piv+dx*.10
        p=alvo+dx*(.006+(.009 if sexo=='male' else .016)*sin(frac*pi*.74))
        if sexo=='male':
            p.z=min(p.z,topo-.014)
        return p

    verts=[tuple(escalpo(a*2*pi/cortes,.035+j/22*.965)) for j in range(23) for a in range(cortes)]
    faces=[]
    for j in range(22):
        for i in range(cortes):
            a=j*cortes+i
            b=j*cortes+(i+1)%cortes
            faces.append((a,a+cortes,b+cortes,b))
    faces.append(tuple(range(cortes)))
    casco=superficie("Volume contínuo do cabelo",verts,faces,base)
    nivelar_rig(rig,casco,"Head")
    sub(casco)
    for k in range(46 if sexo=="female" else 34):
        a=k*2*pi/(46 if sexo=="female" else 34)
        f=rng.uniform(.77,.99)
        giro=(.27+.19*sin(a))*(1 if a<pi else -1)
        pts=[]
        for j in range(11):
            t=j/10
            p=escalpo(a+giro*sin(t*2),f*(.24+.76*t))
            p.z+=.003*sin(pi*t)
            pts.append(tuple(p))
        caimento(pts,.0042 if k%3 else .0058,tons[k%len(tons)] if k%4==0 else base,
                 rig,"Head","Mecha penteada",(.07,.55,.8,1,1,.98,.85,.72,.56,.32,.05))
    if sexo=="female":
        bun=Vector((0,piv.y+.056,topo+.019))
        ovalo=oval("Coque baixo arredondado",bun,(.100,.084,.065),base,detalhe=3)
        nivelar_rig(rig,ovalo,"Head")
        for k in range(12):
            a=k*2*pi/12
            pts=[]
            for j in range(11):
                t=j/10
                b=a+.91*t
                f=sin(.35+2.52*t)
                pts.append(tuple(bun+Vector((.101*f*sin(b),.083*f*cos(b),.064*cos(.35+2.52*t)))))
            caimento(pts,.009,base if k%3 else tons[0],rig,"Head","Trança do coque",
                    (.2,.7,1,1,1,1,.88,.73,.5,.31,.1))
    else:
        chapeu(rig, topo, piv.y)


def chapeu(rig, topo, y):
    tecido=material("Palha dourada trançada","a46e32","d9ac58",55,.0028,.69,True)
    orla=material("Linha da aba", "996533","c79a54",92,.0017,.63,True)
    escuro=material("Fita escura do chapéu","3f2b20","665138",101,.001,.68)
    h=topo-.011
    perfis=((.109,.095,h+.007),(.139,.119,h+.002),(.160,.134,h-.004),
            (.198,.157,h-.012),(.244,.180,h-.008),(.252,.184,h+.006),
            (.250,.183,h+.012),(.237,.174,h+.015),(.178,.143,h+.007),
            (.146,.122,h+.007),(.145,.122,h+.035),(.137,.116,h+.089),
            (.119,.101,h+.130),(.085,.075,h+.151),(.042,.037,h+.156),(.003,.003,h+.157))
    n=72
    verts,faces=[],[]
    for rx,ry,z in perfis:
        for i in range(n):
            a=i*2*pi/n
            verts.append((rx*sin(a),y-ry*cos(a),z-.038*cos(a)+.003*sin(2*a)))
    for j in range(len(perfis)-1):
        for i in range(n):
            a=j*n+i
            q=j*n+(i+1)%n
            faces.append((a,q,q+n,a+n))
    faces.append(tuple(range(len(verts)-n,len(verts))))
    o=superficie("Chapéu de palha com copa e aba",verts,faces,tecido)
    nivelar_rig(rig,o,"Head")
    sub(o)
    for k in range(7):
        r=.160+.0142*k
        pts=[(r*sin(a*2*pi/n),y-.755*r*cos(a*2*pi/n),
              h+.011-.038*cos(a*2*pi/n)+.001*sin(a*4*pi/n)) for a in range(n)]
        f=fio("Trama da aba",pts,.0015,orla,fechado=True)
        nivelar_rig(rig,f,"Head")
    for k in range(3):
        z=h+.019+.008*k
        r=.147-.0014*k
        pts=[(r*sin(a*2*pi/n),y-.84*r*cos(a*2*pi/n),
              z-.038*cos(a*2*pi/n)+.003*sin(a*4*pi/n)) for a in range(n)]
        f=fio("Fita do chapéu",pts,.0053,escuro,fechado=True)
        nivelar_rig(rig,f,"Head")


def acabamento_camisa(rig, obj, sexo, altura, pesco):
    arvore=bvh(obj)
    botao=material("Botão de madeira", "55372b", "896344", 68,.0009,.54)
    costura=material("Costura do tecido", "526283" if sexo=="male" else "ab614c", rugoso=.71)
    alto=pesco-.047
    no=altura-.052
    if sexo=="male":
        pts=[]
        for i in range(10):
            z=no+(alto-no)*i/9
            p=superficie_frontal(arvore,0,z)
            if p:
                pts.append((.003,p.y-.003,z))
        if len(pts)>2:
            caimento(pts,.0031,costura,rig,"Spine1","Vista dos botões")
        for i in range(4):
            z=no+.063+i*.080
            p=superficie_frontal(arvore,0,z)
            if p:
                o=oval("Botão",(0,p.y-.006,z),(.012,.0047,.012),botao,detalhe=2)
                nivelar_rig(rig,o,"Spine1")
        z=alto-.144
        pontos=[(.062,z+.094),(.144,z+.091),(.143,z+.008),(.10,z-.011),(.063,z+.013),(.062,z+.094)]
        esboco=[]
        for x,z in pontos:
            p=superficie_frontal(arvore,x,z)
            if p:
                esboco.append((x,p.y-.003,z))
        if len(esboco)>3:
            caimento(esboco,.0029,costura,rig,"Spine2","Pesponto do bolso")
        for s in (-1,1):
            pts=[]
            for x,z in ((.019,alto-.016),(.051,alto+.019),(.077,alto+.074),(.124,alto+.052),(.102,alto-.020)):
                p=superficie_frontal(arvore,s*x,z)
                if p:
                    pts.append((s*x,p.y-.004,z))
            if len(pts)>2:
                caimento(pts,.0025,costura,rig,"Spine2","Costura da gola")
    else:
        pts=[]
        for i in range(15):
            x=(i-7)*.012
            z=alto+.035+(x/.088)**2*.034
            p=superficie_frontal(arvore,x,z)
            if p:
                pts.append((x,p.y-.002,z))
        if len(pts)>3:
            caimento(pts,.0027,costura,rig,"Spine2","Costura do decote")


def criar(sexo):
    v=anatomia(sexo)
    rig=armar(NOMES[sexo], v)
    pele, camisa, altura, pesco=roupa_e_pele(sexo,rig,v)
    olhos=[]
    for lado,codigo in (("Left","l"),("Right","r")):
        idx=list(indices_do_grupo(f"helper-{codigo}-eye"))
        esfera=v[idx]
        raio=(esfera.max(axis=0)-esfera.min(axis=0))/2
        centro=rig.data.bones[lado+"Eye"].head_local.copy()
        o=oval("Olho de íris castanha",centro+Vector((0,-.005,0)),(max(.021,raio[0]*1.19), max(.019,raio[1]*1.22), max(.019,raio[2]*1.32)),olho_materia(),detalhe=3)
        nivelar_rig(rig,o,lado+"Eye")
        olhos.append((o,centro))
    arcada(rig,pele,olhos[0][1],sexo)
    if sexo=="male":
        bigode(rig,pele,olhos[0][1])
    cabelo(rig,pele,v,sexo,olhos[0][1])
    acabamento_camisa(rig,camisa,sexo,altura,pesco)
    return rig,pele
