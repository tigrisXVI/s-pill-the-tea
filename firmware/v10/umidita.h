// umidita.h - Scatoletta Blistra v1.0 (I-9, I-15): quanto e' asciutta l'aria vicino alle pillole, e quando cambiare il gel.
//
// Sensore AHT20 (I2C, indirizzo 0x38) attaccato sotto il tetto. Misura l'aria intorno alle cassette, non dentro uno
// scomparto: e' un'indicazione, non la misura esatta di ogni scomparto (la prova T7 dice quanto differiscono).
//
// Il gel di silice tiene almeno l'11% del suo peso in acqua al 20% di umidita' e almeno il 22% al 40%
// (scheda di un produttore). Sopra il 40% le compresse sensibili all'umidita' cominciano a soffrire.
// Regola: gel nuovo a ogni ricarica settimanale (7 giorni) finche' la prova T7 non dice che dura di piu';
// il sensore anticipa l'avviso se l'aria diventa umida prima.
#pragma once
#include <stdint.h>
#include <math.h>

namespace blistra {

struct Lettura { float umidita, temperatura; bool valida; };

// I 7 byte che manda l'AHT20 dopo il comando di misura (0xAC 0x33 0x00): stato, 20 bit di umidita', 20 di temperatura, CRC
inline uint8_t crc8_aht(const uint8_t* d, int n) {
  uint8_t c = 0xFF;
  for (int i = 0; i < n; i++) { c ^= d[i]; for (int b = 0; b < 8; b++) c = (c & 0x80) ? (uint8_t)((c << 1) ^ 0x31) : (uint8_t)(c << 1); }
  return c;
}
inline Lettura decodifica_aht20(const uint8_t b[7]) {
  Lettura l{0, 0, false};
  if (b[0] & 0x80) return l;                         // ancora occupato
  if (crc8_aht(b, 6) != b[6]) return l;              // dati rovinati
  uint32_t h = ((uint32_t)b[1] << 12) | ((uint32_t)b[2] << 4) | (b[3] >> 4);
  uint32_t t = (((uint32_t)b[3] & 0x0F) << 16) | ((uint32_t)b[4] << 8) | b[5];
  l.umidita = h * 100.f / 1048576.f;
  l.temperatura = t * 200.f / 1048576.f - 50.f;
  l.valida = true;
  return l;
}

enum class Gel : uint8_t { BUONO, CAMBIA_PRESTO, CAMBIA_ORA };

class StatoGel {
 public:
  float soglia_presto = 30.f;     // % di umidita' relativa
  float soglia_ora = 40.f;
  float giorni_max = 7.f;         // I-15: promemoria anche se il sensore non dice niente (o non c'e')
  // da chiamare una volta l'ora con una lettura valida; ore = ore passate dall'ultimo cambio del gel
  Gel aggiorna(float umidita, float ore) {
    media_ = n_ == 0 ? umidita : 0.9f * media_ + 0.1f * umidita;   // media mobile su circa 10 ore: niente allarmi per un respiro
    n_++;
    // pendenza (punti percentuali al giorno) sulle ultime letture: dice fra quanti giorni si arriva a soglia_ora
    float d = ore / 24.f;
    sx_ += d; sy_ += media_; sxx_ += d * d; sxy_ += d * media_; m_++;
    if (media_ >= soglia_ora || ore / 24.f >= giorni_max) return Gel::CAMBIA_ORA;
    if (media_ >= soglia_presto || giorni_a_soglia() < 1.f || ore / 24.f >= giorni_max - 1.f) return Gel::CAMBIA_PRESTO;
    return Gel::BUONO;
  }
  void gel_cambiato() { n_ = 0; m_ = 0; sx_ = sy_ = sxx_ = sxy_ = 0; }
  float media() const { return media_; }
  float giorni_a_soglia() const {                   // stima lineare; molto grande se l'aria non sta diventando piu' umida
    if (m_ < 12) return 1e9f;
    float den = m_ * sxx_ - sx_ * sx_; if (fabsf(den) < 1e-9f) return 1e9f;
    float b = (m_ * sxy_ - sx_ * sy_) / den;
    if (b <= 0.01f) return 1e9f;
    return (soglia_ora - media_) / b;
  }
 private:
  float media_ = 0, sx_ = 0, sy_ = 0, sxx_ = 0, sxy_ = 0;
  int n_ = 0, m_ = 0;
};

}  // namespace blistra
