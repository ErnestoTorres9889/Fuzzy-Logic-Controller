"""
plant_model.py

A lightweight simulation of a commercial-building water distribution
system fed by a VFD-driven booster pump, so the fuzzy controller has
something realistic (with lag and disturbances) to control.

Model:
    - Pump speed (0-100%) drives a target discharge pressure via a
      pump curve (roughly linear + slight droop under demand).
    - Actual pressure moves toward that target with first-order lag
      (pipe/tank inertia) rather than jumping instantly.
    - Random demand fluctuation (fixtures opening/closing across the
      building) perturbs pressure, similar to real usage patterns.
"""

import random


class WaterSystemPlant:
    def __init__(self, initial_pressure=35.0):
        self.pressure = initial_pressure
        self.pump_speed = 50.0          # %, 0-100
        self.demand_disturbance = 10.0  # 0-100 slider: how "busy" the building is
        self.time_constant = 2.5        # seconds, pipe/tank lag

    def pump_curve_pressure(self):
        """Target steady-state pressure the pump would produce at the
        current speed, reduced somewhat under high demand (droop)."""
        base = self.pump_speed * 1.0  # ~1 psi per % speed, simplified
        droop = (self.demand_disturbance / 100.0) * 8.0
        return max(0.0, base - droop)

    def step(self, speed_adjustment, dt):
        """Apply a speed trim (from the fuzzy controller) and advance
        the plant by dt seconds."""
        self.pump_speed = max(0.0, min(100.0, self.pump_speed + speed_adjustment * dt / 5.0))

        target = self.pump_curve_pressure()
        # First-order lag toward target
        alpha = dt / (self.time_constant + dt)
        self.pressure += (target - self.pressure) * alpha

        # Random demand noise (fixtures, other floors, etc.)
        noise = random.uniform(-1.0, 1.0) * (0.3 + self.demand_disturbance / 100.0)
        self.pressure = max(0.0, self.pressure + noise)

        return self.pressure
