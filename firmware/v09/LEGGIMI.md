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
