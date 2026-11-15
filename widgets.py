import collections
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QLinearGradient, QPixmap, QIcon, QPolygonF
from PySide6.QtWidgets import QWidget
from core import EMPTY

def icon(kind, color="#c4b5fd"):
    pm = QPixmap(44, 44); pm.fill(Qt.transparent); p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing); p.scale(2, 2)
    p.setPen(QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)); p.setBrush(Qt.NoBrush)
    if kind == "home":
        p.drawPolyline(QPolygonF([QPointF(3, 11), QPointF(11, 4), QPointF(19, 11)])); p.drawRect(QRectF(6, 11, 10, 7))
    elif kind == "usb":
        p.drawLine(11, 4, 11, 16); p.drawEllipse(QPointF(11, 18), 2, 2); p.drawRect(QRectF(8, 2, 6, 3)); p.drawLine(11, 10, 16, 8); p.drawLine(11, 12, 6, 10)
    elif kind == "mode":
        p.drawRoundedRect(QRectF(2, 6, 18, 10), 5, 5); p.drawLine(6, 11, 10, 11); p.drawLine(8, 9, 8, 13); p.drawEllipse(QPointF(15, 10), 1, 1); p.drawEllipse(QPointF(17, 12), 1, 1)
    elif kind == "cal":
        p.drawEllipse(QPointF(11, 11), 7, 7); p.drawEllipse(QPointF(11, 11), 2, 2); p.drawLine(11, 1, 11, 5); p.drawLine(11, 17, 11, 21); p.drawLine(1, 11, 5, 11); p.drawLine(17, 11, 21, 11)
    elif kind == "test":
        p.drawEllipse(QPointF(8, 8), 4, 4); p.drawEllipse(QPointF(14, 15), 4, 4); p.drawLine(11, 11, 12, 12)
    elif kind == "gear":
        p.drawEllipse(QPointF(11, 11), 3, 3); p.drawEllipse(QPointF(11, 11), 7, 7)
        for a, b in ((11, 1, 11, 4), (11, 18, 11, 21), (1, 11, 4, 11), (18, 11, 21, 11)): pass
        for x1, y1, x2, y2 in ((11, 1, 11, 4), (11, 18, 11, 21), (1, 11, 4, 11), (18, 11, 21, 11)): p.drawLine(x1, y1, x2, y2)
    else:
        p.drawEllipse(QPointF(11, 11), 8, 8); p.drawLine(11, 10, 11, 16); p.drawPoint(QPointF(11, 6.5))
    p.end(); return QIcon(pm)

XBF = {"A": ("A", "#3ddc57"), "B": ("B", "#e5484d"), "X": ("X", "#3b82f6"), "Y": ("Y", "#f5c518")}
PSF = {"A": ("✕", "#6aa7ff"), "B": ("○", "#ff6b6b"), "X": ("□", "#ff8fd1"), "Y": ("△", "#4ade80")}
NSF = {"A": ("B", "#d1d5db"), "B": ("A", "#d1d5db"), "X": ("Y", "#d1d5db"), "Y": ("X", "#d1d5db")}
def _L(f, lb, rb, lt, rt, back, start, guide): return dict(face=f, LB=lb, RB=rb, LT=lt, RT=rt, BACK=back, START=start, GUIDE=guide)
LAYOUTS = {"Xbox 360": _L(XBF, "LB", "RB", "LT", "RT", "Back", "Start", "Xbox"), "Xbox One": _L(XBF, "LB", "RB", "LT", "RT", "View", "Menu", "Xbox"),
           "Xbox Series X": _L(XBF, "LB", "RB", "LT", "RT", "Share", "Menu", "Xbox"), "PS4": _L(PSF, "L1", "R1", "L2", "R2", "Share", "Options", "PS"),
           "PS5": _L(PSF, "L1", "R1", "L2", "R2", "Create", "Options", "PS"), "Nintendo Switch": _L(NSF, "L", "R", "ZL", "ZR", "−", "+", "Home")}
