"""Lógica sin interfaz: configuración, detección de dispositivos, XInput y entrada cruda."""
import os, re, sys, json, subprocess, ctypes, threading
from ctypes import wintypes

DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "8BitDoConfigurator")
os.makedirs(DIR, exist_ok=True)
CFG = os.path.join(DIR, "config.json")
DEFAULTS = {"startup": False, "auto": True, "interval": 3, "pinned": "", "deadzone": 8, "cal": {}, "cal_ok": False,
            "controller": "Joy-Con (R)", "target": "XInput"}

def load_cfg():
    try:
        d = json.load(open(CFG, encoding="utf-8")); return {**DEFAULTS, **d}
    except Exception:
        return dict(DEFAULTS)
def save_cfg(c):
    json.dump(c, open(CFG, "w", encoding="utf-8"), indent=2)

# VID:PID con los que Windows ve al adaptador cuando emula otros mandos
KNOWN = {("045E", "028E"): ("Xbox 360 Controller", "XInput"), ("057E", "2009"): ("Switch Pro Controller", "Switch"),
         ("054C", "05C4"): ("DualShock 4", "PlayStation"), ("054C", "09CC"): ("DualShock 4", "PlayStation"),
         ("054C", "0CE6"): ("DualSense", "PlayStation")}

# Combinaciones oficiales (manuales de support.8bitdo.com): mantener 3 s, el LED parpadea 2 veces
MODES = [("XInput · Xbox 360 / PC", "XInput", "↑"), ("DInput · PC genérico", "DInput", "←"), ("macOS", "Mac", "→"),
         ("PlayStation Classic", "PSC", "↓"), ("Nintendo Switch", "Switch", "L"), ("Mega Drive / Genesis Mini", "MD", "↑ + ←")]
ALL6 = ["XInput", "DInput", "Mac", "PSC", "Switch", "MD"]
CTRL = {"Joy-Con (L)": ("botón de función*", ALL6), "Joy-Con (R)": ("HOME", ALL6), "Switch Pro": ("botón de función*", ALL6),
        "DualShock 4 (PS4)": ("SHARE", ["XInput", "DInput"]), "DualSense (PS5)": ("CREATE", ALL6)}

CREATE_NO_WINDOW = 0x08000000
PS = ("Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match '^(USB|HID)\\\\VID_' } | "
      "Select-Object InstanceId,FriendlyName,Class,Manufacturer,Status | ConvertTo-Json -Compress")

