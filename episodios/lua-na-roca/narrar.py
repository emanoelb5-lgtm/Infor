"""Gera a locução aprovada, em um arquivo separado por trecho."""

import argparse
import asyncio
import json
from pathlib import Path

import edge_tts


EPISODIO = Path(__file__).resolve().parent
VOZ = "pt-BR-ThalitaMultilingualNeural"


async def narrar(destino: Path, roteiro: Path = EPISODIO / "roteiro.json") -> None:
    trechos = json.loads(roteiro.read_text(encoding="utf-8"))
    vozes = await edge_tts.list_voices()
    if VOZ not in {voz["ShortName"] for voz in vozes}:
        raise RuntimeError(f"A locução requer {VOZ}, indisponível neste serviço.")

    destino.mkdir(parents=True, exist_ok=True)
    for trecho in trechos:
        caminho = destino / f'{trecho["id"]}.mp3'
        temporario = caminho.with_suffix(".tmp")
        locucao = edge_tts.Communicate(
            trecho.get("pronuncia", trecho["texto"]),
            voice=VOZ,
            rate=trecho["ritmo"],
            pitch=trecho["tom"],
            connect_timeout=15,
            receive_timeout=30,
        )
        await locucao.save(str(temporario))
        if temporario.stat().st_size < 1024:
            raise RuntimeError(f"Áudio incompleto: {trecho['id']}")
        temporario.replace(caminho)
        print(caminho.name, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=EPISODIO / "assets" / "voz")
    parser.add_argument("--roteiro", type=Path, default=EPISODIO / "roteiro.json")
    args = parser.parse_args()
    asyncio.run(narrar(args.destino, args.roteiro))
