// Prova del "motore che si ascolta" su 600 giri simulati della croce di Malta.
// g++ -O2 -std=c++17 -I../v09 test_ascolta.cpp -o t3 && ./t3
//
// Modello del motorino N20 (60 giri/min, riduttore 1:300, 6 denti di corrente per giro del rotore):
//  - un giro della croce = 2,4 giri dell'uscita = 720 giri del rotore = 4320 denti
//  - corrente: 45 mA a vuoto, +30 mA quando il perno trascina la ruota (attrito delle lamelle), +inerzia
//  - i denti valgono circa l'8% della corrente; rumore dell'ADC 3 mA a 40 kHz; la velocita' cala col carico
// Cosa succede nei 600 giri:
//  - giri 0-299 normali; dal 300 la polvere fa crescere l'attrito piano piano (fino a +150% al giro 600,
//    dove il motorino si fermerebbe)
//  - nel 2% dei giri una pillola si incastra per un attimo (picco di 120 mA per 15 gradi)
#include <cstdio>
#include <cmath>
#include <random>
#include "ascolta_motore.h"
using namespace blistra;

int main() {
  std::mt19937 rng(3); std::normal_distribution<float> N(0, 1); std::uniform_real_distribution<float> U(0, 1);
  const float FS = 40000, DENTI_GIRO = 4320, PI = 3.14159265f;
  ContaIncrespature conta(FS); Ascolta asc;
  int picchi_veri = 0, picchi_presi = 0, falsi_picchi = 0, primo_avviso = -1, giro_blocco = 600;
  double err_conteggio = 0; int giri_misurati = 0;
  float fase_dente = 0;
  for (int g = 0; g < 600; g++) {
    float attrito = g < 300 ? 1.f : 1.f + 1.5f * (g - 300) / 300.f;
    bool incastro = U(rng) < 0.02f && g > 25; float phi_inc = 110 + 130 * U(rng);
    if (incastro) picchi_veri++;
    float somma[SETTORI] = {0}; int n[SETTORI] = {0};
    uint32_t c0 = conta.conteggio; float phi = 0; int denti_veri = 0;
    while (phi < 360.f) {
      bool presa = phi > 102 && phi < 258;
      float acc = presa ? cosf((phi - 180) / 78.f * PI / 2) : 0;           // la ruota accelera e poi frena
      float carico = 45 + (presa ? 30 * attrito + 12 * acc : 0);
      if (incastro && fabsf(phi - phi_inc) < 7.5f) carico += 120;
      float vel = 1.f - 0.002f * (carico - 45);                            // piu' carico, piu' lento
      float ddenti = vel * 1800.f / FS;                                     // 1800 denti al secondo a vuoto
      fase_dente += ddenti; while (fase_dente >= 1) { fase_dente -= 1; denti_veri++; }
      float i = carico * (1 + 0.08f * sinf(2 * PI * fase_dente)) + 3 * N(rng);
      conta.campione(i);
      phi += ddenti * 360.f / DENTI_GIRO;
      // la fase per la firma viene SOLO dal conteggio dei denti (come nella scatola vera)
      float phi_stima = fmodf((conta.conteggio - c0) * 360.f / DENTI_GIRO, 360.f);
      int k = (int)(phi_stima / 10) % SETTORI; somma[k] += conta.lenta(); n[k]++;
    }
    if (g >= 5) { err_conteggio += fabs((double)(conta.conteggio - c0) - denti_veri) / denti_veri; giri_misurati++; }
    float giro[SETTORI]; for (int k = 0; k < SETTORI; k++) giro[k] = n[k] ? somma[k] / n[k] : 0;
    Esame e = asc.esamina(giro, 0);
    if (e.d == Diagnosi::PICCO) { if (incastro) picchi_presi++; else falsi_picchi++; }
    if (e.d == Diagnosi::ATTRITO_IN_AUMENTO && primo_avviso < 0) primo_avviso = g;
    if (e.d == Diagnosi::ATTRITO_IN_AUMENTO && g < 300) falsi_picchi++;
  }
  printf("Conteggio dei denti: errore medio %.2f%% per giro (la croce si ferma comunque sul disco di blocco)\n", 100 * err_conteggio / giri_misurati);
  printf("Pillole incastrate per un attimo: riconosciute %d su %d (il motore torna indietro e riprova)\n", picchi_presi, picchi_veri);
  printf("Falsi allarmi nei giri normali: %d\n", falsi_picchi);
  printf("L'attrito comincia a crescere al giro 300; avviso \"pulisci la ruota\" al giro %d, il blocco sarebbe al giro %d:\n", primo_avviso, giro_blocco);
  printf("  %d giri prima, cioe' circa %d giorni prima con 4 dosi al giorno per ruota\n", giro_blocco - primo_avviso, (giro_blocco - primo_avviso) / 4);
  return (picchi_presi * 10 >= picchi_veri * 9 && falsi_picchi == 0 && primo_avviso > 300 && primo_avviso < 420) ? 0 : 1;
}
