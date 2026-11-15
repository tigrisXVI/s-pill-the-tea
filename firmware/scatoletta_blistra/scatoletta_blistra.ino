/*
  Scatoletta Blistra - programma per ESP32 (prototipo v0.5)

  Cosa fa
  - Fino a 4 dosi al giorno, 28 scomparti (7 giorni x 4) + 1 di riposo.
  - All'ora della dose gira il carosello: le palette spingono le pillole su per la rampa
    fino al ripiano pesato. Pesa la dose e la confronta con quella attesa.
  - Suona, accende le luci gialle e scrive sul display che e' ora. Chi prende le pillole preme il
    TASTO GRANDE: un piccolo servo alza lo sportello, il ripiano vibra e le pillole scendono dallo
    scivolo e cadono nel bicchierino. Ripesa: se il ripiano e' vuoto la dose e' "erogata".
    Poi il servo abbassa la leva e lo sportello si richiude da solo, per gravita'.
  - Lo sportello si puo' sempre alzare anche a mano: funziona lo stesso.
  - Il carosello gira SOLO a sportello chiuso.
  - Pressione lunga del tasto a riposo: verifica del carico (pesa uno a uno tutti i 28 scomparti).

  Librerie: "ArduinoJson" (versione 7); "U8g2" (display), "Adafruit NeoPixel" (luci), "ESP32Servo" (sportello).
  Display, luci e servo si possono spegnere uno a uno in config.h (USA_DISPLAY, USA_LUCI, USA_SERVO).
  Scheda: "ESP32 Dev Module" (core ESP32 3.x).
  Monitor seriale a 115200:
    z = zero   a = avanti di uno   s = sensori   p = prova una dose (scomparto 1)
    t = tara della bilancia   c = taratura con un peso noto (scrivi i grammi, es. c7.5)   v = prova vibrazione
    k = verifica del carico   o = apri lo sportello   x = chiudi lo sportello
*/

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <ArduinoJson.h>
#include <time.h>
#include "config.h"
#if USA_DISPLAY
  #include <Wire.h>
  #include <U8g2lib.h>
  #if DISPLAY_SSD1306
    U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);
  #else
    U8G2_SH1106_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);
  #endif
#endif
#if USA_LUCI
  #include <Adafruit_NeoPixel.h>
  Adafruit_NeoPixel barra(NUMERO_LUCI, PIN_LUCI, NEO_GRB + NEO_KHZ800);
#endif
#if USA_SERVO
  #include <ESP32Servo.h>
  Servo servo;
#endif

#define VERSIONE "0.5"

enum Stato { RIPOSO, IN_ATTESA, VERIFICA, ERRORE };
Stato stato = RIPOSO;
const char* NOMI_STATO[] = { "idle", "waiting", "refill", "error" };

Preferences memoria;
long posizione = 0;
int spicchioCorrente = 0;
long ultimaDoseFatta = -1;

long doseInCorso = -1;
int scompartoInCorso = 0, dosePrevistaMg = 0, pesoArrivatoMg = 0;
unsigned long inizioAttesa = 0, ultimoBip = 0;
String esito = "";              // all | partial | untouched  (ultima dose)
String statoDettaglio = "";     // partial | misload  (mostrato in Blistra)

String orari[4] = { ORA_DOSE_1, ORA_DOSE_2, ORA_DOSE_3, ORA_DOSE_4 };
String personaId = "", nomeScatola = "Scatoletta";
String gettone = "";
unsigned long gettonePresoAlle = 0, ultimoContatto = 0, ultimaConfig = 0;
String ultimoEvento = "accesa";
char carichi[SPICCHI] = {0};    // esito della verifica: 'o' giusto, 'b' da controllare, 'e' vuoto

// ---------------------------------------------------------------- motore

const uint8_t FASI[8][4] = { {1,0,0,0}, {1,1,0,0}, {0,1,0,0}, {0,1,1,0}, {0,0,1,0}, {0,0,1,1}, {0,0,0,1}, {1,0,0,1} };
const uint8_t PIN_MOTORE[4] = { PIN_MOTORE_1, PIN_MOTORE_2, PIN_MOTORE_3, PIN_MOTORE_4 };
int fase = 0;

void motoreSpento() { for (int i = 0; i < 4; i++) digitalWrite(PIN_MOTORE[i], LOW); }
bool magneteZero()     { return digitalRead(PIN_HALL_ZERO) == LOW; }
bool sportelloChiuso() { return digitalRead(PIN_HALL_SPORT) == LOW; }

