# Progettazione evolutiva dello scomparto e dell'uscita

`sim_scomparto.py` usa una simulazione fisica (pybullet). Modella:
- l'anello con l'uscita;
- la ruota con divisori e scivoli, mossa con il profilo vero della croce di Malta;
- pillole vere: compresse grandi, medie, piccole, minuscole (3 mm) e capsule.

Le prove sono "difficili": da 2 a 8 pillole per dose, attrito tra 0,3 e 0,7 (compresse lisce o appiccicose per l'umidità) e 0,8 s per uscire.

`evolvi.py` fa evolvere 4 geni:
- la larghezza dell'uscita;
- l'angolo e la lunghezza degli scivoli;
- la durata dello scatto della croce.

La popolazione è di 6 genitori e 8 figli per 14 generazioni. In ogni generazione tutti affrontano le stesse 12 prove. La fitness è: riuscite − 2 × perdite − volume perso dagli scivoli.

`verifica.py` ripete le cose con più prove (40 a testa, stesse prove per tutti).

## Risultati

| Larghezza dell'uscita | Scomparti svuotati del tutto | Pillole perse dallo scomparto dopo |
|---|---|---|
| 10 mm | 28% | 0% |
| 12 mm | 98% | 0% |
| 14 mm (disegno attuale) | 98% | 0% |
| 16 mm | 98% | 0% |
| 17,2 mm (migliore dell'evoluzione) | 98% | 0% |
| 19 mm | 98% | 0% |

**Cosa ho imparato:**
- Sotto i 12 mm le pillole grandi si appoggiano sui bordi e non escono. Dai 12 mm in su si è su un altopiano.
- L'uscita di oggi (14 mm) è già sull'altopiano, con 2 mm di margine.
- Allargarla non migliora niente e toglie margine allo scomparto chiuso che copre l'uscita. Quindi la tengo così.
- L'evoluzione ha eliminato da sola gli scivoli (lunghezza → 0): non aiutano e rubano spazio.
- Una prova su 40 fallisce con tutte le larghezze: è un caso difficile da guardare da vicino (probabilmente una capsula in piedi in un angolo). Il firmware fa già la "scossa" all'indietro e riprova, ma nella simulazione la scossa non c'è.
