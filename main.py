import sys, os, time, datetime, platform, threading
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import *
from core import *
from widgets import *

QSS = """
QWidget{color:#e5e7eb;font-family:'Segoe UI';font-size:13px}
#win{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #170a3a,stop:.55 #0a1030,stop:1 #05202c)}
#side{background:rgba(8,6,26,215);border-right:1px solid #2a2150}
#side QPushButton{text-align:left;padding:11px 14px;border:none;border-radius:10px;font-size:14px;background:transparent;color:#d1d5db}
#side QPushButton:checked{background:#4c2a9a;color:white}
#side QPushButton:hover:!checked{background:#241a52}
#card{background:rgba(20,16,52,200);border:1px solid #3f3380;border-radius:14px}
#h1{font-size:24px;font-weight:700;color:white}
#sub{color:#a78bfa}
#cap{color:#a78bfa;font-size:12px}
#big{font-size:20px;font-weight:700;color:white}
#primary{background:qlineargradient(x1:0,x2:1,stop:0 #7c3aed,stop:1 #5b21b6);border:1px solid #a78bfa;border-radius:10px;padding:10px 20px;font-weight:700;color:white}
#primary:hover{background:#8b5cf6}
#sec{background:rgba(30,24,70,200);border:1px solid #4c3a9a;border-radius:10px;padding:9px 16px}
#sec:hover{background:#2e2368}
QComboBox,QSpinBox{background:#17123a;border:1px solid #4c3a9a;border-radius:8px;padding:6px 10px;min-height:22px}
QComboBox QAbstractItemView{background:#17123a;selection-background-color:#5b21b6}
QListWidget,QTableWidget{background:transparent;border:none;gridline-color:#2a2150;alternate-background-color:rgba(255,255,255,8)}
QHeaderView::section{background:#1b1445;color:#c4b5fd;border:none;padding:6px}
QTableWidget::item:selected{background:#4c2a9a}
QProgressBar{background:#17123a;border:none;border-radius:5px;max-height:10px;text-align:center;color:transparent}
QProgressBar::chunk{background:#22d3ee;border-radius:5px}
QTabWidget::pane{border:1px solid #3f3380;border-radius:10px}
QTabBar::tab{background:#17123a;padding:8px 16px;border-top-left-radius:8px;border-top-right-radius:8px;margin-right:3px}
QTabBar::tab:selected{background:#4c2a9a}
QSlider::groove:horizontal{height:6px;background:#17123a;border-radius:3px}
QSlider::handle:horizontal{background:#a78bfa;width:16px;margin:-6px 0;border-radius:8px}
QStatusBar{background:#08061a;color:#9ca3af}
QCheckBox{spacing:8px}
"""
PILL = {"ok": ("#22e06b", "rgba(34,224,107,40)"), "bad": ("#f87171", "rgba(248,113,113,40)"), "warn": ("#facc15", "rgba(250,204,21,40)")}

def L(t="", name=None, wrap=False):
    l = QLabel(t)
    if name: l.setObjectName(name)
    l.setWordWrap(wrap); l.setTextFormat(Qt.RichText); return l
def card():
    f = QFrame(); f.setObjectName("card"); return f
def button(t, name="sec", ic=None):
    b = QPushButton(t); b.setObjectName(name); b.setCursor(Qt.PointingHandCursor)
    if ic: b.setIcon(icon(ic, "#ffffff")); b.setIconSize(QSize(18, 18))
    return b
def pill(l, text, state):
    c, bg = PILL[state]; l.setText(f"●  {text}"); l.setStyleSheet(f"color:{c};background:{bg};border:1px solid {c};border-radius:12px;padding:4px 14px;font-weight:700")
def header(title, sub, right=None):
    w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); v = QVBoxLayout(); v.setSpacing(2); v.addWidget(L(title, "h1")); v.addWidget(L(sub, "sub"))
    h.addLayout(v); h.addStretch()
    if right:
        for r in (right if isinstance(right, list) else [right]): h.addWidget(r)
    return w
def page(*items):
    w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(28, 22, 28, 16); v.setSpacing(14)
    for x in items: v.addLayout(x) if isinstance(x, QLayout) else v.addWidget(x)
    return w, v
def stat(caption):
    c = card(); v = QVBoxLayout(c); v.addWidget(L(caption, "cap")); val = L("—", "big"); v.addWidget(val); return c, val