void unPasso() {
  fase = (fase + DIREZIONE + 8) % 8;
  for (int i = 0; i < 4; i++) digitalWrite(PIN_MOTORE[i], FASI[fase][i]);
  delayMicroseconds(MICROSECONDI_PASSO);
  posizione++;
}

// Gira solo a sportello chiuso: se qualcuno lo apre, si ferma e aspetta.
bool avanza(long passi) {
  for (long i = 0; i < passi; i++) {
    if (!sportelloChiuso()) {
      motoreSpento();
      unsigned long da = millis();
      while (!sportelloChiuso()) { delay(50); if (millis() - da > 60000UL) return false; }
    }
    unPasso();
    if ((i & 255) == 0) yield();
  }
  motoreSpento();
  return true;
}

void errore(const char* perche);
int leggiPulsante();

// Lo zero si cerca sempre girando nello stesso verso (le palette salgono la rampa solo in quel verso).
bool cercaZero() {
  long limite = (long)(PASSI_PER_GIRO * 1.3), n = 0;
  while (magneteZero() && n < limite) { if (!avanza(1)) return false; n++; }
  while (!magneteZero() && n < limite) { if (!avanza(1)) return false; n++; }
  if (n >= limite) { motoreSpento(); return false; }
  if (!avanza(PASSI_DOPO_ZERO)) return false;
  posizione = 0; spicchioCorrente = 0;
  return true;
}

void vaiASpicchio(int k) {
  long bersaglio = lround(k * PASSI_PER_GIRO / SPICCHI);
  if (bersaglio < posizione || k == 0) { if (!cercaZero()) { errore("zero non trovato o sportello aperto"); return; } }
  if (!avanza(bersaglio - posizione)) { errore("sportello rimasto aperto"); return; }
  spicchioCorrente = k;
}
void vaiARiposo() { vaiASpicchio(0); }

// ---------------------------------------------------------------- bilancia (HX711, senza librerie)

float scala = 0;        // conteggi per milligrammo (si trova con il comando c)
long tara = 0;

bool hxPronto() { return digitalRead(PIN_HX711_DOUT) == LOW; }

long hxLeggiUna() {
  unsigned long da = millis();
  while (!hxPronto()) { if (millis() - da > 300) return 0; delay(1); }
  long v = 0;
  for (int i = 0; i < 24; i++) {
    digitalWrite(PIN_HX711_SCK, HIGH); delayMicroseconds(1);
    v = (v << 1) | digitalRead(PIN_HX711_DOUT);
    digitalWrite(PIN_HX711_SCK, LOW); delayMicroseconds(1);
  }
  digitalWrite(PIN_HX711_SCK, HIGH); delayMicroseconds(1); digitalWrite(PIN_HX711_SCK, LOW);   // canale A, guadagno 128
  if (v & 0x800000) v |= ~0xFFFFFFL;
  return v;
}

// Media "robusta": scarta le letture piu' lontane (la piastra si e' appena fermata).
long hxLeggi(int n = 16) {
  long l[32]; n = n > 32 ? 32 : n;
  for (int i = 0; i < n; i++) l[i] = hxLeggiUna();
  for (int i = 1; i < n; i++) for (int j = i; j > 0 && l[j] < l[j - 1]; j--) { long t = l[j]; l[j] = l[j - 1]; l[j - 1] = t; }
  long s = 0; int k = 0;
  for (int i = n / 4; i < n - n / 4; i++) { s += l[i]; k++; }
  return s / (k ? k : 1);
}

int pesoMg() { return scala > 0 ? (int)lround((hxLeggi() - tara) / scala) : 0; }

void faiTara() { delay(300); tara = hxLeggi(24); memoria.putLong("tara", tara); }

// ---------------------------------------------------------------- vibrazione, suoni, luce

void vibra(int ms) {
  ledcWrite(PIN_VIBRO, VIBRA_FORZA);
  delay(ms);
  ledcWrite(PIN_VIBRO, 0);
  delay(700);           // la piastra si ferma prima di pesare
}

// Luci: un colore per ogni situazione. Il display e i suoni dicono sempre la stessa cosa,
// cosi' chi distingue male i colori non perde niente.
enum Colore { SPENTO, GIALLO, VERDE, ROSSO, BLU, BIANCO };
void luci(Colore c, bool lampeggia = false) {
#if USA_LUCI
  static const uint8_t RGB[6][3] = { {0,0,0}, {255,150,0}, {0,220,60}, {255,0,0}, {0,60,255}, {120,120,120} };
  bool acceso = !lampeggia || (millis() / 400) % 2;
  for (int i = 0; i < NUMERO_LUCI; i++) barra.setPixelColor(i, acceso ? barra.Color(RGB[c][0], RGB[c][1], RGB[c][2]) : 0);
  barra.show();
#endif
}

