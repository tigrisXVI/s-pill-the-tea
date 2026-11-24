S-PILL THE TEA v0.5 - ESP32 PROGRAM
(prototype: checked on the computer only, never tested on a real board)

1. Arduino IDE 2 -> Boards Manager: "esp32" by Espressif (version 3.x) -> board "ESP32 Dev Module".
2. Library Manager: "ArduinoJson" by Benoit Blanchon (version 7), "U8g2" (display), "Adafruit NeoPixel" (lights),
   "ESP32Servo" (door). The load cell (HX711) is read directly by the program.
   No display, lights or servo? Set USA_DISPLAY, USA_LUCI or USA_SERVO to 0 in config.h.
3. Copy spill_the_tea/config.example.h to spill_the_tea/config.h, open it and enter your Wi-Fi, dose times (up to 4)
   and, if you use Blistra, your family circle's details.
   DO NOT publish config.h once you have written your passwords in it.
4. Upload the program and open the Serial Monitor at 115200 baud.

First calibration (once only, with the lid removed):
- command z : the carousel looks for its home position. If it stops with the rest compartment NOT centred on the shelf,
  change PASSI_DOPO_ZERO in config.h.
- command t : with the shelf empty, sets the tare.
- command c7.5 : place a 1 euro coin (7.5 g) on the shelf and type c7.5. This saves the scale factor.
- command s : checks that the weight reading is correct.
- command v : tests the vibration.
- commands o / x : open and close the door with the servo. Adjust SERVO_CHIUSO and SERVO_APERTO in config.h:
  at rest the lever must sit just below the door's ledge, without touching it.
Tip: on the HX711 module, set the RATE jumper to 80 samples per second (faster).

Everyday use:
- When a dose is due, the box chimes, the light bar flashes yellow and the display reads "It's time".
- Short press of the big button: the servo lifts the door, the shelf vibrates and the pills fall into the cup.
  After 20 seconds (or another press of the button) the lever drops and the door closes by itself.
- The door can also be lifted by hand: the box dispenses all the same.
- Long press while waiting: silence for 30 seconds.
- Long press at rest: load check (weighs the 28 compartments one by one, door closed, about 2 minutes).
- The carousel never turns while the door is open.
- Power: panel-mount USB-C socket (right side) -> switch -> 5V pin of the ESP32.
  The servo must be powered from 5 V, not 3.3 V. The hole at the back is only for programming the ESP32 with a cable.

Compartments: 1-4 Monday (doses 1, 2, 3, 4), 5-8 Tuesday, ... 25-28 Sunday. Compartment 0 is the rest position and stays empty.

Known limitations of v0.3
- A 2 mm mini-tablet weighs about 10 mg: the scale cannot reliably tell it apart from an empty shelf.
- The scale tells you the pills have FALLEN into the cup, not that the person has swallowed them.
- If a dose is not taken, the pills go back into their compartment and stay there.
- The connection to Blistra is encrypted but does not yet verify the certificate (to be added before any real use).
