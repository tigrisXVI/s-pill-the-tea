// riconosci_pillole.h - Scatoletta Blistra v0.9
//
// La bilancia sotto il piattino non dice solo "c'e' qualcosa": capisce QUALI pillole ci sono.
//
// Idea: ogni tipo di pillola ha un peso medio e una variabilita' (le compresse non sono identiche).
// La scatoletta li IMPARA: ogni volta che pesa una pillola di cui sa il tipo, aggiorna media e varianza
// (algoritmo di Welford, numericamente stabile, poca memoria). Impara anche quanto "balla" la bilancia a vuoto.
//
// Quando cade una dose, il peso misurato W viene confrontato con tutte le combinazioni plausibili
// (quella attesa, una pillola in meno, una in piu', una scambiata...). Ogni combinazione ha una media
// (somma dei pesi) e una varianza (somma delle varianze + rumore della bilancia): si sceglie quella
// piu' probabile (verosimiglianza gaussiana). La dose viene data SOLO se:
//   1) la combinazione piu' probabile e' proprio quella attesa,
//   2) e' almeno RAPPORTO_MIN volte piu' probabile della seconda (margine di sicurezza),
//   3) il peso non e' strano per nessuna combinazione (|z| < Z_MAX: altrimenti c'e' un oggetto estraneo).
// Altrimenti il piattino resta chiuso e l'app dice cosa manca o cosa c'e' in piu'.
//
// Senza Arduino: si compila anche sul computer (test/test_riconosci.cpp).

#pragma once
#include <math.h>
#include <stdint.h>

namespace blistra {

constexpr int MAX_TIPI = 8;          // tipi di pillola nella stessa dose
constexpr int MAX_PER_TIPO = 4;      // pillole dello stesso tipo nella stessa dose
constexpr float Z_MAX = 4.0f;        // oltre 4 deviazioni standard il peso non e' spiegabile
constexpr float RAPPORTO_MIN = 20.f; // la combinazione attesa deve essere 20 volte piu' probabile della seconda

struct Stima {                        // media e varianza imparate (Welford)
  uint32_t n = 0; float media = 0, m2 = 0;
  void aggiungi(float x) { n++; float d = x - media; media += d / n; m2 += d * (x - media); }
  float varianza(float prior) const {  // con poche misure si fida di piu' del valore di partenza
    float v = n > 1 ? m2 / (n - 1) : prior;
    float w = n / (n + 5.0f);          // dopo 5 misure pesa a meta'
    return w * v + (1 - w) * prior;
  }
};

struct Tipo {
  float peso_app = 0;                // peso scritto nell'app (mg), il punto di partenza
  Stima s;
  float media() const { return s.n >= 3 ? s.media : peso_app; }
  float sd() const {                 // variabilita' di partenza: 3% del peso o 1 mg
    float p = fmaxf(0.03f * peso_app, 1.0f);
    return sqrtf(s.varianza(p * p));
  }
};

enum class Esito : uint8_t { OK, MANCA, IN_PIU, SCAMBIO, INCERTO, ESTRANEO };

struct Risultato {
  Esito esito;
  int8_t diff[MAX_TIPI];  // per ogni tipo: pillole in piu' (+) o in meno (-) rispetto alla dose attesa
  float z;                // quanto e' lontano il peso dalla combinazione scelta, in deviazioni standard
  float rapporto;         // quante volte la scelta e' piu' probabile della seconda
};

class Riconoscitore {
 public:
  Tipo tipi[MAX_TIPI];
  int n_tipi = 0;
  Stima rumore;             // letture a vuoto: quanto balla la bilancia (mg)

  int aggiungi_tipo(float peso_mg) { tipi[n_tipi].peso_app = peso_mg; return n_tipi++; }
  void impara_pillola(int tipo, float peso_mg) { tipi[tipo].s.aggiungi(peso_mg); }
  void impara_vuoto(float lettura_mg) { rumore.aggiungi(lettura_mg); }
  float sd_bilancia() const { return sqrtf(rumore.varianza(4.0f * 4.0f)); }   // partenza: 4 mg

  // Due tipi si possono distinguere dal peso? (serve all'app: avvisa se due farmaci pesano quasi uguale)
  bool distinguibili(int a, int b) const {
    float d = fabsf(tipi[a].media() - tipi[b].media());
    float s = sqrtf(tipi[a].sd() * tipi[a].sd() + tipi[b].sd() * tipi[b].sd() + 2 * sd_bilancia() * sd_bilancia());
    return d > Z_MAX * s;            // separati di almeno 4 deviazioni standard
  }

