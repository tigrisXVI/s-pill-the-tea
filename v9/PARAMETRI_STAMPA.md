# Blistra v0.9 – file di stampa e parametri

Generati da `cad/esporta_v9.py` dal CAD parametrico (`cad/scatoletta_v3.py`, modello 2m (due ruote)).

## Cartelle

- `stl/` – un STL per pezzo, già orientato per la stampa (`stampa/`), più assieme e componenti.
- `3mf/` – `blistra_v09_assieme.3mf` (assieme a colori) e `piatto_1..4.3mf` (pezzi già disposti su un piano 250×210 mm).
- `step/` – non nel repository (263 MB): si trova nello zip consegnato. Sono solidi validi ma **sfaccettati**, convertiti dalla mesh: vanno bene per misurare, fare FEA e assemblare, non per modificare raccordi e curve. Per modifiche si parte dal CAD parametrico.

## Stampante e materiale

| Voce | Valore |
|---|---|
| Stampante | FDM a filo, piano almeno 250 x 210 mm |
| Ugello | 0.4 mm, acciaio inox o temprato per i pezzi a contatto con le pillole |
| Materiale | PETG (densità 1.27 g/cm³) |
| Ugello °C | 230-250 |
| Piano °C | 70-80 |
| Ventola | 30-50% |
| Essiccazione | 65 C per 6-8 h se il filo ha preso umidita' |

## Regole generali

- nessun gioco funzionale sotto 0,3 mm nel piano e sotto 2 strati in verticale (rapporto R&D, sezione 7)
- compensazione dei fori XY dal campione di prova T2
- smusso 0,4 mm sul primo strato dei pezzi che scorrono
- perni caricati: in acciaio, non stampati in verticale

## Pezzi