def blabel(name, lay):
    d = LAYOUTS[lay]
    if name in d["face"]: return "Botón " + d["face"][name][0]
    if name in d: return d[name]
    return {"UP": "D-Pad ↑", "DOWN": "D-Pad ↓", "LEFT": "D-Pad ←", "RIGHT": "D-Pad →", "LS": "L3", "RS": "R3"}.get(name, name)

class Pad(QWidget):
    def __init__(s):
        super().__init__(); s.st = EMPTY; s.lay = "Xbox Series X"; s.setMinimumSize(420, 280)
    def set(s, st): s.st = st or EMPTY; s.update()
    def node(s, p, r, on, color, txt="", rect=False, fs=14):
        c = QColor(color)
        if on and not rect:
            g = QColor(color); g.setAlpha(90); p.setPen(Qt.NoPen); p.setBrush(g); p.drawEllipse(r.adjusted(-9, -9, 9, 9))
        p.setPen(QPen(c, 2)); p.setBrush(c if on else QColor("#1b1b28"))
        p.drawRoundedRect(r, 8, 8) if rect else p.drawEllipse(r)
        if txt:
            p.setFont(QFont("Segoe UI", fs, QFont.Bold)); p.setPen(QColor("white") if on else c); p.drawText(r, Qt.AlignCenter, txt)
    def paintEvent(s, _):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); sc = min(s.width() / 600, s.height() / 400)
        p.translate((s.width() - 600 * sc) / 2, (s.height() - 400 * sc) / 2); p.scale(sc, sc)
        D = LAYOUTS[s.lay]; st = s.st; B = st["btn"]
        body = QPainterPath(); body.addRoundedRect(QRectF(110, 90, 380, 190), 95, 95); body.addEllipse(QRectF(95, 200, 150, 160)); body.addEllipse(QRectF(355, 200, 150, 160))
        g = QLinearGradient(0, 90, 0, 360); g.setColorAt(0, QColor("#2c2c40")); g.setColorAt(1, QColor("#0e0e16"))
        p.setPen(QPen(QColor("#7c3aed"), 3)); p.setBrush(g); p.drawPath(body.simplified()); G = "#22e06b"
        for x, k, v in ((125, "LT", st["lt"]), (375, "RT", st["rt"])):
            p.setPen(QPen(QColor("#f59e0b"), 2)); p.setBrush(QColor("#1b1b28")); p.drawRoundedRect(QRectF(x, 28, 100, 18), 5, 5)
            p.setPen(Qt.NoPen); p.setBrush(QColor("#f59e0b")); p.drawRoundedRect(QRectF(x, 28, 100 * v, 18), 5, 5)
            p.setPen(QColor("white")); p.setFont(QFont("Segoe UI", 9, QFont.Bold)); p.drawText(QRectF(x, 28, 100, 18), Qt.AlignCenter, D[k])
        s.node(p, QRectF(125, 58, 100, 24), "LB" in B, G, D["LB"], True, 10); s.node(p, QRectF(375, 58, 100, 24), "RB" in B, G, D["RB"], True, 10)
        for name, x, y in (("LS", 200, 160), ("RS", 350, 235)):
            s.node(p, QRectF(x - 34, y - 34, 68, 68), name in B, "#a855f7")
            ax, ay = (st["lx"], st["ly"]) if name == "LS" else (st["rx"], st["ry"])
            p.setPen(QPen(QColor("#a855f7"), 2)); p.setBrush(QColor("#a855f7") if (abs(ax) > .1 or abs(ay) > .1) else QColor("#2a2a3d"))
            p.drawEllipse(QPointF(x + ax * 14, y - ay * 14), 22, 22)
        cx, cy = 250, 235
        for k, r in (("UP", QRectF(cx - 12, cy - 36, 24, 34)), ("DOWN", QRectF(cx - 12, cy + 2, 24, 34)), ("LEFT", QRectF(cx - 36, cy - 12, 34, 24)), ("RIGHT", QRectF(cx + 2, cy - 12, 34, 24))):
            s.node(p, r, k in B, "#a855f7", "", True)
        for k, (x, y) in {"Y": (420, 130), "A": (420, 190), "X": (390, 160), "B": (450, 160)}.items():
            t, c = D["face"][k]; s.node(p, QRectF(x - 17, y - 17, 34, 34), k in B, c, t, False, 13)
        s.node(p, QRectF(268, 138, 24, 24), "BACK" in B, G, ""); s.node(p, QRectF(308, 138, 24, 24), "START" in B, G, ""); s.node(p, QRectF(280, 98, 40, 34), "GUIDE" in B, G, "")
        p.setPen(QColor("#9ca3af")); p.setFont(QFont("Segoe UI", 8))
        p.drawText(QRectF(255, 162, 50, 14), Qt.AlignCenter, D["BACK"]); p.drawText(QRectF(300, 162, 60, 14), Qt.AlignCenter, D["START"]); p.drawText(QRectF(280, 84, 40, 14), Qt.AlignCenter, D["GUIDE"])

