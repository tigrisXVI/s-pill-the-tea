"""Scrive PARAMETRI_STAMPA.md da parametri_stampa.json:  python3 cad/parametri_md.py v10"""
import json, sys, os
cart = sys.argv[1] if len(sys.argv) > 1 else 'v10'
d = json.load(open(os.path.join(cart, 'parametri_stampa.json')))
m, st, t = d['materiale'], d['stampante'], d['totale']
L = [f"# Blistra {d['versione']}: file di stampa e parametri\n",
     f"Generati da `cad/esporta_{d['versione'].replace('.', '').replace('v', 'v')}.py` dal CAD parametrico (modello {d['modello']}).\n",
     "## Cartelle\n",
     "- `stl/`: un STL per pezzo, già orientato per la stampa (`stampa/`), più assieme e componenti.",
     "- `3mf/`: l'assieme a colori e i piatti `piatto_1…` (pezzi già disposti su un piano 250 × 210 mm).",
     "- `step/`: non nel repository (troppo pesante), è nello zip consegnato. Solidi validi ma **sfaccettati**, convertiti dalla mesh: per misurare, FEA e assiemi; per modificare si parte dal CAD parametrico.\n",
     "## Stampante e materiale\n", "| Voce | Valore |", "|---|---|",
     f"| Stampante | {st['tipo']} |", f"| Ugello | {st['ugello_mm']} mm, {st['ugello_materiale']} |",
     f"| Materiale | {m['nome']} (densità {m['densita_g_cm3']} g/cm³) |"]
if 'requisito' in m: L.append(f"| Requisito | {m['requisito']} |")
L += [f"| Ugello °C | {m['ugello_C']} |", f"| Piano °C | {m['piano_C']} |", f"| Ventola | {m['ventola']} |", f"| Essiccazione | {m['essiccazione']} |\n",
      "## Regole generali\n"] + [f"- {r}" for r in d['regole_generali']] + [""]
if 'ferramenta' in d:
    L += ["## Ferramenta da comprare\n", "| Cosa | Quanti | Dove |", "|---|---|---|"] + [f"| {f['cosa']} | {f['quanti']} | {f['dove']} |" for f in d['ferramenta']] + [""]
L += ["## Pezzi\n", "| Pezzo | Volume cm³ | Massa g | Ingombro mm | Strato mm | Pareti | Riempimento | Supporti cm² | Tocca le pillole | Tempo min | Note |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for p in d['pezzi']:
    L.append(f"| {p['pezzo']} | {p['volume_cm3']} | {p['massa_g_petg']} | {' × '.join(str(x) for x in p['ingombro_mm'])} | {p['layer_mm']} | {p['pareti']} | {p['riempimento']} | {p['supporti_cm2']} | {'sì' if p['contatto_pillole'] else 'no'} | {p['tempo_stimato_min']} | {p.get('nota', '')} |")
L += ["", "## Piatti\n"] + [f"- **{f}**: {', '.join(p)}" for f, p in d['piatti']]
L += ["", f"## Totale\n\n{t['volume_cm3']} cm³, circa {t['massa_g']} g di PETG, circa {t['tempo_stimato_h']} h di stampa.\n",
      "I tempi sono stime dal volume, non uscite di uno slicer: vanno verificati nello slicer con la propria stampante. Filamento ed elettricità non sono conteggiati nel costo del progetto."]
open(os.path.join(cart, 'PARAMETRI_STAMPA.md'), 'w').write('\n'.join(L) + '\n')
print('scritto', os.path.join(cart, 'PARAMETRI_STAMPA.md'))
