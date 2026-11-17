// limite_coppia.h - Scatoletta Blistra v1.0 (I-3): il motorino non puo' piu' spingere fino a rompere i denti.
//
// Con la stessa resistenza da 0,5 ohm della v0.9 (ascolta_motore.h) il firmware sa quanta corrente tira il motorino.
// In un motore a spazzole la coppia cresce con la corrente: C = Cs * (I - I0) / (Is - I0).
// Se la corrente supera quella che corrisponde a coppia_max per piu' di t_ms (o quella di coppia_subito anche per un attimo),
// il motore si ferma subito,
// torna indietro un attimo (la "scossa") e riprova. Dopo TENTATIVI prove si arrende: BLOCCO, avviso nell'app.
//
// Perche' 15 N*mm: sul pignone da 10 denti (raggio 5 mm, largo 2 mm) danno 3 N sul dente, cioe' circa 7,5 MPa
// di flessione (Lewis, Y = 0,201). Il PETG piu' debole trovato nelle schede tecniche regge 31,9 MPa: sicurezza x4.
// Per girare la ruota bastano circa 1 N*mm anche con le pillole piu' "appiccicose" (attrito 0,74): margine x15.
// Valori del motorino N20 100:1 a 6 V generico (Cs, Is, I0): da scheda del venditore e stima, vanno misurati (prova T8).
#pragma once
#include <stdint.h>

namespace blistra {

struct Motorino {
  float coppia_stallo_nmm = 34.3f;   // 0,35 kg*cm
  float i_stallo_ma = 350.f;
  float i_vuoto_ma = 40.f;
  float coppia(float i_ma) const {    // N*mm stimati dalla corrente
    float c = coppia_stallo_nmm * (i_ma - i_vuoto_ma) / (i_stallo_ma - i_vuoto_ma);
    return c < 0 ? 0 : c;
  }
  float corrente_per(float coppia_nmm) const {
    return i_vuoto_ma + (i_stallo_ma - i_vuoto_ma) * coppia_nmm / coppia_stallo_nmm;
  }
};

enum class Azione : uint8_t { CONTINUA, FERMA_E_SCOSSA, BLOCCO };

class LimiteCoppia {
 public:
  Motorino m;
  float coppia_max_nmm = 15.f;
  float t_ms = 10.f;        // quanto a lungo puo' stare sopra il limite (lo spunto all'avvio dura meno)
  float coppia_subito_nmm = 22.f;   // sopra questa si ferma al primo campione: il dente resta sotto 11 MPa (sicurezza x3)
  float avvio_ms = 30.f;    // all'avvio la corrente e' alta per qualche ms: si ignora
  int tentativi = 3;

  void parti() { sopra_ms_ = 0; da_ms_ = 0; }
  // un campione di corrente filtrata ogni dt_ms
  Azione campione(float i_ma, float dt_ms) {
    da_ms_ += dt_ms;
    if (da_ms_ < avvio_ms) return Azione::CONTINUA;
    if (i_ma > m.corrente_per(coppia_max_nmm)) sopra_ms_ += dt_ms; else sopra_ms_ = 0;
    if (sopra_ms_ < t_ms && i_ma < m.corrente_per(coppia_subito_nmm)) return Azione::CONTINUA;
    sopra_ms_ = 0; prove_++;
    return prove_ >= tentativi ? Azione::BLOCCO : Azione::FERMA_E_SCOSSA;
  }
  void giro_riuscito() { prove_ = 0; }
  int prove() const { return prove_; }
  float soglia_ma() const { return m.corrente_per(coppia_max_nmm); }
 private:
  float sopra_ms_ = 0, da_ms_ = 0;
  int prove_ = 0;
};

}  // namespace blistra
