# Blistra v1.2: file di stampa e parametri

Generati da `cad/esporta_v12.py` dal CAD parametrico (modello 2m (due ruote)).

## Cartelle

- `stl/`: un STL per pezzo, già orientato per la stampa (`stampa/`), più assieme e componenti.
- `3mf/`: l'assieme a colori e i piatti `piatto_1…` (pezzi già disposti su un piano 250 × 210 mm).
- `step/`: non nel repository (troppo pesante), è nello zip consegnato. Solidi validi ma **sfaccettati**, convertiti dalla mesh: per misurare, FEA e assiemi; per modificare si parte dal CAD parametrico.

## Stampante e materiale

| Voce | Valore |
|---|---|
| Stampante | FDM a filo, piano almeno 250 x 210 mm |
| Ugello | 0.4 mm, acciaio inox o temprato per i pezzi a contatto con le pillole |
| Materiale | PETG (densità 1.27 g/cm³) |
| Requisito | scheda tecnica con almeno 45 MPa di trazione nel piano XY (I-14): le schede trovate vanno da 31,9 a 68,4 MPa |
| Ugello °C | 230-250 |
| Piano °C | 70-80 |
| Ventola | 30-50% |
| Essiccazione | 65 C per 6-8 h se il filo ha preso umidita' |

## Regole generali

- nessun gioco funzionale sotto 0,3 mm nel piano e sotto 2 strati in verticale (rapporto R&D, sezione 7); unica eccezione voluta: 0,2 mm tra divisori e sportellini (I-6)
- compensazione dei fori XY dal campione di prova T2
- smusso 0,4 mm sul primo strato dei pezzi che scorrono
- perni caricati: in acciaio, non stampati in verticale
- pezzi a contatto con le pillole: PETG naturale (senza colore), strati da 0,12, ugello d'acciaio (I-8)

## Ferramenta da comprare

