# Firmware v1.0: le correzioni del rapporto R&D

Due librerie nuove, senza Arduino, che si provano sul computer come quelle della v0.9:

```
cd firmware/test
g++ -O2 -std=c++17 -I../v10 test_limite_umidita.cpp -o t4 && ./t4
```

## `limite_coppia.h` (I-3): il motorino non rompe più i denti

Usa la stessa resistenza da 0,5 ohm della v0.9: niente hardware in più.

- Sopra 176 mA per 10 ms (circa 15 N·mm), oppure sopra 253 mA anche per un attimo (22 N·mm), il motore si ferma.
- Poi torna indietro un attimo e riprova. Dopo 3 prove dà BLOCCO e l'app avvisa.
- Per girare la ruota basta circa 1 N·mm, anche con le pillole più "appiccicose".

| Prova (simulata) | Risultato |
|---|---|
| 2000 giri normali, con pillole che si incastrano per un attimo | 0 blocchi falsi; un colpo forte di 10 ms fa solo una scossa in più |
| Ruota bloccata (corrente fino a quella di stallo in 60 ms) | stop dopo 35 ms, coppia massima 20 N·mm, dente a 10 MPa: sicurezza ×3 sul PETG più debole (31,9 MPa) |

Per questo i pignoni restano larghi 2 mm. Gli ingranaggi da 4 mm della proposta I-3 avrebbero allargato la scatola di 4 mm. Se la prova T8 mostra che il limite non basta, sono il passo successivo.

I valori del motorino (0,35 kg·cm e 350 mA a motore fermo, 40 mA a vuoto) vengono dal venditore o sono stime: vanno misurati (prova T8).

## `umidita.h` (I-9, I-15): quando cambiare il gel

- Legge il sensore AHT20 (I2C, indirizzo 0x38) e controlla il CRC.
- Il sensore è attaccato sotto il tetto: misura l'aria intorno alle cassette, non dentro uno scomparto. La prova T7 dice quanto le due misure differiscono.
- Avvisi:
  - *cambia presto* sopra il 30% di umidità, o se al ritmo attuale si arriva al 40% entro un giorno;
  - *cambia ora* sopra il 40%, o comunque dopo **7 giorni**.
- I 7 giorni vengono dal rapporto: il gel tiene meno acqua di quanto stimato all'inizio (11–22% del suo peso, non 25%). Si allungheranno solo se la prova T7 lo permette.

| Prova (simulata) | Risultato |
|---|---|
| Lettura AHT20 costruita a mano (55,0% e 23,0 °C) | letta giusta; un byte rovinato viene scartato |
| Aria che diventa umida di 3 punti al giorno | "cambia presto" il 4° giorno, "cambia ora" il 7° |
| Aria sempre asciutta | "cambia ora" il 7° giorno (promemoria) |

## Collegamenti nuovi

- AHT20: VCC 3,3 V, GND, SDA e SCL sullo stesso bus I2C del display (4 fili, nel canale dei cavi).
- Nessun'altra modifica alla scheda.
