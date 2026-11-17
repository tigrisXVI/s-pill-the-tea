"""I dieci compiti di ricerca per il Message Batches API (rapporto R&D v0.9, punto 9 del brief).
I compiti 1-9 sono indipendenti e vanno in un unico batch; il 10 (conclusioni integrate) parte dopo, con i risultati dei primi nove."""

MODELLO = "claude-opus-5-5"
MAX_TOKENS = 32000

SISTEMA = """You are part of an industrial R&D team validating Blistra v0.9, an open-source 3D-printed motorised pill dispenser for older adults.
Rules:
- Never invent measurements, material properties, test results or sources. If you cannot find a value, say so.
- Prefer manufacturer datasheets, pharmacopoeias, regulators and peer-reviewed papers over generic websites.
- Tag every value with one evidence class: MEAS (verified experimental data), DS (manufacturer datasheet or official specification), LIT (published literature), CALC (engineering calculation, show the formula and inputs), HYP (hypothesis requiring validation).
- Give a direct source URL for every DS and LIT value.
- Be critical: look for problems and contradictions, do not confirm the design by default.
- Do not treat this research as experimental validation.
Output: first a JSON object in a ```json block with this shape:
{"task": str, "findings": [{"topic": str, "claim": str, "value": str|null, "unit": str|null, "evidence": "MEAS|DS|LIT|CALC|HYP", "source_url": str|null, "confidence": "high|medium|low", "notes": str}], "tables": [{"title": str, "columns": [str], "rows": [[str]]}], "risks_for_blistra": [str], "open_questions": [str], "lab_tests_needed": [str]}
then a short Markdown summary (max 600 words)."""

COMPITI = [
 ("b01-tablet-database", "Tablet and capsule dimensional database",
  "Build a database of at least 60 commercially documented oral solid dosage forms commonly taken by adults over 65 (EU and US). Cover small/medium/large round tablets, oval and oblong tablets, flat and biconvex, scored and unscored, hard capsules sizes 000-5, soft capsules and unusual shapes. For each: product and manufacturer, length, width, THICKNESS, shape, surface (film-coated, uncoated, sugar-coated), mass if stated, dimensional tolerance if stated, source URL (SmPC section 3, DailyMed SPL 'size', manufacturer charts) and reliability. Thickness is the main gap in the existing data: prioritise sources that state it."),
 ("b02-polymer-properties", "Polymer material properties",
  "For PLA, PETG, PCTG, ABS, ASA, TPU 95A, PA6/PA12 (unfilled), PC and PP filaments for FDM: tensile strength and modulus in XY and Z, flexural properties, Charpy/Izod impact (XY and Z), HDT at 0.45 and 1.8 MPa, glass transition, coefficient of thermal expansion, water absorption (24 h and saturation), density, Shore hardness, printing temperature and enclosure needs. Use at least two manufacturers per material (Bambu Lab, Prusa, Polymaker, Ultimaker, BASF Forward AM, Fiberlogy) and report the spread between them."),
 ("b03-friction-contact", "Friction and mechanical interaction with tablets",
  "Find measured static and kinetic friction coefficients between pharmaceutical tablets/capsules (film-coated, uncoated, gelatin) and polymer or steel surfaces; between printed polymers and themselves (PETG on PETG, PLA on PLA) as a function of layer orientation and roughness; tablet breaking force and friability ranges; and the effect of humidity on tablet friction and static charge. Report test methods (pin-on-disk, inclined plane, ASTM D1894) so results can be compared."),
 ("b04-thermal-environment", "Thermal and environmental behaviour",
  "Quantify for PETG, ASA, PC and PP: creep under constant load at 23-40 C, dimensional change with humidity, UV ageing (yellowing, loss of impact), behaviour from -20 to +70 C, cyclic temperature effects. Also: realistic indoor and in-car temperature/humidity ranges in Europe, moisture uptake of common tablets at 60-75% RH (mass change %), silica gel adsorption capacity vs RH, and moisture permeation through printed PETG walls of 1.2-2 mm."),
 ("b05-fdm-accuracy", "FDM manufacturing accuracy",
  "Collect measured data on desktop FDM accuracy: hole and shaft deviation vs nominal size, dimensional tolerance classes (ISO 286 IT grades), elephant foot, shrinkage per material, effect of layer height, nozzle diameter, extrusion width, orientation, overhang angle and printer calibration; repeatability between prints and between printers; recommended clearances for running fits, snap fits and gears (module 1). Distinguish printer-dependent values from controlled studies."),
 ("b06-failure-modes", "Mechanical failure modes",
  "Using the attached v0.9 parameters, identify failure modes of: a 15-slot Geneva drive printed in PETG (pin, slot, locking disc), module-1 printed spur gears with 2 mm face width (10/24 teeth), cantilever snap fits 1.2 mm thick, 100 g bar load cells (overload, creep), living and pin hinges, PETG parts under drop impact. Give published fatigue and wear data for printed polymers and printed gears, and the calculation methods (Lewis, AGMA, Hertz) with appropriate safety factors for printed parts."),
 ("b07-cad-optimisation", "CAD geometry optimisation",
  "Review the attached v0.9 geometry (compartment 24x13 mm, exit 14x13 mm, tray 21.6x19.6 mm, refill opening 7.2x10 mm, axle 0.3 mm radial clearance, wiper gap 0.1 mm, flap clearance 0.05 mm). Propose geometric modifications. For each: the existing problem, the engineering principle, the expected improvement (quantified where possible), disadvantages, and how to validate it. Also propose ways to cut print time and material. Do not assume measurements that are not attached."),
 ("b08-material-comparison", "Material and manufacturing comparison",
  "Build a quantitative decision matrix for Blistra comparing PETG, PCTG, ASA, PC, PA12, PP and resin (SLA) for: pill-contact parts, the Geneva drive and gears, and the outer shell. Include cost per kg (EU 2026), printability on an open desktop printer, post-processing, cleanability, and alternatives to printing for a small series (injection moulding of the wheel, CNC, SLS PA12). State the weights you use and run a sensitivity analysis."),
 ("b09-standards-regulation", "Standards, certifications and regulation",
  "Map the regulatory and standards landscape for a home automatic pill dispenser in the EU (MDR qualification and class, EN/IEC standards for electrical safety and EMC of a 5 V USB device, radio equipment directive for Wi-Fi), the US (FDA product codes NXB and the Class II remote medication management system), and for materials in contact with medicines (USP <661.1>/<661.2>, Ph. Eur. 3.1/3.2, EU 10/2011 as analogy). Explain what a student prototype used in a family needs versus a product placed on the market. Give official URLs."),
]

FINALE = ("b10-integrated-conclusions", "Integrated engineering conclusions",
  "You receive the JSON results of nine independent research tasks about Blistra v0.9 plus the design parameters. Cross-check them: list contradictions between tasks and resolve them with the best evidence, or mark them unresolved. Then produce the integrated conclusions: how valid the current design is, its technical limits, the most promising materials, the geometric changes with concrete benefits (ranked by importance, cost and difficulty), and the laboratory tests needed for a reliable prototype. Keep every evidence tag and source from the inputs.")