  // ENTRATA -> USCITA. Quando la scatoletta e' stata ricaricata dall'alto, ogni scomparto e' stato pesato in entrata (W_in).
  // All'uscita le pillole sono LE STESSE: la variabilita' delle compresse sparisce e resta solo il rumore della bilancia
  // (due misure: sqrt(2) volte). Cosi' si vede anche una pillola minuscola rimasta incastrata nello scomparto.
  struct Uscita { bool ok; float z; int tipo_probabile; int8_t quante; };   // tipo_probabile: la pillola che manca (-) o avanza (+)
  Uscita controlla_uscita(float W_in, float W_out) const {
    float s = sqrtf(2.f) * sd_bilancia(), d = W_out - W_in;
    Uscita u{fabsf(d) < Z_MAX * s, d / s, -1, 0};
    if (!u.ok) {                                     // quale pillola spiega meglio la differenza?
      float best = 1e9f;
      for (int k = 0; k < n_tipi; k++) for (int q = 1; q <= 2; q++) {
        float e = fabsf(fabsf(d) - q * tipi[k].media()) / sqrtf(s * s + q * tipi[k].sd() * tipi[k].sd());
        if (e < best) { best = e; u.tipo_probabile = k; u.quante = d < 0 ? -q : q; }
      }
      if (best > Z_MAX) u.tipo_probabile = -1;       // nessuna pillola nota: briciole o oggetto estraneo
    }
    return u;
  }

  // attesa[i] = quante pillole del tipo i ci devono essere. W = peso misurato (mg, gia' tarato a vuoto).
  Risultato controlla(const int8_t* attesa, float W) const {
    int8_t cur[MAX_TIPI], migliore[MAX_TIPI] = {0};
    float ll1 = -1e30f, ll2 = -1e30f, z1 = 1e9f, zmin = 1e9f;
    // tutte le combinazioni con al massimo 2 pillole di differenza in totale (le piu' plausibili)
    for (int i = 0; i < n_tipi; i++) cur[i] = attesa[i];
    esplora(attesa, cur, 0, 0, W, migliore, ll1, ll2, z1, zmin);
    Risultato r; r.z = z1; r.rapporto = expf(fminf(ll1 - ll2, 80.f));
    int piu = 0, meno = 0;
    for (int i = 0; i < MAX_TIPI; i++) { r.diff[i] = i < n_tipi ? migliore[i] - attesa[i] : 0; if (r.diff[i] > 0) piu += r.diff[i]; else meno -= r.diff[i]; }
    if (zmin > Z_MAX) r.esito = Esito::ESTRANEO;
    else if (piu == 0 && meno == 0) r.esito = r.rapporto >= RAPPORTO_MIN ? Esito::OK : Esito::INCERTO;
    else if (r.rapporto < RAPPORTO_MIN) r.esito = Esito::INCERTO;
    else if (piu && meno) r.esito = Esito::SCAMBIO;
    else r.esito = meno ? Esito::MANCA : Esito::IN_PIU;
    return r;
  }

 private:
  void esplora(const int8_t* att, int8_t* cur, int i, int dist, float W, int8_t* best,
               float& ll1, float& ll2, float& z1, float& zmin) const {
    if (i == n_tipi) {
      float mu = 0, var = sd_bilancia() * sd_bilancia();
      for (int k = 0; k < n_tipi; k++) { mu += cur[k] * tipi[k].media(); var += cur[k] * tipi[k].sd() * tipi[k].sd(); }
      float z = (W - mu) / sqrtf(var);
      float ll = -0.5f * z * z - 0.5f * logf(var) - 3.5f * dist;   // a priori: ogni pillola sbagliata e' circa 30 volte meno probabile della dose giusta
      zmin = fminf(zmin, fabsf(z));
      if (ll > ll1) { ll2 = ll1; ll1 = ll; z1 = fabsf(z); for (int k = 0; k < n_tipi; k++) best[k] = cur[k]; }
      else if (ll > ll2) ll2 = ll;
      return;
    }
    for (int d = -2; d <= 2; d++) {
      int c = att[i] + d, nd = dist + (d < 0 ? -d : d);
      if (c < 0 || c > MAX_PER_TIPO || nd > 2) continue;
      cur[i] = c;
      esplora(att, cur, i + 1, nd, W, best, ll1, ll2, z1, zmin);
    }
    cur[i] = att[i];
  }
};

}  // namespace blistra