def scan_pnp():
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", PS], capture_output=True,
                           text=True, timeout=20, creationflags=CREATE_NO_WINDOW)
        data = json.loads(r.stdout or "[]")
    except Exception:
        return []
    if isinstance(data, dict): data = [data]
    out = []
    for d in data:
        m = re.search(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", (d.get("InstanceId") or "").upper())
        if m: out.append({"vid": m[1], "pid": m[2], "name": d.get("FriendlyName") or "", "cls": d.get("Class") or "",
                          "mfr": d.get("Manufacturer") or "", "src": "PnP"})
    return out

def scan_hid():
    try:
        import hid
        return [{"vid": f"{d['vendor_id']:04X}", "pid": f"{d['product_id']:04X}", "name": d.get("product_string") or "",
                 "cls": "HID", "mfr": d.get("manufacturer_string") or "", "src": "HID"} for d in hid.enumerate()]
    except Exception:
        return []

def scan_devices():
    g = {}
    for d in scan_pnp() + scan_hid():
        e = g.setdefault((d["vid"], d["pid"]), {"vid": d["vid"], "pid": d["pid"], "names": set(), "cls": set(), "mfr": set(), "src": set()})
        if d["name"]: e["names"].add(d["name"])
        if d["cls"]: e["cls"].add(d["cls"])
        if d["mfr"] and "(Standard" not in d["mfr"]: e["mfr"].add(d["mfr"])
        e["src"].add(d["src"])
    res = []
    for e in g.values():
        txt = " ".join(e["names"] | e["mfr"]).upper()
        k = KNOWN.get((e["vid"], e["pid"]))
        e["known"] = k
        e["is8"] = e["vid"] == "2DC8" or "8BITDO" in txt
        e["pad"] = e["is8"] or bool(k) or bool(re.search(r"CONTROLLER|GAMEPAD|JOYSTICK|XBOX|GAME ", txt))
        e["title"] = sorted(e["names"], key=len)[-1] if e["names"] else (k[0] if k else "Dispositivo USB")
        res.append(e)
    res.sort(key=lambda x: (not x["is8"], not x["pad"], x["title"]))
    return res

def pick_adapter(devs, pinned):
    if pinned:
        for d in devs:
            if f"{d['vid']}:{d['pid']}" == pinned: return d, "fijado"
    for d in devs:
        if d["is8"]: return d, "8bitdo"
    for d in devs:
        if d["known"]: return d, "emulado"
    return None, ""

def detect_mode(devs, xin, raw):
    if xin is not None: return "XInput"
    for d in devs:
        if d["known"]: return d["known"][1]
    return "DInput" if raw else "—"

def build_report(devs, xin, raw):
    l = ["8BitDo Configurator – informe de diagnóstico", f"Python {sys.version.split()[0]}", ""]
    for d in devs:
        l.append(f"{d['vid']}:{d['pid']}  {d['title']}  clase={','.join(d['cls'])}  fuente={','.join(d['src'])}  8bitdo={d['is8']} mando={d['pad']}")
    l += ["", f"XInput: {'activo' if xin is not None else 'sin mando'}", f"Entrada cruda: {raw['name'] if raw else 'sin mando'}"]
    return "\n".join(l)

# ---------------- XInput ----------------
class GP(ctypes.Structure):
    _fields_ = [("b", wintypes.WORD), ("lt", ctypes.c_ubyte), ("rt", ctypes.c_ubyte), ("lx", ctypes.c_short),
                ("ly", ctypes.c_short), ("rx", ctypes.c_short), ("ry", ctypes.c_short)]
class XS(ctypes.Structure):
    _fields_ = [("pkt", wintypes.DWORD), ("gp", GP)]
_get = None
try:
    _x = None
    for n in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
        try: _x = ctypes.WinDLL(n); break
        except OSError: pass
    if _x:
        try: _get = _x[100]
        except Exception: _get = _x.XInputGetState
except Exception:
    _get = None
MASK = {"UP": 1, "DOWN": 2, "LEFT": 4, "RIGHT": 8, "START": 0x10, "BACK": 0x20, "LS": 0x40, "RS": 0x80,
        "LB": 0x100, "RB": 0x200, "GUIDE": 0x400, "A": 0x1000, "B": 0x2000, "X": 0x4000, "Y": 0x8000}
EMPTY = {"btn": set(), "lt": 0, "rt": 0, "lx": 0, "ly": 0, "rx": 0, "ry": 0}

def read_pad():
    if not _get: return None
    for i in range(4):
        st = XS()
        try:
            if _get(i, ctypes.byref(st)) != 0: continue
        except Exception:
            return None
        g = st.gp; b = {n for n, m in MASK.items() if g.b & m}
        if g.lt > 40: b.add("LT")
        if g.rt > 40: b.add("RT")
        return {"btn": b, "lt": g.lt / 255, "rt": g.rt / 255, "lx": g.lx / 32768, "ly": g.ly / 32768,
                "rx": g.rx / 32768, "ry": g.ry / 32768}
    return None

# ---------------- Entrada cruda (DirectInput / HID vía SDL) ----------------
class Raw:
    def __init__(s):
        s.pg = None; s.j = None
        try:
            os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
            import pygame
            pygame.display.init(); pygame.joystick.init(); s.pg = pygame
        except Exception:
            s.pg = None
    def read(s):
        if not s.pg: return None
        try:
            pg = s.pg
            for e in pg.event.get():
                if e.type == pg.JOYDEVICEADDED and s.j is None: s.j = pg.joystick.Joystick(e.device_index)
                elif e.type == pg.JOYDEVICEREMOVED: s.j = None
            if s.j is None and pg.joystick.get_count() > 0: s.j = pg.joystick.Joystick(0)
            j = s.j
            if j is None: return None
            return {"name": j.get_name(), "axes": [j.get_axis(i) for i in range(j.get_numaxes())],
                    "buttons": [j.get_button(i) for i in range(j.get_numbuttons())],
                    "hats": [j.get_hat(i) for i in range(j.get_numhats())]}
        except Exception:
            s.j = None; return None
