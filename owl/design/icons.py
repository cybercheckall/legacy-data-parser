"""
Owl brand + crisp HiDPI shell icons (no emoji / wordmark).
"""

import os
from math import cos, sin, radians

from PyQt6.QtCore import Qt, QRectF, QPointF, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath

from owl.paths import BRAND_DIR

OWL_ICON_CANDIDATES = (
    "owl_icon.png",
    "owl-.svg",
    "owl_icon.ico",
    "owl_icon.jpg",
)

# Logical icon size used in the toolbar
ICON_LOGICAL = 18


def owl_logo_path() -> str | None:
    for name in OWL_ICON_CANDIDATES:
        path = os.path.join(BRAND_DIR, name)
        if os.path.isfile(path):
            return path
    return None


def owl_logo_pixmap(size: int = 22) -> QPixmap:
    path = owl_logo_path()
    if path:
        pix = QPixmap(path)
        if not pix.isNull():
            return pix.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor("#5b4636")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(1, 1, size - 2, size - 2)
    p.setBrush(QBrush(QColor("#f5f0e8")))
    p.drawEllipse(size // 4, size // 3, size // 2, size // 2)
    p.end()
    return pix


def owl_logo_icon(size: int = 22) -> QIcon:
    return QIcon(owl_logo_pixmap(size))


def _paint_icon(logical: int, color: QColor, draw_fn, fill: bool = False) -> QIcon:
    """Paint at 2× for Retina sharpness."""
    dpr = 2.0
    px = int(logical * dpr)
    pix = QPixmap(px, px)
    pix.fill(Qt.GlobalColor.transparent)
    pix.setDevicePixelRatio(dpr)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    pen = QPen(
        color,
        1.65,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin,
    )
    painter.setPen(pen)
    if fill:
        painter.setBrush(QBrush(color))
    else:
        painter.setBrush(Qt.BrushStyle.NoBrush)
    draw_fn(painter, logical, color)
    painter.end()

    icon = QIcon()
    icon.addPixmap(pix)
    return icon


def icon_back(size: int = ICON_LOGICAL, color: str = "#3c4043") -> QIcon:
    c = QColor(color)

    def draw(p: QPainter, s: int, _c: QColor):
        # Chevron pointing left, optically centered
        x0, x1 = s * 0.62, s * 0.34
        y0, y1, y2 = s * 0.28, s * 0.50, s * 0.72
        p.drawLine(QPointF(x0, y0), QPointF(x1, y1))
        p.drawLine(QPointF(x1, y1), QPointF(x0, y2))

    return _paint_icon(size, c, draw)


def icon_forward(size: int = ICON_LOGICAL, color: str = "#3c4043") -> QIcon:
    c = QColor(color)

    def draw(p: QPainter, s: int, _c: QColor):
        x0, x1 = s * 0.38, s * 0.66
        y0, y1, y2 = s * 0.28, s * 0.50, s * 0.72
        p.drawLine(QPointF(x0, y0), QPointF(x1, y1))
        p.drawLine(QPointF(x1, y1), QPointF(x0, y2))

    return _paint_icon(size, c, draw)


def icon_reload(size: int = ICON_LOGICAL, color: str = "#3c4043") -> QIcon:
    c = QColor(color)

    def draw(p: QPainter, s: int, col: QColor):
        m = s * 0.20
        rect = QRectF(m, m, s - 2 * m, s - 2 * m)
        p.drawArc(rect, 55 * 16, 270 * 16)
        # Arrow head at top-right of arc
        tip = QPointF(s * 0.72, s * 0.22)
        p.setBrush(QBrush(col))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.moveTo(tip)
        path.lineTo(tip.x() - 4.2, tip.y() + 0.8)
        path.lineTo(tip.x() + 0.2, tip.y() + 4.5)
        path.closeSubpath()
        p.drawPath(path)

    return _paint_icon(size, c, draw)


def icon_star(size: int = ICON_LOGICAL, color: str = "#3c4043") -> QIcon:
    c = QColor(color)

    def draw(p: QPainter, s: int, _c: QColor):
        cx, cy, r = s / 2, s / 2 + 0.2, s * 0.36
        pts = []
        for i in range(5):
            ang = -90 + i * 72
            pts.append(QPointF(cx + r * cos(radians(ang)), cy + r * sin(radians(ang))))
            ang2 = ang + 36
            pts.append(QPointF(cx + r * 0.42 * cos(radians(ang2)), cy + r * 0.42 * sin(radians(ang2))))
        path = QPainterPath(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        path.closeSubpath()
        p.drawPath(path)

    return _paint_icon(size, c, draw)


def icon_shield(size: int = ICON_LOGICAL, color: str = "#ea8600") -> QIcon:
    c = QColor(color)

    def draw(p: QPainter, s: int, col: QColor):
        path = QPainterPath()
        path.moveTo(s * 0.50, s * 0.14)
        path.lineTo(s * 0.80, s * 0.28)
        path.lineTo(s * 0.80, s * 0.50)
        path.cubicTo(s * 0.80, s * 0.72, s * 0.62, s * 0.84, s * 0.50, s * 0.90)
        path.cubicTo(s * 0.38, s * 0.84, s * 0.20, s * 0.72, s * 0.20, s * 0.50)
        path.lineTo(s * 0.20, s * 0.28)
        path.closeSubpath()
        fill = QColor(col)
        fill.setAlpha(28)
        p.setBrush(QBrush(fill))
        p.drawPath(path)

    return _paint_icon(size, c, draw)


def icon_menu(size: int = ICON_LOGICAL, color: str = "#3c4043") -> QIcon:
    """Vertical kebab (⋮) — cleaner than three loose dots."""
    c = QColor(color)

    def draw(p: QPainter, s: int, col: QColor):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(col))
        r = 1.55
        cx = s / 2
        for y in (s * 0.28, s * 0.50, s * 0.72):
            p.drawEllipse(QPointF(cx, y), r, r)

    return _paint_icon(size, c, draw)


def icon_plus(size: int = 16, color: str = "#3c4043") -> QIcon:
    c = QColor(color)

    def draw(p: QPainter, s: int, _c: QColor):
        m = s * 0.30
        p.drawLine(QPointF(s / 2, m), QPointF(s / 2, s - m))
        p.drawLine(QPointF(m, s / 2), QPointF(s - m, s / 2))

    return _paint_icon(size, c, draw)


def icon_close(size: int = 12, color: str = "#5f6368") -> QIcon:
    """Clear × for tab close buttons."""
    c = QColor(color)

    def draw(p: QPainter, s: int, _c: QColor):
        m = s * 0.28
        p.setPen(QPen(c, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(m, m), QPointF(s - m, s - m))
        p.drawLine(QPointF(s - m, m), QPointF(m, s - m))

    return _paint_icon(size, c, draw)


def icon_size() -> QSize:
    return QSize(ICON_LOGICAL, ICON_LOGICAL)
