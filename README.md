# Scatoletta Blistra

*The little box that remembers, so tired hands don't have to.*

> *Scatoletta* is Italian for "little box". Blistra is the family app it belongs to.

Every morning, in kitchens everywhere, someone sits down in front of a row of blister packs and loses a small, quiet battle. The foil will not tear. A pill slips through fingers stiffened by arthritis and rolls beneath the table. A lid refuses to open; a Tuesday compartment is mistaken for a Wednesday one; the noon dose is simply forgotten somewhere between lunch and the evening news. None of it makes headlines. All of it matters.

**Scatoletta Blistra is an open-source, motorised pill box built to end that battle gently.**

When the hour comes, it chimes, glows, and writes it on its screen: *It's time.* One press of a large, round button — the kind you could find in the dark — and the pills for that moment, and only those, fall into a small cup that slides out and rests in the palm of a hand. No foil to pierce. No tiny lids to pry open. No guessing which day it is.

On their way out, the pills cross a scale. The box weighs every dose, so it knows whether the right amount really left the wheel; if something is wrong, it says so instead of staying silent. And if the family wishes, it tells the [Blistra app](https://tigrisxvi.github.io/blistra/) that the morning dose has been taken — or, more importantly, that it hasn't.

It is made for the people we owe the most to: older adults, people living with arthritis or tremor, anyone whose hands have grown weaker than their will to stay independent.

![The box, closed](docs/immagini/v5_chiusa.png)

**Interactive 3D model:** https://tigrisxvi.github.io/scatoletta-blistra/ (English and Italian)

**Blistra app:** https://tigrisxvi.github.io/blistra/ (try it without an account in demo mode)

**Status: prototype v0.5, designed and verified on the computer only. It has not yet been printed or tested on real hardware.**

> ⚠️ This is not a certified medical device. Do not use it as the only reminder for important medication. Anyone who builds it does so at their own risk.

## What it believes in

- **Made for tired hands.** Every choice starts from a person who can no longer press out a blister: one big button, a cup you can hold, no fine movements required.
- **Honest about what it knows.** The scale can tell that the pills *fell*; it cannot tell that they were *swallowed*. The box never pretends otherwise.
- **Open, all the way down.** Every model, every line of firmware, every simulation is published and free to study, rebuild and improve. A good idea for the elderly should not sit behind a patent or a price tag.
- **Built from what is at hand.** Inexpensive hobby electronics, a single printing material, and parts rescued from old CD drives and hard disks: screws, magnets, limit switches, little LEDs given a second life.

### Why not just buy one?

Commercial carousel dispensers do exist. A typical wireless model sells for around €150, holds 28 compartments, sounds its alarms and locks with a metal key. They are good products — but they still ask the user to tip a tray of pills into an unsteady palm, and they cannot be opened, repaired or adapted by the people who use them. Scatoletta Blistra asks a different question: *what if the box did the hardest part itself, and anyone were free to build it?*

## New in v1.2: the real parts

v1.2 is v1.0 adapted to the components actually purchased: 28BYJ-48 stepper motors with ULN2003 drivers, an SG90 servo, a 0.96" OLED display, a single load cell, cassettes held in place by one M2.5 screw, and wheel homing with a small limit-switch button. Model in `cad/scatoletta_v12.py`, checks in `cad/controlli_v12.py` (all green), print files and hardware in [`v12/`](v12/LEGGIMI.md). Viewer: [3D model v1.2](https://tigrisxvi.github.io/scatoletta-blistra/modello-3d/v12.html).

## New in v1.0: fixes from the R&D report

v1.0 is v0.9 with the problems found in the [R&D report](rd/) corrected. Model in `cad/scatoletta_v10.py`; the checks in `cad/controlli_v10.py` all pass (no interference; Geneva drive, refilling, cabling and stability all OK). Print files in `v10/` (`v10/PARAMETRI_STAMPA.md`). Viewer: [3D model v1.0](https://tigrisxvi.github.io/scatoletta-blistra/modello-3d/v10.html).

| | Problem in v0.9 | Fix in v1.0 |
|---|---|---|
| I-1 | Top refilling lets only 5 pills out of 59 through | A narrow tray hanging from the upper load cell: two lever-operated floors that tilt to 42° when the lid opens and return with a small torsion spring. Pills up to 6.3 × 12 × 16.7 mm now pass: 36 out of 55 (previously 5) |
| I-2 | Printed axle with 0.3 mm of play: the wiper strips touch the ring (93% probability) | 6 × 16 mm steel pin in the cassette, wheel bore reamed to 6.0 H7; wiper strips at 0.3 mm |
| I-3 | With the motor stalled, pinion teeth reach 36–83 MPa | Current limit in the firmware (`firmware/v10/limite_coppia.h`): 10 MPa maximum; steel Geneva-drive pin |
| I-4 | A finger on the tray can break the 100 g load cells | Stops under the free ends of both cells, at 0.5 mm |
| I-5 | A dose of 5 medicines covers 119% of the weighing tray | 30 × 24 mm tray (previously 24 × 22), 6 mm walls |
| I-6, I-12 | 0.05 mm lids, 0.76 mm wiper strips and 1 mm latches: too fine to print | 1.6 mm single-layer (0.2) lids set off from the dividers, 1.2 mm wiper strips, 1.2 mm latches, steel-wire hinges |
| I-7, I-13 | The box cannot tell whether a pill fits, or whether it may be loaded at all | App 3.4.1: pill dimensions, a list of medicines that must not be loaded (dabigatran), a warning for moisture-sensitive ones |
| I-8, I-10, I-11, I-14 | Generic print settings | Natural PETG and a steel nozzle for parts in contact with pills; shell in ASA or PC if it sits in the sun; base with 2 walls; PETG of at least 45 MPa |
| I-9, I-15 | Silica gel saturates sooner than expected | AHT20 humidity sensor under the roof (`firmware/v10/umidita.h`) and fresh gel at every refill, at least every 7 days |

The base is 2 mm wider (110 mm) to keep more than 40 degrees of sideways stability with the new parts.

## New in v0.9

- **Geneva drive (Maltese cross).** The mechanism of old film projectors and clocks replaces the ring gear and pinion. Behind each wheel there are 15 slots, one under each divider. The motor turns a 24-tooth gear carrying a pin: on every revolution the pin enters a slot and advances the wheel by exactly one compartment (24 degrees). For the rest of the revolution a locking disc holds the wheel still, even without power and even if someone tries to turn it by hand. `cad/croce_check.py` simulates a full revolution of the gear: no collisions, exactly 24.0 degrees, wheel locked at rest. The gear's pin is a screw salvaged from a hard disk.
- **Refilling from the top, weighed on the way in.** In the front of the roof there are two small lids. The pills for one compartment drop onto a tray hanging from a second load cell (channel B of the same HX711), which weighs them. When the lid closes, its finger tilts the tray by 30–36 degrees and the pills slide down the chute into the upper front compartment (54 degrees). No extra motors. A hard-disk screw driven into the keel keeps the tray level. `cad/ricarica_check.py` checks the movement.
- **In → out.** On the way out, the lower scale weighs the dose again: they are the same pills, so they must weigh the same. In simulated tests (`firmware/test`) it catches 100% of wrong compartments, even with a 40 mg pill, with no false alarms.
- **All in PETG**, a single material.

## Under test: v0.8, two wheels and two motors (the most compact)

The wheels are driven by a gear on their rim, with the N20 motor tucked into the corner that the round wheel leaves free. Doses fall onto a **weighing tray** (100 g load cell) that a micro servo opens only if the weight matches the one set in the app; beneath it sits the cup, in an open alcove like that of a coffee machine, with a magnet in its base and a Hall sensor in the foot. Dark body and a coloured, finely ribbed cap with rounded edges; a 21 mm round button on the cap. At the front, behind a grille, a 20 mm speaker with a MAX98357A amplifier: it sounds the alarm and can say "It's time for your pills". Wheels with a true ring gear (module 1) and 20-tooth pinions. The upper wires run under the roof and drop through a channel in the central wall; power comes from a USB-C socket at the back; the ESP32-S3's Wi-Fi antenna is 15 mm from the nearest metal. The viewer simulates the pills with real physics (Rapier).

**3D printing:** every part in a single material, PETG with a 0.4 mm nozzle; 1.2 mm walls (3 perimeters), 0.3–0.4 mm clearances for moving parts, module-1 teeth. `cad/controlli_v8.py` picks for each part the print orientation with the fewest overhangs (the STLs in `v8/2m/stl/stampa/` are already oriented this way): supports are needed mainly under the roof of the body's alcove. The base is printed upside down; the iron plate is glued in from below, followed by four rubber feet.

**Cassettes and lids:** the cassette (the ring around the wheel) is printed opaque and open at the front. Each compartment of the wheel has its own transparent lid (clear PETG), with a hinge near the hub (pin: a piece of 0.8 mm wire), two latches that snap onto the ramps of the dividers and a tab to open it with a finger. The lids turn with the wheel: the pills never rub against stationary parts, and refilling happens one compartment at a time.

**Wheel position:** each wheel has a 3 × 1 mm magnet in its ring gear, under the closed compartment, and a Hall sensor (DRV5032) in the central wall, 1.7 mm away through the bottom of the cassette. The box homes itself at power-up and on every turn, and if a wheel skips a tooth it notices and withholds the dose. What the firmware must do: `firmware/v08_cosa_deve_fare.md`.

**Without power:** a DS3231 clock with a coin cell in the rear chamber; the dose and the wheel positions are saved to the ESP32's memory at every step. A dose missed because of a power cut is never released on its own afterwards.

**Humidity:** the hub of each wheel has a pocket for about 2 g of silica gel, closed by a slotted cap; 1.2 mm holes carry dry air into every compartment (pills cannot pass through them). The lids close directly on top of the dividers.

**App-controlled cassette lock:** for each cassette a tooth enters a notch in the flange and locks it; a micro servo hidden in the lower front corner, under the wheel, turns it a quarter of a turn. In the app's guided refill, the "Unlock cassettes" button releases the locks for 2 minutes; when the cassette goes back in (the wheel sensor sees the magnet again) the lock closes by itself. The checks verify that, when locked, the cassette cannot come out.

**Test pieces (before printing the whole box):** `cad/prove_v8.py` creates in `v8/2m/prove/`:
- *test 1, wheel segment*: a quarter of a wheel with 3 compartments, wiper strips, lids, and the piece of cassette with the outlet and axle. Put real pills (tiny ones too) into the compartments and turn back and forth 20 times: nothing should slip between wheel and ring, the compartment next to the outlet must not empty itself, and the wheel must turn with its wiper strips without forcing.
- *test 2, weighing tray*: tray, bracket and a base for the load cell. With the cell, an HX711 and an ESP32, weigh a 90 mg pill and a 12 mg pill 10 times each: this shows how precise the scale really is.

**Guided refill in the app:** in the Blistra app, choose the "v0.8" model for the box: the guided refill splits the compartments between the left cassette (odd numbers) and the right cassette (even numbers), showing the number printed on the hub and the pills to put in.

**Strength:** the upper part overhangs the cup's alcove and rests on the rear column. `cad/controlli_v8.py` computes the real cross-sections of the body: with someone pressing the button with 5 kg, the column works at about 1.2 MPa against 15 MPa of PETG inter-layer strength (12× safety factor); the 1.2 mm wall would buckle only at 4.1 MPa (3.4×); the top moves by 0.2 mm. The corners of the alcove have a 45° chamfer across the full width and two gussets at the sides.

**Small pills:** at the tip of each divider there is a PETG wiper strip that comes within 0.1 mm of the stationary ring without touching it (it press-fits in place and can be filed): nothing passes between wheel and ring, and each compartment stays closed until it reaches the outlet. The other gaps along the pills' path are 0.6 mm or less (wheel–ring 0.3, wheel–cover 0.3, cassette–funnel 0.6, funnel–tray 0.4, tray–bulkhead 0.6), so even a 3 × 1.6 mm pill cannot get stuck.

**Stability:** almost all the weight is in the base (10 cm wide), which holds a 104 × 76 × 6 mm iron plate (about 370 g out of 680). Centre of gravity 5.2 cm above the table: it tips over only when tilted 44° sideways, 50° forwards or 47° backwards. Underneath, four rubber feet.

1.2 mm walls, 1 mm cassettes. Body 10.5 × 5 × 20.4 cm (1.08 l), base 11.9 × 10 cm, one compartment 4.3 cm³. Model in `cad/scatoletta_v8.py`, checks in `cad/controlli_v8.py` (no interference), parts in `v8/2m/`, viewer: [3D model v0.8](https://tigrisxvi.github.io/scatoletta-blistra/modello-3d/v8.html). Not yet printed.

## Under test: v0.7 with two wheels

Two upright wheels holding 14 doses each, each with its own motor, in cassettes that slide out sideways. The compartment that reaches the bottom empties itself: no doors and no servos. Scale under the cup. **11 × 8 × 17.5 cm (1.5 litres), one third of v0.5.** Model in `cad/scatoletta_v7.py`, checks in `cad/controlli_v7.py`, parts in `v7/stl/`, viewer: [3D model v0.7](https://tigrisxvi.github.io/scatoletta-blistra/modello-3d/v7.html). Not yet printed or simulated.

## Under test: v0.6 on two levels

Two 14-compartment carousels stacked one above the other: the footprint is almost halved (about 18 × 12 cm instead of 24.5 × 17.5). Cone-shaped floors, two guillotine doors, scale under the cup. Model in `cad/scatoletta_v6.py`, checks in `cad/controlli_v6.py`, parts in `v6/stl/`, viewer: [3D model v0.6](https://tigrisxvi.github.io/scatoletta-blistra/modello-3d/v6.html). Not yet printed or simulated.

## What it looks like (v0.5)

- **A single rounded shell** hides the mechanism. On top sits a **jewellery-box lid**, coloured and hinged at the back: it opens for refilling.
- **At the front**, on a sloping band: a 1.3" display showing the time and the next dose, a large 30 mm button, and a line of light that shines through the plastic only when it switches on (yellow: it's time; white: take your pills; green: taken; red: needs checking; blue: verifying).
- **Below**, an alcove holding the removable **cup** into which the pills fall.
- **On the right side**, the power switch — recessed so it cannot be turned off by accident — and the USB-C socket.

## How it works inside

- **29 compartments** on a carousel: 4 doses a day (morning, lunch, afternoon, evening) for 7 days, plus one rest compartment that always stays empty.
- **Fixed ramp floor:** the floor rises in a helix and, under the outlet, becomes a flat shelf sloping outwards. The carousel's dividers float vertically in the hub and follow the ramp, so pills cannot get wedged.
- **Weighed, vibrating shelf:** under the outlet there is a plate on a load cell (HX711) with a tiny vibration motor. The vibration coaxes down even the tablets that friction would otherwise hold back; the weight confirms that the dose has left.
- **Motorised door:** when the button is pressed, a micro servo lifts the door by 35° with a lever, uncovering the opening in the wall. To close, the lever drops and the door falls shut under its own weight: it never pushes down, so it cannot pinch fingers. A Hall sensor prevents the carousel from turning while the door is open.
- **Chute:** the pills slide down at 40° and fall into the cup.
- **ESP32** with a 28BYJ-48 stepper motor and a buzzer. It can optionally connect to the Blistra web app.

Size: 245 × 175 × 103 mm (the shell fits a printer with a 256 mm bed).

v0.5 reuses the mechanism of v0.3 and v0.4 (`cad/scatoletta_v3.py`, `cad/scatoletta_v4.py`) and draws the exterior in `cad/scatoletta_v5.py`. The PDF datasheets still describe v0.3: carousel, ramp, plate and chute have not changed.

## What's in the project

| Folder | Contents |
|---|---|
| `cad/` | Parametric 3D model in Python (manifold3d + trimesh), electronics, screws and cables (`elettronica_v5.py`), interference checks, Blender renders, datasheets |
| `stl/stampa/` | Parts ready for 3D printing |
| `stl/assieme/` | Parts in their assembled position |
| `firmware/` | ESP32 program (Arduino IDE) and calibration instructions |
| `simulazioni/` | Physics simulation in Blender of the pills falling, with results |
| `docs/` | PDF datasheets (dimensions, sensors, wiring diagram), images and the 3D viewer (`docs/modello-3d/`, three.js under the MIT licence) |

## Simulations

Rigid-body simulation of v0.3 (Blender/Bullet) with a realistic friction of 0.35 and a 50 Hz, 0.6 mm vibration for 3 seconds, with tablets ranging from 2 mm mini-tablets up to one as large as an Augmentin:

- 238 doses out of 240 reached the bottom of the chute (the 2 misses were in the worst case, friction 0.5);
- 80 out of 80 with the exact v0.3 geometry. The ramp and the sloping part of the chute are the same in v0.5; the final drop into the cup (about 2 cm) was not simulated.

A simulation is no substitute for a real test: a printed prototype still has to be tried.

## Building it

1. Print the parts in `stl/stampa/` (PLA or PETG). Print the shell in white so the light can shine through; the lid in whatever colour you like.
2. Components: ESP32 DevKit, 28BYJ-48 motor with ULN2003 driver, 100 g load cell with HX711, 8×2 mm vibration motor with a MOSFET, 2 A3144 Hall sensors with magnets, buzzer, SG90 micro servo, 1.3" I2C OLED display (SH1106), 8-LED WS2812 strip, 30 mm low-profile arcade button, KCD11 rocker switch, panel-mount USB-C socket, 2 neodymium magnets (4×2 and 6×3 mm), 2 pins of 2 mm (or pieces of filament) for the door and lid hinges.
   The boards (ESP32, ULN2003, HX711, MOSFET) and the buzzer go in the compartment under the floor, stuck down with 3–4 mm double-sided foam tape; the wires pass through the three holes in the front wall. In the 3D viewer, "Show electronics" shows where everything goes.
3. Screws:

| Qty | Screw | Where |
|---|---|---|
| 4 | M3×14 socket head | floor onto the base |
| 2 + 2 nuts | M3×8 countersunk + M3 nuts | motor under the floor (head flush, under the hub) |
| 2 | M3×8 socket head | load cell onto the floor, from below |
| 2 | M3×6 low head (2 mm) | plate onto the load cell; the caps go on top, glued |
| 4 | M3×10 socket head | chute onto the base, from outside |
| 2 | M2×6 | USB-C socket on the side |
| 2 + 1 | M2 from the servo bag | servo onto its cradle, lever onto the horn |

4. Firmware: follow `firmware/LEGGIMI.txt` (English version: `firmware/README.txt`). Copy `config.example.h` to `config.h` and write your passwords there: `config.h` must never be published.

## Contributing

Print tests, photos, measurements, corrections and ideas are all welcome: open an issue or a pull request. If you build one for someone you love, we would love to hear how it went.

## Licences

- Hardware (3D models, STLs, datasheets): [CERN-OHL-S-2.0](LICENSES/CERN-OHL-S-2.0.txt)
- Software (firmware, CAD and simulation scripts): [MIT](LICENSES/MIT.txt)
- Documentation and images: [CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt)

© 2026 Giuseppe Vasco
