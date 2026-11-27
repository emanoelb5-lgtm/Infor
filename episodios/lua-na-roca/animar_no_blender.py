"""Grava as curvas de atuação e renderiza oito vistas de um grão de feijão."""

import argparse
import json
from math import radians
from pathlib import Path
import sys

import bpy
from mathutils import Vector


QUADROS = 120
DESTINO = Path(__file__).resolve().parent / "assets" / "movimento"

# Tempo da tomada, posição do ponto de contato, escala e giro.
POSES = {
    "rosto": [(0, 222, 415, 1, 0), (.23, 222, 415, 1, 0), (.57, 219, 412, 1, 2.6),
              (.79, 220, 413, 1, 2.0), (1, 220, 413, 1, 2.0)],
    "conversa": [(0, 62, 538, 1, 0), (.21, 62, 538, 1, 0),
                 (.49, 62, 538, 1, 6.7), (.66, 62, 538, 1, 5.5),
                 (.86, 62, 538, 1, 1.4), (1, 62, 538, 1, 1.4)],
    "plantar": [(0, 359, -63, .9, -12), (.12, 342, 98, .9, -10),
                (.36, 268, 444, .9, 1.6), (.47, 260, 475, .9, 5),
                (.56, 260, 475, .9, 5), (.64, 269, 399, .9, 0),
                (.84, 374, 142, .9, -12), (1, 443, -161, .9, -18)],
    "tocar-solo": [(0, 381, -95, .88, -13), (.23, 295, 314, .88, -6),
                   (.43, 257, 490, .88, 1.2), (.56, 248, 495, .88, 4.5),
                   (.64, 251, 489, .88, 4), (.81, 309, 292, .88, -6),
                   (1, 440, -115, .88, -16)],
    "saco": [(0, 31, -58, .71, 10), (.17, 194, 234, .73, 12),
             (.33, 261, 352, .74, 5), (.44, 273, 374, .74, -21),
             (.57, 276, 376, .74, -26), (.68, 269, 373, .74, -29),
             (.78, 246, 337, .74, -12), (1, 23, -119, .73, 9)],
    "vagens": [(0, 447, -88, .75, -14), (.16, 398, 48, .76, -11),
               (.39, 302, 188, .76, 2), (.46, 290, 198, .76, 5),
               (.53, 288, 176, .76, 5), (.70, 369, 49, .75, -8),
               (1, 542, -103, .74, -21)],
    "lapis": [(0, 44, 286, .81, -12), (.15, 126, 436, .82, -14),
              (.22, 136, 440, .82, -14), (.39, 159, 437, .82, -12),
              (.54, 182, 442, .82, -12), (.69, 206, 437, .82, -11),
              (.78, 227, 440, .82, -10), (.88, 241, 404, .82, -7),
              (1, 222, 253, .82, -11)],
    "broto": [(0, 258, 511, .025, 15), (.1, 257, 511, .07, 16),
              (.29, 258, 511, .34, 10), (.52, 253, 511, .69, 2),
              (.73, 253, 511, 1, -2), (.9, 253, 511, 1.015, 0),
              (1, 253, 511, 1.015, 0)],
}


def gravar_curvas(destino):
    cena = bpy.context.scene
    cena.frame_start, cena.frame_end = 1, QUADROS + 1
    controles = {}
    for nome, poses in POSES.items():
        objeto = bpy.data.objects.new(nome, None)
        cena.collection.objects.link(objeto)
        controles[nome] = objeto
        for tempo, x, y, escala, giro in poses:
            quadro = round(tempo * QUADROS) + 1
            objeto.location = (x, y, 0)
            objeto.scale = (escala, escala, escala)
            objeto.rotation_euler.z = radians(giro)
            for canal in ("location", "scale", "rotation_euler"):
                objeto.keyframe_insert(canal, frame=quadro, group=nome)
        for curva in objeto.animation_data.action.fcurves:
            for ponto in curva.keyframe_points:
                ponto.interpolation = "BEZIER"
                ponto.handle_left_type = "AUTO_CLAMPED"
                ponto.handle_right_type = "AUTO_CLAMPED"

    amostras = {nome: [] for nome in controles}
    for quadro in range(1, QUADROS + 2):
        cena.frame_set(quadro)
        for nome, objeto in controles.items():
            valores = (*objeto.location[:2], objeto.scale.x, objeto.rotation_euler.z * 180 / 3.141592653589793)
            amostras[nome].append([round(v, 4) for v in valores])
    (destino / "curvas.json").write_text(json.dumps(amostras, separators=(",", ":")) + "\n", encoding="utf-8")


