# 🐻 Mini Osa — Ender 3 V3 KE (build documentado con Klipper)

Documentación completa de **"Mini Osa"**, una **Creality Ender 3 V3 KE** modificada y afinada de punta a punta, corriendo **Klipper** sobre una **BTT Pad 7 (CB1)**. Este repo reúne los mods (hardware y software), la configuración, lo que se logró y el roadmap a futuro.

> ⚠️ **Nota de privacidad:** este repo NO incluye credenciales ni datos privados (tokens, claves de OctoEverywhere, temas de notificación, etc.). Solo configuración y mods publicables.

---

## 📋 Qué es

Una Ender 3 V3 KE de uso **productivo/laboral** (impresión de piezas para señalética y trabajo), llevada a un punto de **velocidad + fiabilidad + automatización** muy por encima del stock, sin perder calidad. Cerebro: **BTT Pad 7 con módulo CB1**, Klipper v0.13 + Mainsail + KlipperScreen.

---

## 🔧 Mods físicos (hardware)

| Mod | Detalle |
|-----|---------|
| **Hotend Unicorn** | Mod oficial Creality para boquillas Unicorn + boquilla reforzada (acero endurecido), 0.4mm y 0.6mm |
| **Cooling FatBurner** | Shroud dual 5015 24V + ventilador 4020 dedicado al hotend |
| **Guías lineales eje Y** | Reemplazo del carro Y stock por rieles lineales |
| **Carriage Y en ASA** | Pieza custom que unifica carros + placa de aluminio → **−400 g de masa en Y** |
| **Refuerzo eje Z** | Pieza impresa en PETG |
| **Frame braces** | Stiffener arms (PETG) para rigidez del marco |
| **Cepillo limpia-boquilla** | Mod de Printables + macro `WIPE_NOZZLE` automática |
| **Auto Z-offset por celda de carga** | Sistema PRTouch (HX711) — *ver abajo* |
| **Extrusor** | Sprite original dual-gear (direct drive) |
| **Probe** | BLTouch original Creality (malla) + nozzle-as-probe HX711 (Z-offset) |

---

## 💻 Stack de software / firmware

- **Klipper v0.13** + **Mainsail** (web) + **KlipperScreen** (pantalla táctil, tema `simple-red`)
- **Tema Mainsail:** Frosted Gray (negro alto contraste)
- **KAMP** — malla adaptativa + purga de línea
- **Shake&Tune** — análisis de input shaper
- **Spoolman** — gestión de bobinas
- **klipper-backup** — respaldo automático de config a GitHub (cada 4h + botón manual)
- **TMC Autotune** — optimización automática del chopper de los drivers (X/Y/Z)
- **Timelapse** (moonraker-timelapse + crowsnest)
- **OctoEverywhere** — acceso remoto + detección de fallas por IA
- **Mobileraker + Companion** — app móvil con notificaciones push
- **Notificaciones ntfy** — avisos de inicio/fin/falla de impresión
- **gcode_shell_command** — macro `BACKUP_AHORA` (botón de respaldo en Mainsail)
- **Cola de impresión** (Moonraker job_queue)

---

## 🎯 Logros y tuning

### Calibración mecánica
- **Trama de cama** nivelada a **0.011 mm** de spread (desde 0.234 mm).
- **Malla** full-bed 7×7 persistida + cacheada (recalibra cada 10 prints o si la temp de cama cambia >5 °C). La cama es un cuenco cóncavo suave (~0.30 mm).
- **Skew correction** activo.

### Input Shaper (ADXL345)
- **X:** `3hump_ei @ 99.8 Hz` (eje liviano)
- **Y:** `mzv @ 32.4 Hz` (resonancia dominada por rigidez de marco/correa, no por masa)

### Velocidad y aceleración
- **`max_accel: 18000`** (desde 12k stock) — techo travel **térmicamente sostenible**.
- Hallazgo clave: el cuello del eje Y **no es el motor, es el driver TMC2208** (calor por **corriente** I²R, no por aceleración). A 0.95A daba OTPW (>120 °C); se bakeó en **0.80A** estable. Para desbloquear 24k → mod de refrigeración del driver (roadmap).
- Insight: a 0.6mm los prints son **flow-limited** (los limita el MVS del filamento, no las velocidades del slicer).

