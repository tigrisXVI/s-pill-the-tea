"""Invia, controlla e raccoglie i batch. Serve una chiave API Anthropic (variabile ANTHROPIC_API_KEY) e `pip install anthropic`.
  python3 esegui_batch.py invia1      # manda i compiti 1-9
  python3 esegui_batch.py stato       # stato di tutti i batch salvati in stato.json
  python3 esegui_batch.py raccogli    # scarica i risultati finiti in risultati/
  python3 esegui_batch.py invia2      # manda il compito 10 con i risultati 1-9
  python3 esegui_batch.py unisci      # crea risultati/CONSOLIDATO.md e risultati/contraddizioni.json
"""
import json, os, re, sys, time
import anthropic
from compiti import MODELLO, MAX_TOKENS, SISTEMA, FINALE
QUI = os.path.dirname(os.path.abspath(__file__)); RIS = os.path.join(QUI, 'risultati'); STATO = os.path.join(QUI, 'stato.json')
os.makedirs(RIS, exist_ok=True)
client = anthropic.Anthropic()
def leggi_stato(): return json.load(open(STATO)) if os.path.exists(STATO) else {"batch": []}
def salva_stato(s): json.dump(s, open(STATO, 'w'), indent=1)

def invia(richieste, fase):
    b = client.messages.batches.create(requests=richieste)
    s = leggi_stato(); s["batch"].append({"id": b.id, "fase": fase, "creato": time.strftime('%Y-%m-%d %H:%M'), "richieste": [r["custom_id"] for r in richieste]}); salva_stato(s)
    print('batch', b.id, 'inviato:', len(richieste), 'richieste')

def stato():
    s = leggi_stato()
    for x in s["batch"]:
        b = client.messages.batches.retrieve(x["id"]); x["processing_status"] = b.processing_status; x["conteggi"] = b.request_counts.model_dump()
        print(x["fase"], x["id"], b.processing_status, b.request_counts)
    salva_stato(s)

def raccogli():
    for x in leggi_stato()["batch"]:
        if client.messages.batches.retrieve(x["id"]).processing_status != "ended": print(x["id"], 'non ancora finito'); continue
        for r in client.messages.batches.results(x["id"]):
            out = {"custom_id": r.custom_id, "esito": r.result.type}
            if r.result.type == "succeeded":
                testo = "".join(c.text for c in r.result.message.content if getattr(c, "type", "") == "text")
                m = re.search(r"```json\s*(\{.*?\})\s*```", testo, re.S)
                out["json"] = json.loads(m.group(1)) if m else None; out["testo"] = testo; out["uso"] = r.result.message.usage.model_dump()
            else: out["errore"] = str(r.result)
            json.dump(out, open(os.path.join(RIS, r.custom_id + '.json'), 'w'), indent=1, ensure_ascii=False)
            print(r.custom_id, out["esito"])

def invia2():
    prec = [json.load(open(os.path.join(RIS, f))) for f in sorted(os.listdir(RIS)) if f.startswith('b0') and f.endswith('.json')]
    mancano = [p["custom_id"] for p in prec if p["esito"] != "succeeded"]
    if len(prec) < 9 or mancano: sys.exit(f'servono i 9 risultati riusciti; mancano o falliti: {mancano or 9 - len(prec)}')
    dati = json.dumps([{"task": p["custom_id"], "result": p["json"]} for p in prec], ensure_ascii=False)
    cid, titolo, compito = FINALE
    invia([{"custom_id": cid, "params": {"model": MODELLO, "max_tokens": MAX_TOKENS, "system": SISTEMA,
            "messages": [{"role": "user", "content": f"# Task: {titolo}\n\n{compito}\n\n# Results of tasks 1-9\n```json\n{dati}\n```"}]}}], 'fase2')

def unisci():
    """Unisce tutti i risultati e segnala i valori in disaccordo: stesso argomento, numeri diversi di oltre il 20%."""
    tutti = [json.load(open(os.path.join(RIS, f))) for f in sorted(os.listdir(RIS)) if f.startswith('b') and f.endswith('.json')]
    righe, per_tema = [], {}
    for t in tutti:
        for f in (t.get("json") or {}).get("findings", []):
            righe.append(f"| {t['custom_id']} | {f.get('topic','')} | {f.get('claim','')} | {f.get('value') or ''} {f.get('unit') or ''} | {f.get('evidence','')} | {f.get('source_url') or ''} |")
            num = re.findall(r"[-+]?\d+(?:\.\d+)?", str(f.get('value') or ''))
            if num: per_tema.setdefault((f.get('topic','').lower(), (f.get('unit') or '').lower()), []).append((float(num[0]), t['custom_id'], f.get('source_url')))
    contr = [{"tema": k[0], "unita": k[1], "valori": v} for k, v in per_tema.items() if len(v) > 1 and max(x[0] for x in v) > 1.2 * max(1e-9, min(x[0] for x in v))]
    json.dump(contr, open(os.path.join(RIS, 'contraddizioni.json'), 'w'), indent=1, ensure_ascii=False)
    fin = next((t for t in tutti if t['custom_id'].startswith('b10')), None)
    with open(os.path.join(RIS, 'CONSOLIDATO.md'), 'w') as f:
        f.write('# Blistra v0.9 - risultati consolidati dei batch\n\n')
        if fin: f.write('## Conclusioni integrate (compito 10)\n\n' + fin.get('testo', '') + '\n\n')
        f.write(f'## Tutti i risultati ({len(righe)})\n\n| Compito | Tema | Affermazione | Valore | Evidenza | Fonte |\n|---|---|---|---|---|---|\n' + '\n'.join(righe) + '\n')
        f.write(f'\n## Valori in disaccordo da controllare: {len(contr)} (dettagli in contraddizioni.json)\n')
    print('CONSOLIDATO.md scritto;', len(righe), 'risultati,', len(contr), 'possibili contraddizioni')

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'invia1': invia([json.loads(l) for l in open(os.path.join(QUI, 'richieste_fase1.jsonl'))], 'fase1')
    elif cmd == 'stato': stato()
    elif cmd == 'raccogli': raccogli()
    elif cmd == 'invia2': invia2()
    elif cmd == 'unisci': unisci()
    else: print(__doc__)