def material_feijao():
    material = bpy.data.materials.new("Feijão rajado")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    luz = nodes.get("Principled BSDF")
    luz.inputs["Roughness"].default_value = .39
    luz.inputs["Coat Weight"].default_value = .13
    luz.inputs["Coat Roughness"].default_value = .44
    textura = nodes.new("ShaderNodeTexNoise")
    textura.inputs["Scale"].default_value = 10
    textura.inputs["Detail"].default_value = 3.8
    textura.inputs["Roughness"].default_value = .7
    cor = nodes.new("ShaderNodeValToRGB")
    pontos = cor.color_ramp.elements
    pontos.remove(pontos[1])
    pontos[0].position = .24
    pontos[0].color = (.092, .022, .015, 1)
    for posicao, rgb in ((.42, (.208, .057, .031)), (.52, (.49, .26, .132)), (.69, (.62, .36, .18))):
        pontos.new(posicao).color = (*rgb, 1)
    links.new(textura.outputs["Fac"], cor.inputs[0])
    links.new(cor.outputs[0], luz.inputs["Base Color"])
    return material


def luz_area(nome, local, watts, cor, tamanho):
    data = bpy.data.lights.new(nome, "AREA")
    data.energy, data.color, data.size = watts, cor, tamanho
    objeto = bpy.data.objects.new(nome, data)
    bpy.context.scene.collection.objects.link(objeto)
    objeto.location = local
    objeto.rotation_euler = (-objeto.location).to_track_quat("-Z", "Y").to_euler()


def renderizar_graos(destino):
    destino.mkdir(parents=True, exist_ok=True)
    cena = bpy.context.scene
    cena.render.engine = "CYCLES"
    cena.cycles.samples = 72
    cena.cycles.use_denoising = False
    cena.render.resolution_x = cena.render.resolution_y = 144
    cena.render.resolution_percentage = 100
    cena.render.film_transparent = True
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_mode = "RGBA"
    cena.world = bpy.data.worlds.new("Ambiente difuso")
    cena.world.color = (.20, .17, .13)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=44, ring_count=26)
    feijao = bpy.context.object
    feijao.name = "Feijão"
    for vertice in feijao.data.vertices:
        x, y, z = vertice.co
        vertice.co = (.66*x + .25*z*z - .16, .47*y*(1-.11*z), z*(1.07 + .055*x))
    feijao.data.update()
    feijao.data.materials.append(material_feijao())
    for face in feijao.data.polygons:
        face.use_smooth = True
    assert len(feijao.data.polygons) > 900
    assert feijao.dimensions.length > 1.8

    bpy.ops.object.camera_add(location=(.24, -6, 1.04))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((0,0,0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type, camera.data.ortho_scale = "ORTHO", 2.65
    cena.camera = camera
    luz_area("Luz suave", (-3.4,-4,3.2), 430, (1,.91,.78), 3.5)
    luz_area("Preenchimento", (3,-.8,1.2), 105, (.79,.87,1), 2.8)
    luz_area("Contorno", (.8,2.7,2.1), 175, (1,.84,.70), 2.0)
    for i in range(8):
        feijao.rotation_euler = (radians(i * 18 - 36), radians(-9 + i * 4), radians(i * 45))
        cena.render.filepath = str(destino / f"feijao-{i:02d}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--curvas", type=Path, default=DESTINO)
    cli.add_argument("--graos", type=Path)
    argumentos = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    args = cli.parse_args(argumentos)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    gravar_curvas(args.curvas.resolve())
    if args.graos:
        renderizar_graos(args.graos.resolve())