class Scanner(QThread):
    done = Signal(list)
    def __init__(s): super().__init__(); s.stop = False; s.ev = threading.Event(); s.interval = 3
    def run(s):
        while not s.stop:
            s.done.emit(scan_devices()); s.ev.wait(s.interval); s.ev.clear()

class Main(QMainWindow):
    def __init__(s):
        super().__init__(); s.setWindowTitle("8BitDo USB Adapter Configurator"); s.resize(1240, 780); s.setMinimumSize(1050, 680)
        s.cfg = load_cfg(); s.lay = "Xbox Series X"; s.devs = []; s.ad = None; s.how = ""; s.miss = 0; s.t0 = None; s.xin = None; s.rawd = None
        s.prev = set(); s.tested = set(); s.combos = []; s.pads = []; s.n = 0; s.measure = False; s.rng = {}; s.raw = Raw()
        root = QWidget(); root.setObjectName("win"); s.setCentralWidget(root); h = QHBoxLayout(root); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
        side = QFrame(); side.setObjectName("side"); side.setFixedWidth(220); sv = QVBoxLayout(side); sv.setContentsMargins(12, 20, 12, 14); sv.setSpacing(4)
        s.stack = QStackedWidget(); s.nav = []
        items = [("Inicio", "home", s.p_home), ("Dispositivos", "usb", s.p_dev), ("Modo del adaptador", "mode", s.p_mode), ("Calibración", "cal", s.p_cal),
                 ("Prueba de mando", "test", s.p_test), ("Ajustes", "gear", s.p_set), ("Acerca de", "info", s.p_about)]
        for i, (n, ic, f) in enumerate(items):
            b = QPushButton("  " + n); b.setIcon(icon(ic, "#ffffff")); b.setIconSize(QSize(20, 20)); b.setCheckable(True); b.setAutoExclusive(True)
            b.clicked.connect(lambda _, i=i: s.go(i)); sv.addWidget(b); s.nav.append(b); s.stack.addWidget(f())
        sv.addStretch(); sv.addWidget(L("<span style='font-size:30px;font-weight:700'>8BitDo</span><br><span style='color:#9ca3af;font-size:9px'>PLAY MORE, WIRELESS</span>"))
        h.addWidget(side); h.addWidget(s.stack, 1); s.go(0)
        s.sp = QLabel(); s.sb = s.statusBar(); s.sb.addWidget(s.sp); s.sb.addPermanentWidget(QLabel(f"Windows {platform.release()}   ·   v2.0"))
        s.setStyleSheet(QSS); s.toast_l = QLabel(root); s.toast_l.hide()
        s.sc = Scanner(); s.sc.interval = s.cfg["interval"]; s.sc.done.connect(s.on_scan); s.sc.start()
        s.t2 = QTimer(s); s.t2.timeout.connect(s.tick); s.t2.start(16); s.render_home()
    def closeEvent(s, e):
        s.sc.stop = True; s.sc.ev.set(); s.sc.wait(3000); e.accept()
    def go(s, i): s.stack.setCurrentIndex(i); s.nav[i].setChecked(True)
    def toast(s, t):
        l = s.toast_l; l.setText(t); l.setStyleSheet("background:#1b1445;border:1px solid #22e06b;border-radius:10px;padding:12px 18px;color:white;font-weight:600")
        l.adjustSize(); l.move(s.centralWidget().width() - l.width() - 24, 20); l.raise_(); l.show(); QTimer.singleShot(4500, l.hide)
    def act(s, t): s.alist.insertItem(0, f"{datetime.datetime.now():%H:%M:%S}   {t}")
    def mkcombo(s):
        c = QComboBox(); c.addItems(list(LAYOUTS)); c.setCurrentText(s.lay); c.currentTextChanged.connect(s.setlay); s.combos.append(c); return c
    def setlay(s, t):
        s.lay = t
        for c in s.combos: c.blockSignals(True); c.setCurrentText(t); c.blockSignals(False)
        for p in s.pads: p.lay = t; p.update()
        s.refresh_cal()
    # ---------------- Inicio ----------------
    def p_home(s):
        s.pill_top = QLabel(); rb = button("Reescanear", "sec", "usb"); rb.clicked.connect(s.rescan)
        hero = card(); hh = QHBoxLayout(hero); hh.setContentsMargins(20, 14, 20, 14); s.art = AdapterArt(); hh.addWidget(s.art)
        info = QVBoxLayout(); s.pill_h = QLabel(); s.h_title = L("", "h1"); s.h_info = L("", wrap=True); s.h_info.setStyleSheet("font-size:14px"); s.h_help = L("", wrap=True); s.h_help.setStyleSheet("color:#fcd34d")
        info.addWidget(s.pill_h, 0, Qt.AlignLeft); info.addWidget(s.h_title); info.addWidget(s.h_info); info.addWidget(s.h_help); info.addStretch(); hh.addLayout(info, 1)
        row = QHBoxLayout(); c1, s.v_mode = stat("MODO DETECTADO POR WINDOWS"); c2, s.v_pad = stat("MANDO ACTIVO"); c3, s.v_tgt = stat("MODO OBJETIVO (ASISTENTE)")
        for c in (c1, c2, c3): row.addWidget(c)
        bot = QHBoxLayout(); q = card(); qv = QVBoxLayout(q); qv.addWidget(L("<b>Acciones rápidas</b>"))
        for t, i, ic in (("Cambiar modo del adaptador", 2, "mode"), ("Calibrar mando", 3, "cal"), ("Probar botones", 4, "test"), ("Diagnóstico de dispositivos", 1, "usb")):
            b = button(t, "sec", ic); b.clicked.connect(lambda _, i=i: s.go(i)); qv.addWidget(b)
        qv.addStretch(); a = card(); av = QVBoxLayout(a); av.addWidget(L("<b>Actividad</b>")); s.alist = QListWidget(); av.addWidget(s.alist)
        bot.addWidget(q, 1); bot.addWidget(a, 2)
        w, v = page(header("Inicio", "Estado del adaptador 8BitDo y del mando", [s.pill_top, rb]), hero, row, bot); return w
    def rescan(s): s.sc.ev.set(); s.sb.showMessage("Buscando dispositivos…", 2000)
    def on_scan(s, devs):
        s.devs = devs; d, how = pick_adapter(devs, s.cfg["pinned"])
        if d is None and s.ad is not None and s.miss < 1: s.miss += 1; return  # evita parpadeos
        s.miss = 0; was = s.ad is not None; s.ad, s.how = d, how
        if d and not was: s.t0 = time.time(); s.toast(f"Adaptador detectado: {d['title']}"); s.act(f"Conectado: {d['title']} ({d['vid']}:{d['pid']})")
        if was and not d: s.act("Adaptador desconectado"); s.toast("Adaptador desconectado")
        s.render_home(); s.fill_table()
    def render_home(s):
        d = s.ad; s.art.on = d is not None
        if d:
            st, txt = ("ok", "DETECTADO") if s.how in ("8bitdo", "fijado") else ("warn", "DISPOSITIVO COMPATIBLE")
            s.h_title.setText(d["title"]); s.h_help.setText("" if s.how != "emulado" else "Windows lo ve emulando otro mando (modo actual del adaptador). Si es tu adaptador, fíjalo en «Dispositivos».")
            el = int(time.time() - (s.t0 or time.time()))
            s.h_info.setText(f"<b>VID:PID:</b> {d['vid']}:{d['pid']}<br><b>Clase:</b> {', '.join(sorted(d['cls'])) or '—'}<br><b>Detectado por:</b> {', '.join(sorted(d['src']))}<br><b>Conectado hace:</b> {el//3600:02d}:{el%3600//60:02d}:{el%60:02d}")
        else:
            st, txt = "bad", "NO DETECTADO"; s.h_title.setText("Adaptador no encontrado")
            s.h_info.setText("1. Conecta el adaptador directamente a un puerto USB del PC (sin hub).<br>2. Pulsa su botón <b>pair</b> y empareja el mando.<br>3. Abre <b>Dispositivos</b> para ver todo lo que Windows detecta y fija el tuyo.")
            s.h_help.setText("")
        pill(s.pill_h, txt, st); pill(s.pill_top, txt, st); pill_s = {"ok": "Adaptador conectado", "warn": "Dispositivo compatible", "bad": "Adaptador no detectado"}[st]
        s.sp.setText(f"●  {pill_s}"); s.sp.setStyleSheet(f"color:{PILL[st][0]}")
    # ---------------- Dispositivos ----------------
    def p_dev(s):
        rb = button("Reescanear", "sec", "usb"); rb.clicked.connect(s.rescan)
        s.showall = QCheckBox("Mostrar todos los dispositivos USB/HID"); s.showall.stateChanged.connect(lambda _: s.fill_table())
        s.tbl = QTableWidget(0, 5); s.tbl.setHorizontalHeaderLabels(["", "Dispositivo", "VID:PID", "Clase", "Fuente"]); s.tbl.verticalHeader().hide()
        s.tbl.setSelectionBehavior(QAbstractItemView.SelectRows); s.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers); s.tbl.setAlternatingRowColors(True)
        hd = s.tbl.horizontalHeader(); hd.setSectionResizeMode(1, QHeaderView.Stretch); s.tbl.setColumnWidth(0, 40)
        bar = QHBoxLayout(); b1 = button("Fijar seleccionado como mi adaptador", "primary"); b1.clicked.connect(s.pin); b2 = button("Quitar fijado"); b2.clicked.connect(s.unpin)
        b3 = button("Copiar informe"); b3.clicked.connect(lambda: (QGuiApplication.clipboard().setText(build_report(s.devs, s.xin, s.rawd)), s.sb.showMessage("Informe copiado", 3000)))
        b4 = button("Administrador de dispositivos"); b4.clicked.connect(lambda: os.startfile("devmgmt.msc") if hasattr(os, "startfile") else None)
        for b in (b1, b2, b3, b4): bar.addWidget(b)
        bar.addStretch(); c = card(); cv = QVBoxLayout(c); cv.addWidget(s.tbl)
        s.pin_l = L("", "sub"); w, v = page(header("Dispositivos", "Todo lo que Windows ve conectado por USB/HID", rb), s.showall, c, bar, s.pin_l); return w
    def fill_table(s):
        if not hasattr(s, "tbl"): return
        rows = [d for d in s.devs if s.showall.isChecked() or d["pad"]]; s.tbl.setRowCount(len(rows)); s.rows = rows
        for i, d in enumerate(rows):
            tag = "★" if d is s.ad else ("●" if d["is8"] else "")
            vals = [tag, d["title"], f"{d['vid']}:{d['pid']}", ", ".join(sorted(d["cls"])), ", ".join(sorted(d["src"]))]
            for j, t in enumerate(vals): s.tbl.setItem(i, j, QTableWidgetItem(t))
        s.pin_l.setText(f"Adaptador fijado: {s.cfg['pinned'] or 'ninguno (detección automática)'}   ·   ★ = en uso   ● = fabricante 8BitDo")
    def pin(s):
        r = s.tbl.currentRow()
        if 0 <= r < len(s.rows): d = s.rows[r]; s.cfg["pinned"] = f"{d['vid']}:{d['pid']}"; save_cfg(s.cfg); s.rescan(); s.on_scan(s.devs)
    def unpin(s): s.cfg["pinned"] = ""; save_cfg(s.cfg); s.on_scan(s.devs)
    # ---------------- Modo ----------------
    def p_mode(s):
        c = card(); cv = QGridLayout(c); cv.setContentsMargins(18, 14, 18, 14)
        s.c_ctrl = QComboBox(); s.c_ctrl.addItems(list(CTRL)); s.c_ctrl.setCurrentText(s.cfg["controller"]); s.c_mode = QComboBox()
        cv.addWidget(L("Mando que vas a usar con el adaptador", "cap"), 0, 0); cv.addWidget(L("Modo que quieres en el adaptador", "cap"), 0, 1); cv.addWidget(s.c_ctrl, 1, 0); cv.addWidget(s.c_mode, 1, 1)
        s.steps = L("", wrap=True); s.steps.setStyleSheet("font-size:14px"); sc = card(); sv = QVBoxLayout(sc); sv.setContentsMargins(20, 16, 20, 16); sv.addWidget(s.steps)
        vb = button("Verificar cómo lo ve Windows", "primary", "test"); vb.clicked.connect(s.verify); s.ver = L("", wrap=True)
        note = L("<span style='color:#9ca3af'>El adaptador 8BitDo no se configura con software: su modo se cambia con combinaciones de botones del mando "
                 "(según los manuales oficiales en support.8bitdo.com). Esta guía te muestra la combinación exacta y comprueba el resultado. "
                 "*En Joy-Con (L) y Switch Pro el manual indica el botón con un icono.</span>", wrap=True)
        s.c_ctrl.currentTextChanged.connect(s.upd_modes); s.c_mode.currentIndexChanged.connect(s.upd_steps); s.upd_modes()
        w, v = page(header("Modo del adaptador", "Guía paso a paso para cambiar entre XInput, DInput, macOS, Switch, PSC y MD"), c, sc, vb, s.ver, note); v.addStretch(); return w
    def upd_modes(s):
        pre, avail = CTRL[s.c_ctrl.currentText()]; s.c_mode.blockSignals(True); s.c_mode.clear()
        for n, k, d in MODES:
            if k in avail: s.c_mode.addItem(n, k)
        i = s.c_mode.findData(s.cfg["target"]); s.c_mode.setCurrentIndex(max(0, i)); s.c_mode.blockSignals(False); s.upd_steps()
    def upd_steps(s):
        ctl = s.c_ctrl.currentText(); pre, _ = CTRL[ctl]; k = s.c_mode.currentData()
        if k is None: return
        d = [m for m in MODES if m[1] == k][0][2]
        if d == "L" and ctl in ("DualSense (PS5)", "DualShock 4 (PS4)"): d = "L1"
        key = lambda t: f"<span style='background-color:#3b2f7a;color:#ffffff;font-weight:700'>&nbsp;{t}&nbsp;</span>"
        combo = " + ".join([key(pre)] + [key(x.strip()) for x in d.split("+")])
        s.cfg["controller"] = ctl; s.cfg["target"] = k; save_cfg(s.cfg); s.v_tgt.setText([m[0] for m in MODES if m[1] == k][0])
        s.steps.setText("<b>1.</b> Conecta el adaptador al PC y empareja el mando (botón <b>pair</b> del adaptador hasta que el LED parpadee rápido).<br><br>"
                        f"<b>2.</b> Con el mando conectado, mantén pulsado durante <b>3 segundos</b>:&nbsp;&nbsp;{combo}<br>"
                        "&nbsp;&nbsp;&nbsp;&nbsp;El LED del adaptador parpadeará dos veces.<br><br>"
                        "<b>3.</b> Si el modo no cambia, vuelve a emparejar el mando.<br><br><b>4.</b> Pulsa <b>Verificar</b> para ver cómo lo detecta Windows.<br><br>"
                        "<span style='color:#9ca3af'>Para cancelar el modo manual: mantén el botón pair del adaptador hasta que el LED se apague y vuelve a emparejar.</span>")
    def verify(s):
        k = s.c_mode.currentData(); m = detect_mode(s.devs, s.xin, s.rawd); names = {"XInput": "XInput (Xbox 360)", "Switch": "Nintendo Switch Pro", "PlayStation": "PlayStation", "DInput": "DInput / HID genérico", "—": "nada"}
        ok = (k == "XInput" and m == "XInput") or (k == "Switch" and m == "Switch") or (k == "DInput" and m in ("DInput", "PlayStation"))
        if ok: s.ver.setText(f"<span style='color:#22e06b'><b>✔ Correcto.</b></span> Windows lo detecta como {names[m]}.")
        elif k in ("Mac", "PSC", "MD"): s.ver.setText(f"<span style='color:#facc15'>Ese modo no se puede comprobar desde Windows (detectado ahora: {names[m]}). Pruébalo en el equipo destino.</span>")
        else: s.ver.setText(f"<span style='color:#f87171'><b>✘ Aún no.</b></span> Windows detecta: {names[m]}. Repite la combinación y vuelve a emparejar.")
    # ---------------- Calibración ----------------
    def p_cal(s):
        s.sl = Stick("Stick izquierdo"); s.sr = Stick("Stick derecho"); col = QVBoxLayout(); col.addWidget(s.sl); col.addWidget(s.sr)
        pad = Pad(); s.pads.append(pad); mid = QVBoxLayout(); mid.addWidget(s.mkcombo(), 0, Qt.AlignLeft); mid.addWidget(pad, 1)
        s.bars = {}; br = QHBoxLayout()
        for k in ("LT", "RT"): pb = QProgressBar(); pb.setRange(0, 100); s.bars[k] = pb; br.addWidget(QLabel(k)); br.addWidget(pb)
        mid.addLayout(br); s.dzl = L("Zona muerta: 8 %"); sl = QSlider(Qt.Horizontal); sl.setRange(0, 30); sl.setValue(s.cfg["deadzone"]); sl.valueChanged.connect(s.set_dz); mid.addWidget(s.dzl); mid.addWidget(sl)
        s.rngl = L("Pulsa «Medir rango» y gira ambos sticks y gatillos al máximo.", wrap=True); mid.addWidget(s.rngl)
        right = card(); right.setFixedWidth(270); rv = QVBoxLayout(right); rv.addWidget(L("<b>Resultados de la prueba</b>")); s.cl = {}
        s.names = ["A", "B", "X", "Y", "LB", "RB", "LT", "RT", "LS", "RS", "GUIDE", "UP", "DOWN", "LEFT", "RIGHT", "START", "BACK"]
        for n in s.names: l = QLabel(); s.cl[n] = l; rv.addWidget(l)
        rv.addStretch(); b1 = button("Medir rango"); b1.clicked.connect(s.toggle_measure); s.mb = b1; b2 = button("Reiniciar prueba"); b2.clicked.connect(s.reset)
        b3 = button("Calibración de Windows (joy.cpl)"); b3.clicked.connect(lambda: os.startfile("joy.cpl") if hasattr(os, "startfile") else None)
        b4 = button("Guardar calibración", "primary", "cal"); b4.clicked.connect(s.savecal)
        for b in (b1, b2, b3, b4): rv.addWidget(b)
        row = QHBoxLayout(); row.addLayout(col); row.addLayout(mid, 1); row.addWidget(right)
        s.set_dz(s.cfg["deadzone"]); s.refresh_cal(); w, v = page(header("Calibración y prueba de botones", "Comprueba cada botón, mide el rango de sticks y gatillos"), row); return w
    def set_dz(s, v): s.cfg["deadzone"] = v; s.dzl.setText(f"Zona muerta: {v} %"); s.sl.dz = v; s.sr.dz = v; s.sl.update(); s.sr.update()
    def refresh_cal(s):
        if not hasattr(s, "cl"): return
        for n, l in s.cl.items(): l.setText(("<span style='color:#22e06b'>✔</span> " if n in s.tested else "○ ") + blabel(n, s.lay))
    def reset(s): s.tested.clear(); s.rng = {}; s.refresh_cal()
    def toggle_measure(s):
        s.measure = not s.measure; s.mb.setText("Detener medición" if s.measure else "Medir rango")
        if s.measure: s.rng = {}
    def savecal(s):
        ok = len(s.tested) == len(s.names); s.cfg["cal_ok"] = ok; s.cfg["cal"] = {k: [round(a, 3), round(b, 3)] for k, (a, b) in s.rng.items()}; save_cfg(s.cfg)
        QMessageBox.information(s, "Calibración", "Calibración completa guardada." if ok else f"Faltan {len(s.names)-len(s.tested)} botones por probar. Progreso guardado.")
    # ---------------- Prueba ----------------
    def p_test(s):
        s.cs = L(""); pad = Pad(); s.pads.append(pad); tabs = QTabWidget(); tabs.addTab(pad, "Mando (XInput)"); s.rawview = RawView(); tabs.addTab(s.rawview, "Entrada cruda (DirectInput / HID)")
        c = card(); c.setFixedWidth(290); cv = QVBoxLayout(c); hh = QHBoxLayout(); hh.addWidget(L("<b>Registro de entradas</b>")); cl = button("Limpiar"); hh.addWidget(cl); cv.addLayout(hh)
        s.log = QListWidget(); cl.clicked.connect(s.log.clear); cv.addWidget(s.log); row = QHBoxLayout(); row.addWidget(tabs, 1); row.addWidget(c)
        s.mon = Monitor(); top = QHBoxLayout(); top.addWidget(L("Diseño:")); top.addWidget(s.mkcombo()); top.addStretch(); top.addWidget(s.cs)
        w, v = page(header("Prueba de mando", "Al pulsar un botón físico se ilumina en pantalla"), top, row, L("<b>Monitor en vivo</b>  <span style='color:#22e06b'>■ A</span>  <span style='color:#38bdf8'>■ X</span>  <span style='color:#a855f7'>■ RT</span>  <span style='color:#fb923c'>■ Stick izq. X</span>"), s.mon); return w
    # ---------------- Ajustes / Acerca ----------------
    def p_set(s):
        c = card(); v = QVBoxLayout(c); v.setContentsMargins(20, 16, 20, 16); s.c1 = QCheckBox("Iniciar con Windows"); s.c2 = QCheckBox("Buscar el adaptador automáticamente"); s.c1.setChecked(s.cfg["startup"]); s.c2.setChecked(s.cfg["auto"])
        s.spin = QSpinBox(); s.spin.setRange(1, 30); s.spin.setValue(s.cfg["interval"]); s.spin.setSuffix(" s"); v.addWidget(s.c1); v.addWidget(s.c2); v.addWidget(L("Intervalo de búsqueda", "cap")); v.addWidget(s.spin, 0, Qt.AlignLeft)
        b = button("Aplicar", "primary"); b.clicked.connect(s.apply_set); fb = button("Abrir carpeta de configuración"); fb.clicked.connect(lambda: os.startfile(DIR) if hasattr(os, "startfile") else None)
        v.addWidget(b, 0, Qt.AlignLeft); v.addWidget(fb, 0, Qt.AlignLeft); w, vv = page(header("Ajustes", "Preferencias de la aplicación"), c); vv.addStretch(); return w
    def apply_set(s):
        s.cfg.update(startup=s.c1.isChecked(), auto=s.c2.isChecked(), interval=s.spin.value()); save_cfg(s.cfg); s.sc.interval = s.cfg["interval"]
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if s.cfg["startup"]: winreg.SetValueEx(k, "8BitDoConfigurator", 0, winreg.REG_SZ, f'"{sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])}"')
            else:
                try: winreg.DeleteValue(k, "8BitDoConfigurator")
                except OSError: pass
        except Exception: pass
        s.sb.showMessage("Ajustes aplicados", 3000)
    def p_about(s):
        t = L("Aplicación independiente, no afiliada a 8BitDo.<br><br><b>Qué hace:</b> detecta el adaptador y los mandos por PnP, HID, XInput y DirectInput; guía el cambio de modo con las combinaciones oficiales y verifica el resultado; mide rango y prueba cada botón.<br><br>"
              "<b>Qué no hace:</b> escribir el modo directamente en el adaptador. 8BitDo no publica ese protocolo y sus manuales indican que el modo se cambia con combinaciones de botones del mando. Las actualizaciones de firmware se hacen con la herramienta oficial de 8BitDo.", wrap=True)
        c = card(); v = QVBoxLayout(c); v.setContentsMargins(20, 16, 20, 16); v.addWidget(t); w, vv = page(header("Acerca de", "8BitDo USB Adapter Configurator v2.0"), c); vv.addStretch(); return w
    # ---------------- Bucle de entrada ----------------
    def tick(s):
        s.n += 1; st = read_pad(); s.xin = st; s.rawd = s.raw.read(); s.rawview.set(s.rawd)
        for p in s.pads: p.set(st)
        s.cs.setText("<span style='color:#22e06b'>●</span> Mando XInput conectado" if st else "<span style='color:#9ca3af'>● Sin mando XInput</span>")
        if s.n % 30 == 0:
            s.v_pad.setText((s.rawd["name"] if s.rawd else "Ninguno") if not st else "Xbox 360 (XInput)"); s.v_mode.setText({"XInput": "XInput", "Switch": "Switch Pro", "PlayStation": "PlayStation", "DInput": "DInput / HID", "—": "—"}[detect_mode(s.devs, st, s.rawd)])
            if s.ad: s.render_home()
        if not st: s.prev = set(); return
        s.sl.set(st["lx"], st["ly"]); s.sr.set(st["rx"], st["ry"]); s.bars["LT"].setValue(int(st["lt"] * 100)); s.bars["RT"].setValue(int(st["rt"] * 100)); s.mon.push(st)
        if s.measure:
            for k in ("lx", "ly", "rx", "ry", "lt", "rt"):
                a, b = s.rng.get(k, (st[k], st[k])); s.rng[k] = (min(a, st[k]), max(b, st[k]))
            if s.n % 6 == 0: s.rngl.setText("<br>".join(f"{k.upper()}: {a:+.2f} … {b:+.2f}" for k, (a, b) in s.rng.items()))
        now = st["btn"]; t = datetime.datetime.now().strftime("%H:%M:%S")
        for n in now - s.prev: s.log.insertItem(0, f"{t}   {blabel(n, s.lay)} pulsado")
        for n in s.prev - now: s.log.insertItem(0, f"{t}   {blabel(n, s.lay)} soltado")
        if now - s.tested: s.tested |= now; s.refresh_cal()
        s.prev = set(now)

if __name__ == "__main__":
    a = QApplication(sys.argv); m = Main(); m.show(); sys.exit(a.exec())