class Stick(QWidget):
    def __init__(s, t):
        super().__init__(); s.t = t; s.x = s.y = 0; s.dz = 8; s.trail = collections.deque(maxlen=40); s.setFixedSize(190, 210)
    def set(s, x, y): s.x, s.y = x, y; s.trail.append((x, y)); s.update()
    def paintEvent(s, _):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); c = QPointF(95, 105)
        p.setPen(QColor("white")); p.setFont(QFont("Segoe UI", 10, QFont.Bold)); p.drawText(6, 16, s.t)
        p.setPen(QPen(QColor("#4c3a9a"), 2)); p.drawEllipse(c, 70, 70); p.drawLine(25, 105, 165, 105); p.drawLine(95, 35, 95, 175)
        p.setBrush(QColor(124, 58, 237, 60)); p.setPen(Qt.NoPen); p.drawEllipse(c, 70 * s.dz / 100, 70 * s.dz / 100)
        for i, (x, y) in enumerate(s.trail): p.setBrush(QColor(34, 211, 238, int(10 + 120 * i / 40))); p.drawEllipse(QPointF(95 + x * 66, 105 - y * 66), 3, 3)
        p.setBrush(QColor("#22d3ee")); p.drawEllipse(QPointF(95 + s.x * 66, 105 - s.y * 66), 8, 8)
        p.setPen(QColor("#cbd5e1")); p.setFont(QFont("Segoe UI", 9)); p.drawText(QRectF(0, 184, 190, 20), Qt.AlignCenter, f"X {s.x:+.2f}    Y {s.y:+.2f}")

class Monitor(QWidget):
    def __init__(s):
        super().__init__(); s.h = collections.deque(maxlen=240); s.setMinimumHeight(110)
    def push(s, st): s.h.append(("A" in st["btn"], "X" in st["btn"], st["rt"], (st["lx"] + 1) / 2)); s.update()
    def paintEvent(s, _):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); w, h = s.width() - 10, s.height() - 14
        for i, col in enumerate(("#22e06b", "#38bdf8", "#a855f7", "#fb923c")):
            p.setPen(QPen(QColor(col), 2)); pts = [QPointF(5 + j * w / 240, 7 + h - (float(v[i]) * h * .22 + (3 - i) * h * .25)) for j, v in enumerate(s.h)]
            for a, b in zip(pts, pts[1:]): p.drawLine(a, b)