// Display: due righe, la prima grande. Ridisegna solo se il testo cambia.
void schermo(const String& grande, const String& piccola = "") {
#if USA_DISPLAY
  static String ultimo = "";
  if (grande + "|" + piccola == ultimo) return;
  ultimo = grande + "|" + piccola;
  display.clearBuffer();
  display.setFont(grande.length() <= 5 ? u8g2_font_logisoso32_tf : u8g2_font_helvB18_tf);
  display.drawStr((128 - display.getStrWidth(grande.c_str())) / 2, grande.length() <= 5 ? 38 : 30, grande.c_str());
  display.setFont(u8g2_font_helvB10_tf);
  display.drawStr((128 - display.getStrWidth(piccola.c_str())) / 2, 60, piccola.c_str());
  display.sendBuffer();
#endif
}

// Sportello: il servo alza una leva che spinge sotto la mensola dello sportello. Per chiudere la leva
// torna giu' e lo sportello scende per il suo peso: non spinge mai verso il basso, quindi non schiaccia.
int angoloServo = SERVO_CHIUSO;
void muoviServo(int verso) {
#if USA_SERVO
  if (!servo.attached()) servo.attach(PIN_SERVO, 500, 2400);
  while (angoloServo != verso) { angoloServo += verso > angoloServo ? 1 : -1; servo.write(angoloServo); delay(SERVO_MS_PER_GRADO); }
#endif
}
void apriSportello()   { muoviServo(SERVO_APERTO); }
void chiudiSportello() {
#if USA_SERVO
  muoviServo(SERVO_CHIUSO); delay(400); servo.detach();     // a riposo il servo e' spento: niente ronzio
#endif
}

void bip(int frequenza, int ms) { tone(PIN_CICALINO, frequenza, ms); delay(ms + 30); noTone(PIN_CICALINO); }
void melodiaDose()   { bip(880, 180); bip(1175, 180); bip(1568, 320); }
void melodiaOk()     { bip(1568, 120); bip(2093, 220); }
void melodiaErrore() { bip(300, 400); bip(220, 600); }

void errore(const char* perche) {
  Serial.printf("ERRORE: %s\n", perche);
  ultimoEvento = String("errore: ") + perche;
  stato = ERRORE; motoreSpento(); ledcWrite(PIN_VIBRO, 0); luci(ROSSO); schermo("Errore", "premi il tasto"); melodiaErrore();
}

void stampaSensori() {
  Serial.printf("zero: %s  sportello: %s  peso: %d mg  scomparto: %d  passi: %ld\n",
    magneteZero() ? "SI" : "no", sportelloChiuso() ? "CHIUSO" : "aperto", pesoMg(), spicchioCorrente, posizione);
}

// ---------------------------------------------------------------- orologio e scomparti

bool oraValida(struct tm* t) { return getLocalTime(t, 50) && t->tm_year > 120; }
int minutiDi(const String& hhmm) { return hhmm.length() == 5 ? hhmm.substring(0, 2).toInt() * 60 + hhmm.substring(3, 5).toInt() : -1; }
int giornoBlistra(const struct tm& t) { return (t.tm_wday + 6) % 7; }     // lunedi' = 0
long numeroGiorno(const struct tm& t) { return (long)(t.tm_year + 1900) * 400L + t.tm_yday; }
int scompartoDi(int giorno, int dose) { return giorno * 4 + dose + 1; }   // 1..28

// A quale delle 4 dosi appartiene l'orario di un farmaco: a quella con l'orario piu' vicino (come fa Blistra).
int doseDiOrario(const String& hhmm) {
  int m = minutiDi(hhmm), migliore = -1, distanza = 100000;
  for (int i = 0; i < 4; i++) {
    int o = minutiDi(orari[i]); if (o < 0) continue;
    int d = abs(o - m); if (d < distanza) { distanza = d; migliore = i; }
  }
  return migliore;
}

// ---------------------------------------------------------------- Blistra
#if USA_BLISTRA

const String BASE_DOC = String("projects/") + FIREBASE_PROGETTO + "/databases/(default)/documents";
const String BASE_URL = String("https://firestore.googleapis.com/v1/") + BASE_DOC;
JsonDocument pesi;      // farmaco -> mg di una pillola, da Blistra

