"""Gera a biblioteca de personagens do Infor e verifica os pesos e as ações."""

import argparse
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PASTA = Path(__file__).resolve().parent
sys.path[:0] = [str(PASTA), str(PASTA.parents[1] / "episodios/lua-na-roca-3d")]
from cenas import camera
from cenografia import caixa, iluminacao, material, raio_sol
from modelos import NOMES
from movimento import Ator, Marcha, progressao


def adicionar(sexo, centro, rumo, fabricar=Ator):
    antigos = set(bpy.data.objects)
    ator = fabricar(sexo)
    colecao = bpy.data.collections.new(NOMES[sexo])
    bpy.context.scene.collection.children.link(colecao)
    for o in set(bpy.data.objects) - antigos:
        for original in list(o.users_collection):
            original.objects.unlink(o)
        colecao.objects.link(o)
    colecao.asset_mark()
    colecao.asset_data.description = "Personagem do Infor. Malha ponderada, armadura humanoide e ações de demonstração."
    colecao.asset_data.author = "Infor"
    colecao.asset_data.tags.new("Elenco")
    colecao.asset_data.tags.new("Rig humanoide")
    sem_peso = [
        (o.name, len([v for v in o.data.vertices if not v.groups]))
        for o in colecao.objects if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
    ]
    if any(n for _, n in sem_peso):
        raise RuntimeError(f"Vértices sem peso: {sem_peso}")

    s = 1 if centro>0 else -1
    trajeto = Marcha((centro+s*.12,.43,0),(centro,.02,0),.04,.42,4,s,.074)
    lateral = Marcha((centro,.02,0),(centro+s*.32,-.01,0),.51,.80,2,s,.076)
    for f in range(1,193):
        u=(f-1)/191
        gesto=progressao(u,.76,.91)*(1-progressao(u,.96,1))
        ator.pose((f-1)/24,u,trajeto if u<=.50 else lateral,lambda x,y:0,rumo,
                  (-s*.11,.055),("Right" if s>0 else "Left",(-s*.34,-.35,1.11),gesto),
                  .025+.064*gesto)
        ator.registrar(f)
    acao = ator.obj.animation_data.action
    acao.name = NOMES[sexo] + " — andar, passo lateral e gesto"
    acao.use_fake_user = True
    acao.asset_mark()
    acao.asset_data.description = "24 fps. Caminhada até o quadro 82, passo lateral nos quadros 98–154, indicação no final."
    # Os contatos usam interpolação por amostra para os pés permanecerem no apoio.
    for curva in acao.fcurves:
        for chave in curva.keyframe_points:
            chave.interpolation = "LINEAR"
    return ator,colecao


def verificar(atores, cena):
    for ator, colecao in atores:
        meshes=[o for o in colecao.objects if o.type=="MESH"]
        conteudo={o.name:len(o.data.polygons) for o in meshes}
        if len(ator.ossos) < 55 or len(ator.obj.animation_data.action.fcurves) < 100:
            raise RuntimeError("A armadura ou a animação ficou incompleta.")
        cena.frame_set(1)
        raiz = ator.obj.matrix_world.translation.copy()
        pé1 = ator.obj.matrix_world @ ator.ossos["LeftFoot"].head
        cena.frame_set(76)
        pé2 = ator.obj.matrix_world @ ator.ossos["LeftFoot"].head
        if (ator.obj.matrix_world.translation-raiz).length < .28 or (pé1-pé2).length < .20:
            raise RuntimeError("A ação de caminhada precisa deslocar a raiz e o pé.")
        cena.frame_set(132)
        dg = bpy.context.evaluated_depsgraph_get()
        polígonos = sum(len(o.evaluated_get(dg).data.polygons) for o in meshes)
        print(f"{colecao.name} | {len(ator.ossos)} ossos | {sum(conteudo.values())} faces-base | "
              f"{polígonos} faces avaliadas | sem vértices sem peso", flush=True)


def main(saida, *, fabricar=Ator, denoise=True,
         fonte_arte="A base MPFB é CC0.", fonte_codigo="personagens/elenco"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cena = bpy.context.scene
    cena.render.fps = 24
    cena.frame_end = 192
    cena.render.engine = "CYCLES"
    cena.cycles.samples = 48
    cena.cycles.use_denoising = denoise
    cena.render.resolution_x, cena.render.resolution_y = 1440, 1080
    cena.view_settings.view_transform = "AgX"
    cena.view_settings.look = "AgX - Medium High Contrast"
    cena.view_settings.exposure = .24
    iluminacao("dia",(0,0,1))
    raio_sol("Contraluz do estúdio",(0,2.1,3.4),(0,0,1.13),280,(.84,.91,1),3.4)
    caixa("Piso neutro",(0,0,-.066),(200,200,.10),material("Fundo fosco","9a8e79",rugoso=.82))
    cam = camera()
    cam((.08,-5.70,1.72),(0,0,1.00),2.55)
    atores = (
        adicionar("female",-.54,.126,fabricar),
        adicionar("male",.58,-.126,fabricar),
    )
    for t,n in ((1,"Pose inicial"),(13,"Caminhada"),(81,"Chegada"),
                (98,"Passo lateral"),(155,"Indicar"),(192,"Repouso")):
        cena.timeline_markers.new(n,frame=t)
    nota=bpy.data.texts.new("Como reutilizar o elenco")
    nota.write(
        "ELENCO DO INFOR\n\n"
        "As coleções Dona Maria e Seu João são assets independentes.\n"
        "Em outra cena, use Anexar > Collection para importar um personagem inteiro.\n"
        "A armadura aceita poses com ossos de raiz, tronco, membros, dedos e olhos.\n"
        "No Action Editor, selecione a ação marcada do personagem para ver a marcha,\n"
        "o passo lateral e o gesto. A ação tem 192 quadros a 24 fps.\n"
        f"As malhas e materiais estão contidos neste .blend. {fonte_arte}\n"
        f"Fonte: github.com/emanoelb5-lgtm/Infor/tree/main/{fonte_codigo}\n"
    )
    verificar(atores,cena)
    cena.frame_set(79)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = atores[0][0].obj
    try:
        for tela in bpy.data.screens:
            for area in tela.areas:
                if area.type == "VIEW_3D":
                    area.spaces.active.region_3d.view_distance = 3.20
                    area.spaces.active.region_3d.view_location = Vector((0,.10,1))
    except AttributeError:
        pass
    saida.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(saida.resolve()),compress=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saida",type=Path)
    main(parser.parse_args(sys.argv[sys.argv.index("--")+1:]).saida)
