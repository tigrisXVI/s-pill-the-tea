// Scatoletta Blistra v0.3 - impostazioni
// Questo e' l'unico file da modificare prima di caricare il programma.
// NON pubblicarlo online dopo averci scritto le password.

#pragma once

// ---- Wi-Fi di casa ----------------------------------------------------------
#define WIFI_NOME       "NOME-DELLA-RETE"
#define WIFI_PASSWORD   "PASSWORD-DELLA-RETE"

// ---- Collegamento a Blistra -------------------------------------------------
// 0 = la scatoletta lavora da sola con gli orari scritti qui sotto.
// 1 = legge persona, orari e pesi da Blistra e segna le dosi nella cerchia.
#define USA_BLISTRA     0

// Un account Blistra creato apposta per la scatoletta, entrato nella cerchia con il codice invito.
#define BLISTRA_EMAIL     "scatoletta@esempio.it"
#define BLISTRA_PASSWORD  "password-dell-account-scatoletta"
// In Blistra: Cerchia > Scatoletta > Imposta > "Dati per il programma".
#define BLISTRA_CERCHIA   "ID-DELLA-CERCHIA"
#define BLISTRA_SCATOLA   "ID-DELLA-SCATOLETTA"
#define FIREBASE_API_KEY  "LA-TUA-API-KEY"
#define FIREBASE_PROGETTO "blistra-64e03"

// ---- Orari: fino a 4 dosi al giorno (usati senza Blistra, o finche' Blistra non risponde) ----
// Scomparti: 1 = lunedi' dose 1, 2 = lunedi' dose 2, 3 = lunedi' dose 3, 4 = lunedi' dose 4, 5 = martedi' dose 1 ... 28 = domenica dose 4.
// Lascia "" per le dosi che non servono: i loro scomparti restano vuoti.
#define ORA_DOSE_1      "08:00"
#define ORA_DOSE_2      "13:00"
#define ORA_DOSE_3      "17:00"
#define ORA_DOSE_4      "21:00"
#define MINUTI_DI_ATTESA 90       // poi la dose e' "non presa" e la scatoletta torna a riposo
#define FUSO_ORARIO     "CET-1CEST,M3.5.0,M10.5.0/3"

// ---- Piedini (vedi lo schema nelle schede tecniche) -------------------------------
#define PIN_MOTORE_1    16        // ULN2003 IN1..IN4
#define PIN_MOTORE_2    17
#define PIN_MOTORE_3    18
#define PIN_MOTORE_4    19
#define PIN_HX711_DOUT  21        // cella di carico
#define PIN_HX711_SCK   22
#define PIN_VIBRO       13        // gate del MOSFET del motorino vibrante
#define PIN_HALL_ZERO   25        // sensore di Hall sotto il mozzo
#define PIN_HALL_SPORT  26        // sensore di Hall dello sportello
#define PIN_CICALINO    27
#define PIN_LED         23
#define PIN_PULSANTE    32

// ---- Meccanica -------------------------------------------------------------------
#define SPICCHI          29       // 28 scomparti + 1 di riposo
#define PASSI_PER_GIRO   4076.0   // 28BYJ-48 a mezzi passi (alcuni esemplari: 4096)
#define DIREZIONE        1        // -1 se il carosello gira al contrario (deve salire la rampa)
#define MICROSECONDI_PASSO 1300
#define PASSI_DOPO_ZERO  40       // passi tra "il sensore vede il magnete" e "scomparto di riposo centrato sul ripiano"

// ---- Pesatura e vibrazione ------------------------------------------------------------
#define VIBRA_MS         3000     // quanto vibra la piastra a ogni tentativo
#define VIBRA_FORZA      255      // 0-255 (PWM sul motorino)
#define TENTATIVI_VIBRA  3
#define SOGLIA_VUOTA_MG  25       // sotto questo peso la piastra e' "vuota" (le minicompresse da 2 mm pesano circa 10 mg!)
#define TOLLERANZA_PCT   15       // carico giusto se il peso e' entro +-15% di quello atteso
#define TOLLERANZA_MG    40       // ...o entro +-40 mg