// NOTA: connessione cifrata ma certificato non verificato. Prima di un uso reale: client.setCACert(...).
bool chiedi(const char* metodo, const String& url, const String& corpo, JsonDocument& risposta, JsonDocument* filtro, bool conGettone) {
  WiFiClientSecure client; client.setInsecure();
  HTTPClient http; http.useHTTP10(true); http.setTimeout(12000);
  if (!http.begin(client, url)) return false;
  http.addHeader("Content-Type", "application/json");
  if (conGettone) http.addHeader("Authorization", "Bearer " + gettone);
  int codice = http.sendRequest(metodo, corpo);
  bool ok = codice >= 200 && codice < 300;
  if (ok) {
    DeserializationError e = filtro ? deserializeJson(risposta, http.getStream(), DeserializationOption::Filter(*filtro))
                                    : deserializeJson(risposta, http.getStream());
    if (e) { Serial.printf("JSON: %s\n", e.c_str()); ok = false; }
  } else Serial.printf("HTTP %d\n", codice);
  http.end();
  return ok;
}

bool accedi() {
  if (gettone.length() && millis() - gettonePresoAlle < 50UL * 60UL * 1000UL) return true;
  JsonDocument corpo, risposta, filtro;
  corpo["email"] = BLISTRA_EMAIL; corpo["password"] = BLISTRA_PASSWORD; corpo["returnSecureToken"] = true;
  filtro["idToken"] = true;
  String testo; serializeJson(corpo, testo);
  if (!chiedi("POST", String("https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=") + FIREBASE_API_KEY, testo, risposta, &filtro, false)) { gettone = ""; return false; }
  gettone = risposta["idToken"].as<String>(); gettonePresoAlle = millis();
  return gettone.length() > 0;
}

String docScatola() { return String("/families/") + BLISTRA_CERCHIA + "/devices/" + BLISTRA_SCATOLA; }

void leggiImpostazioni() {
  if (!accedi()) return;
  JsonDocument r;
  if (!chiedi("GET", BASE_URL + docScatola(), "", r, nullptr, true)) return;
  JsonObject f = r["fields"];
  int i = 0;
  for (JsonObject v : f["times"]["arrayValue"]["values"].as<JsonArray>()) { if (i < 4) orari[i++] = v["stringValue"] | ""; }
  if (i) for (; i < 4; i++) orari[i] = "";
  const char* p = f["patientId"]["stringValue"]; if (p) personaId = p;
  const char* n = f["name"]["stringValue"]; if (n) nomeScatola = n;
  pesi.clear();
  for (JsonPair kv : f["weights"]["mapValue"]["fields"].as<JsonObject>())
    pesi[kv.key()] = String(kv.value()["integerValue"] | "0").toInt();
  Serial.printf("Blistra: %s %s %s %s, persona %s\n", orari[0].c_str(), orari[1].c_str(), orari[2].c_str(), orari[3].c_str(), personaId.c_str());
}

void mandaStato() {
  if (!accedi()) return;
  JsonDocument corpo, r;
  JsonObject st = corpo["fields"]["status"]["mapValue"]["fields"].to<JsonObject>();
  char ms[24]; snprintf(ms, sizeof ms, "%llu", (unsigned long long)time(nullptr) * 1000ULL);
  st["lastSeen"]["integerValue"] = ms;
  st["state"]["stringValue"] = statoDettaglio.length() ? statoDettaglio.c_str() : NOMI_STATO[stato];
  st["sector"]["integerValue"] = String(spicchioCorrente);
  st["lastEvent"]["stringValue"] = ultimoEvento;
  if (esito.length()) st["outcome"]["stringValue"] = esito;
  JsonObject car = st["loads"]["mapValue"]["fields"].to<JsonObject>();
  for (int k = 1; k < SPICCHI; k++) if (carichi[k]) car[String(k)]["stringValue"] = carichi[k] == 'o' ? "ok" : carichi[k] == 'b' ? "bad" : "empty";
  st["fw"]["stringValue"] = VERSIONE;
  String testo; serializeJson(corpo, testo);
  chiedi("PATCH", BASE_URL + docScatola() + "?updateMask.fieldPaths=status", testo, r, nullptr, true);
}

