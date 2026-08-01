"""
membership_widget.py

Embeds matplotlib in the PyQt window to visualize the fuzzy controller's
membership functions and where the current crisp error / delta-error
values fall on them -- this is the piece that makes the fuzzy logic
"visible" rather than a black box.
"""

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

FACE = "#20262e"
GRID = "#3a4048"
TEXT = "#c8ced4"
COLORS = {"N": "#e05a5a", "Z": "#e0c85a", "P": "#5ac07a"}


class MembershipCanvas(FigureCanvas):
    def __init__(self, controller, parent=None):
        self.controller = controller
        fig = Figure(figsize=(5, 4), facecolor=FACE)
        super().__init__(fig)
        self.setParent(parent)

        self.ax_error = fig.add_subplot(211)
        self.ax_delta = fig.add_subplot(212)
        fig.subplots_adjust(hspace=0.55, left=0.08, right=0.97, top=0.92, bottom=0.12)

        self._style_axis(self.ax_error, "Error  (setpoint - pressure)  [psi]")
        self._style_axis(self.ax_delta, "\u0394 Error  (rate of change)  [psi/s]")

        self.refresh()

    def _style_axis(self, ax, title):
        ax.set_facecolor(FACE)
        ax.set_title(title, color=TEXT, fontsize=9, loc="left")
        ax.tick_params(colors=TEXT, labelsize=7)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        ax.grid(True, color=GRID, linewidth=0.5, alpha=0.6)

    def _plot_sets(self, ax, sets, current_value, title):
        ax.clear()
        self._style_axis(ax, title)
        lo = min(s.a for s in sets)
        hi = max(s.c for s in sets)
        xs = np.linspace(lo, hi, 400)
        for s in sets:
            ys = [s.mu(x) for x in xs]
            color = COLORS.get(s.name, "#8888ff")
            ax.plot(xs, ys, color=color, linewidth=1.6, label=s.name)
            ax.fill_between(xs, ys, color=color, alpha=0.08)

        ax.axvline(current_value, color="#ffffff", linewidth=1.2, linestyle="--", alpha=0.85)
        ax.set_ylim(-0.05, 1.1)
        ax.set_xlim(lo, hi)
        ax.legend(loc="upper right", fontsize=7, facecolor=FACE, edgecolor=GRID,
                   labelcolor=TEXT, framealpha=0.6)

    def refresh(self):
        c = self.controller
        self._plot_sets(self.ax_error, c.ERROR_SETS, c.last_error,
                         "Error  (setpoint - pressure)  [psi]")
        self._plot_sets(self.ax_delta, c.DELTA_SETS, c.last_delta_error,
                         "\u0394 Error  (rate of change)  [psi/s]")
        self.draw_idle()
