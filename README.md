# Commercial Booster Pump — Fuzzy Logic Controller (PyQt5)

A desktop HMI-style app simulating a fuzzy-logic-controlled water
booster pump for a commercial building, with live analog gauges and
membership-function visualization.

## What changed vs. your original snippet
- **2-input Sugeno FLC** (error *and* Δerror) with a classic 3×3 rule
  table, instead of a single-input controller. This is what makes it
  behave like a real controller instead of oscillating — the
  Δerror term acts like the "D" in PID, damping overshoot.
- **VFD slew-rate limiting** on the output, so pump speed ramps
  realistically instead of jumping.
- **Plant model** (`plant_model.py`) with pump-curve droop under
  demand, first-order lag, and random demand noise, so there's a
  believable system to control.
- **Live visualization**: analog gauges for pressure/speed, and
  matplotlib membership-function plots that show exactly which fuzzy
  sets are firing at each instant.

## Files
- `fuzzy_controller.py` — the fuzzy logic (membership functions, rule
  base, Sugeno inference, defuzzification)
- `plant_model.py` — simulated pump/pressure system
- `gauge_widget.py` — hand-drawn analog gauge (QPainter)
- `membership_widget.py` — embedded matplotlib membership plots
- `main.py` — the application window / simulation loop

## Run it
```bash
pip install PyQt5 matplotlib
python main.py
```

Click **Start**, adjust the **Setpoint** and **Building Demand**
slider, and watch the gauges + membership plots respond in real time.
The event log at the bottom timestamps setpoint/demand changes.

## Why not MATLAB
MATLAB's Fuzzy Logic Toolbox is convenient for *designing* rules
offline, but everything it provides (triangular MFs, rule inference,
defuzzification) is implemented directly here in plain Python, so the
app runs standalone with no license dependency. If you want to
prototype rule tables interactively before hand-coding them, MATLAB's
`fuzzyLogicDesigner` is a reasonable tool for that step — just not
needed for the running application itself.