// Legge i farmaci della persona. Se "segna" e' vero, li segna come presi (e scala le scorte);
// in ogni caso restituisce il peso atteso della dose (mg), oppure -1 se non si sa.
int farmaciDellaDose(int giorno, int dose, bool segna, const struct tm* adesso) {
  if (!accedi() || personaId == "") return -1;
  JsonDocument filtro, lista;
  JsonObject ff = filtro["documents"][0].to<JsonObject>(); ff["name"] = true; ff["fields"] = true;
  String url = BASE_URL + "/families/" + BLISTRA_CERCHIA + "/meds?pageSize=100"
    "&mask.fieldPaths=patientId&mask.fieldPaths=times&mask.fieldPaths=days&mask.fieldPaths=units&mask.fieldPaths=stock";
  if (!chiedi("GET", url, "", lista, &filtro, true)) return -1;

  JsonDocument corpo;
  JsonArray scritture = corpo["writes"].to<JsonArray>();
  JsonObject registro = scritture.add<JsonObject>();
  char data[11] = "", ora[6] = "", ms[24];
  if (adesso) { strftime(data, sizeof data, "%Y-%m-%d", adesso); strftime(ora, sizeof ora, "%H:%M", adesso); }
  snprintf(ms, sizeof ms, "%llu", (unsigned long long)time(nullptr) * 1000ULL);
  registro["update"]["name"] = BASE_DOC + "/families/" + BLISTRA_CERCHIA + "/logs/" + data;
  JsonObject voci = registro["update"]["fields"]["entries"]["mapValue"]["fields"].to<JsonObject>();
  JsonArray maschera = registro["updateMask"]["fieldPaths"].to<JsonArray>();
  int quante = 0; long atteso = 0; bool pesoNoto = true;

  for (JsonObject d : lista["documents"].as<JsonArray>()) {
    JsonObject f = d["fields"];
    if (personaId != (f["patientId"]["stringValue"] | "")) continue;
    bool giornoGiusto = false;
    for (JsonObject g : f["days"]["arrayValue"]["values"].as<JsonArray>()) if (String(g["integerValue"] | "-1").toInt() == giorno) giornoGiusto = true;
    if (!giornoGiusto) continue;
    String nome = d["name"].as<String>(), id = nome.substring(nome.lastIndexOf('/') + 1);
    double unita = 1;
    if (!f["units"]["integerValue"].isNull()) unita = String(f["units"]["integerValue"] | "1").toDouble();
    else if (!f["units"]["doubleValue"].isNull()) unita = f["units"]["doubleValue"] | 1.0;
    int qui = 0;
    for (JsonObject v : f["times"]["arrayValue"]["values"].as<JsonArray>()) {
      String t = v["stringValue"] | "";
      if (t.length() != 5 || doseDiOrario(t) != dose) continue;
      qui++;
      if (segna) {
        String chiave = id + "_" + t.substring(0, 2) + t.substring(3, 5);
        JsonObject e = voci[chiave]["mapValue"]["fields"].to<JsonObject>();
        e["at"]["stringValue"] = ora; e["by"]["stringValue"] = "box"; e["byName"]["stringValue"] = nomeScatola; e["ts"]["integerValue"] = ms;
        maschera.add(String("entries.`") + chiave + "`");
      }
    }
    if (!qui) continue;
    quante += qui;
    long mg = pesi[id] | 0;
    if (mg > 0) atteso += (long)lround(mg * unita * qui); else pesoNoto = false;
    JsonObject conta = f["stock"]["mapValue"]["fields"]["count"];
    if (segna && (!conta["integerValue"].isNull() || !conta["doubleValue"].isNull())) {
      JsonObject tr = scritture.add<JsonObject>();
      tr["transform"]["document"] = nome;
      JsonObject ft = tr["transform"]["fieldTransforms"].add<JsonObject>();
      ft["fieldPath"] = "stock.count"; ft["increment"]["doubleValue"] = -unita * qui;
    }
  }
  if (segna && quante && adesso) {
    String testo; serializeJson(corpo, testo);
    JsonDocument r;
    bool ok = chiedi("POST", BASE_URL + ":commit", testo, r, nullptr, true);
    Serial.printf("Blistra: %d dosi segnate (%s)\n", quante, ok ? "ok" : "non riuscito");
  }
  if (!quante) return 0;
  return pesoNoto ? (int)atteso : -1;
}

#else
void leggiImpostazioni() {}
void mandaStato() {}
int farmaciDellaDose(int, int, bool, const struct tm*) { return -1; }
#endif

bool caricoGiusto(int misurato, int atteso) {
  if (atteso < 0) return misurato > SOGLIA_VUOTA_MG;          // peso non noto: basta che ci sia qualcosa
  if (atteso == 0) return misurato <= SOGLIA_VUOTA_MG;
  int tol = max((int)TOLLERANZA_MG, atteso * TOLLERANZA_PCT / 100);
  return abs(misurato - atteso) <= tol;
}

