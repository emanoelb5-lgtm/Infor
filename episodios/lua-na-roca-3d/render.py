"""Renderiza um plano Blender a partir de uma coreografia determinística."""

import argparse
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cenas import PLANOS


def renderizar(args):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = args.amostras
    scene.cycles.use_denoising = args.denoise
    scene.cycles.use_light_tree = False
    scene.cycles.max_bounces = 3
    scene.cycles.diffuse_bounces = 1
    scene.cycles.glossy_bounces = 2
    scene.cycles.transparent_max_bounces = 3
    scene.cycles.adaptive_threshold = 0.16
    scene.cycles.adaptive_min_samples = min(5, args.amostras)
    scene.cycles.sample_clamp_indirect = 1.6
    scene.render.use_persistent_data = True
    scene.render.resolution_x, scene.render.resolution_y = args.largura, args.altura
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 93
    scene.render.fps = args.fps
    scene.render.threads_mode = "FIXED"
    scene.render.threads = args.threads
    scene.render.use_motion_blur = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.31
    cena = PLANOS[args.plano]()
    args.pasta.mkdir(parents=True, exist_ok=True)
    if args.previa:
        quadros = [(f"previa-{int(fracao*100):03d}",fracao) for fracao in args.previa]
    else:
        quadros = [(f"{i:04d}", i/(args.quadros - 1)) for i in range(args.primeiro, args.ultimo)]
    for i,(nome,u) in enumerate(quadros):
        scene.frame_set(args.primeiro+i+1)
        cena(u*args.duracao, u)
        scene.render.filepath = str((args.pasta / (nome + ".jpg")).resolve())
        bpy.ops.render.render(write_still=True)


def argumentos():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plano", required=True, choices=sorted(PLANOS))
    p.add_argument("--pasta", required=True, type=Path)
    p.add_argument("--quadros", type=int, default=2)
    p.add_argument("--primeiro", type=int, default=0)
    p.add_argument("--ultimo", type=int)
    p.add_argument("--duracao", type=float, default=5)
    p.add_argument("--fps", type=int, default=18)
    p.add_argument("--largura", type=int, default=540)
    p.add_argument("--altura", type=int, default=960)
    p.add_argument("--amostras", type=int, default=11)
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--previa", type=float, nargs="+")
    p.add_argument("--denoise", action="store_true")
    args = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if args.ultimo is None:
        args.ultimo = args.quadros
    if args.quadros < 2 or args.duracao <= 0:
        p.error("Indique pelo menos dois quadros e uma duração positiva.")
    if not 0 <= args.primeiro < args.ultimo <= args.quadros:
        p.error("A faixa de quadros precisa caber no plano.")
    return args


if __name__ == "__main__":
    renderizar(argumentos())