| Pezzo | Volume cm³ | Massa g | Ingombro mm | Layer mm | Pareti | Riempimento | Supporti cm² | Contatto pillole | Tempo min |
|---|---|---|---|---|---|---|---|---|---|
| 10_ruota_dx | 31.78 | 40.4 | 98.4 × 98.9 × 15.8 | 0.12 | 3 | 25% gyroid | 11.21 | sì | 71 |
| 10_ruota_sx | 31.78 | 40.4 | 98.4 × 98.9 × 15.8 | 0.12 | 3 | 25% gyroid | 11.21 | sì | 71 |
| 10_spazzole_dx | 0.31 | 0.4 | 93.4 × 94.0 × 12.6 | 0.12 | 3 | 25% gyroid | 0.0 | sì | 1 |
| 10_spazzole_sx | 0.31 | 0.4 | 93.4 × 94.0 × 12.6 | 0.12 | 3 | 25% gyroid | 0.0 | sì | 1 |
| 10_sportellini_dx | 5.77 | 7.3 | 92.3 × 2.8 × 93.4 | 0.12 | 3 | 25% gyroid | 4.64 | sì | 13 |
| 10_sportellini_sx | 5.77 | 7.3 | 92.3 × 2.8 × 93.4 | 0.12 | 3 | 25% gyroid | 4.64 | sì | 13 |
| 10_tappo_mozzo_dx | 2.21 | 2.8 | 45.2 × 4.4 × 45.2 | 0.12 | 3 | 25% gyroid | 1.92 | sì | 5 |
| 10_tappo_mozzo_sx | 2.21 | 2.8 | 45.2 × 4.4 × 45.2 | 0.12 | 3 | 25% gyroid | 1.92 | sì | 5 |
| 12_tasto | 2.23 | 2.8 | 9.1 × 26.0 × 26.0 | 0.2 | 3 | 25% gyroid | 0.89 | no | 4 |
| 13_fermo_dx | 0.05 | 0.1 | 8.1 × 1.7 × 9.5 | 0.16 | 4 | 100% | 0.04 | no | 0 |
| 13_fermo_sx | 0.05 | 0.1 | 8.1 × 1.7 × 9.5 | 0.16 | 4 | 100% | 0.04 | no | 0 |
| 14_croce_dx | 1.14 | 1.4 | 26.0 × 26.0 × 4.2 | 0.16 | 4 | 100% | 0.01 | no | 3 |
| 14_croce_sx | 1.14 | 1.4 | 26.0 × 26.0 × 4.2 | 0.16 | 4 | 100% | 0.01 | no | 3 |
| 15_pignone_dx | 0.14 | 0.2 | 12.0 × 11.7 × 2.0 | 0.16 | 4 | 100% | 0.0 | no | 0 |
| 15_pignone_sx | 0.14 | 0.2 | 12.0 × 11.7 × 2.0 | 0.16 | 4 | 100% | 0.0 | no | 0 |
| 16_vaschetta_alta | 0.26 | 0.3 | 8.3 × 5.9 × 16.8 | 0.12 | 3 | 25% gyroid | 0.11 | sì | 1 |
| 17_staffa_alta | 0.35 | 0.4 | 7.6 × 11.9 × 26.1 | 0.16 | 4 | 100% | 0.03 | no | 1 |
| 18_scivolo_dx | 0.67 | 0.9 | 11.1 × 14.4 × 18.7 | 0.12 | 3 | 25% gyroid | 0.0 | sì | 1 |
| 18_scivolo_sx | 0.67 | 0.9 | 11.1 × 14.4 × 18.7 | 0.12 | 3 | 25% gyroid | 0.0 | sì | 1 |
| 19_sportello_dx | 0.1 | 0.1 | 13.8 × 9.5 × 6.8 | 0.12 | 3 | 25% gyroid | 0.14 | sì | 0 |
| 19_sportello_sx | 0.1 | 0.1 | 13.8 × 9.5 × 6.8 | 0.12 | 3 | 25% gyroid | 0.14 | sì | 0 |
| 1_guscio | 60.6 | 77.0 | 106.3 × 52.9 × 143.6 | 0.2 | 3 | 25% gyroid | 70.59 | no | 109 |
| 2_cappello | 26.89 | 34.1 | 105.2 × 52.9 × 58.6 | 0.2 | 3 | 25% gyroid | 29.36 | no | 49 |
| 3_piede | 39.54 | 50.2 | 119.2 × 108.0 × 8.4 | 0.2 | 3 | 15% gyroid | 0.0 | no | 71 |
| 4_imbuto | 4.66 | 5.9 | 23.4 × 44.9 × 28.4 | 0.12 | 3 | 25% gyroid | 1.24 | sì | 10 |
| 5_piattino | 1.06 | 1.3 | 5.7 × 27.2 × 25.9 | 0.12 | 3 | 25% gyroid | 0.77 | sì | 2 |
| 6_staffa_cella | 0.25 | 0.3 | 5.2 × 36.6 × 6.0 | 0.16 | 4 | 100% | 0.11 | no | 1 |
| 7_bicchierino | 15.52 | 19.7 | 72.4 × 34.0 × 27.4 | 0.12 | 3 | 25% gyroid | 8.7 | sì | 34 |
| 9_cassetta_dx | 33.83 | 43.0 | 104.0 × 104.0 × 21.1 | 0.2 | 3 | 25% gyroid | 15.71 | no | 61 |
| 9_cassetta_sx | 33.83 | 43.0 | 104.0 × 104.0 × 21.1 | 0.2 | 3 | 25% gyroid | 15.71 | no | 61 |

Note per i pezzi a contatto con le pillole: ugello in acciaio, superfici lisce, lavare prima dell'uso.

## Piatti

- **piatto_1.3mf**: 3_piede, 9_cassetta_dx
- **piatto_2.3mf**: 9_cassetta_sx, 10_ruota_sx
- **piatto_3.3mf**: 10_ruota_dx, 10_spazzole_sx, 10_spazzole_dx, 1_guscio
- **piatto_4.3mf**: 2_cappello, 4_imbuto, 6_staffa_cella, 7_bicchierino, 5_piattino, 12_tasto, 14_croce_dx, 14_croce_sx, 18_scivolo_dx, 18_scivolo_sx, 17_staffa_alta, 15_pignone_sx, 15_pignone_dx, 19_sportello_sx, 19_sportello_dx, 16_vaschetta_alta, 10_tappo_mozzo_dx, 10_tappo_mozzo_sx, 10_sportellini_dx, 10_sportellini_sx, 13_fermo_sx, 13_fermo_dx

## Totale

303.4 cm³, circa 385 g di PETG, circa 9.9 h di stampa.

I tempi sono stime dal volume, non uscite di uno slicer: vanno verificati nello slicer con la propria stampante. Filamento ed elettricità non sono conteggiati nel costo del progetto.