// ---------------------------------------------------------------- dosi

int giornoInCorso = 0, doseNumInCorso = 0;

void iniziaDose(long numero, int giorno, int dose) {
  int k = scompartoDi(giorno, dose);
  Serial.printf("Dose %ld: scomparto %d\n", numero, k);
  if (spicchioCorrente == 0) faiTara();                         // sul ripiano c'e' lo scomparto di riposo, vuoto
  vaiASpicchio(k);
  if (stato == ERRORE) return;
  delay(600);
  pesoArrivatoMg = pesoMg();
  dosePrevistaMg = farmaciDellaDose(giorno, dose, false, nullptr);
  bool giusto = caricoGiusto(pesoArrivatoMg, dosePrevistaMg);
  statoDettaglio = giusto ? "" : "misload";
  Serial.printf("peso sul ripiano %d mg, atteso %d mg -> %s\n", pesoArrivatoMg, dosePrevistaMg, giusto ? "giusto" : "DA CONTROLLARE");
  doseInCorso = numero; scompartoInCorso = k; giornoInCorso = giorno; doseNumInCorso = dose;
  inizioAttesa = millis(); ultimoBip = 0;
  stato = IN_ATTESA;
  ultimoEvento = String("dose pronta, scomparto ") + k;
  mandaStato();
}

void chiudiDose(const char* come) {
  ultimaDoseFatta = doseInCorso;
  memoria.putLong("ultima", ultimaDoseFatta);
  chiudiSportello();                                            // la leva scende, lo sportello si richiude da solo
  esito = come;
  struct tm adesso; bool ora = oraValida(&adesso);
  if (esito == "all" || esito == "partial") {
    if (ora) farmaciDellaDose(giornoInCorso, doseNumInCorso, true, &adesso);
    ultimoEvento = esito == "all" ? "dose erogata" : "dose erogata a meta'";
    if (esito == "all") { luci(VERDE); schermo("Presa", "brava, bravo!"); melodiaOk(); }
    else { luci(ROSSO); schermo("Controlla", "ne manca qualcuna"); melodiaErrore(); }
    delay(2500);
  } else { ultimoEvento = "dose non presa"; luci(ROSSO); schermo("Saltata", "dose non presa"); delay(1500); }
  statoDettaglio = esito == "partial" ? "partial" : "";
  Serial.println(ultimoEvento);
  // torna a riposo solo a sportello chiuso (avanza() aspetta da sola)
  if (!sportelloChiuso()) schermo("Chiudi", "lo sportello");
  vaiARiposo();
  if (stato != ERRORE) { stato = RIPOSO; luci(SPENTO); }
  doseInCorso = -1;
  mandaStato();
}

// Sportello aperto: vibra finche' il ripiano e' vuoto (al massimo TENTATIVI_VIBRA volte).
void eroga() {
  luci(BIANCO); schermo("Prendi", "le pillole");
  int prima = pesoMg(), dopo = prima;
  for (int i = 0; i < TENTATIVI_VIBRA; i++) {
    vibra(VIBRA_MS);
    dopo = pesoMg();
    Serial.printf("vibrazione %d: sul ripiano restano %d mg\n", i + 1, dopo);
    if (dopo <= SOGLIA_VUOTA_MG) break;
    if (sportelloChiuso()) break;                                 // l'hanno richiuso: non insistere
  }
  if (dopo <= SOGLIA_VUOTA_MG || dopo < prima - SOGLIA_VUOTA_MG) {
    // lascia il tempo di prendere le pillole dalla vaschetta prima di richiudere
    for (unsigned long da = millis(); millis() - da < (unsigned long)SECONDI_APERTO * 1000UL; ) { if (leggiPulsante()) break; delay(50); }
  }
  if (dopo <= SOGLIA_VUOTA_MG) chiudiDose("all");
  else if (dopo < prima - SOGLIA_VUOTA_MG) chiudiDose("partial");
  else { ultimoEvento = "le pillole non scendono: prendile dall'alto"; statoDettaglio = "partial"; mandaStato(); }
}

void seguiAttesa() {
  unsigned long ora = millis();
  luci(GIALLO, true); schermo("E' ora", "premi il tasto");
  if (ultimoBip == 0 || ora - ultimoBip > 30000UL) { melodiaDose(); ultimoBip = millis(); }
  if (!sportelloChiuso()) { delay(300); eroga(); return; }
  // pillole prese dall'alto senza vibrare: il ripiano si e' svuotato da solo
  if (pesoArrivatoMg > SOGLIA_VUOTA_MG && (ora / 1000) % 5 == 0 && pesoMg() <= SOGLIA_VUOTA_MG) { chiudiDose("all"); return; }
  if (ora - inizioAttesa > (unsigned long)MINUTI_DI_ATTESA * 60000UL) chiudiDose("untouched");
}

