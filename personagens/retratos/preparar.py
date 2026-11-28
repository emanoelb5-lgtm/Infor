"""Registra a malha produzida pelo TripoSR na imagem frontal do personagem."""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import trimesh

W,H=1024,1536
S=2
TAMANHOS={"maria":1.655,"joao":1.686}


def mascara(rgb):
    claros=rgb.min(axis=2)<239
    r=ndimage.binary_fill_holes(claros)
    labels,_=ndimage.label(r)
    areas=np.bincount(labels.ravel())
    areas[0]=0
    return labels==areas.argmax()


def projetar(pontos,faces):
    imagem=Image.new("1",(W//S,H//S))
    d=ImageDraw.Draw(imagem)
    xy=pontos[:,:2]/S
    for i,j,k in faces:
        p,q,r=xy[[i,j,k]]
        d.polygon([tuple(p),tuple(q),tuple(r)],fill=1)
    return np.asarray(imagem,dtype=bool)


def intervalos(linha):
    bordas=np.flatnonzero(np.diff(np.pad(linha.astype(np.int8),(1,1))))
    return bordas.reshape((-1,2))


def faixa_silhueta(a,b):
    fonte = np.arange(W//S,dtype=float)
    mapa = np.zeros((H//S,W//S))
    for j,(m,q) in enumerate(zip(a,b,strict=True)):
        pares = []
        for l,r in intervalos(m):
            if r-l < 5:
                continue
            candidatos = [(x,y) for x,y in intervalos(q)
                          if y-x >= 5 and min(r,y)-max(l,x) > .40*min(r-l,y-x)]
            if not candidatos:
                pares.extend(((l,0),(r,0)))
                continue
            x,y = candidatos[0][0],candidatos[-1][1]
            razão = (y-x)/(r-l)
            if .55 <= razão <= 1.85 and max(abs(x-l),abs(y-r)) < 41:
                pares.extend(((l,x-l),(r,y-r)))
            else:
                pares.extend(((l,0),(r,0)))
        if pares:
            xs,delta=zip(*pares,strict=True)
            mapa[j]=np.interp(fonte,xs,delta)
    return ndimage.gaussian_filter(mapa,sigma=(4.7,1.7),mode="nearest")


def reduzir_pontas(u,v,fg,centro):
    distância,perto = ndimage.distance_transform_edt(~fg,return_indices=True)
    ji,ii = np.clip(np.rint(v).astype(int),0,H-1),np.clip(np.rint(u).astype(int),0,W-1)
    d=distância[ji,ii]
    zona=(abs(u-centro)>275)&(v>711)&(v<1079)
    porção=np.clip((d-5)/12,0,.92)*zona
    u=u+porção*(perto[1,ji,ii]-u)
    v=v+porção*(perto[0,ji,ii]-v)
    return u,v


def uv_frente(rgb, silhueta, caminho):
    # Continua as cores das bordas para a superfície não herdar halos do fundo.
    interior=ndimage.binary_erosion(silhueta,iterations=3)
    distância,perto=ndimage.distance_transform_edt(~interior,return_indices=True)
    atlas=np.full_like(rgb,125)
    margem=distância<55
    atlas[margem]=rgb[perto[0,margem],perto[1,margem]]
    Image.fromarray(atlas).save(caminho,quality=94,subsampling=0,optimize=True)


def calibrar(nome,imagem,malha,pasta):
    rgb=np.asarray(Image.open(imagem).convert("RGB"))
    if rgb.shape!=(H,W,3):
        raise ValueError("A referência usada nesta produção mede 1024 × 1536 px.")
    fg=mascara(rgb)
    linha,coluna=np.where(fg)
    yy=(float(linha.min()),float(linha.max()))
    xx=(float(coluna.min()),float(coluna.max()))
    corpo=trimesh.load_mesh(malha,process=False)
    peças=corpo.split(only_watertight=False)
    maior=max(peças,key=lambda m:m.area)
    if maior.area < .95*corpo.area:
        raise ValueError("Há uma parte relevante separada do corpo na reconstrução.")
    trimesh.smoothing.filter_taubin(maior,lamb=.47,nu=.54,iterations=5)
    v=maior.vertices.astype(np.float64)
    t=maior.faces.astype(np.uint32)
    centro=(xx[0]+xx[1])*.5
    unit=TAMANHOS[nome]/(yy[1]-yy[0])
    u=np.interp(v[:,1],(v[:,1].min(),v[:,1].max()),xx)
    vv=np.interp(v[:,2],(v[:,2].min(),v[:,2].max()),yy[::-1])
    proj=projetar(np.column_stack((u,vv)),t)
    alvo=fg[::S,::S]
    mapa=faixa_silhueta(proj,alvo)
    u+=S*ndimage.map_coordinates(mapa,[vv/S,u/S],order=1,mode="nearest")
    u,vv=reduzir_pontas(u,vv,fg,centro)
    depois=projetar(np.column_stack((u,vv)),t)
    similaridade=(depois&alvo).sum()/(depois|alvo).sum()
    # TripoSR voltado para +X. O Infor trabalha com a frente em -Y.
    normal=maior.vertex_normals.copy()
    escala=unit*(yy[1]-yy[0])/(v[:,2].max()-v[:,2].min())
    z=(yy[1]-vv)*unit+.007
    deslocamento=(np.quantile(v[:,0],.05)+np.quantile(v[:,0],.95))*.5
    coords=np.column_stack(((u-centro)*unit,-(v[:,0]-deslocamento)*escala,z))
    peso=np.clip((normal[:,0]+.042)/.34,0,1)
    peso=peso*peso*(3-2*peso)
    afastamento=ndimage.distance_transform_edt(~fg)
    d=ndimage.map_coordinates(afastamento,[vv,u],order=1,mode="nearest")
    peso*=np.clip((45-d)/20,0,1)
    cores=maior.visual.vertex_colors[:,:3]
    if len(coords)>=65536:
        raise ValueError("A malha ultrapassou a faixa de índices deste ativo.")
    pasta.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(pasta/f"{nome}.npz",pos=np.round(coords*10000).astype("int16"),
        faces=t.astype("uint16"),cor=cores.astype("uint8"),
        projeção=np.round(255*peso).astype("uint8"),centro=centro,unidade=unit,base=yy[1])
    uv_frente(rgb,fg,pasta/f"{nome}.jpg")
    print(f"{nome}: {len(coords)} vértices | {len(t)} faces | silhueta frontal {similaridade:.1%}",flush=True)
    return similaridade


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("nome",choices=list(TAMANHOS))
    p.add_argument("imagem",type=Path)
    p.add_argument("malha",type=Path)
    p.add_argument("destino",type=Path)
    a=p.parse_args()
    calibrar(a.nome,a.imagem,a.malha,a.destino)