### PRTouch — auto Z-offset por celda de carga (custom)
Sistema tipo Nebula Pad **portado a Klipper mainline**: módulo `hx711s.py` propio (sin binarios .so), usa la boquilla como sonda vía celda de carga HX711. Mide 2 puntos, promedia, cachea, y aplica el offset como valor **absoluto** (`SET_GCODE_OFFSET Z=`). Integrado en `START_PRINT`. Resuelto el problema de doble-conteo malla+offset vía `zero_reference_position`.

### Otros arreglos finos
- **`G28` centra la boquilla** (no el sensor) al terminar el homing.
- **TMC Autotune** con `motor: creality-42-34` — sin tocar las corrientes validadas; CoolStep reduce corriente bajo carga baja (driver más frío).
- Monitor de temperatura de driver (`driver_temp_watch`) que avisa OTPW en pantalla.

---

## 🖨️ Perfiles OrcaSlicer

Perfiles afinados para 0.4mm y 0.6mm (proceso + filamento), con: Arachne, scarf seam, `arc_fitting`, overhang speeds, exclude objects, `travel_acceleration 18000`, etc. Filamentos calibrados al milímetro (PA, flow, MVS) para ASA, CR-PETG y MMLA.

---

## ⚠️ Limitaciones conocidas

- **Techo térmico del driver Y** a 0.80A/18k (sin mod de refrigeración).
- **Flow-limited** a 0.6mm (limita la boquilla/hotend, no la mecánica).
- Resonancia del eje Y limitada por rigidez de marco/correa.
- Extrusor sin UART (corriente fija, sin telemetría TMC).

---

## 🚀 Roadmap / futuras actualizaciones

- [ ] **Mod de refrigeración del driver Y** (disipadores + cinta térmica) → desbloquear **24k de aceleración** a 0.95A.
- [ ] **Boquilla de alto flujo** (E3D × Creality High-Flow "Unicorn", ~52 mm³/s) → subir el MVS para prints más rápidos.
- [ ] **Upgrade del cerebro** de la Pad 7: CB1 (1GB) → **CB2 (2GB)** o **CM4 (4/8GB)** para más RAM/fluidez.
- [ ] Acelerómetro permanente en el cabezal (evitar el hot-plug del ADXL).
- [ ] Validar 18k/0.80A en print real largo con cama caliente sostenida.

---

## 📁 Estructura del repo

```
printer_data/config/   → configuración Klipper/Moonraker (sin secretos)
  printer.cfg          → config principal (kinematics, TMC, probe, input shaper)
  gcode_macro.cfg      → macros custom (START_PRINT, WIPE_NOZZLE, G28, BACKUP_AHORA, PRTOUCH_*)
  tmc_autotune.cfg     → TMC Autotune
  ADXL345.cfg          → acelerómetro + Shake&Tune
  KAMP_Settings.cfg    → malla adaptativa + purga
mods/                  → módulos custom (hx711s.py = PRTouch)
docs/                  → documentación extendida
```

---

## 🙏 Créditos

Construido sobre el trabajo de la comunidad: [Klipper](https://www.klipper3d.org/), [Mainsail](https://docs.mainsail.xyz/), [KlipperScreen](https://klipperscreen.readthedocs.io/), [KAMP](https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging), [Shake&Tune](https://github.com/Frix-x/klippain-shaketune), [Spoolman](https://github.com/Donkie/Spoolman), [klipper-backup](https://github.com/Staubgeborener/klipper-backup), [klipper_tmc_autotune](https://github.com/andrewmcgr/klipper_tmc_autotune), [OctoEverywhere](https://octoeverywhere.com/), [Mobileraker](https://github.com/Clon1998/mobileraker), FatBurner shroud, y los temas de 01Felice y Frosted Gray.

---

*Documentación generada y mantenida con asistencia de Claude. Mini Osa sigue evolucionando — este README se actualiza con cada mejora.* 🐻