class RawView(QWidget):
    def __init__(s):
        super().__init__(); s.d = None; s.setMinimumHeight(240)
    def set(s, d): s.d = d; s.update()
    def paintEvent(s, _):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); d = s.d
        p.setPen(QColor("white")); p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        if not d: p.setPen(QColor("#9ca3af")); p.drawText(s.rect(), Qt.AlignCenter, "Sin mando DirectInput/HID detectado"); return
        p.drawText(10, 22, d["name"]); p.setFont(QFont("Segoe UI", 9))
        for i, v in enumerate(d["axes"][:8]):
            y = 40 + i * 22; p.setPen(QColor("#cbd5e1")); p.drawText(10, y + 12, f"Eje {i}"); p.setPen(QPen(QColor("#4c3a9a"), 1)); p.setBrush(QColor("#17123a")); p.drawRoundedRect(QRectF(60, y, 220, 14), 4, 4)
            p.setPen(Qt.NoPen); p.setBrush(QColor("#a855f7")); p.drawRoundedRect(QRectF(60 + 110 + min(0, v) * 110, y, abs(v) * 110, 14), 4, 4)
        for i, v in enumerate(d["buttons"][:32]):
            r = QRectF(310 + (i % 8) * 34, 40 + (i // 8) * 34, 28, 28); p.setPen(QPen(QColor("#22e06b"), 1.5)); p.setBrush(QColor("#22e06b") if v else QColor("#1b1b28")); p.drawRoundedRect(r, 6, 6)
            p.setPen(QColor("white") if v else QColor("#6b7280")); p.drawText(r, Qt.AlignCenter, str(i))
        for i, h in enumerate(d["hats"][:2]):
            p.setPen(QColor("#cbd5e1")); p.drawText(310, 190 + i * 20, f"Hat {i}: {h}")

class AdapterArt(QWidget):
    def __init__(s):
        super().__init__(); s.on = False; s.ph = 0.0; s.setMinimumSize(230, 230); t = QTimer(s); t.timeout.connect(s.pulse); t.start(40)
    def pulse(s): s.ph = (s.ph + .07) % 6.283; s.update()
    def paintEvent(s, _):
        import math
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); sc = min(s.width() / 240, s.height() / 230)
        p.translate((s.width() - 240 * sc) / 2, (s.height() - 230 * sc) / 2); p.scale(sc, sc)
        col = QColor("#22d3ee") if s.on else QColor("#4b5563")
        for r in (95, 72, 50):
            c = QColor(col); c.setAlpha(110 if s.on else 60); p.setPen(QPen(c, 2)); p.setBrush(Qt.NoBrush); p.drawEllipse(QPointF(120, 205), r, r * .22)
        p.setBrush(QColor("#b8bcc6")); p.setPen(QPen(QColor("#6b7280"), 2)); p.drawRoundedRect(QRectF(98, 14, 44, 42), 3, 3)
        p.setBrush(QColor("#222")); p.setPen(Qt.NoPen); p.drawRect(QRectF(106, 28, 8, 8)); p.drawRect(QRectF(126, 28, 8, 8))
        p.setBrush(QColor("#c2562e")); p.setPen(QPen(QColor("#7c2d12"), 2)); p.drawRoundedRect(QRectF(80, 56, 80, 140), 5, 5)
        p.setPen(QPen(QColor("#7c2d12"), 1.5))
        for y in (88, 120, 152): p.drawLine(80, y, 160, y)
        for x, y1, y2 in ((120, 56, 88), (100, 88, 120), (140, 88, 120), (120, 120, 152), (100, 152, 196), (140, 152, 196)): p.drawLine(x, y1, x, y2)
        p.setBrush(QColor("#9a3f1f")); p.drawRoundedRect(QRectF(88, 94, 64, 20), 10, 10); p.setPen(QColor("#fde68a")); p.setFont(QFont("Segoe UI", 9, QFont.Bold)); p.drawText(QRectF(88, 94, 64, 20), Qt.AlignCenter, "8BitDo")
        a = 90 + 100 * (math.sin(s.ph) * .5 + .5) if s.on else 0; g = QColor("#38bdf8"); g.setAlpha(int(a)); p.setPen(Qt.NoPen); p.setBrush(g); p.drawEllipse(QPointF(120, 172), 13, 13)
        p.setBrush(QColor("#38bdf8") if s.on else QColor("#374151")); p.drawEllipse(QPointF(120, 172), 4, 4)
