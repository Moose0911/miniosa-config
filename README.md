# 🐻 Mini Osa — Ender 3 V3 KE · Klipper Build & Tuning

![Printer](https://img.shields.io/badge/Printer-Ender_3_V3_KE-orange)
![Firmware](https://img.shields.io/badge/Firmware-Klipper_v0.13-red)
![Host](https://img.shields.io/badge/Host-BTT_Pad_7_·_CB1-blue)
![Max Accel](https://img.shields.io/badge/Max_Accel-18000_mm·s⁻²-brightgreen)
![Status](https://img.shields.io/badge/Status-en_producción-success)

> Una **Ender 3 V3 KE de ~US$220** llevada con mods de comunidad + trabajo custom a un nivel de *motion* y automatización que **roza máquinas 3-7× su precio** — sin perder calidad. Todo documentado: configs, mods, hallazgos de ingeniería y roadmap.

Este repositorio es el registro técnico completo de **"Mini Osa"**, una impresora de uso productivo. No es solo un backup de config: es la **historia de cómo se afinó**, con los datos y las decisiones detrás de cada cambio.

> 🔒 **Privacidad:** este repo no contiene credenciales ni datos privados (tokens, claves de acceso remoto, temas de notificación — todo redactado/excluido).

---

## Índice

- [Resumen rápido](#resumen-rápido)
- [Qué es y por qué](#qué-es-y-por-qué)
- [De fábrica a ahora](#de-fábrica-a-ahora)
- [Mods de hardware](#mods-de-hardware)
- [Stack de software](#stack-de-software)
- [Calibración y tuning (las historias)](#calibración-y-tuning-las-historias)
- [Perfiles de impresión](#perfiles-de-impresión)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Roadmap](#roadmap)
- [Créditos](#créditos)
- [Comparativas vs otras impresoras](#comparativas-vs-otras-impresoras)
- [Licencia y aviso](#licencia-y-aviso)

---

## Resumen rápido

| | |
|---|---|
| **Modelo base** | Creality Ender 3 V3 KE (bedslinger, direct drive) |
| **Volumen** | 220 × 220 × 240 mm |
| **Cerebro / host** | BTT Pad 7 con módulo **CB1** (Allwinner H616, 1GB) |
| **Firmware** | **Klipper v0.13** mainline + Mainsail + KlipperScreen |
| **Aceleración** | **18.000 mm/s²** (stock KE: 8.000) — roadmap 24k |
| **Boquilla** | Unicorn endurecida, 0.4 / 0.6 mm |
| **Auto Z-offset** | **PRTouch (celda de carga HX711) portado a Klipper mainline** |
| **Input shaper** | X: 3hump_ei @ 99.8 Hz · Y: mzv @ 32.4 Hz |
| **Acceso remoto** | OctoEverywhere (+ detección de fallas por IA) · Mobileraker |
| **Respaldo** | config versionada en Git |

---

## Qué es y por qué

Mini Osa es una Ender 3 V3 KE de **uso laboral** (piezas para señalética). El objetivo del build no fue "la más rápida del mundo", sino una máquina **rápida, fiable y automatizada** que produzca sin babysitting y mantenga calidad — exprimiendo una plataforma económica con mods de comunidad y trabajo custom donde hizo falta.

La filosofía de tuning fue siempre **medir, no adivinar**: cada número de este repo salió de una prueba en vivo (barridos de velocidad, curvas de fuerza de la celda de carga, telemetría térmica de los drivers, etc.), no de copiar valores de internet.

---

## De fábrica a ahora

| Aspecto | De fábrica (stock) | **Mini Osa (actual)** |
|---------|--------------------|------------------------|
| **Aceleración** | 8.000 mm/s² | **18.000 mm/s²** (+125%) |
| **Corriente driver Y** | 0.75 A | **0.80 A** (validada contra sobrecalentamiento) |
| **Masa del eje Y** | carro stock | **−400 g** (carro ASA custom + rieles lineales) |
| **Firmware / host** | Creality (fork de Klipper / Nebula) | **Klipper mainline en BTT Pad 7 + suite de mods** |
| **Auto Z-offset** | strain-gauge stock (cerrado) | **PRTouch HX711 portado a Klipper + BLTouch para malla** |
| **Nivelación** | auto-level | **trama a 0.011 mm + malla 7×7 cacheada por temperatura** |
| **Refrigeración** | ventilador stock | **FatBurner dual 5015 + 4020 dedicado** |
| **Acceso/monitoreo** | LAN básico | **remoto + IA + push al teléfono + timelapse** |

---

## Mods de hardware

| Mod | Detalle |
|-----|---------|
| **Hotend Unicorn** | Mod oficial Creality + boquilla Unicorn reforzada (acero endurecido), 0.4 y 0.6 mm |
| **Cooling FatBurner** | Shroud dual 5015 24V + ventilador 4020 dedicado al hotend |
| **Rieles lineales eje Y** | Reemplazo del carro Y stock |
| **Carriage Y en ASA** | Pieza custom que unifica carros + placa de aluminio → **−400 g de masa en Y** |
| **Refuerzo eje Z** | Pieza en PETG |
| **Frame braces** | Stiffener arms (PETG) para rigidez del marco |
| **Cepillo limpia-boquilla** | Mod de Printables + macro `WIPE_NOZZLE` automática |
| **PRTouch (celda de carga HX711)** | Auto Z-offset usando la boquilla como sonda — *ver tuning* |
| **BLTouch** | Probe original Creality (para la malla) |

---

## Stack de software

**Núcleo:** Klipper v0.13 · Mainsail (tema Frosted Gray) · KlipperScreen (tema simple-red)

**Suite de mods:**
- 🟢 **KAMP** — malla adaptativa + purga de línea
- 🟢 **Shake&Tune** — análisis de input shaper
- 🟢 **Spoolman** — gestión de filamento
- 🟢 **TMC Autotune** — optimización del chopper de los drivers (X/Y/Z)
- 🟢 **Timelapse** (moonraker-timelapse + crowsnest)
- 🟢 **OctoEverywhere** — acceso remoto + detección de fallas por IA
- 🟢 **Mobileraker + Companion** — app móvil con notificaciones push
- 🟢 **ntfy** — avisos de inicio / fin / falla
- 🟢 **gcode_shell_command** — botón "Backup ahora" en Mainsail
- 🟢 **Cola de impresión** (Moonraker job_queue)
- 🟢 **Respaldo de config versionado en Git**

---

## Calibración y tuning (las historias)

Esta es la parte interesante: no *qué* valores, sino *por qué* y *cómo se descubrieron*.

### 🎚️ Input shaper — la masa no era el problema
Se quitaron **−400 g** del eje Y (carro custom + rieles) esperando subir la frecuencia de resonancia. **No subió.** Eso demostró que la resonancia del eje Y está dominada por la **rigidez del marco y la correa**, no por la masa de la chapa. El beneficio del adelgazamiento fue **menos inercia → más aceleración** (que sí se aprovechó), no un cambio de frecuencia.
- **X:** `3hump_ei @ 99.8 Hz` (eje liviano) · **Y:** `mzv @ 32.4 Hz`

### 🔥 Aceleración — el cuello no era el motor, era el *driver*
La saga más interesante del build. Barridos de velocidad mostraron que el eje Y fallaba a alta aceleración… pero **el motor estaba frío**. El que se calentaba era el **chip TMC2208** (calor I²R por la **corriente**, no por la aceleración). A 0.95 A el driver cruzaba 120 °C → **OTPW** (sobretemperatura) ya en la primera capa.

| Punto | max_accel | Nota |
|-------|-----------|------|
| **Stock (Creality KE)** | 8.000 mm/s² | spec de fábrica |
| **Tuning previo** | 12.000 mm/s² | había llegado a 15k, bajó por seguridad |
| **Actual** | **18.000 mm/s²** | horneado a 0.80 A — **térmicamente sostenible** |
| **Roadmap** | 24.000 mm/s² | requiere mod de refrigeración del driver (0.95 A) |

Conclusión: 18k es el techo **sostenible** con la refrigeración actual. Para 24k hay que disipar el driver (en el roadmap). Se agregó un monitor (`driver_temp_watch`) que avisa OTPW en pantalla.

### 🎯 PRTouch — celda de carga portada a Klipper mainline
La KE stock tiene auto-nivelación por celda de carga, pero **cerrada** (firmware Creality). Se **portó el sistema a Klipper mainline**: un módulo `hx711s.py` propio (sin binarios `.so`) que usa la **boquilla como sonda** vía una celda de carga HX711. Mide 2 puntos, promedia, cachea y aplica el offset como valor **absoluto** (`SET_GCODE_OFFSET Z=`).
- **Bug resuelto #1:** el offset se acumulaba por print (era relativo) → se pasó a absoluto.
- **Bug resuelto #2:** la malla y el offset se contaban **doble** → arreglado con `zero_reference_position`.
- El signo del offset se validó con una **curva de fuerza** de la galga (el umbral de contacto hunde ~0.11 mm bajo la superficie real).

### 📐 Malla y nivelación
- Trama de cama nivelada a mano a **0.011 mm** de spread (desde 0.234).
- Malla full-bed **7×7** persistida + cacheada (recalibra cada 10 prints o si la temp de cama cambia >5 °C). La cama es un cuenco cóncavo suave (~0.30 mm).

### 🧩 Otros hallazgos documentados
- **Flow-limited:** a 0.6 mm los prints los limita el **MVS del filamento**, no las velocidades del slicer. La "500 mm/s" de fábrica es teórica; en la práctica imprime ~57-61 mm/s con el material calibrado.
- **Cámara a 0 fps:** era **contención de bus USB** (la cámara y el MCU comparten hub) — no CPU. Mitigado con resolución + buffers de captura.
- **Lag de KlipperScreen:** **presión de RAM** (la placa de 1GB corre dos impresoras + toda la suite). Mitigado con `swappiness` + governor `performance`.
- **Gotcha de Klipper:** una macro no puede llamarse con patrón letra+dígito (ej. `_G28_…`) — el parser la trunca. (Aprendido a la mala.)

---

## Perfiles de impresión

Perfiles de OrcaSlicer afinados para **0.4 mm y 0.6 mm** (proceso + filamento), con: generador de paredes Arachne, *scarf seam*, `arc_fitting`, velocidades de overhang, *exclude objects*, `travel_acceleration 18000`, etc. Filamentos calibrados al milímetro (Pressure Advance, flow ratio, MVS) para ASA, CR-PETG y PLA-MMLA.

---

## Estructura del repositorio

```
README.md                       → este documento
mods/
  hx711s.py                     → módulo PRTouch (celda de carga) para Klipper
printer_data/config/
  printer.cfg                   → config principal (kinematics, TMC, probe, input shaper)
  gcode_macro.cfg               → macros (START_PRINT, WIPE_NOZZLE, G28, PRTOUCH_*, BACKUP_AHORA)
  tmc_autotune.cfg              → TMC Autotune
  ADXL345.cfg                   → acelerómetro + Shake&Tune
  KAMP_Settings.cfg             → malla adaptativa + purga
  moonraker.conf                → Moonraker (notificaciones, spoolman, update_manager)
  variables.cfg                 → estado de calibración persistido
  crowsnest.conf / KlipperScreen.conf / ...
```

> 💡 Si solo te interesan los archivos: todo lo importante está en `printer_data/config/` y `mods/`. Las comparativas con otras impresoras están al **final** para no estorbar.

---

## Limitaciones conocidas

- **Techo térmico del driver Y** a 0.80 A / 18k (sin mod de refrigeración).
- **Flow-limited** a 0.6 mm (lo limita el hotend/boquilla, no la mecánica).
- Resonancia del eje Y limitada por rigidez de marco/correa (no por masa).
- Extrusor sin UART (corriente fija, sin telemetría TMC).
- Es una **bedslinger económica**: sin encerramiento, sin multimaterial nativo, RAM justa en la placa de 1GB.

---

## Roadmap

- [ ] **Mod de refrigeración del driver Y** (disipadores + cinta térmica) → desbloquear **24.000 mm/s²** a 0.95 A.
- [ ] **Boquilla de alto flujo** (E3D × Creality High-Flow "Unicorn", ~52 mm³/s) → subir el MVS para prints más rápidos.
- [ ] **Upgrade del cerebro** de la Pad 7: CB1 (1GB) → **CB2 (2GB)** o **CM4 (4/8GB)** para más RAM/fluidez.
- [ ] Acelerómetro permanente en el cabezal (evitar el reconexión del ADXL).
- [ ] Validar 18k / 0.80 A en print largo con cama caliente sostenida.

---

## Créditos

Construido sobre el trabajo de la comunidad:
[Klipper](https://www.klipper3d.org/) · [Mainsail](https://docs.mainsail.xyz/) · [KlipperScreen](https://klipperscreen.readthedocs.io/) · [KAMP](https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging) · [Shake&Tune](https://github.com/Frix-x/klippain-shaketune) · [Spoolman](https://github.com/Donkie/Spoolman) · [klipper-backup](https://github.com/Staubgeborener/klipper-backup) · [klipper_tmc_autotune](https://github.com/andrewmcgr/klipper_tmc_autotune) · [OctoEverywhere](https://octoeverywhere.com/) · [Mobileraker](https://github.com/Clon1998/mobileraker) · FatBurner shroud · temas de 01Felice y Frosted Gray.

---

## Comparativas vs otras impresoras

> ⚠️ **Leer con criterio.** Las aceleraciones son cifras **de fábrica/anunciadas**, y **la aceleración NO equivale a velocidad real**: casi todas estas máquinas crucean a ~250-300 mm/s para mantener calidad, y los prints suelen estar *flow-limited*. Mini Osa es una **bedslinger económica afinada** que compite en *motion* con máquinas mucho más caras — pero esas ganan en **comodidad, fiabilidad, encerramiento, multimaterial y soporte**. Esto es una historia de *"rinde por encima de su precio"*, no de *"es mejor que una Bambu"*.

### Segmento (bedslingers económicas, ~US$220-400)

| Impresora | Tipo | Accel (spec) | Vel. máx (spec) | Precio aprox. | Notas |
|-----------|------|-------------|-----------------|---------------|-------|
| Ender 3 V3 KE *(stock)* | Bedslinger | 8.000 mm/s² | 500 mm/s | ~US$220 | La base de este build |
| **🐻 Mini Osa *(este build)*** | **Bedslinger** | **18.000 mm/s²** | **500 mm/s** | **~US$220 + mods** | **KE afinada + custom** |
| Sovol SV07 | Bedslinger (Klipper) | ~12.000 mm/s² | 500 mm/s | ~US$340 | Klipper de fábrica |
| Bambu Lab A1 | Bedslinger | ~10.000 mm/s² | 500 mm/s | ~US$320-400 | Plug-and-play, AMS lite |

### Superiores (CoreXY / premium, ~US$550-1.500)

| Impresora | Tipo | Accel (spec) | Vel. máx (spec) | Precio aprox. | Notas |
|-----------|------|-------------|-----------------|---------------|-------|
| Bambu Lab P1S | CoreXY (cerrada) | ~20.000 mm/s² | 500 mm/s | ~US$550-700 | Encerrada, AMS opcional |
| Bambu Lab X1C | CoreXY (cerrada) | ~20.000 mm/s² | 500 mm/s | ~US$1.000-1.300 | Lidar, sensores, AMS |
| Prusa MK4S | Bedslinger | ~7.000 real (perfiles conservadores) | — | ~US$800-1.100 | Calidad y soporte de referencia |
| Voron 2.4 *(DIY)* | CoreXY | 20.000-100.000+ mm/s² | — | ~US$1.000-1.500 | DIY, el techo de motion |

**Lectura honesta:** Mini Osa, a **18.000 mm/s²** (24k en roadmap), iguala o supera en aceleración a casi todo el segmento e incluso roza a CoreXY que cuestan **3-7× más** — un logro notable para una bedslinger de US$220. Pero seamos justos: una P1S/X1C te da encerramiento, multimaterial, fiabilidad llave-en-mano y silencio que esta máquina no tiene. El valor de Mini Osa no es "ganarle a una Bambu", sino **demostrar cuánto rinde una plataforma barata bien entendida y bien afinada**.

> *Nota: las cifras "600 mm/s / 20.000 mm/s²" que a veces se ven asociadas a "Ender 3 V3" corresponden a la **Ender 3 V3** (CoreXZ), un modelo distinto y más caro — no a la **V3 KE**, que es 500 mm/s / 8.000 mm/s² de fábrica.*

### 💸 La cuenta: ¿fue rentable? (spoiler: no 😅)

> *Estimación aproximada en contexto de **precios uruguayos** (ajustá con tus números reales — los precios en Uruguay varían mucho con impuestos/importación).*

| Ítem | Aprox. (UY) |
|------|------------|
| Ender 3 V3 KE (base) | ~US$300-400 |
| BTT Pad 7 + CB1 (cerebro + pantalla) | ~US$150-220 |
| Mod hotend Unicorn + boquillas endurecidas | ~US$40-70 |
| FatBurner + ventiladores 5015/4020 | ~US$30-50 |
| Rieles lineales eje Y + carro custom | ~US$40-80 |
| BLTouch | ~US$30-50 |
| Celda de carga HX711 + ADXL345 (×2) | ~US$25-40 |
| Refuerzos, braces, piezas impresas + filamento | ~US$30-60 |
| Correas, PTFE, tornillería, conectores, varios | ~US$40-70 |
| **Subtotal en partes** | **~US$700-1.000** |
| Upgrades ya planeados (CM4 + boquilla alto flujo) | +~US$200-300 |
| Envíos, intentos fallidos, filamento de pruebas | 🤷 *(suman)* |
| Horas de ingeniería y tuning | *incontables* 🫠 |

**El remate:** una **Creality K2 Plus Combo + CFS** — CoreXY **cerrada**, 350³, multicolor (4-16 colores con RFID), cofre calefaccionado, cámara — cuesta **US$1.499** (precio US; en Uruguay, bastante más). Sumando la impresora + el Pad 7 + todos los mods + los upgrades planeados + (sobre todo) las **horas**, Mini Osa terminó **en el mismo barrio de precio** que esa máquina muy superior y llave-en-mano.

**Moraleja honesta:** si el objetivo fuera puramente económico, **la jugada racional habría sido comprar la K2 Plus Combo.** Pero modear una KE no se hace por rentabilidad a corto plazo — se hace por **aprender, entender la máquina a fondo y el gusto de exprimirla hasta el último mm/s²**. Ese aprendizaje (y este repo que documenta el viaje) es el verdadero retorno. 🐻

---

## Licencia y aviso

Configuración y documentación compartidas **tal cual**, con fines educativos y de referencia para la comunidad. Sin garantía: aplicá cualquier valor bajo tu propio criterio y riesgo — cada impresora es distinta.

*Documentación generada y mantenida con asistencia de Claude. Mini Osa sigue evolucionando; este README se actualiza con cada mejora.* 🐻