// A riposo il display mostra l'ora e la prossima dose.
void schermoRiposo() {
  struct tm t;
  if (!oraValida(&t)) { schermo("--:--", WiFi.status() == WL_CONNECTED ? "cerco l'ora..." : "senza Wi-Fi"); return; }
  char ora[6]; snprintf(ora, sizeof ora, "%02d:%02d", t.tm_hour, t.tm_min);
  int adesso = t.tm_hour * 60 + t.tm_min, prossima = -1;
  for (int d = 0; d < 4; d++) { int m = minutiDi(orari[d]); if (m > adesso && (prossima < 0 || m < minutiDi(orari[prossima]))) prossima = d; }
  if (prossima < 0) for (int d = 0; d < 4; d++) { int m = minutiDi(orari[d]); if (m >= 0 && (prossima < 0 || m < minutiDi(orari[prossima]))) prossima = d; }
  schermo(ora, prossima < 0 ? String("nessuna dose") : String("prossima ") + orari[prossima]);
}

void controllaOrari() {
  struct tm t;
  if (!oraValida(&t)) return;
  int adesso = t.tm_hour * 60 + t.tm_min;
  for (int d = 0; d < 4; d++) {
    int inizio = minutiDi(orari[d]); if (inizio < 0) continue;
    long numero = numeroGiorno(t) * 4 + d;
    if (adesso >= inizio && adesso < inizio + MINUTI_DI_ATTESA && numero > ultimaDoseFatta) { iniziaDose(numero, giornoBlistra(t), d); return; }
  }
}

// ---------------------------------------------------------------- verifica del carico

// Porta uno a uno gli scomparti sul ripiano, li pesa e li confronta con la dose attesa (sportello chiuso).
void verificaCarico() {
  if (!sportelloChiuso()) { bip(300, 300); Serial.println("Chiudi lo sportello prima della verifica."); return; }
  stato = VERIFICA; ultimoEvento = "verifica del carico"; luci(BLU); schermo("Verifica", "circa 2 minuti"); mandaStato();
  vaiARiposo(); faiTara();
  int sbagliati = 0;
  for (int k = 1; k < SPICCHI && stato != ERRORE; k++) {
    vaiASpicchio(k); delay(600);
    int mg = pesoMg();
    int giorno = (k - 1) / 4, dose = (k - 1) % 4;
    int atteso = minutiDi(orari[dose]) < 0 ? 0 : farmaciDellaDose(giorno, dose, false, nullptr);
    bool ok = caricoGiusto(mg, atteso);
    carichi[k] = mg <= SOGLIA_VUOTA_MG && atteso <= 0 ? 'e' : ok ? 'o' : 'b';
    if (!ok) sbagliati++;
    Serial.printf("scomparto %2d: %5d mg (atteso %d) %s\n", k, mg, atteso, ok ? "ok" : "DA CONTROLLARE");
  }
  vaiARiposo();
  if (stato != ERRORE) stato = RIPOSO;
  luci(sbagliati ? ROSSO : VERDE);
  statoDettaglio = sbagliati ? "misload" : "";
  ultimoEvento = sbagliati ? String(sbagliati) + " scomparti da controllare" : "carico giusto";
  schermo(sbagliati ? "Controlla" : "Tutto ok", ultimoEvento);
  if (sbagliati) melodiaErrore(); else melodiaOk();
  mandaStato(); delay(3000); luci(SPENTO);
}

// ---------------------------------------------------------------- pulsante, avvio, ciclo

int leggiPulsante() {
  if (digitalRead(PIN_PULSANTE) == HIGH) return 0;
  unsigned long da = millis();
  while (digitalRead(PIN_PULSANTE) == LOW) { delay(10); if (millis() - da > 2000) break; }
  bool lunga = millis() - da >= 2000;
  if (lunga) { bip(1200, 80); while (digitalRead(PIN_PULSANTE) == LOW) delay(10); }
  delay(40);
  return millis() - da < 30 ? 0 : (lunga ? 2 : 1);
}

void collegaWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA); WiFi.begin(WIFI_NOME, WIFI_PASSWORD);
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) delay(250);
  Serial.println(WiFi.status() == WL_CONNECTED ? "Wi-Fi collegato" : "Wi-Fi non disponibile");
}

