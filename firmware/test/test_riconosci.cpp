// Prova del riconoscimento delle pillole su 20 000 dosi simulate.
// Compila e lancia:  g++ -O2 -std=c++17 -I../v09 test_riconosci.cpp -o test && ./test
//
// Simulazione realistica:
//  - ogni compressa vera pesa il suo peso medio +/- 3% (la Farmacopea ammette +/- 5-7,5%)
//  - la bilancia (cella da 100 g + HX711, media di 10 letture) ha un rumore di 3 mg
//  - prima la scatoletta impara: 20 pillole per tipo durante la ricarica + 50 letture a vuoto
//  - poi 20 000 dosi: 90% giuste, 5% con una pillola in meno, 3% con una in piu', 2% con una scambiata
#include <cstdio>
#include <random>
#include <vector>
#include "riconosci_pillole.h"
using namespace blistra;

struct Farmaco { const char* nome; float mg; };

int main() {
  std::mt19937 rng(42);
  std::normal_distribution<float> N01(0, 1);
  const Farmaco F[] = {{"compressa grande (metformina)", 560}, {"media (ramipril)", 180}, {"media (pantoprazolo)", 150},
                       {"piccola (bisoprololo)", 90}, {"minuscola", 40}};
  const int T = 5; const float VAR = 0.03f, RUMORE = 3.0f;
  Riconoscitore R;
  for (int i = 0; i < T; i++) R.aggiungi_tipo(F[i].mg * (1 + 0.02f * N01(rng)));   // il peso scritto nell'app e' un po' sbagliato
  for (int i = 0; i < T; i++) for (int k = 0; k < 20; k++) R.impara_pillola(i, F[i].mg * (1 + VAR * N01(rng)) + RUMORE * N01(rng));
  for (int k = 0; k < 50; k++) R.impara_vuoto(RUMORE * N01(rng));

  printf("Tipi che la bilancia sa distinguere tra loro:\n");
  for (int a = 0; a < T; a++) for (int b = a + 1; b < T; b++)
    if (!R.distinguibili(a, b)) printf("  ATTENZIONE: %s e %s pesano troppo simile per distinguerle solo dal peso\n", F[a].nome, F[b].nome);

  int giuste = 0, giuste_ok = 0, errori = 0, errori_presi = 0, errori_passati = 0, incerti = 0;
  int presi_tipo[3] = {0}, tot_tipo[3] = {0};
  std::uniform_real_distribution<float> U(0, 1);
  for (int d = 0; d < 20000; d++) {
    int8_t att[MAX_TIPI] = {0}, vero[MAX_TIPI];
    int ntipi = 1 + rng() % 3;
    for (int k = 0; k < ntipi; k++) att[rng() % T] += 1 + (U(rng) < 0.2f);
    for (int i = 0; i < MAX_TIPI; i++) vero[i] = att[i];
    float u = U(rng); int errore = -1;
    std::vector<int> presenti; for (int i = 0; i < T; i++) if (att[i]) presenti.push_back(i);
    if (u < 0.05f) { vero[presenti[rng() % presenti.size()]]--; errore = 0; }
    else if (u < 0.08f) { vero[presenti[rng() % presenti.size()]]++; errore = 1; }
    else if (u < 0.10f) { int a = presenti[rng() % presenti.size()], b; do b = rng() % T; while (b == a); vero[a]--; vero[b]++; errore = 2; }
    float W = 0;
    for (int i = 0; i < T; i++) for (int k = 0; k < vero[i]; k++) W += F[i].mg * (1 + VAR * N01(rng));
    W += RUMORE * N01(rng);
    Risultato r = R.controlla(att, W);
    if (r.esito == Esito::INCERTO) incerti++;
    if (errore < 0) { giuste++; if (r.esito == Esito::OK) giuste_ok++; }
    else {
      errori++; tot_tipo[errore]++;
      if (r.esito == Esito::OK) errori_passati++; else { errori_presi++; presi_tipo[errore]++; }
    }
  }
  printf("\nDosi giuste:   %d, date senza problemi: %.2f%% (le altre: l'app chiede di controllare)\n", giuste, 100.0 * giuste_ok / giuste);
  printf("Dosi sbagliate: %d, fermate: %.2f%%  (pillola in meno %.1f%%, in piu' %.1f%%, scambiata %.1f%%)\n", errori, 100.0 * errori_presi / errori,
         100.0 * presi_tipo[0] / tot_tipo[0], 100.0 * presi_tipo[1] / tot_tipo[1], 100.0 * presi_tipo[2] / tot_tipo[2]);
  printf("Dosi sbagliate che sarebbero passate: %d su 20000 (%.3f%%)\n", errori_passati, 100.0 * errori_passati / 20000);
  printf("Casi incerti (si chiede all'utente): %d\n", incerti);
  return errori_passati * 100 > errori * 2 ? 1 : 0;   // il test fallisce se passa piu' del 2% delle dosi sbagliate (solo peso, senza pesata in entrata)
}
