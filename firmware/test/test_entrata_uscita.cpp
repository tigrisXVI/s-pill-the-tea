// Prova del controllo ENTRATA -> USCITA su 20 000 scomparti simulati.
// g++ -O2 -std=c++17 -I../v09 test_entrata_uscita.cpp -o test2 && ./test2
// Ricarica dall'alto: le pillole di ogni scomparto passano sul piattino pesato in entrata (W_in) e poi,
// al momento della dose, su quello in uscita (W_out). Errori simulati in uscita:
//  2% una pillola resta incastrata nello scomparto, 1% ne cade una in piu' dallo scomparto vicino,
//  0,5% una briciola (5-20 mg) si stacca da una compressa.
#include <cstdio>
#include <random>
#include "riconosci_pillole.h"
using namespace blistra;
int main() {
  std::mt19937 rng(7); std::normal_distribution<float> N01(0, 1); std::uniform_real_distribution<float> U(0, 1);
  const float MG[] = {560, 180, 150, 90, 40}; const int T = 5; const float RUMORE = 3.0f;
  Riconoscitore R; for (int i = 0; i < T; i++) R.aggiungi_tipo(MG[i]);
  for (int i = 0; i < T; i++) for (int k = 0; k < 20; k++) R.impara_pillola(i, MG[i] * (1 + 0.03f * N01(rng)));
  for (int k = 0; k < 50; k++) R.impara_vuoto(RUMORE * N01(rng));
  int giusti = 0, giusti_ok = 0, err = 0, err_presi = 0, tipo_giusto = 0, minuscola = 0, minuscola_presa = 0, briciole = 0, briciole_viste = 0;
  for (int d = 0; d < 20000; d++) {
    float pesi[8]; int tipi[8], n = 1 + rng() % 4;
    float Win = 0, Wout = 0;
    for (int k = 0; k < n; k++) { tipi[k] = rng() % T; pesi[k] = MG[tipi[k]] * (1 + 0.03f * N01(rng)); Win += pesi[k]; }
    Wout = Win; float u = U(rng); int errore = 0, quale = -1;
    if (u < 0.02f) { int k = rng() % n; Wout -= pesi[k]; errore = 1; quale = tipi[k]; }
    else if (u < 0.03f) { int t = rng() % T; Wout += MG[t] * (1 + 0.03f * N01(rng)); errore = 1; quale = t; }
    else if (u < 0.035f) { Wout -= 5 + 15 * U(rng); errore = 2; }
    Win += RUMORE * N01(rng); Wout += RUMORE * N01(rng);
    auto r = R.controlla_uscita(Win, Wout);
    if (!errore) { giusti++; giusti_ok += r.ok; }
    else if (errore == 2) { briciole++; briciole_viste += !r.ok; }   // una briciola non cambia la dose: si conta a parte
    else { err++; err_presi += !r.ok; if (quale >= 0 && r.tipo_probabile == quale) tipo_giusto++;
           if (quale == 4) { minuscola++; minuscola_presa += !r.ok; } }
  }
  printf("Scomparti giusti: %d, dati senza allarme: %.2f%%\n", giusti, 100.0 * giusti_ok / giusti);
  printf("Scomparti con un errore: %d, fermati: %.2f%%\n", err, 100.0 * err_presi / err);
  printf("  pillola minuscola (40 mg) mancante o in piu': fermata %d su %d\n", minuscola_presa, minuscola);
  printf("  quando manca/avanza una pillola, l'app indovina quale: %.1f%%\n", 100.0 * tipo_giusto / err);
  printf("Briciole da 5-20 mg (non cambiano la dose): segnalate %d su %d\n", briciole_viste, briciole);
  return err_presi * 1000 < err * 995;
}
