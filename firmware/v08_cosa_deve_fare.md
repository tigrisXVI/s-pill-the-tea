# Firmware della v0.8: cosa deve fare

Il firmware in `scatoletta_blistra/` è ancora quello della v0.5 (un carosello). Queste sono le regole per quello della v0.8 (due ruote), da scrivere quando arrivano i pezzi.

## 1. Sapere sempre dove sono le ruote

Ogni ruota ha un magnete da 3 × 1 mm nella corona, sotto lo scomparto chiuso. Nella parete centrale c'è un sensore di Hall (DRV5032) per ruota, a 1,7 mm dal magnete.

- **All'accensione:** ogni ruota gira piano finché il suo sensore vede il magnete. Quella è la posizione 0 (scomparto chiuso sopra l'uscita).
- **A ogni giro completo:** quando la ruota ripassa sul magnete, il firmware controlla che il conto dei passi sia giusto. Se non lo è, la ruota ha saltato dei denti: la scatola si ferma, non dà la dose e avvisa l'app ("ruota da controllare").
- **Prima di ogni dose:** se dall'ultimo azzeramento sono passati più di 7 scomparti, prima di dare la dose la ruota si riazzera tornando indietro sul magnete.
- **Se il sensore non vede mai il magnete** (cassetta sfilata o motorino rotto) dopo un giro e mezzo: errore, nessuna dose, avviso.

## 2. Corrente che va via

- **Orologio:** modulo DS3231 con pila a bottone nella camera dietro, collegato all'ESP32 in I2C. L'ora si prende dall'orologio, poi si corregge con internet (NTP) quando c'è il Wi-Fi.
- **Memoria:** dopo ogni passo di una ruota, e quando una dose cambia stato, il firmware scrive nella memoria flash dell'ESP32 (Preferences): numero dell'ultima dose data, esito, posizione di ogni ruota.
- **Alla riaccensione:** legge la memoria, azzera le ruote sul magnete e torna allo scomparto giusto. Se nel frattempo è passata l'ora di una dose, non la dà da sola: la segna come "saltata per mancanza di corrente" e avvisa l'app. Una dose vecchia non deve mai uscire da sola.

## 3. Senza internet

- Gli orari e i pesi delle pillole sono salvati anche sulla scatola, quindi le dosi escono comunque all'ora giusta.
- Gli esiti si mettono in coda e partono quando torna il Wi-Fi.
- La password del Wi-Fi si imposta dall'app, mai scritta nel codice (`config.h` non va pubblicato).

## 4. Fermo delle cassette

Il fermo è meccanico: un dente a un quarto di giro che si gira con una moneta. Il firmware se ne accorge lo stesso, perché quando una cassetta è sfilata il sensore di quella ruota non vede più il magnete. A quel punto la scatola entra in "ricarica" e non dà dosi. Quando la cassetta torna dentro, la ruota si azzera e i pesi si ricontrollano.
