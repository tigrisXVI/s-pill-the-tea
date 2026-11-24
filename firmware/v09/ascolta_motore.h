// ascolta_motore.h - S-pill the tea v0.9: il motore che si ascolta
//
// Hardware: una resistenza da 0,5 ohm sul ritorno a massa del driver DRV8833 (gira un motorino alla volta),
// un filtro RC (1 kohm + 22 nF) e un ingresso analogico dell'ESP32-S3 letto a 40 kHz (ADC continuo). Costo: pochi centesimi.
//
// Dalla corrente si ricavano tre cose:
//  1) CONTEGGIO DELLE INCRESPATURE (ripple counting). Le spazzole del motorino N20 cambiano contatto 6 volte
//     per giro del rotore e ogni volta la corrente ha un piccolo dente. Contandoli si sa di quanto ha girato
//     il motorino, quindi a che punto del giro e' l'ingranaggio della croce, senza encoder ne' sensori.
//     (Si tara da sola: il magnete della ruota passa davanti al sensore di Hall una volta ogni 15 giri della croce.)
//  2) LA FIRMA DEL GIRO. Durante un giro della croce la corrente ha sempre la stessa forma: bassa quando la ruota
//     e' ferma, piu' alta quando il perno la trascina. La scatola impara la forma normale (media e varianza per
//     ogni tratto di 10 gradi) e confronta ogni giro nuovo con questa.
//  3) DIAGNOSI.
//     - PICCO: in un tratto la corrente e' molto sopra il normale -> probabilmente una pillola si sta incastrando:
//       il motore torna indietro di poco e riprova (la "scossa").
//     - ATTRITO IN AUMENTO: giro dopo giro serve un po' piu' di forza (polvere di compresse, lamelle consumate):
//       l'app avvisa "pulisci la ruota" settimane prima che si blocchi.
//     - BLOCCO: corrente da motore fermo per piu' di 80 ms -> stop, indietro, avviso.

#pragma once
#include <math.h>
#include <stdint.h>

namespace blistra {

// ---------------- 1) contatore delle increspature
class ContaIncrespature {
 public:
  // fc_alta: filtro passa-alto per togliere la parte lenta; isteresi in frazione dell'ampiezza tipica
  explicit ContaIncrespature(float fs_hz = 40000.f)
      : a_(expf(-2.f * 3.14159f * 60.f / fs_hz)), b_(expf(-2.f * 3.14159f * 4000.f / fs_hz)) {}
  // da chiamare per ogni campione di corrente (mA). Ritorna true quando conta un dente.
  bool campione(float i_ma) {
    lenta_ = a_ * lenta_ + (1 - a_) * i_ma;          // componente lenta (carico)
    x_ = b_ * x_ + (1 - b_) * (i_ma - lenta_);      // solo le increspature, senza il fruscio sopra 4 kHz
    float x = x_;
    amp_ = 0.999f * amp_ + 0.001f * fabsf(x);         // ampiezza media, si adatta da sola
    float soglia = 0.6f * amp_;
    if (!alto_ && x > soglia) { alto_ = true; conteggio++; return true; }
    if (alto_ && x < -soglia) alto_ = false;
    return false;
  }
  float lenta() const { return lenta_; }
  uint32_t conteggio = 0;
 private:
  float a_, b_, lenta_ = 0, amp_ = 1, x_ = 0;
  bool alto_ = false;
};

// ---------------- 2) firma del giro della croce
constexpr int SETTORI = 36;                           // tratti da 10 gradi

class FirmaGiro {
 public:
  float media[SETTORI] = {0}, var[SETTORI] = {0}, base[SETTORI] = {0};   // base: la forma dei primi 20 giri, quando tutto e' pulito
  int giri = 0;
  float energia_base = 0, energia_ewma = 0;           // forza media del giro (corrente sopra quella a vuoto): all'inizio e adesso
  // corrente media di ogni tratto del giro appena finito
  void impara(const float* giro) {
    float vuoto = giro[0];
    for (int k = 1; k < SETTORI; k++) vuoto = fminf(vuoto, giro[k]);   // il tratto piu' basso: il motore gira a vuoto
    float e = 0;
    for (int k = 0; k < SETTORI; k++) {
      e += (giro[k] - vuoto) / SETTORI;
      if (giri == 0) { media[k] = giro[k]; var[k] = 25.f; continue; }
      float a = giri < 20 ? 1.f / (giri + 1) : 0.05f; // prima media vera, poi media mobile (si adatta lentamente)
      float d = giro[k] - media[k];
      media[k] += a * d; var[k] = (1 - a) * (var[k] + a * d * d);
    }
    giri++;
    if (giri == 20) for (int k = 0; k < SETTORI; k++) base[k] = media[k];
    if (giri > 20) {                                  // forza nei tratti in cui il perno trascina la ruota, rispetto all'inizio
      float vb = base[0], mx = 0; for (int k = 0; k < SETTORI; k++) vb = fminf(vb, base[k]);
      for (int k = 0; k < SETTORI; k++) mx = fmaxf(mx, base[k] - vb);
      float num = 0, den = 0;
      for (int k = 0; k < SETTORI; k++) if (base[k] - vb > 0.5f * mx) { num += giro[k] - vuoto; den += base[k] - vb; }
      float r = den > 0 ? num / den : 1.f;
      energia_ewma = giri == 21 ? r : 0.9f * energia_ewma + 0.1f * r;
      energia_base = 1.f;
    }
    (void)e;
  }
};

enum class Diagnosi : uint8_t { OK, PICCO, ATTRITO_IN_AUMENTO, BLOCCO, IMPARA };

struct Esame { Diagnosi d; int settore; float z; float aumento; };   // aumento: +% di forza rispetto all'inizio

class Ascolta {
 public:
  FirmaGiro firma;
  float soglia_picco = 6.0f;      // deviazioni standard
  float soglia_attrito = 0.25f;   // +25% di corrente media: e' ora di pulire
  float corrente_blocco = 300.f;  // mA (motorino N20 da 6 V fermo: circa 350 mA)

  // giro[k] = corrente media nel tratto k del giro (dai campioni e dal conteggio delle increspature)
  Esame esamina(const float* giro, float picco_ms_sopra_blocco) {
    Esame e{Diagnosi::OK, -1, 0, 0};
    if (picco_ms_sopra_blocco > 80.f) { e.d = Diagnosi::BLOCCO; return e; }
    if (firma.giri < 20) { firma.impara(giro); e.d = Diagnosi::IMPARA; return e; }
    for (int k = 0; k < SETTORI; k++) {
      float sd = sqrtf(firma.var[k]) + 2.f;           // +2 mA: rumore minimo dell'ADC
      float z = (giro[k] - firma.media[k]) / sd;
      if (z > e.z) { e.z = z; e.settore = k; }
    }
    if (e.z > soglia_picco) { e.d = Diagnosi::PICCO; return e; }   // un giro strano non si impara
    firma.impara(giro);
    e.aumento = firma.giri > 20 ? firma.energia_ewma - 1.f : 0.f;
    if (e.aumento > soglia_attrito) e.d = Diagnosi::ATTRITO_IN_AUMENTO;
    return e;
  }
};

}  // namespace blistra