| Cosa | Quanti | Dove |
|---|---|---|
| spina cilindrica d'acciaio 6 x 16 mm (ISO 2338) | 2 | assi delle ruote (I-2) |
| alesatore a mano 6 mm H7 | 1 | foro delle ruote (I-2) |
| spina d'acciaio 3 x 4 mm, o chiodo da 3 mm tagliato | 2 | perni delle croci di Malta (I-3) |
| vite M2 (di recupero da un hard disk) | 2 | assi delle croci di Malta |
| vite M3 x 6 (non piu' lunga) | 4 | alette degli stepper sulla piastra |
| vite M2,5 x 8 + dado M2,5 | 2 + 2 | fissaggio delle cassette |
| pulsantino 6 x 6 mm alto 7 | 2 | finecorsa delle ruote |
| filo d'acciaio da 0,8 mm (graffette) | circa 50 cm | cerniere degli sportellini (I-6) e dei fondi della ricarica (I-1) |
| molla a torsione piccola (filo 0,3-0,4 mm, gamba 6-8 mm) | 2 | ritorno dei fondi della ricarica dall'alto (I-1) |
| piastra di ferro 104 x 76 x 6 mm | 1 | zavorra nel piede |
| magnete 6 x 1,5 mm + sensore di Hall DRV5032 | 1 + 1 | bicchierino |
| piedini di gomma adesivi | 4 | sotto il piede |

## Pezzi

| Pezzo | Volume cm³ | Massa g | Ingombro mm | Strato mm | Pareti | Riempimento | Supporti cm² | Tocca le pillole | Tempo min | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| 10_ruota_dx | 32.55 | 41.3 | 98.4 × 98.9 × 15.8 | 0.12 | 3 | 25% gyroid | 11.89 | sì | 72 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8); foro centrale stampato a 5,8 mm: ALESARLO a 6,0 H7 (alesatore a mano) prima di montare la ruota (I-2) |
| 10_ruota_sx | 32.55 | 41.3 | 98.4 × 98.9 × 15.8 | 0.12 | 3 | 25% gyroid | 11.89 | sì | 72 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8); foro centrale stampato a 5,8 mm: ALESARLO a 6,0 H7 (alesatore a mano) prima di montare la ruota (I-2) |
| 10_spazzole_dx | 0.54 | 0.7 | 93.1 × 93.6 × 12.6 | 0.12 | 3 | 25% gyroid | 0.0 | sì | 1 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 10_spazzole_sx | 0.54 | 0.7 | 93.1 × 93.6 × 12.6 | 0.12 | 3 | 25% gyroid | 0.0 | sì | 1 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 10_sportellini_dx | 7.6 | 9.6 | 92.3 × 3.4 × 93.4 | 0.12 | 3 | 25% gyroid | 5.4 | sì | 16 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8); cerniere con filo d'acciaio da 0,8 mm (graffetta) (I-6) |
| 10_sportellini_sx | 7.6 | 9.6 | 92.3 × 3.4 × 93.4 | 0.12 | 3 | 25% gyroid | 5.4 | sì | 16 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8); cerniere con filo d'acciaio da 0,8 mm (graffetta) (I-6) |
| 10_tappo_mozzo_dx | 2.21 | 2.8 | 45.2 × 4.4 × 45.2 | 0.12 | 3 | 25% gyroid | 1.92 | sì | 4 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 10_tappo_mozzo_sx | 2.21 | 2.8 | 45.2 × 4.4 × 45.2 | 0.12 | 3 | 25% gyroid | 1.92 | sì | 4 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 12_tasto | 2.23 | 2.8 | 9.1 × 26.0 × 26.0 | 0.2 | 3 | 25% gyroid | 0.89 | no | 4 |  |
| 14_croce_dx | 1.11 | 1.4 | 25.9 × 25.9 × 4.2 | 0.16 | 4 | 100% | 0.0 | no | 2 | ingranaggio: piano, denti nel piano XY; PETG con almeno 45 MPa nel piano (I-14); foro del perno 3,0 mm: spina d'acciaio 3 x 4 a pressione (I-3) |
| 14_croce_sx | 1.11 | 1.4 | 25.9 × 25.9 × 4.2 | 0.16 | 4 | 100% | 0.0 | no | 2 | ingranaggio: piano, denti nel piano XY; PETG con almeno 45 MPa nel piano (I-14); foro del perno 3,0 mm: spina d'acciaio 3 x 4 a pressione (I-3) |
| 15_pignone_dx | 0.38 | 0.5 | 12.0 × 11.9 × 8.4 | 0.16 | 4 | 100% | 0.25 | no | 0 | ingranaggio: piano, denti nel piano XY; PETG con almeno 45 MPa nel piano (I-14); foro a doppio D (albero 5 mm, piatti 3): se e' stretto, passare una lima piatta |
| 15_pignone_sx | 0.38 | 0.5 | 12.0 × 11.9 × 8.4 | 0.16 | 4 | 100% | 0.25 | no | 0 | ingranaggio: piano, denti nel piano XY; PETG con almeno 45 MPa nel piano (I-14); foro a doppio D (albero 5 mm, piatti 3): se e' stretto, passare una lima piatta |
| 16_fondo_dx | 0.13 | 0.2 | 10.2 × 6.3 × 18.4 | 0.12 | 3 | 25% gyroid | 0.04 | sì | 0 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 16_fondo_sx | 0.13 | 0.2 | 10.2 × 6.3 × 18.4 | 0.12 | 3 | 25% gyroid | 0.04 | sì | 0 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 17_staffa_alta | 2.13 | 2.7 | 20.3 × 16.4 × 47.0 | 0.16 | 4 | 100% | 0.84 | no | 4 | ingranaggio: piano, denti nel piano XY; PETG con almeno 45 MPa nel piano (I-14) |
| 18_scivolo_dx | 0.12 | 0.2 | 6.2 × 8.3 × 25.4 | 0.12 | 3 | 25% gyroid | 0.07 | sì | 0 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 18_scivolo_sx | 0.12 | 0.2 | 6.2 × 8.3 × 25.4 | 0.12 | 3 | 25% gyroid | 0.07 | sì | 0 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 19_sportello_dx | 0.16 | 0.2 | 11.3 × 19.7 × 6.3 | 0.12 | 3 | 25% gyroid | 0.11 | sì | 0 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 19_sportello_sx | 0.16 | 0.2 | 11.3 × 19.7 × 6.3 | 0.12 | 3 | 25% gyroid | 0.11 | sì | 0 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 1_guscio | 70.19 | 89.1 | 106.3 × 64.2 × 143.6 | 0.2 | 3 | 25% gyroid | 81.67 | no | 126 | PETG va bene in casa; se la scatoletta puo' stare al sole o in auto, stampare guscio e cappello in ASA o PC (stampante chiusa) (I-10); dadi M2,5 delle cassette: si infilano da fuori nei blocchetti sotto le alette |
| 2_cappello | 40.26 | 51.1 | 105.2 × 64.2 × 68.6 | 0.2 | 3 | 25% gyroid | 37.91 | no | 72 | PETG va bene in casa; se la scatoletta puo' stare al sole o in auto, stampare guscio e cappello in ASA o PC (stampante chiusa) (I-10); piastre degli stepper e tasche dei finecorsa: stampare con supporti solo sul piano (bracci orizzontali) |
| 3_piede | 46.16 | 58.6 | 122.2 × 112.0 × 8.4 | 0.2 | 2 | 15% gyroid | 0.0 | no | 83 | solo regge la piastra d'acciaio: 2 pareti e 15% bastano (I-11) |
| 4_imbuto | 4.65 | 5.9 | 26.4 × 44.9 × 28.4 | 0.12 | 3 | 25% gyroid | 2.0 | sì | 10 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 5_piattino | 1.46 | 1.8 | 6.7 × 29.2 × 31.9 | 0.12 | 3 | 25% gyroid | 1.08 | sì | 3 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 6_staffa_cella | 0.26 | 0.3 | 5.2 × 38.6 × 6.0 | 0.16 | 4 | 100% | 0.11 | no | 0 | ingranaggio: piano, denti nel piano XY; PETG con almeno 45 MPa nel piano (I-14) |
| 7_bicchierino | 15.52 | 19.7 | 72.4 × 34.0 × 27.4 | 0.12 | 3 | 25% gyroid | 8.7 | sì | 34 | ugello in acciaio, superfici lisce, lavare prima dell'uso (I-8) |
| 9_cassetta_dx | 34.32 | 43.6 | 104.0 × 104.0 × 21.1 | 0.2 | 3 | 25% gyroid | 15.88 | no | 61 | foro della torretta 6,0 mm: la spina d'acciaio 6 x 16 entra a pressione (se balla, una goccia di colla epossidica) (I-2); aletta con foro da 2,8 per la vite M2,5 x 8 |
| 9_cassetta_sx | 34.32 | 43.6 | 104.0 × 104.0 × 21.1 | 0.2 | 3 | 25% gyroid | 15.88 | no | 61 | foro della torretta 6,0 mm: la spina d'acciaio 6 x 16 entra a pressione (se balla, una goccia di colla epossidica) (I-2); aletta con foro da 2,8 per la vite M2,5 x 8 |

## Piatti

- **piatto_1.3mf**: 3_piede, 9_cassetta_dx
- **piatto_2.3mf**: 9_cassetta_sx, 10_ruota_sx
- **piatto_3.3mf**: 10_ruota_dx, 10_spazzole_sx, 10_spazzole_dx, 1_guscio
- **piatto_4.3mf**: 2_cappello, 4_imbuto, 6_staffa_cella, 7_bicchierino, 5_piattino, 12_tasto, 14_croce_dx, 14_croce_sx, 19_sportello_sx, 19_sportello_dx, 17_staffa_alta, 15_pignone_sx, 15_pignone_dx, 18_scivolo_dx, 18_scivolo_sx, 16_fondo_sx, 16_fondo_dx, 10_tappo_mozzo_dx, 10_tappo_mozzo_sx, 10_sportellini_dx, 10_sportellini_sx

## Totale

341.1 cm³, circa 433 g di PETG, circa 10.8 h di stampa.

I tempi sono stime dal volume, non uscite di uno slicer: vanno verificati nello slicer con la propria stampante. Filamento ed elettricità non sono conteggiati nel costo del progetto.
