# Scatoletta Blistra v1.2

La v1.0 adattata ai pezzi che ho davvero. Modello in `cad/scatoletta_v12.py` (sottoclasse della v1.0), controlli in `cad/controlli_v12.py`: tutti verdi (interferenze, croce di Malta, stepper e finecorsa, ricarica, cassette che si sfilano, cavi, stabilità).

**Da stampare:** `blistra_v12_stampa.zip` (pezzi già orientati per la stampa). Parametri di stampa come nella v1.0 (`v10/PARAMETRI_STAMPA.md`).

Corpo 105 × 64 × 218 mm, piede 122 × 112 mm, peso circa 770 g. Si ribalta solo oltre 41° di lato, 46° in avanti e 41° indietro.

## Cosa è cambiato

- **Motori:** 2 stepper 28BYJ-48 con 2 driver ULN2003 al posto dei motorini N20 e del DRV8833. Stanno dietro in alto, uno per lato, avvitati con 2 viti M3 a una piastra del cappello. Le due croci di Malta sono a 126°, il pignone (10 denti, mozzo da 9 mm, foro a doppio D) è a 17,1 mm dalla croce.
- **Zero delle ruote:** un pulsantino 6 × 6 × 7 per lato fa da finecorsa. Lo preme il perno d'acciaio della croce quando l'ingranaggio è a 52–68° dal riposo, cioè nel tratto in cui la ruota è bloccata. Il firmware gira fino allo scatto, poi torna indietro di 60° (circa 820 passi interi): quello è il riposo. Il pulsantino segna il riposo della croce, non lo scomparto. Quale scomparto è in basso lo conta il firmware, e la cassetta si infila con lo scomparto chiuso in basso.
- **Cassette:** fissate con una vite M2,5 al posto dei fermi col servo. L'aletta sta sulla flangia, il dado si infila da fuori nel blocchetto del guscio e il cacciavite passa dalla tacca nel fianco.
- **Ricarica dall'alto:** niente seconda cella. La canaletta è fissa, incollata su due appoggi del guscio. Tutto è 10 mm più su e le pareti della canaletta scendono di 10 mm.
- **Elettronica:** servo SG90 (su due colonnine), OLED 0,96" I2C, cicalino da 12 mm dietro la griglia davanti. Nella camera dietro ci sono i 2 ULN2003 in verticale, a sinistra, uno sopra l'altro, e l'HX711 e l'ESP32-S3 a destra; la presa USB-C è all'altezza dell'ESP32. Le schede scorrono in costole con la scanalatura. Il nastro dei cavi parte da z 81.
- **Tolti:** orologio RTC, altoparlante e amplificatore, sensore AHT20, seconda cella, servo dei fermi, magneti e sensori di Hall delle ruote.
- **Guscio:** più largo (64 mm invece di 53) e 10 mm più alto. Il piede è 3 mm più lungo dietro e 2 mm più largo.

## Ferramenta da comprare

| Cosa | Quanti | Dove va |
|---|---|---|
| Vite M3 × 6 (che fa il filetto nel PETG) | 4 | alette degli stepper. **Non più lunghe di 6 mm:** una da 8 tocca il perno della croce |
| Vite M2,5 × 8 + dado M2,5 | 2 + 2 | fissano le cassette |
| Pulsantino 6 × 6 mm, alto 7 | 2 | finecorsa delle ruote |
| Spina d'acciaio 6 × 16 mm | 2 | asse delle ruote (come v1.0) |
| Perno d'acciaio 3 × 4 mm | 2 | perno delle croci (come v1.0) |
| Vite M2 (va bene quella di un hard disk) | 2 | asse delle croci (come v1.0) |
| Filo d'acciaio da 0,8 mm | circa 30 cm | cerniere di sportellini e fondi (come v1.0) |
| Mollette di torsione piccole | 2 | fondi della ricarica (come v1.0) |
| Piastra di ferro 104 × 76 × 6 mm | 1 | zavorra nel piede (come v1.0) |
| Magnete 6 × 1,5 mm + sensore di Hall DRV5032 | 1 + 1 | bicchierino (come v1.0) |
| Piedini di gomma adesivi | 4 | sotto il piede |

Non servono più: magneti 3 × 1 e sensori di Hall delle ruote, viti dei fermi.

## Montaggio: le cose nuove

1. Stepper: infila il pignone sull'albero. Appoggia lo stepper alla piastra 4 mm più avanti e fallo scorrere indietro nell'asola finché il pignone ingrana. Poi avvita le due M3 × 6.
2. Finecorsa: spingi il pulsantino nella sua tasca finché il perno della croce lo fa scattare (c'è 0,27 mm di corsa). Poi fissalo con una goccia di colla a caldo.
3. Cassette: si infilano a guscio e cappello montati, con lo scomparto chiuso in basso. Poi va avvitata la vite M2,5 dalla tacca nel fianco.

## Da fare

- Il firmware è ancora quello della v1.0. Va cambiato per gli stepper (8 pin per i due ULN2003), il finecorsa, il cicalino e l'ora presa dal Wi-Fi (non c'è più l'RTC).
