import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDoubleSpinBox, QSlider, QGroupBox, QFrame, QTextEdit
)

from fuzzy_controller import FuzzyPressureController
from plant_model import WaterSystemPlant
from gauge_widget import AnalogGauge
from membership_widget import MembershipCanvas

DARK_BG = "#181c22"
PANEL_BG = "#20262e"
ACCENT = "#4aa3e0"
TEXT = "#c8ced4"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commercial Booster Pump \u2014 Fuzzy Logic Controller")
        self.resize(1180, 760)

        self.setpoint = 50.0
        self.controller = FuzzyPressureController(setpoint=self.setpoint)
        self.plant = WaterSystemPlant(initial_pressure=35.0)
        self.dt = 0.5  # seconds per simulation tick
        self.running = False
        self.elapsed = 0.0

        self._build_ui()
        self._apply_dark_theme()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self._build_gauge_panel(), 2)
        body.addWidget(self._build_membership_panel(), 3)
        body.addWidget(self._build_control_panel(), 2)
        root.addLayout(body, 1)

        root.addWidget(self._build_log_panel())

    def _build_header(self):
        frame = QFrame()
        frame.setObjectName("headerFrame")
        layout = QHBoxLayout(frame)
        title = QLabel("BOOSTER PUMP STATION \u2014 FUZZY LOGIC CONTROL")
        title.setFont(QFont("Arial", 15, QFont.Bold))
        title.setStyleSheet(f"color: {ACCENT};")
        subtitle = QLabel("Commercial building water service  \u2022  Sugeno FLC (error + \u0394error, 3\u00d73 rule base)")
        subtitle.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
        text_box = QVBoxLayout()
        text_box.addWidget(title)
        text_box.addWidget(subtitle)
        layout.addLayout(text_box)
        layout.addStretch()

        self.status_label = QLabel("\u25CF STOPPED")
        self.status_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.status_label.setStyleSheet("color: #d05a5a;")
        layout.addWidget(self.status_label)
        return frame

    def _build_gauge_panel(self):
        box = QGroupBox("Field Instruments")
        layout = QVBoxLayout(box)

        self.pressure_gauge = AnalogGauge(
            "Discharge Pressure", 0, 100, "psi",
            warn_low=35, warn_high=None, danger_low=20, danger_high=None,
        )
        self.speed_gauge = AnalogGauge(
            "VFD Pump Speed", 0, 100, "%",
            warn_high=90, danger_high=100,
        )
        layout.addWidget(self.pressure_gauge)
        layout.addWidget(self.speed_gauge)
        return box

    def _build_membership_panel(self):
        box = QGroupBox("Fuzzy Inference \u2014 Live Membership Function Scale Simulation")
        layout = QVBoxLayout(box)
        self.membership_canvas = MembershipCanvas(self.controller)
        layout.addWidget(self.membership_canvas)

        self.rule_label = QLabel("Active rules: \u2014")
        self.rule_label.setWordWrap(True)
        self.rule_label.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
        layout.addWidget(self.rule_label)
        return box

    def _build_control_panel(self):
        box = QGroupBox("Controls")
        layout = QVBoxLayout(box)

        # Setpoint
        layout.addWidget(QLabel("Pressure Setpoint (psi)"))
        self.setpoint_spin = QDoubleSpinBox()
        self.setpoint_spin.setRange(10.0, 90.0)
        self.setpoint_spin.setValue(self.setpoint)
        self.setpoint_spin.valueChanged.connect(self._on_setpoint_changed)
        layout.addWidget(self.setpoint_spin)

        # Demand disturbance
        layout.addWidget(QLabel("Building Demand (fixture usage)"))
        self.demand_slider = QSlider(Qt.Horizontal)
        self.demand_slider.setRange(0, 100)
        self.demand_slider.setValue(int(self.plant.demand_disturbance))
        self.demand_slider.valueChanged.connect(self._on_demand_changed)
        layout.addWidget(self.demand_slider)
        self.demand_value_label = QLabel(f"{self.plant.demand_disturbance:.0f} %")
        self.demand_value_label.setStyleSheet(f"color: {TEXT};")
        layout.addWidget(self.demand_value_label)

        layout.addSpacing(10)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self._start)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.reset_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

        readout = QGridLayout()
        self.error_readout = QLabel("0.0")
        self.delta_readout = QLabel("0.0")
        self.output_readout = QLabel("0.0")
        for lbl in (self.error_readout, self.delta_readout, self.output_readout):
            lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        readout.addWidget(QLabel("Error (psi):"), 0, 0)
        readout.addWidget(self.error_readout, 0, 1)
        readout.addWidget(QLabel("\u0394 Error (psi/s):"), 1, 0)
        readout.addWidget(self.delta_readout, 1, 1)
        readout.addWidget(QLabel("Speed trim (%):"), 2, 0)
        readout.addWidget(self.output_readout, 2, 1)
        layout.addLayout(readout)

        return box

    def _build_log_panel(self):
        box = QGroupBox("Event Log")
        layout = QVBoxLayout(box)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(110)
        layout.addWidget(self.log)
        return box

    def _apply_dark_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background-color: {DARK_BG}; color: {TEXT}; }}
            QGroupBox {{
                border: 1px solid #3a4048; border-radius: 6px; margin-top: 10px;
                font-weight: bold; color: {ACCENT};
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
            #headerFrame {{ background-color: {PANEL_BG}; border-radius: 6px; padding: 6px; }}
            QPushButton {{
                background-color: #2c333c; border: 1px solid #47505b; border-radius: 4px;
                padding: 6px; color: {TEXT};
            }}
            QPushButton:hover {{ background-color: #384250; }}
            QDoubleSpinBox, QTextEdit {{
                background-color: #12161b; border: 1px solid #3a4048; color: {TEXT};
            }}
        """)

    # ----------------------------------------------------------- handlers
    def _on_setpoint_changed(self, value):
        self.setpoint = value
        self.controller.setpoint = value
        self._log(f"Setpoint changed to {value:.1f} psi")

    def _on_demand_changed(self, value):
        self.plant.demand_disturbance = float(value)
        self.demand_value_label.setText(f"{value} %")

    def _start(self):
        if not self.running:
            self.running = True
            self.timer.start(int(self.dt * 1000))
            self.status_label.setText("\u25CF RUNNING")
            self.status_label.setStyleSheet("color: #5ac07a;")
            self._log("Controller started.")

    def _stop(self):
        if self.running:
            self.running = False
            self.timer.stop()
            self.status_label.setText("\u25CF STOPPED")
            self.status_label.setStyleSheet("color: #d05a5a;")
            self._log("Controller stopped.")

    def _reset(self):
        self._stop()
        self.plant = WaterSystemPlant(initial_pressure=35.0)
        self.controller = FuzzyPressureController(setpoint=self.setpoint)
        self.elapsed = 0.0
        self.membership_canvas.controller = self.controller
        self._refresh_displays()
        self._log("System reset.")

    def _log(self, message):
        self.log.append(f"[t={self.elapsed:5.1f}s] {message}")

    # -------------------------------------------------------------- loop
    def _tick(self):
        self.elapsed += self.dt
        adjustment = self.controller.update(self.plant.pressure, self.dt)
        self.plant.step(adjustment, self.dt)
        self._refresh_displays()

    def _refresh_displays(self):
        self.pressure_gauge.set_value(self.plant.pressure)
        self.speed_gauge.set_value(self.plant.pump_speed)
        self.membership_canvas.refresh()

        c = self.controller
        self.error_readout.setText(f"{c.last_error:.2f}")
        self.delta_readout.setText(f"{c.last_delta_error:.2f}")
        self.output_readout.setText(f"{c._previous_output:.2f}")

        if c.last_rule_firing:
            top_rules = sorted(c.last_rule_firing.items(), key=lambda kv: -kv[1][2])[:3]
            text = "  |  ".join(f"{label} (\u03bc={strength:.2f})"
                                 for label, (_, _, strength) in top_rules)
            self.rule_label.setText(f"Active rules: {text}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
