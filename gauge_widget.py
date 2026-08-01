import math
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QConicalGradient
from PyQt5.QtWidgets import QWidget


class AnalogGauge(QWidget):
    def __init__(self, title, min_value, max_value, units,
                 warn_low=None, warn_high=None, danger_low=None, danger_high=None,
                 parent=None):
        super().__init__(parent)
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.units = units
        self.value = min_value
        self.warn_low = warn_low
        self.warn_high = warn_high
        self.danger_low = danger_low
        self.danger_high = danger_high

        self.start_angle = 225   # degrees, measured like a compass from bottom-left
        self.span_angle = -270   # sweep clockwise 270 degrees

        self.setMinimumSize(220, 220)

    def set_value(self, value):
        self.value = max(self.min_value, min(self.max_value, value))
        self.update()

    def _value_to_angle(self, value):
        fraction = (value - self.min_value) / (self.max_value - self.min_value)
        return self.start_angle + fraction * self.span_angle

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        painter.translate(self.width() / 2.0, self.height() / 2.0)
        painter.scale(side / 220.0, side / 220.0)

        self._draw_face(painter)
        self._draw_ticks(painter)
        self._draw_bands(painter)
        self._draw_needle(painter)
        self._draw_text(painter)

        painter.end()

    def _draw_face(self, p):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(24, 28, 34))
        p.drawEllipse(QRectF(-100, -100, 200, 200))
        p.setBrush(QColor(32, 38, 46))
        p.drawEllipse(QRectF(-92, -92, 184, 184))
        p.setPen(QPen(QColor(70, 78, 90), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(-92, -92, 184, 184))

    def _draw_bands(self, p):
        """Colored arc showing normal / warn / danger zones."""
        radius = 80
        rect = QRectF(-radius, -radius, radius * 2, radius * 2)

        def band(lo, hi, color):
            a1 = self._value_to_angle(lo)
            a2 = self._value_to_angle(hi)
            span = a2 - a1
            pen = QPen(color, 8, Qt.SolidLine, Qt.FlatCap)
            p.setPen(pen)
            p.drawArc(rect, int(a1 * 16), int(span * 16))

        lo = self.min_value
        hi = self.max_value

        if self.danger_low is not None:
            band(lo, self.danger_low, QColor(200, 60, 60))
            lo = self.danger_low
        if self.warn_low is not None:
            band(lo, self.warn_low, QColor(210, 160, 40))
            lo = self.warn_low
        normal_hi = self.warn_high if self.warn_high is not None else (
            self.danger_high if self.danger_high is not None else hi)
        band(lo, normal_hi, QColor(60, 170, 90))
        if self.warn_high is not None:
            nxt = self.danger_high if self.danger_high is not None else hi
            band(self.warn_high, nxt, QColor(210, 160, 40))
        if self.danger_high is not None:
            band(self.danger_high, hi, QColor(200, 60, 60))

    def _draw_ticks(self, p):
        p.setPen(QPen(QColor(180, 190, 200), 1.5))
        steps = 10
        for i in range(steps + 1):
            value = self.min_value + (self.max_value - self.min_value) * i / steps
            angle_deg = self._value_to_angle(value)
            angle_rad = math.radians(angle_deg)
            outer = 84
            inner = 72 if i % 1 == 0 else 78
            x1 = outer * math.cos(angle_rad)
            y1 = -outer * math.sin(angle_rad)
            x2 = inner * math.cos(angle_rad)
            y2 = -inner * math.sin(angle_rad)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            label_r = 62
            lx = label_r * math.cos(angle_rad)
            ly = -label_r * math.sin(angle_rad)
            p.setFont(QFont("Arial", 8))
            p.setPen(QColor(200, 205, 210))
            text = f"{value:.0f}"
            p.drawText(QRectF(lx - 15, ly - 8, 30, 16), Qt.AlignCenter, text)
            p.setPen(QPen(QColor(180, 190, 200), 1.5))

    def _draw_needle(self, p):
        angle_deg = self._value_to_angle(self.value)
        angle_rad = math.radians(angle_deg)
        length = 68
        tip = QPointF(length * math.cos(angle_rad), -length * math.sin(angle_rad))

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(230, 80, 70))
        back_angle1 = angle_rad + math.radians(90)
        back_angle2 = angle_rad - math.radians(90)
        base_w = 4
        b1 = QPointF(base_w * math.cos(back_angle1), -base_w * math.sin(back_angle1))
        b2 = QPointF(base_w * math.cos(back_angle2), -base_w * math.sin(back_angle2))
        p.drawPolygon(tip, b1, b2)

        p.setBrush(QColor(220, 220, 225))
        p.drawEllipse(QRectF(-8, -8, 16, 16))
        p.setBrush(QColor(60, 64, 70))
        p.drawEllipse(QRectF(-4, -4, 8, 8))

    def _draw_text(self, p):
        p.setPen(QColor(235, 238, 240))
        p.setFont(QFont("Arial", 13, QFont.Bold))
        p.drawText(QRectF(-90, 30, 180, 24), Qt.AlignCenter, f"{self.value:.1f} {self.units}")
        p.setFont(QFont("Arial", 9))
        p.setPen(QColor(160, 168, 176))
        p.drawText(QRectF(-90, 50, 180, 18), Qt.AlignCenter, self.title)
