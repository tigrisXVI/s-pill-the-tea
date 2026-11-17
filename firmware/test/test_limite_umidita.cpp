// Prove al computer del limite di coppia (I-3) e dello stato del gel (I-9, I-15).
#include <cstdio>
#include <random>
#include "limite_coppia.h"
#include "umidita.h"
using namespace blistra;

int main() {
  std::mt19937 rng(7); std::normal_distribution<float> rumore(0.f, 4.f);
  int errori = 0;
  // 1) giri normali con pillole che si incastrano per un attimo: il limite non deve scattare
  LimiteCoppia L; int falsi = 0, scosse_inutili = 0;
  for (int g = 0; g < 2000; g++) {
    L.parti(); bool scattato = false;
    for (int k = 0; k < 400; k++) {                       // 2 s a 200 campioni/s
      float t = k * 5.f, i = 48.f + rumore(rng);
      if (t < 20) i = 300.f;                                // spunto all'avvio
      if (g % 7 == 0 && t > 800 && t < 815) i = 160.f;      // una pillola che si incastra per 15 ms (sotto la soglia)
      if (g % 11 == 0 && t > 900 && t < 910) i = 250.f;     // un colpo forte ma brevissimo (10 ms)
      Azione a = L.campione(i, 5.f);
      if (a == Azione::BLOCCO) scattato = true;
      if (a == Azione::FERMA_E_SCOSSA) { scosse_inutili++; L.parti(); }   // indietro e riprova: costa mezzo secondo
    }
    if (scattato) falsi++; L.giro_riuscito();
  }
  printf("soglia %.0f mA (coppia %.0f N*mm)\n", L.soglia_ma(), L.coppia_max_nmm);
  printf("giri normali con piccoli incastri: %d blocchi falsi su 2000, %d scosse in piu' (il colpo forte da 10 ms)\n", falsi, scosse_inutili); if (falsi) errori++;
  // 2) ruota bloccata: la corrente sale a quella di stallo in 60 ms
  L = LimiteCoppia(); L.parti(); float t_stop = -1, coppia_max = 0; int scosse = 0; Azione a = Azione::CONTINUA;
  for (int prova = 0; prova < 5 && a != Azione::BLOCCO; prova++) {
    L.parti();
    for (int k = 0; k < 200; k++) {
      float t = k * 1.f, i = t < 100 ? 48.f : fminf(350.f, 48.f + (t - 100) * 302.f / 60.f);
      coppia_max = fmaxf(coppia_max, L.m.coppia(i));
      a = L.campione(i, 1.f);
      if (a != Azione::CONTINUA) { if (t_stop < 0) t_stop = t - 100; if (a == Azione::FERMA_E_SCOSSA) scosse++; break; }
    }
  }
  float sigma = (coppia_max / 5.f) / (2.f * 1.f * 0.201f);
  printf("ruota bloccata: il motore si ferma %.0f ms dopo l'inizio del blocco; coppia massima %.1f N*mm, dente a %.1f MPa; %d scosse poi %s\n",
         t_stop, coppia_max, sigma, scosse, a == Azione::BLOCCO ? "BLOCCO" : "??");
  if (a != Azione::BLOCCO || sigma > 31.9f / 3.f || scosse != 2) errori++;
  // 3) AHT20: un esempio costruito a mano (55,0% e 23,0 gradi)
  uint32_t h = (uint32_t)(0.55f * 1048576.f), t = (uint32_t)((23.f + 50.f) / 200.f * 1048576.f);
  uint8_t b[7] = {0x1C, (uint8_t)(h >> 12), (uint8_t)(h >> 4), (uint8_t)(((h & 0xF) << 4) | (t >> 16)), (uint8_t)(t >> 8), (uint8_t)t, 0};
  b[6] = crc8_aht(b, 6);
  Lettura l = decodifica_aht20(b);
  printf("AHT20: %.1f%% %.1f gradi (attesi 55,0 e 23,0)\n", l.umidita, l.temperatura);
  if (!l.valida || fabsf(l.umidita - 55.f) > 0.1f || fabsf(l.temperatura - 23.f) > 0.1f) errori++;
  b[2] ^= 1; if (decodifica_aht20(b).valida) { printf("CRC: dato rovinato non riconosciuto\n"); errori++; }
  // 4) gel: aria che diventa umida di 3 punti al giorno partendo dal 18%
  StatoGel G; int giorno_presto = -1, giorno_ora = -1;
  for (int ora = 0; ora < 24 * 10; ora++) {
    float rh = 18.f + 3.f * ora / 24.f + rumore(rng) * 0.3f;
    Gel s = G.aggiorna(rh, (float)ora);
    if (s == Gel::CAMBIA_PRESTO && giorno_presto < 0) giorno_presto = ora / 24;
    if (s == Gel::CAMBIA_ORA && giorno_ora < 0) giorno_ora = ora / 24;
  }
  printf("gel che si satura: 'cambia presto' il giorno %d, 'cambia ora' il giorno %d\n", giorno_presto, giorno_ora);
  if (giorno_presto < 0 || giorno_ora < 0 || giorno_presto > giorno_ora) errori++;
  StatoGel G2; Gel s2 = Gel::BUONO; int g2 = -1;   // aria sempre asciutta: solo il promemoria dei 7 giorni
  for (int ora = 0; ora < 24 * 8; ora++) { s2 = G2.aggiorna(15.f, (float)ora); if (s2 == Gel::CAMBIA_ORA && g2 < 0) g2 = ora / 24; }
  printf("aria asciutta: 'cambia ora' il giorno %d (promemoria dei 7 giorni)\n", g2);
  if (g2 != 7) errori++;
  printf(errori ? "ERRORI: %d\n" : "tutto ok\n", errori);
  return errori;
}
