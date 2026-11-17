"""Crea richieste_fase1.jsonl (compiti 1-9) con il contesto della v0.9 allegato a ogni richiesta.
Nessuna chiamata all'API: serve solo a preparare e controllare le richieste."""
import json, os
from compiti import MODELLO, MAX_TOKENS, SISTEMA, COMPITI
QUI = os.path.dirname(os.path.abspath(__file__)); RD = os.path.dirname(QUI)

def contesto():
    cad = json.load(open(os.path.join(RD, 'rd_cad.json')))
    pills = json.load(open(os.path.join(RD, 'pills.json')))
    return ("Blistra v0.9 parameters from the parametric CAD (mm, cm3):\n```json\n" + json.dumps({k: v for k, v in cad.items() if k != 'parts'}, indent=1)
            + "\n```\nPrinted parts (name, volume cm3, mass g PETG, bounding box mm):\n```json\n" + json.dumps(cad['parts']) +
            "\n```\nTablet geometries already collected (thickness ranges marked t_est=true are hypotheses):\n```json\n" + json.dumps(pills) + "\n```")

def richiesta(cid, titolo, compito, ctx):
    return {"custom_id": cid, "params": {
        "model": MODELLO, "max_tokens": MAX_TOKENS, "system": SISTEMA,
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 25}],
        "messages": [{"role": "user", "content": f"# Task: {titolo}\n\n{compito}\n\n# Context\n{ctx}"}]}}

if __name__ == '__main__':
    ctx = contesto(); ids = set()
    with open(os.path.join(QUI, 'richieste_fase1.jsonl'), 'w') as f:
        for cid, titolo, compito in COMPITI:
            assert cid not in ids; ids.add(cid)
            f.write(json.dumps(richiesta(cid, titolo, compito, ctx), ensure_ascii=False) + '\n')
    print(len(ids), 'richieste scritte in richieste_fase1.jsonl')