void comandoSeriale() {
  char c = Serial.read();
  if (c == 'z') { stato = RIPOSO; vaiARiposo(); stampaSensori(); }
  if (c == 'a') { vaiASpicchio((spicchioCorrente + 1) % SPICCHI); stampaSensori(); }
  if (c == 's') stampaSensori();
  if (c == 't') { faiTara(); Serial.println("tara fatta"); }
  if (c == 'v') { vibra(VIBRA_MS); stampaSensori(); }
  if (c == 'k' && stato == RIPOSO) verificaCarico();
  if (c == 'o') { apriSportello(); stampaSensori(); }
  if (c == 'x') { chiudiSportello(); stampaSensori(); }
  if (c == 'p' && stato == RIPOSO) iniziaDose(ultimaDoseFatta, 0, 0);
  if (c == 'c') {                                   // es. "c7.5" con una moneta da 1 euro (7,5 g) sul ripiano
    delay(50); String g = "";
    while (Serial.available()) { char x = Serial.read(); if ((x >= '0' && x <= '9') || x == '.') g.concat(x); }
    float grammi = g.toDouble();
    if (grammi > 0) { scala = (hxLeggi(24) - tara) / (grammi * 1000.0f); memoria.putFloat("scala", scala); Serial.printf("scala: %.4f conteggi/mg\n", scala); }
  }
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 4; i++) pinMode(PIN_MOTORE[i], OUTPUT);
  motoreSpento();
  pinMode(PIN_HALL_ZERO, INPUT_PULLUP); pinMode(PIN_HALL_SPORT, INPUT_PULLUP); pinMode(PIN_PULSANTE, INPUT_PULLUP);
  pinMode(PIN_CICALINO, OUTPUT);
#if USA_LUCI
  barra.begin(); barra.setBrightness(LUMINOSITA_LUCI); luci(BLU);
#endif
#if USA_DISPLAY
  Wire.begin(PIN_DISPLAY_SDA, PIN_DISPLAY_SCL); display.begin(); schermo("Blistra", "avvio...");
#endif
  chiudiSportello();
  pinMode(PIN_HX711_DOUT, INPUT); pinMode(PIN_HX711_SCK, OUTPUT); digitalWrite(PIN_HX711_SCK, LOW);
  ledcAttach(PIN_VIBRO, 20000, 8); ledcWrite(PIN_VIBRO, 0);

  memoria.begin("scatoletta", false);
  ultimaDoseFatta = memoria.getLong("ultima", -1);
  scala = memoria.getFloat("scala", 0); tara = memoria.getLong("tara", 0);

  Serial.printf("\nScatoletta Blistra %s\n", VERSIONE);
  if (scala <= 0) Serial.println("Bilancia da tarare: svuota il ripiano, 't', poi metti un peso noto e scrivi 'c' e i grammi (es. c7.5).");
  bip(1568, 100);
  collegaWifi();
  configTzTime(FUSO_ORARIO, "pool.ntp.org", "time.google.com");
  vaiARiposo();
  if (stato != ERRORE) faiTara();
  leggiImpostazioni();
  mandaStato();
  stampaSensori();
  luci(SPENTO);
}

void loop() {
  if (Serial.available()) comandoSeriale();
  int tasto = leggiPulsante();
  if (stato == RIPOSO) {
    if (tasto == 2) verificaCarico();
    else if (tasto == 1) { bip(1568, 100); stampaSensori(); }
    else { schermoRiposo(); controllaOrari(); }
  } else if (stato == IN_ATTESA) {
    if (tasto == 1) {                                 // il tasto grande: "ci sono", apri lo sportello
      bip(1568, 100); schermo("Apro", "lo sportello"); apriSportello();
      if (sportelloChiuso()) { delay(300); eroga(); }   // senza servo (o se il sensore non lo vede aperto) eroga lo stesso
    } else if (tasto == 2) ultimoBip = millis();        // pressione lunga: zittisce per 30 secondi
    if (stato == IN_ATTESA) seguiAttesa();
  } else if (stato == ERRORE) {
    luci(ROSSO, true);
    if (tasto) { stato = RIPOSO; statoDettaglio = ""; vaiARiposo(); }
  }
  if (millis() - ultimoContatto > 60000UL) {
    ultimoContatto = millis();
    collegaWifi();
    if (WiFi.status() == WL_CONNECTED) {
      if (stato == RIPOSO && (ultimaConfig == 0 || millis() - ultimaConfig > 600000UL)) { ultimaConfig = millis(); leggiImpostazioni(); }
      mandaStato();
    }
  }
  delay(20);
}
