# Firmware v0.9: la bilancia che riconosce le pillole

`riconosci_pillole.h` è una libreria senza Arduino. Si prova sul computer:

```
cd firmware/test
g++ -O2 -std=c++17 -I../v09 test_riconosci.cpp -o t1 && ./t1
g++ -O2 -std=c++17 -I../v09 test_entrata_uscita.cpp -o t2 && ./t2
```

## Come funziona

1. **Impara.** Ogni pillola pesata durante la ricarica aggiorna media e varianza del suo tipo (algoritmo di Welford). Le letture a vuoto insegnano quanto "balla" la bilancia.
2. **Solo dal peso** (`controlla`). Prova tutte le combinazioni vicine alla dose attesa (una pillola in meno, in più, scambiata). Sceglie la più probabile con una verosimiglianza gaussiana e dà la dose solo se la combinazione giusta vince con margine (×20).
3. **Entrata → uscita** (`controlla_uscita`). Con la ricarica dall'alto ogni scomparto viene pesato quando entra e quando esce. Sono le stesse pillole, quindi la variabilità delle compresse sparisce e resta solo il rumore della bilancia.

## Risultati su 20 000 dosi simulate

Le compresse sono simulate con ±3% di peso e la bilancia con 3 mg di rumore.

| Controllo | Dosi giuste date | Dosi sbagliate fermate | Sbagliate che passano |
|---|---|---|---|
| Solo peso | 96,1% (le altre: "controlla tu") | 98,6% | 28 su 20 000 (0,14%) |
| Entrata → uscita | 100% | 100% (anche la pillola da 40 mg) | 0 |

Quando manca o avanza una pillola, l'app indovina quale nell'88% dei casi.

Il controllo "solo peso" ha un limite: se due farmaci pesano quasi uguale (150 e 180 mg), non può distinguerli. La libreria lo segnala già quando si imposta la terapia (`distinguibili`). È anche il motivo per cui la pesata in entrata conta così tanto.

# Il motore che si ascolta (`ascolta_motore.h`)

**Hardware.** Si aggiunge pochissimo:
- una resistenza da 0,5 ohm tra il GND del modulo DRV8833 e la massa (gira un motorino alla volta);
- un filtro di 1 kohm e 22 nF;
- un ingresso analogico dell'ESP32-S3, letto a 40 kHz in modalità continua.

Dalla corrente il firmware ricava tre cose:
1. **Conta le increspature.** A ogni cambio di contatto delle spazzole la corrente fa un piccolo dente. Contandoli si sa di quanto ha girato il motorino, quindi a che punto del giro è la croce di Malta, senza encoder.
2. **Impara la firma del giro**: com'è di solito la corrente in ognuno dei 36 tratti da 10 gradi.
3. **Fa la diagnosi:**
   - *picco*: una pillola si sta incastrando, quindi il motore torna indietro e riprova;
   - *attrito in aumento*: è ora di pulire la ruota;
   - *blocco*: il motore si ferma.

Prova: `g++ -O2 -std=c++17 -I../v09 test_ascolta.cpp -o t3 && ./t3` (600 giri simulati).

| Cosa | Risultato |
|---|---|
| Errore del conteggio dei denti | 1,1% per giro della croce (circa 4 gradi; la croce resta ferma per 204 gradi del giro, quindi va bene) |
| Pillole incastrate per un attimo | riconosciute 13 su 13 |
| Falsi allarmi nei giri normali | 0 |
| Polvere che fa crescere l'attrito | avviso "pulisci la ruota" 226 giri prima del blocco, circa 56 giorni prima con 4 dosi al giorno |
