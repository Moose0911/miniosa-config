# hx711s.py — Creality KE/SE PRTouch load cell sensor
# Portado a Klipper v0.13.0+ — sin .so de Creality, sin modulos externos.
# Formatos MCU (firmware Creality GD32F303, oct-2023):
#   debug_hx711s  oid=%c arg[0]=%u arg[1]=%u arg[2]=%u arg[3]=%u
#   result_hx711s oid=%c vd=%c it=%c tr=%hu nt=%u v0=%i v1=%i v2=%i v3=%i
# Calibrado 2026-06-01: ruido ~600 cuentas, contacto ~-10000 cuentas (nozzle caliente 235C).
import time, math, logging

DEBUG_FMT  = 'debug_hx711s oid=%c arg[0]=%u arg[1]=%u arg[2]=%u arg[3]=%u'
RESULT_FMT = 'result_hx711s oid=%c vd=%c it=%c tr=%hu nt=%u v0=%i v1=%i v2=%i v3=%i'

class HX711S:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.s_count = config.getint('count', 1, 1, 4)
        self.base_avgs = [0, 0, 0, 0]
        self.all_vals = [[], [], [], []]
        self.need_wait = False
        self.pi_count = 0
        self.show_msg = False
        self.is_shutdown = True
        self.is_timeout = True
        self.s_clk_pin = []
        self.s_sdo_pin = []
        for i in range(self.s_count):
            self.s_clk_pin.append(config.get('sensor%d_clk_pin' % i,
                None if i == 0 else self.s_clk_pin[i-1]))
            self.s_sdo_pin.append(config.get('sensor%d_sdo_pin' % i,
                None if i == 0 else self.s_sdo_pin[i-1]))
        import mcu as mcu_module
        self.mcu = mcu_module.get_printer_mcu(self.printer, config.get('use_mcu', 'mcu'))
        self.oid = self.mcu.create_oid()
        self.query_cmd = None
        self._resp_wrappers = []
        self.mcu.register_config_callback(self._build_config)
        w1 = self.mcu.register_serial_response(
            self._handle_debug_hx711s, DEBUG_FMT, self.oid)
        w2 = self.mcu.register_serial_response(
            self._handle_result_hx711s, RESULT_FMT, self.oid)
        self._resp_wrappers = [w1, w2]
        self.printer.register_event_handler('klippy:mcu_identify', self._handle_mcu_identify)
        self.printer.register_event_handler('klippy:shutdown', self._handle_shutdown)
        self.printer.register_event_handler('klippy:disconnect', self._handle_disconnect)
        self.gcode.register_command('READ_HX711', self.cmd_READ_HX711,
            desc='Read HX711 raw values. C=count(10)')
        self.gcode.register_command('PRTOUCH_TARE', self.cmd_PRTOUCH_TARE,
            desc='Tare load cell baseline. C=samples(20)')
        self.gcode.register_command('PRTOUCH_READ_DELTA', self.cmd_PRTOUCH_READ_DELTA,
            desc='Read delta from tare. C=samples(10)')
        self.gcode.register_command('PRTOUCH_PROBE', self.cmd_PRTOUCH_PROBE,
            desc='Single-point Z probe. APPLY=1 saves result.')
        self.gcode.register_command('PRTOUCH_PROBE_MULTI', self.cmd_PRTOUCH_PROBE_MULTI,
            desc='Multi-point Z probe (like Creality Nebula Pad). NPOINTS=2 DIST=25 APPLY=1.')

    def _build_config(self):
        self.mcu.add_config_cmd(
            'config_hx711s oid=%d hx711_count=%d' % (self.oid, self.s_count))
        pins = self.printer.lookup_object('pins')
        for i in range(self.s_count):
            clk = pins.lookup_pin(self.s_clk_pin[i])
            sdo = pins.lookup_pin(self.s_sdo_pin[i])
            self.mcu.add_config_cmd(
                'add_hx711s oid=%d index=%d clk_pin=%s sdo_pin=%s' % (
                    self.oid, i, clk['pin'], sdo['pin']))
        cq = self.mcu.alloc_command_queue()
        self.query_cmd = self.mcu.lookup_command(
            'query_hx711s oid=%c times_read=%hu', cq=cq)

    def _handle_mcu_identify(self):
        self.is_shutdown = False
        self.is_timeout = False

    def _handle_debug_hx711s(self, params):
        self.gcode.respond_info('debug_hx711s: ' + str(params))

    def _handle_result_hx711s(self, params):
        while self.need_wait:
            self.delay_s(0.001)
        for i in range(self.s_count):
            key = 'v%d' % i
            if key in params:
                self.all_vals[i].append(params[key] - self.base_avgs[i])
        if self.show_msg:
            self.gcode.respond_info(
                'HX711 v0=%d delta=%.0f' % (
                params.get('v0', 0), params.get('v0', 0) - self.base_avgs[0]))
        for i in range(self.s_count):
            if self.pi_count > 0 and len(self.all_vals[i]) > self.pi_count:
                del self.all_vals[i][0]

    def _handle_shutdown(self):
        self.is_shutdown = True

    def _handle_disconnect(self):
        self.is_timeout = True

    def delay_s(self, secs):
        reactor = self.printer.get_reactor()
        if not self.printer.is_shutdown():
            reactor.pause(reactor.monotonic() + secs)

    def _read_samples(self, count, wait_s=None):
        if self.is_shutdown or self.is_timeout or self.query_cmd is None:
            return [[], [], [], []]
        self.all_vals = [[], [], [], []]
        self.pi_count = count
        self.show_msg = False
        self.query_cmd.send([self.oid, count])
        if wait_s is None:
            wait_s = count * 0.015 + 0.5
        deadline = self.printer.get_reactor().monotonic() + wait_s
        while len(self.all_vals[0]) < count:
            if self.printer.get_reactor().monotonic() > deadline:
                break
            self.delay_s(0.010)
        return self.get_vals()

    def _tare(self, count=20):
        self.base_avgs = [0, 0, 0, 0]
        vals = self._read_samples(count + 5, wait_s=(count + 5) * 0.015 + 1.0)
        for i in range(self.s_count):
            v = vals[i]
            if len(v) > 6:
                v = sorted(v)[2:-2]
            if v:
                self.base_avgs[i] = sum(v) / len(v)
        return list(self.base_avgs)

    def get_vals(self):
        self.need_wait = True
        result = [list(v) for v in self.all_vals]
        self.need_wait = False
        return result

    def read_base(self, cnt, reset_zero=True):
        base = self._tare(cnt)
        for j in range(self.s_count):
            self.gcode.respond_info('HX711 CH%d base=%.0f' % (j, base[j]))
        return base

    def _safe_lift(self, toolhead, lift_mm=2.0, speed=10.0):
        pos = list(toolhead.get_position())
        pos[2] += lift_mm
        toolhead.move(pos, speed)
        toolhead.wait_moves()

    # ── Núcleo del probe: tarea + 2 fases + retorno del Z de contacto ────────

    def _run_probe_at(self, toolhead, threshold, step, speed, min_z,
                      fast_dist, fast_step, fast_speed, tare_cnt, point_label=''):
        """
        Tara y sonda en la posición XY actual. Devuelve contact_z o None.
        NO levanta la boquilla al terminar — el caller debe hacerlo.
        """
        prefix = ('PRTouch [%s]' % point_label) if point_label else 'PRTouch'

        # Tare
        base = self._tare(tare_cnt)
        self.gcode.respond_info('%s: Base=%.0f T=%.0f  rapida %.1fmm@%.0fmm/s  fina %.2fmm@%.0fmm/s' % (
            prefix, base[0], threshold, fast_dist, fast_speed, step, speed))

        contact_z = None
        start_z = toolhead.get_position()[2]

        # Fase rapida
        if fast_dist > 0:
            fast_end_z = max(start_z - fast_dist, min_z + step * 3)
            fast_steps = int((start_z - fast_end_z) / fast_step) + 1
            for i in range(fast_steps):
                pos = list(toolhead.get_position())
                if pos[2] - fast_step < min_z:
                    break
                pos[2] -= fast_step
                toolhead.move(pos, fast_speed)
                toolhead.wait_moves()
                vals = self._read_samples(3, wait_s=0.08)
                if vals[0]:
                    avg_delta = sum(vals[0]) / len(vals[0])
                    self.gcode.respond_info('%s fast: Z=%.2f  delta=%.0f' % (
                        prefix, toolhead.get_position()[2], avg_delta))
                    if abs(avg_delta) > threshold:
                        contact_z = toolhead.get_position()[2]
                        self.gcode.respond_info('%s: CONTACTO (rapida) Z=%.4f  delta=%.0f' % (
                            prefix, contact_z, avg_delta))
                        break

        # Fase fina
        if contact_z is None:
            fine_steps = int((start_z + abs(min_z)) / step) + 1
            for i in range(fine_steps):
                pos = list(toolhead.get_position())
                if pos[2] - step < min_z:
                    break
                pos[2] -= step
                toolhead.move(pos, speed)
                toolhead.wait_moves()
                vals = self._read_samples(5, wait_s=0.15)
                if vals[0]:
                    avg_delta = sum(vals[0]) / len(vals[0])
                    if i % 5 == 0:
                        self.gcode.respond_info('%s fine: Z=%.3f  delta=%.0f' % (
                            prefix, toolhead.get_position()[2], avg_delta))
                    if abs(avg_delta) > threshold:
                        contact_z = toolhead.get_position()[2]
                        self.gcode.respond_info('%s: CONTACTO Z=%.4f  delta=%.0f' % (
                            prefix, contact_z, avg_delta))
                        break

        return contact_z

    def _move_to_probe_pos(self, toolhead, x, y, z=2.0):
        """Levanta a z, mueve a XY, sin cambiar E."""
        pos = list(toolhead.get_position())
        pos[2] = max(pos[2], z)
        toolhead.move(pos, 10.0)
        toolhead.wait_moves()
        pos[0] = x
        pos[1] = y
        toolhead.move(pos, 150.0)  # ~9000mm/min
        toolhead.wait_moves()
        pos[2] = z
        toolhead.move(pos, 10.0)
        toolhead.wait_moves()

    # ─────────────────────── GCODE commands ───────────────────────────────

    def cmd_READ_HX711(self, gcmd):
        if self.query_cmd is None:
            raise self.printer.command_error('HX711S: not ready')
        cnt = gcmd.get_int('C', 10, minval=1, maxval=200)
        saved = list(self.base_avgs)
        self.base_avgs = [0, 0, 0, 0]
        vals = self._read_samples(cnt)
        self.base_avgs = saved
        if not vals[0]:
            raise self.printer.command_error('HX711S: no data (timeout)')
        for i in range(self.s_count):
            if vals[i]:
                self.gcode.respond_info('CH%d: min=%.0f avg=%.0f max=%.0f n=%d' % (
                    i, min(vals[i]), sum(vals[i]) / len(vals[i]),
                    max(vals[i]), len(vals[i])))

    def cmd_PRTOUCH_TARE(self, gcmd):
        if self.query_cmd is None:
            raise self.printer.command_error('HX711S: not ready')
        cnt = gcmd.get_int('C', 20, minval=5, maxval=100)
        self.gcode.respond_info('PRTouch: Taring %d samples...' % cnt)
        base = self._tare(cnt)
        self.gcode.respond_info('PRTouch: Tare OK — CH0=%.0f' % base[0])

    def cmd_PRTOUCH_READ_DELTA(self, gcmd):
        if self.query_cmd is None:
            raise self.printer.command_error('HX711S: not ready')
        cnt = gcmd.get_int('C', 10, minval=1, maxval=100)
        vals = self._read_samples(cnt)
        if not vals[0]:
            raise self.printer.command_error('HX711S: no data')
        for i in range(self.s_count):
            if vals[i]:
                avg = sum(vals[i]) / len(vals[i])
                noise = max(vals[i]) - min(vals[i])
                self.gcode.respond_info(
                    'CH%d delta: avg=%.0f  range=%.0f  (base=%.0f)' % (
                    i, avg, noise, self.base_avgs[i]))

    def cmd_PRTOUCH_PROBE(self, gcmd):
        """
        Sonda en un punto. Usa _run_probe_at en posicion actual.
        T=threshold(8000) D=max_dist(2.5) S=step(0.02) V=speed(1)
        FAST_D=1.5 FAST_S=0.1 FAST_V=5 MIN_Z=-0.15 C=tare(20)
        APPLY=1 aplica SET_GCODE_OFFSET y guarda variable. REF=0 modo absoluto.
        """
        threshold  = gcmd.get_int('T',       8000, minval=50,    maxval=500000)
        max_dist   = gcmd.get_float('D',     2.5,  minval=0.1,   maxval=10.0)
        step       = gcmd.get_float('S',     0.02, minval=0.005, maxval=0.5)
        speed      = gcmd.get_float('V',     1.0,  minval=0.1,   maxval=10.0)
        tare_cnt   = gcmd.get_int('C',       20,   minval=5,     maxval=100)
        min_z      = gcmd.get_float('MIN_Z', -0.15,minval=-1.0,  maxval=5.0)
        fast_dist  = gcmd.get_float('FAST_D',1.5,  minval=0.0,   maxval=9.0)
        fast_step  = gcmd.get_float('FAST_S',0.1,  minval=0.02,  maxval=1.0)
        fast_speed = gcmd.get_float('FAST_V',5.0,  minval=0.5,   maxval=20.0)
        apply_off  = gcmd.get_int('APPLY',   0,    minval=0,     maxval=1)
        sensor_ref = gcmd.get_float('REF',   0.0,  minval=-1.0,  maxval=2.0)

        if self.query_cmd is None:
            raise self.printer.command_error('HX711S: not ready')
        toolhead = self.printer.lookup_object('toolhead')
        if 'z' not in toolhead.get_status(self.printer.get_reactor().monotonic()).get('homed_axes', ''):
            raise self.printer.command_error('PRTouch: debe hacer G28 Z primero')
        if toolhead.get_position()[2] < 0.5:
            raise self.printer.command_error('PRTouch: Z < 0.5mm — muy bajo para iniciar')

        contact_z = self._run_probe_at(toolhead, threshold, step, speed, min_z,
                                       fast_dist, fast_step, fast_speed, tare_cnt)
        self._safe_lift(toolhead, 2.0)

        if contact_z is None:
            raise self.printer.command_error('PRTouch: Sin contacto. Comprobar sensor o reducir T.')

        self.gcode.respond_info('PRTouch: Z contacto = %.4f  (Z actual = %.3f)' % (
            contact_z, toolhead.get_position()[2]))

        if apply_off:
            # Offset ABSOLUTO (Z=, NO Z_ADJUST) -> idempotente, no se acumula print
            # a print (ese era el bug real). Signo -(contact_z): el umbral de 8000
            # cuentas dispara ~0.11mm POR DEBAJO de la superficie real (curva de
            # fuerza 2026-06-01: superficie ~tool +0.07, umbral ~tool -0.04), asi
            # que offset=-contact_z (~+0.04) deja G-Z0 a ~0.03mm = squish suave.
            # OJO: el acople asume threshold=8000; si se cambia, re-validar (ver REF).
            correction = -(contact_z - sensor_ref)
            self.gcode.run_script_from_command('SET_GCODE_OFFSET Z=%.4f MOVE=0' % correction)
            self.gcode.run_script_from_command('SAVE_VARIABLE VARIABLE=prtouch_contact_z VALUE=%.4f' % contact_z)
            self.gcode.respond_info('PRTouch: Offset Z=%.4f aplicado y guardado (contacto=%.4f ref=%.4f)' % (
                correction, contact_z, sensor_ref))

    def cmd_PRTOUCH_PROBE_MULTI(self, gcmd):
        """
        Probe multi-punto (como Creality Nebula Pad): sonda en N puntos,
        promedia los resultados, verifica consistencia.

        Parametros posicion:
          NPOINTS = numero de puntos (default 2)
          X,Y     = centro del patron (default 110,110)
          DIST    = distancia entre puntos mm (default 25, eje Y)
          AXIS    = eje del patron: 'Y' (default) o 'X'

        Parametros probe (iguales a PRTOUCH_PROBE):
          T,D,S,V,C,MIN_Z,FAST_D,FAST_S,FAST_V

        Validacion:
          TOL = tolerancia maxima entre puntos mm (default 0.1)
                Si la dispersion supera TOL: avisa pero sigue con el promedio.

        Resultado:
          APPLY=1 aplica SET_GCODE_OFFSET y guarda prtouch_contact_z con el promedio.
          REF=0 modo absoluto (como Nebula Pad).
        """
        npoints    = gcmd.get_int('NPOINTS',  2,    minval=1,     maxval=5)
        cx         = gcmd.get_float('X',     110.0)
        cy         = gcmd.get_float('Y',     110.0)
        dist       = gcmd.get_float('DIST',   25.0, minval=5.0,   maxval=80.0)
        axis       = gcmd.get('AXIS',        'Y').upper()
        tolerance  = gcmd.get_float('TOL',    0.10, minval=0.01,  maxval=1.0)

        threshold  = gcmd.get_int('T',        8000, minval=50,    maxval=500000)
        max_dist   = gcmd.get_float('D',      2.5,  minval=0.1,   maxval=10.0)
        step       = gcmd.get_float('S',      0.02, minval=0.005, maxval=0.5)
        speed      = gcmd.get_float('V',      1.0,  minval=0.1,   maxval=10.0)
        tare_cnt   = gcmd.get_int('C',        20,   minval=5,     maxval=100)
        min_z      = gcmd.get_float('MIN_Z',  -0.15,minval=-1.0,  maxval=5.0)
        fast_dist  = gcmd.get_float('FAST_D', 1.5,  minval=0.0,   maxval=9.0)
        fast_step  = gcmd.get_float('FAST_S', 0.1,  minval=0.02,  maxval=1.0)
        fast_speed = gcmd.get_float('FAST_V', 5.0,  minval=0.5,   maxval=20.0)
        apply_off  = gcmd.get_int('APPLY',    0,    minval=0,     maxval=1)
        sensor_ref = gcmd.get_float('REF',    0.0,  minval=-1.0,  maxval=2.0)

        if self.query_cmd is None:
            raise self.printer.command_error('HX711S: not ready')
        toolhead = self.printer.lookup_object('toolhead')
        if 'z' not in toolhead.get_status(self.printer.get_reactor().monotonic()).get('homed_axes', ''):
            raise self.printer.command_error('PRTouch: debe hacer G28 Z primero')

        # Calcular posiciones de los puntos
        points = []
        for i in range(npoints):
            if npoints == 1:
                offset = 0.0
            else:
                offset = -dist / 2.0 + i * dist / (npoints - 1)
            if axis == 'X':
                points.append((cx + offset, cy))
            else:
                points.append((cx, cy + offset))

        self.gcode.respond_info('PRTouch multi: %d puntos, eje %s, separacion %.0fmm' % (
            npoints, axis, dist))
        for i, (px, py) in enumerate(points):
            self.gcode.respond_info('  Punto %d: X=%.1f Y=%.1f' % (i + 1, px, py))

        # Sonda en cada punto
        contacts = []
        for i, (px, py) in enumerate(points):
            label = 'P%d' % (i + 1)
            self._move_to_probe_pos(toolhead, px, py, z=2.0)

            contact_z = self._run_probe_at(
                toolhead, threshold, step, speed, min_z,
                fast_dist, fast_step, fast_speed, tare_cnt, point_label=label)

            self._safe_lift(toolhead, 2.0)

            if contact_z is None:
                raise self.printer.command_error(
                    'PRTouch multi: Sin contacto en punto %d (X=%.1f Y=%.1f). '
                    'Comprobar sensor o reducir T.' % (i + 1, px, py))

            contacts.append(contact_z)
            self.gcode.respond_info('PRTouch [P%d]: Z=%.4f' % (i + 1, contact_z))

        # Analizar resultados
        z_avg   = sum(contacts) / len(contacts)
        z_min   = min(contacts)
        z_max   = max(contacts)
        spread  = z_max - z_min

        self.gcode.respond_info(
            'PRTouch multi: promedio=%.4f  min=%.4f  max=%.4f  dispersion=%.4f' % (
            z_avg, z_min, z_max, spread))

        if spread > tolerance:
            self.gcode.respond_info(
                'PRTouch multi: AVISO dispersion %.4fmm > tolerancia %.4fmm — '
                'revisar nivelacion de cama o blob en boquilla' % (spread, tolerance))
        else:
            self.gcode.respond_info('PRTouch multi: OK — dispersion dentro de tolerancia (%.4fmm)' % spread)

        if apply_off:
            # Offset ABSOLUTO e idempotente (ver nota en cmd_PRTOUCH_PROBE).
            # Signo -(z_avg): el umbral dispara por debajo de la superficie real.
            correction = -(z_avg - sensor_ref)
            self.gcode.run_script_from_command('SET_GCODE_OFFSET Z=%.4f MOVE=0' % correction)
            self.gcode.run_script_from_command('SAVE_VARIABLE VARIABLE=prtouch_contact_z VALUE=%.4f' % z_avg)
            self.gcode.respond_info(
                'PRTouch multi: Offset Z=%.4f aplicado y guardado '
                '(promedio=%.4f ref=%.4f dispersion=%.4f)' % (
                correction, z_avg, sensor_ref, spread))


def load_config(config):
    return HX711S(config)
