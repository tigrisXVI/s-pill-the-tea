# Ricerca con il Message Batches API (punto 9 del brief R&D)

Dieci compiti di ricerca su Blistra v0.9, pronti da inviare all'API di Anthropic in modalità batch (costo ridotto del 50%, risposta entro 24 h).

| custom_id | Compito |
|---|---|
| b01-tablet-database | database dimensionale di compresse e capsule (spessore incluso) |
| b02-polymer-properties | proprietà dei polimeri FDM, almeno due produttori per materiale |
| b03-friction-contact | attrito compressa–polimero e polimero–polimero, rottura, umidità |
| b04-thermal-environment | creep, umidità, UV, temperature, assorbimento delle compresse, gel di silice |
| b05-fdm-accuracy | precisione della stampa FDM e giochi consigliati |
| b06-failure-modes | modi di guasto di Ginevra, ingranaggi, incastri, cella di carico |
| b07-cad-optimisation | modifiche geometriche proposte, con vantaggi e svantaggi |
| b08-material-comparison | matrice di scelta dei materiali e alternative alla stampa |
| b09-standards-regulation | norme e regolamenti UE e USA |
| b10-integrated-conclusions | confronto incrociato e conclusioni (secondo batch, usa i risultati 1–9) |

Ogni richiesta allega i parametri della v0.9 (`../rd_cad.json`) e le compresse già raccolte (`../pills.json`), usa la ricerca web (al massimo 25 ricerche) e deve restituire un JSON con valore, unità, classe di evidenza (MEAS/DS/LIT/CALC/HYP) e URL della fonte per ogni dato.

## Come eseguirlo

Serve un account sulla Claude Console con credito e una chiave API. La chiave la inserisci tu nel terminale, non va mai scritta nei file né pubblicata.

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...        # la tua chiave
python3 prepara_batch.py            # rigenera richieste_fase1.jsonl dai dati attuali
python3 esegui_batch.py invia1      # invia i compiti 1-9; l'id del batch finisce in stato.json
python3 esegui_batch.py stato       # ripeti finché lo stato è "ended"
python3 esegui_batch.py raccogli    # salva i risultati in risultati/
python3 esegui_batch.py invia2      # invia il compito 10 con i risultati 1-9
python3 esegui_batch.py stato && python3 esegui_batch.py raccogli
python3 esegui_batch.py unisci      # risultati/CONSOLIDATO.md e risultati/contraddizioni.json
```

`unisci` mette insieme tutti i dati in una tabella e segnala come possibili contraddizioni i valori sullo stesso tema e con la stessa unità che differiscono di oltre il 20%. Vanno poi controllati a mano.

## Costo

Il costo dipende soprattutto dalle pagine lette con la ricerca web. Va controllato sul listino della Console prima dell'invio. Si può fare una prova con un solo compito togliendo le altre righe da `richieste_fase1.jsonl`.

## Limiti

I risultati sono ricerca bibliografica fatta da un modello, non validazione sperimentale. Ogni valore deve essere riscontrato sulla fonte citata. Le prove T1–T12 del rapporto R&D, con compresse finte e campioni di materiale, restano necessarie.
