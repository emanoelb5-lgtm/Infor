"""Cenografia original, materiais procedurais e mecanismos de pose."""

from functools import lru_cache
from math import atan2, cos, pi, sin, sqrt
from random import Random

import bpy
from mathutils import Vector


def cor(hexadecimal):
    valores = [int(hexadecimal[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in valores)


@lru_cache
def material(nome, escuro, claro="", escala=16, relevo=0.035, rugoso=0.75, veio=False):
    mat = bpy.data.materials.new(nome)
    mat.diffuse_color = (*cor(escuro), 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    ligar = mat.node_tree.links.new
    p = nodes.get("Principled BSDF")
    p.inputs["Roughness"].default_value = rugoso
    p.inputs["Specular IOR Level"].default_value = 0.32
    p.inputs["Base Color"].default_value = (*cor(escuro), 1)
    if claro:
        coord = nodes.new("ShaderNodeTexCoord")
        textura = nodes.new("ShaderNodeTexNoise")
        textura.inputs["Scale"].default_value = escala
        textura.inputs["Detail"].default_value = 2.2
        textura.inputs["Roughness"].default_value = 0.68
        if veio:
            separar = nodes.new("ShaderNodeVectorMath")
            separar.operation = "MULTIPLY"
            separar.inputs[1].default_value = (0.17, 2.3, 4.9)
            ligar(coord.outputs["Object"], separar.inputs[0])
            ligar(separar.outputs[0], textura.inputs["Vector"])
        else:
            ligar(coord.outputs["Object"], textura.inputs["Vector"])
        rampa = nodes.new("ShaderNodeValToRGB")
        rampa.color_ramp.elements[0].position = 0.23
        rampa.color_ramp.elements[0].color = (*cor(escuro), 1)
        rampa.color_ramp.elements[1].position = 0.79
        rampa.color_ramp.elements[1].color = (*cor(claro), 1)
        ligar(textura.outputs["Fac"], rampa.inputs[0])
        ligar(rampa.outputs[0], p.inputs["Base Color"])
        if relevo:
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.24
            bump.inputs["Distance"].default_value = relevo
            ligar(textura.outputs["Fac"], bump.inputs["Height"])
            ligar(bump.outputs[0], p.inputs["Normal"])
    return mat


@lru_cache
def brilho(nome, paleta, energia):
    mat = bpy.data.materials.new(nome)
    mat.diffuse_color = (*cor(paleta), 1)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*cor(paleta), 1)
    p.inputs["Emission Color"].default_value = (*cor(paleta), 1)
    p.inputs["Emission Strength"].default_value = energia
    return mat


def lua_materia(nome, direcao):
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    ligar = mat.node_tree.links.new
    nodes.remove(nodes.get("Principled BSDF"))
    face = nodes.new("ShaderNodeNewGeometry")
    escalar = nodes.new("ShaderNodeVectorMath")
    escalar.operation = "DOT_PRODUCT"
    escalar.inputs[1].default_value = Vector(direcao).normalized()
    ligar(face.outputs["Normal"], escalar.inputs[0])
    luz = nodes.new("ShaderNodeMapRange")
    luz.interpolation_type = "SMOOTHSTEP"
    for chave, numero in (("From Min", -0.03), ("From Max", 0.14), ("To Min", 0.0), ("To Max", 1.0)):
        luz.inputs[chave].default_value = numero
    ligar(escalar.outputs[1], luz.inputs[0])
    local = nodes.new("ShaderNodeTexCoord")
    ruido = nodes.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 4.2
    ruido.inputs["Detail"].default_value = 4
    ligar(local.outputs["Generated"], ruido.inputs["Vector"])
    crateras = nodes.new("ShaderNodeTexVoronoi")
    crateras.inputs["Scale"].default_value = 14.0
    ligar(local.outputs["Generated"], crateras.inputs["Vector"])
    mistura = nodes.new("ShaderNodeMixRGB")
    mistura.blend_type = "MULTIPLY"
    mistura.inputs[0].default_value = 0.72
    ligar(ruido.outputs["Fac"], mistura.inputs[1])
    ligar(crateras.outputs["Distance"], mistura.inputs[2])
    paleta = nodes.new("ShaderNodeValToRGB")
    paleta.color_ramp.elements[0].position = 0.12
    paleta.color_ramp.elements[0].color = (*cor("8e8069"), 1)
    paleta.color_ramp.elements[1].position = 0.66
    paleta.color_ramp.elements[1].color = (*cor("f9eccb"), 1)
    ligar(mistura.outputs[0], paleta.inputs[0])
    terminador = nodes.new("ShaderNodeMixRGB")
    terminador.inputs[1].default_value = (*cor("142139"), 1)
    ligar(luz.outputs["Result"], terminador.inputs[0])
    ligar(paleta.outputs[0], terminador.inputs[2])
    emi = nodes.new("ShaderNodeEmission")
    emi.inputs[1].default_value = 1.27
    ligar(terminador.outputs[0], emi.inputs[0])
    ligar(emi.outputs[0], nodes.get("Material Output").inputs["Surface"])
    return mat, escalar.inputs[1]


def agrupar(nome, local=(0, 0, 0), pai=None):
    obj = bpy.data.objects.new(nome, None)
    bpy.context.collection.objects.link(obj)
    obj.parent = pai
    obj.location = local
    return obj


def malha(nome, vertices, faces, mat=None, pai=None, suave=False):
    geo = bpy.data.meshes.new(nome)
    geo.from_pydata(vertices, [], faces)
    geo.update()
    obj = bpy.data.objects.new(nome, geo)
    bpy.context.collection.objects.link(obj)
    obj.parent = pai
    if mat:
        geo.materials.append(mat)
    if suave:
        for poligono in geo.polygons:
            poligono.use_smooth = True
    return obj


@lru_cache
def esfera_malha(mat, detalhe):
    c = 16 if detalhe == 1 else 24
    n = c // 2
    vertices = [(0, 0, 1)]
    for j in range(1, n):
        r = sin(pi * j / n)
        for i in range(c):
            a = 2 * pi * i / c
            vertices.append((r * cos(a), r * sin(a), cos(pi * j / n)))
    fundo = len(vertices)
    vertices.append((0, 0, -1))
    faces = [(0, 1 + i, 1 + (i + 1) % c) for i in range(c)]
    for j in range(n - 2):
        inicio = 1 + j * c
        for i in range(c):
            k, q = inicio + i, inicio + (i + 1) % c
            faces.append((k, k + c, q + c, q))
    base = 1 + (n - 2) * c
    faces.extend((fundo, base + (i + 1) % c, base + i) for i in range(c))
    geo = bpy.data.meshes.new("Esfera " + mat.name)
    geo.from_pydata(vertices, [], faces)
    geo.update()
    geo.materials.append(mat)
    for face in geo.polygons:
        face.use_smooth = True
    return geo


def oval(nome, local, escala, mat, pai=None, detalhe=2):
    obj = bpy.data.objects.new(nome, esfera_malha(mat, detalhe))
    bpy.context.collection.objects.link(obj)
    obj.parent = pai
    obj.location = local
    obj.scale = escala
    return obj


def caixa(nome, local, tamanho, mat, raio=0.025, pai=None):
    vertices = [(x*tamanho[0]/2, y*tamanho[1]/2, z*tamanho[2]/2)
                for z in (-1, 1) for y in (-1, 1) for x in (-1, 1)]
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    obj = malha(nome, vertices, faces, mat, pai)
    obj.location = local
    if raio:
        bordas = obj.modifiers.new("Cantos boleados", "BEVEL")
        bordas.width = raio
        bordas.segments = 2
        obj.modifiers.new("Normais ponderadas", "WEIGHTED_NORMAL")
    return obj


def fio(nome, pontos, espessura, mat, pai=None, fechado=False, suave=True):
    curva = bpy.data.curves.new(nome, "CURVE")
    curva.dimensions = "3D"
    curva.resolution_u = 8
    curva.bevel_depth = espessura
    curva.bevel_resolution = 2
    spline = curva.splines.new("BEZIER" if suave else "POLY")
    spline.use_cyclic_u = fechado
    if suave:
        spline.bezier_points.add(len(pontos) - 1)
        for vertice, ponto in zip(spline.bezier_points, pontos):
            vertice.co = ponto
            vertice.handle_left_type = vertice.handle_right_type = "AUTO"
    else:
        spline.points.add(len(pontos) - 1)
        for vertice, ponto in zip(spline.points, pontos):
            vertice.co = (*ponto, 1)
    obj = bpy.data.objects.new(nome, curva)
    bpy.context.collection.objects.link(obj)
    obj.parent = pai
    curva.materials.append(mat)
    return obj


def torno(nome, perfil, mat, pai=None, local=(0, 0, 0), passos=40, ondulacao=0):
    vertices = []
    for z, r in perfil:
        for i in range(passos):
            a = i * 2*pi/passos
            rr = r * (1 + ondulacao * sin(a*9 + z*3))
            vertices.append((rr*cos(a), rr*sin(a), z))
    faces = []
    for j in range(len(perfil) - 1):
        for i in range(passos):
            a = j * passos + i
            b = j * passos + (i + 1) % passos
            faces.append((a, b, b + passos, a + passos))
    faces.append(tuple(reversed(range(passos))))
    faces.append(tuple(range(len(vertices) - passos, len(vertices))))
    obj = malha(nome, vertices, faces, mat, pai, True)
    obj.location = local
    return obj


def anel(nome, r, z, mat, pai=None, e=0.01, ondulacao=0):
    return fio(nome, [((r+ondulacao*sin(a*9))*cos(a), (r+ondulacao*sin(a*9))*sin(a), z)
                      for a in (2*pi*i/36 for i in range(36))], e, mat, pai, fechado=True)


def braço(obj, inicio, fim, rx, ry=None, sobra=0.07):
    a, b = Vector(inicio), Vector(fim)
    eixo = b - a
    obj.location = (a + b) / 2
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = eixo.to_track_quat("Z", "Y")
    obj.scale = (rx, ry if ry is not None else rx, eixo.length / 2 + sobra)


def raio_sol(nome, local, alvo, energia, rgb, tamanho):
    dados = bpy.data.lights.new(nome, "AREA")
    dados.energy = energia
    dados.color = rgb
    dados.shape = "DISK"
    dados.size = tamanho
    obj = bpy.data.objects.new(nome, dados)
    bpy.context.collection.objects.link(obj)
    obj.location = local
    obj.rotation_euler = (Vector(alvo) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def lampada(nome, local, energia, rgb, tamanho=0.3):
    dados = bpy.data.lights.new(nome, "POINT")
    dados.energy = energia
    dados.color = rgb
    dados.shadow_soft_size = tamanho
    obj = bpy.data.objects.new(nome, dados)
    bpy.context.collection.objects.link(obj)
    obj.location = local
    return obj


def iluminacao(ambiente, centro=(0, 0, 1)):
    x, y, z = centro
    mundo = bpy.data.worlds.new("Céu e luz ambiente")
    bpy.context.scene.world = mundo
    mundo.use_nodes = True
    fundo = mundo.node_tree.nodes.get("Background")
    fundo.inputs[0].default_value = (0.19, 0.24, 0.34, 1)
    fundo.inputs[1].default_value = 0.27 if ambiente == "noite" else 0.5
    noite = ambiente == "noite"
    ouro = ambiente == "varanda"
    raio_sol("Luz principal", (x-3.5, y-4, z+5.8), centro,
             320 if noite else (610 if ouro else 780),
             (0.48, 0.65, 1.0) if noite else (1, 0.80, 0.61), 4.3)
    raio_sol("Recorte", (x+2.7, y+3.7, z+4.2), centro, 580 if noite else 740,
             (0.52, 0.69, 1) if noite else (1, 0.64, 0.33), 3.0)
    raio_sol("Preenchimento", (x+3.5, y-2.8, z+2.7), centro, 130 if noite else 240,
             (0.43, 0.59, 1.0) if noite or ouro else (0.68, 0.82, 1), 5.2)


def ceu(noite=False, horizonte=-1):
    mat = bpy.data.materials.new("Gradiente pintado do céu")
    mat.use_nodes = True
    nos, ligar = mat.node_tree.nodes, mat.node_tree.links.new
    nos.remove(nos.get("Principled BSDF"))
    coord = nos.new("ShaderNodeTexCoord")
    sep = nos.new("ShaderNodeSeparateXYZ")
    ligar(coord.outputs["Generated"], sep.inputs[0])
    r = nos.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].position = 0.02
    r.color_ramp.elements[0].color = (*cor("303b64" if noite else "eaa268"), 1)
    r.color_ramp.elements[1].position = 0.74
    r.color_ramp.elements[1].color = (*cor("091327" if noite else "365878"), 1)
    e = r.color_ramp.elements.new(0.31)
    e.color = (*cor("182744" if noite else "aa7c80"), 1)
    emis = nos.new("ShaderNodeEmission")
    ligar(sep.outputs["Z"], r.inputs[0])
    ligar(r.outputs[0], emis.inputs[0])
    ligar(emis.outputs[0], nos.get("Material Output").inputs[0])
    malha("Horizonte", [(-48, 27, horizonte), (48, 27, horizonte),
                         (48, 27, horizonte+27), (-48, 27, horizonte+27)], [(0, 1, 2, 3)], mat)


def estrelas(y=14, largura=15, altura=12, base=2.0, semente=54):
    rng = Random(semente)
    mats = [brilho("Estrela âmbar", "e8bd8b", 0.7),
            brilho("Estrela perolada", "c5d7f4", 1.2),
            brilho("Estrela turva", "788cbe", 0.75)]
    for i in range(76):
        r = rng.uniform(0.008, 0.022) * (1.8 if i % 13 == 0 else 1)
        oval("Estrela", (rng.uniform(-largura, largura), y, rng.uniform(base, altura)),
             (r, r, r), mats[i % 3], detalhe=1)


def terreno(y_fundo=12, z=0, noite=False, canteiro=False, limpar=()):
    terra = material("Argila e matéria orgânica", "38251c" if noite else "4b2b18",
                    "755138" if noite else "aa6645", 25, 0.1)
    seco = material("Fragmento de terra", "52331f", "955e3d", 19, 0.04)
    rng = Random(441)
    n = 70 if canteiro else 46
    xa, xb = (-7, 7)
    ya, yb = (-7, y_fundo)
    vertices = []
    faces = []
    def perfil_solo(x, y):
        monte = 0.051*sin(3.1*x + 1.1*y) + 0.065*cos(1.7*x - 1.2*y)
        if canteiro:
            monte += 0.105 * (0.5 + 0.5*cos(5.8*x+0.25*sin(y)))**4
        return z + monte
    for j in range(n + 1):
        y = ya + (yb - ya)*j/n
        for i in range(n + 1):
            x = xa + (xb - xa)*i/n
            vertices.append((x,y,perfil_solo(x,y)+rng.uniform(-0.032,0.032)))
    for j in range(n):
        for i in range(n):
            q = j*(n+1) + i
            faces.extend(((q,q+1,q+n+2),(q,q+n+2,q+n+1)))
    malha("Solo com sulcos" if canteiro else "Terreiro", vertices, faces, terra, suave=True)
    def nivel(x,y):
        u=max(0,min(n,(x-xa)*n/(xb-xa)))
        v=max(0,min(n,(y-ya)*n/(yb-ya)))
        i,j=min(n-1,int(u)),min(n-1,int(v))
        a,b=u-i,v-j
        q=j*(n+1)+i
        z00,z10,z01,z11=(vertices[k][2] for k in (q,q+1,q+n+1,q+n+2))
        if b<=a:
            return (1-a)*z00+(a-b)*z10+b*z11
        return (1-b)*z00+a*z11+(b-a)*z01

    for i in range(85 if canteiro else 54):
        x, y = rng.uniform(-3.5, 3.5), rng.uniform(-4.0, 4.0)
        r = rng.uniform(0.014, 0.078)
        if any((x-cx)**2+(y-cy)**2 < (raio+r)**2 for cx,cy,raio in limpar):
            continue
        obj = oval("Torrão", (x,y,nivel(x,y)), (r,r*rng.uniform(0.7,1.7),r*0.55), seco, detalhe=1)
        obj.rotation_euler[2] = rng.uniform(-pi, pi)
    return nivel


def folha(nome, mat, pai, comprimento, largura, curva):
    # Três vincos visíveis da folha e nervura central, em malha de duas faces.
    n = 12
    vertices = []
    faces = []
    for j in range(n+1):
        s = j/n
        w = largura * max(0.014, sin(pi * s)**0.78) 
        z = curva * (0.78*sin(s*pi*0.92) - 0.46*s*s)
        for i in range(7):
            d = (i-3)/3
            vertices.append((w*d, s*comprimento, z - abs(d)**1.2*w*0.24 + sin(s*22)*w*0.05*d*d))
    for j in range(n):
        for i in range(6):
            k = j*7 + i
            faces.append((k, k+1, k+8, k+7))
    obj = malha(nome, vertices, faces, mat, pai, True)
    obj.modifiers.new("Cutícula", "SOLIDIFY").thickness = 0.004
    return obj


def vegetacao(local, semente, tamanho=1.5, folhas=7):
    rng = Random(semente)
    mat_a = material("Folha de taioba", "14382d", "4c7b42", 9, 0.015, 0.53)
    mat_b = material("Folha nova", "244933", "75944a", 12, 0.02, 0.53)
    caule = material("Pecíolos", "3d522d", "759054", 16, 0.011)
    raiz = agrupar("Vegetação de borda", local)
    for i in range(folhas):
        a = i*2*pi/folhas+rng.uniform(-0.3,0.3)
        d = rng.uniform(0.12,0.5)*tamanho
        h = rng.uniform(0.5,1.1)*tamanho
        ponto = (d*cos(a), d*sin(a), h)
        fio("Haste", [(0,0,0), (ponto[0]*0.43, ponto[1]*0.43, h*0.54), ponto],
            tamanho*0.009, caule, raiz)
        f = folha("Limbo lanceolado", (mat_a,mat_b)[i%2], raiz, rng.uniform(0.55,0.99)*tamanho,
                  rng.uniform(0.1,0.19)*tamanho, 0.38*tamanho)
        f.location = ponto
        f.rotation_euler = (rng.uniform(0.11,0.61), rng.uniform(-0.25,0.25), a-pi/2)
    return raiz


def mata(noite=False):
    rng = Random(13)
    dist = [("173837","325053"),("1e4238", "4b6247"),("253f3b", "4c6461")]
    if noite:
        dist = [("101e32","1b354a"), ("152d34","26424a"), ("1a3940","31534a")]
    cores = [material(f"Mata {i}", a, b, 3.6, 0.014) for i, (a,b) in enumerate(dist)]
    for i in range(22):
        x, y = -14 + 28*i/21 + rng.uniform(-0.6,0.6), rng.uniform(8.5,15)
        h = rng.uniform(0.9,2.85)
        for j in range(3):
            obj = oval("Copa distante", (x + rng.uniform(-0.6,0.6), y, h+rng.uniform(-0.42,0.48)),
                       (rng.uniform(0.56,1.28), 0.65, h*rng.uniform(0.62,0.94)), cores[(i+j)%3], detalhe=1)
            obj.rotation_euler[1] = rng.uniform(-0.35,0.35)
    return [vegetacao((x,y,0), i*61+14, s) for i,(x,y,s) in
            enumerate([(-2.9,-0.2,1.3),(2.8,1.0,1.45),(-4.0,3,1.4),(3.8,4,2.1),(-3.5,5.4,2.0),(2.8,5.9,1.7)])]


def madeira():
    return material("Madeira com veios", "482a1c", "a16843", 12, 0.045, veio=True)


def pano(cor1="506e59", cor2="73916b"):
    return material("Tecido " + cor1, cor1, cor2, 108, 0.022, 0.88)


def tablado(y0=0.4, z=0.16, largura=6, fundo=4):
    for i in range(15):
        t = fundo/15
        caixa("Tábua da varanda", (0,y0+i*t,z), (largura,t-0.014,0.15), madeira(), 0.018)


def casa(atras=2.3, lado=0, completa=False):
    madeira_clara = material("Tábuas de cumaru", "794362", "b98265", 11, 0.037, veio=True)
    telha = material("Telha de barro cozido", "432822", "ab694c", 20, 0.039)
    porta = material("Porta verde", "263e3e", "5c7b64", 12, 0.03, veio=True)
    estrutura = agrupar("Casa da roça", (lado, atras, 0.10))
    for i in range(16):
        z = 0.11 + i*0.18
        caixa("Parede da casa", (0,0.83,z), (5.9,0.18,0.17), madeira_clara, 0.013, estrutura)
    painel = caixa("Vão da janela", (1.35,0.719,1.82), (1.03,0.030,0.82),
                   brilho("Janela de fim de tarde", "f0a25b", 1.17), 0.026, estrutura)
    caixa("Porta", (-1.45,0.708,1.15), (1.18,0.09,2.08), porta, 0.024, estrutura)
    for x in (-2.07,-0.83):
        caixa("Batente", (x,0.60,1.15), (0.075,0.08,2.15), madeira(), 0.013, estrutura)
    oval("Trinco", (-1.1,0.60,1.2), (0.045,0.025,0.045), material("Latão", "af7851"), estrutura)
    for x in (0.79,1.35,1.91):
        caixa("Caixilho", (x,0.67,1.82), (0.066,0.07,0.94), madeira(), 0.012, estrutura)
    for z in (1.35,1.82,2.29):
        caixa("Caixilho", (1.35,0.66,z), (1.18,0.07,0.06), madeira(), 0.011, estrutura)
    for x in (-2.87,2.87):
        caixa("Esteio", (x,-1.27,1.51), (0.18,0.18,3.02), madeira(), 0.027, estrutura)
    for i in range(26):
        x = -3.12+i*0.248
        for lado_t in (-1,1):
            z = 3.49 if completa else 3.26
            ficha = caixa("Telha colonial", (x,0.5+lado_t*1.19,z),
                          (0.25,2.47 if completa else 2.30,0.10), telha, 0.049, estrutura)
            ficha.rotation_euler.x = -lado_t*(0.34 if completa else 0.15)
    for t in (-1,1):
        caixa("Viga", (0,0.55+t*2.10,3.0), (6.3,0.16,0.15), madeira(), 0.02, estrutura)
    return painel


def banco(local, largura=0.91):
    raiz = agrupar("Banquinho", local)
    caixa("Assento", (0,0,0.56), (largura,0.58,0.13), madeira(), 0.059, raiz)
    for x in (-largura*0.38,largura*0.38):
        for y in (-0.20,0.20):
            caixa("Pé", (x,y,0.25), (0.076,0.077,0.53), madeira(), 0.019, raiz)
    return raiz


def mesa(local=(0,0,0), largura=3.5, fundo=2.4, altura=0.8):
    raiz = agrupar("Mesa", local)
    for j in range(7):
        f = fundo/7
        caixa("Prancha da mesa", (0,-fundo/2+(j+0.5)*f,altura),
              (largura,f-0.009,0.13), madeira(), 0.023, raiz)
    for x in (-largura*0.40, largura*0.40):
        for y in (-fundo*0.38,fundo*0.38):
            caixa("Perna da mesa", (x,y,altura*0.47), (0.13,0.13,altura), madeira(), 0.022, raiz)
    return raiz


def lampiao(local, escala=1):
    raiz = agrupar("Lamparina", local)
    raiz.scale = (escala,)*3
    cobre = material("Cobre envelhecido", "5a453c", "b98a58", 26, 0.02, 0.42)
    torno("Pé da lamparina", [(0,0.19),(0.035,0.205),(0.09,0.16),(0.15,0.15)], cobre, raiz)
    torno("Topo da lamparina", [(0.40,0.15),(0.478,0.185),(0.51,0.13),(0.57,0.105)], cobre, raiz)
    chama = oval("Chama", (0,0,0.307), (0.043,0.042,0.15), brilho("Chama quente", "ffb746", 5.1), raiz)
    for i in range(5):
        a = i*2*pi/5
        fio("Grade da lamparina", [(r*cos(a),r*sin(a),z) for r,z in ((0.15,0.11),(0.175,0.27),(0.15,0.44))],
            0.013, cobre, raiz)
    fio("Alça", [(-0.11,0,0.48),(-0.19,0,0.66),(0,0,0.75),(0.19,0,0.66),(0.11,0,0.48)], 0.013, cobre, raiz)
    luz = lampada("Luz amarela da chama", (local[0],local[1]-0.13,local[2]+0.27*escala), 165*escala,
                   (1.0,0.42,0.125), 0.27*escala)
    return chama, luz


def caixa_barro(local, escala=1, cor_argila="ae623e"):
    raiz = agrupar("Tigela de cerâmica", local)
    raiz.scale = (escala,)*3
    argila = material("Cerâmica fosca "+cor_argila, "72432b", cor_argila, 31, 0.018, 0.63)
    interna = material("Esmalte âmbar", "88553a", "c79455", 27, 0.012, 0.36)
    perfil = [(0,0.245),(0.025,0.28),(0.07,0.31),(0.14,0.44),(0.22,0.52),
              (0.30,0.55),(0.337,0.546),(0.35,0.52),(0.33,0.49),(0.19,0.41),(0.092,0.25),(0.085,0.02)]
    obj = torno("Parede e fundo da tigela", perfil, argila, raiz, ondulacao=0.013)
    obj.data.materials.append(interna)
    for i, p in enumerate(obj.data.polygons):
        if i >= 6*40:
            p.material_index = 1
    anel("Friso", 0.522, 0.258, interna, raiz, 0.018, 0.005)
    return raiz


def cesto(local, escala=1, alca=False):
    raiz = agrupar("Cesto de fibra", local)
    raiz.scale = (escala,)*3
    fibra = material("Fibra de palha", "775333", "c59a5a", 35, 0.018, 0.84)
    clara = material("Palha clara", "aa7942", "ddbb77", 32, 0.02, 0.83)
    torno("Trama de fundo", [(0,0.28),(0.02,0.32),(0.12,0.40),(0.27,0.49),
          (0.44,0.54),(0.45,0.52),(0.40,0.47),(0.13,0.30),(0.06,0.01)], fibra, raiz)
    for j in range(13):
        z = 0.045+j*0.032
        r = 0.29+0.44*z+0.04*sin(pi*z/0.45)
        anel("Fio de trama", r, z, clara if j % 3 == 0 else fibra, raiz, 0.013, 0.006)
    for j in range(32):
        a = j*2*pi/32
        fio("Urdidura", [(r*cos(a+o),r*sin(a+o),z) for z,r,o in
             ((0.02,0.31,-0.02),(0.16,0.421,0.085),(0.35,0.488,-0.012),(0.44,0.54,0.06))],
             0.012, clara, raiz)
    anel("Borda trançada", 0.537, 0.452, clara, raiz, 0.034)
    if alca:
        fio("Alça", [(-0.48,0,0.37),(-0.43,0,0.72),(0,0,0.95),(0.43,0,0.72),(0.48,0,0.37)], 0.042, fibra, raiz)
    return raiz


def feijao(nome, local, tamanho=0.06, variante=0, pai=None):
    paleta = [("4d281b","9b6648"),("9d5c38","e5aa70"),("6b3628","b97049"),("5c3b2b","bc8760")]
    a,b = paleta[variante % len(paleta)]
    mat = material("Semente rajada " + a, a, b, 12, 0.011, 0.45)
    g = agrupar(nome, local, pai)
    oval("Casca da semente", (0,0,0), (tamanho,tamanho*0.62,tamanho*0.46), mat, g, 1)
    oval("Hilo do feijão", (tamanho*0.19,-tamanho*0.57,0),
         (tamanho*0.20,tamanho*0.079,tamanho*0.137), material("Hilo claro","ddac81"),g,1)
    return g


def vagem(pai, local, inclinacao=0):
    raiz = agrupar("Vagem", local, pai)
    raiz.rotation_euler[2] = inclinacao
    mat = material("Vagem", "42733d", "a2ad54", 22, 0.012, 0.53)
    vertices, faces, costura = [], [], []
    for j in range(27):
        u=j/26
        x=.504*(u-.5)
        y=.086*(sin(pi*u)-.61)+.028*u
        z=.016*sin(2*pi*u)
        r=.004+.036*sin(pi*u)**.56*(1+.13*cos(7*pi*u))
        costura.append((x,y+.93*r,z+r*.38))
        for i in range(12):
            a=2*pi*i/12
            vertices.append((x,y+r*cos(a),z+.83*r*sin(a)))
    for j in range(26):
        for i in range(12):
            a,b=j*12+i,j*12+(i+1)%12
            faces.append((a,b,b+12,a+12))
    faces.extend((tuple(reversed(range(12))),tuple(range(26*12,27*12))))
    malha("Casca contínua da vagem",vertices,faces,mat,raiz,True)
    claro=material("Nervura da vagem","779754","b0c876",27,.006)
    fio("Linha da vagem",costura[::2],.0038,claro,raiz)
    fio("Pedúnculo",[(-.305,-.057,.012),(-.275,-.041,.005),(-.248,-.051,0)],
        .012,tecido_verde(),raiz)
    return raiz


def tecido_verde():
    return material("Caule verde", "345c33", "84934f", 23, 0.012)


def papel():
    return material("Papel de fibra", "c7ad85", "e4ceb0", 103, 0.009, 0.90)


def caderno(local, largura=1.5, altura=2):
    raiz = agrupar("Caderno de campo", local)
    capa = material("Lona encerada", "343f37", "829167", 94, 0.014)
    for lado in (-1,1):
        x = (largura/2+0.011)*lado
        caixa("Capa", (x,0,0.02), (largura+0.09,altura+0.11,0.052), capa, 0.046, raiz)
        caixa("Miolo", (x,0,0.063), (largura+0.004,altura,0.068), papel(), 0.04, raiz)
        p = caixa("Folha aberta", (x,0,0.100), (largura,altura,0.021), papel(), 0.014, raiz)
        p.rotation_euler.y = lado*0.013
        ruling = material("Linhas do caderno", "a69580")
        for j in range(11):
            y = altura*0.21 - 0.142*j*altura/2
            fio("Linha impressa", [(x-largura*.42,y,0.119),(x+largura*.42,y,0.119)], 0.003, ruling, raiz)
        fio("Margem", [(x-largura*.34,altura*.26,0.12),(x-largura*.34,-altura*.49,0.12)],0.004,
            material("Margem vermelha", "b38065"),raiz)
    fio("Costura do caderno", [(0,-altura*0.50,0.127),(0,0,0.129),(0,altura*0.5,0.127)],0.009,capa,raiz)
    return raiz


def gravar(nome, palavra, local, mat, pai=None, tamanho=0.135):
    geo = bpy.data.curves.new(nome, "FONT")
    geo.body = palavra
    geo.size = tamanho
    geo.space_character = 1.1
    geo.materials.append(mat)
    obj = bpy.data.objects.new(nome, geo)
    bpy.context.collection.objects.link(obj)
    obj.parent = pai
    obj.location = local
    return obj


def lapis(local, pai=None):
    raiz = agrupar("Lápis", local, pai)
    tinta = material("Lápis amarelo", "b48028", "d9ae56", 39, 0.012)
    madeira_nua = material("Madeira do apontador", "bd9362", "edcfa0", 30, 0.01)
    grafite = material("Grafite", "3b3533")
    torno("Ponta de grafite", [(0,0.002),(0.046,0.019)], grafite, raiz, passos=12)
    torno("Madeira aparente", [(0.040,0.017),(0.132,0.042)], madeira_nua, raiz, passos=6)
    torno("Corpo do lápis", [(0.132,0.042),(0.75,0.042)], tinta, raiz, passos=6)
    torno("Borracha", [(0.75,0.042),(0.817,0.042),(0.83,0.034)], material("Borracha", "aa6d59"), raiz, passos=12)
    return raiz
