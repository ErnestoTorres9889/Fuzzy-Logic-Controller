from dataclasses import dataclass, field


def triangle(x: float, a: float, b: float, c: float) -> float:
    """Triangular membership function with support (a, c) and peak at b."""
    if x <= a or x >= c:
        return 0.0
    if a < x <= b:
        return (x - a) / (b - a) if b != a else 1.0
    if b < x < c:
        return (c - x) / (c - b) if c != b else 1.0
    return 0.0


@dataclass
class MembershipSet:
    """A named triangular membership function, kept together with its
    (a, b, c) breakpoints so the UI can plot the exact shape used by
    the controller (no duplicated magic numbers between logic + plot)."""
    name: str
    a: float
    b: float
    c: float

    def mu(self, x: float) -> float:
        return triangle(x, self.a, self.b, self.c)


class FuzzyPressureController:
    """2-input / 1-output Sugeno fuzzy controller for a VFD-driven
    booster pump, controlling discharge pressure to a setpoint."""

    # Universe of discourse for the error input (psi)
    ERROR_SETS = [
        MembershipSet("N", -50.0, -25.0, 0.0),
        MembershipSet("Z", -10.0, 0.0, 10.0),
        MembershipSet("P", 0.0, 25.0, 50.0),
    ]

    # Universe of discourse for the delta-error input (psi/s)
    DELTA_SETS = [
        MembershipSet("N", -30.0, -15.0, 0.0),
        MembershipSet("Z", -6.0, 0.0, 6.0),
        MembershipSet("P", 0.0, 15.0, 30.0),
    ]

    # Output singleton values (% VFD speed trim)
    OUTPUT_SINGLETONS = {
        "NB": -50.0,
        "NS": -25.0,
        "Z": 0.0,
        "PS": 25.0,
        "PB": 50.0,
    }

    # Rule base: RULES[error_set][delta_set] -> output label
    RULES = {
        "N": {"N": "NB", "Z": "NB", "P": "NS"},
        "Z": {"N": "NS", "Z": "Z", "P": "PS"},
        "P": {"N": "PS", "Z": "PB", "P": "PB"},
    }

    def __init__(self, setpoint: float, output_limit: float = 50.0,
                 slew_rate_limit: float = 15.0):
        self.setpoint = setpoint
        self.previous_error = 0.0
        self.output_limit = output_limit
        # Max % the output is allowed to change per call, to emulate a
        # real VFD ramp limit and avoid mechanically unrealistic jumps.
        self.slew_rate_limit = slew_rate_limit
        self._previous_output = 0.0

        # Diagnostics from the last update(), used by the UI to draw
        # the membership plots / firing strengths without recomputation.
        self.last_error = 0.0
        self.last_delta_error = 0.0
        self.last_error_membership = {}
        self.last_delta_membership = {}
        self.last_rule_firing = {}  # rule label -> (error_set, delta_set, strength)

    def fuzzify(self, value: float, sets):
        return {s.name: s.mu(value) for s in sets}

    def update(self, current_pressure: float, dt: float) -> float:
        error = self.setpoint - current_pressure
        delta_error = (error - self.previous_error) / dt if dt > 0 else 0.0
        self.previous_error = error

        e_mu = self.fuzzify(error, self.ERROR_SETS)
        de_mu = self.fuzzify(delta_error, self.DELTA_SETS)

        numerator = 0.0
        denominator = 0.0
        firing = {}

        for e_name, e_deg in e_mu.items():
            if e_deg == 0.0:
                continue
            for de_name, de_deg in de_mu.items():
                if de_deg == 0.0:
                    continue
                strength = min(e_deg, de_deg)  # fuzzy AND
                if strength == 0.0:
                    continue
                out_label = self.RULES[e_name][de_name]
                singleton = self.OUTPUT_SINGLETONS[out_label]
                numerator += strength * singleton
                denominator += strength
                firing[f"e={e_name},de={de_name}->{out_label}"] = (
                    e_name, de_name, strength
                )

        raw_output = numerator / denominator if denominator != 0 else 0.0
        raw_output = max(-self.output_limit, min(self.output_limit, raw_output))

        # Slew-rate limiting: real VFDs cannot jump instantly.
        delta_out = raw_output - self._previous_output
        delta_out = max(-self.slew_rate_limit, min(self.slew_rate_limit, delta_out))
        output = self._previous_output + delta_out
        self._previous_output = output

        # Stash diagnostics for the UI
        self.last_error = error
        self.last_delta_error = delta_error
        self.last_error_membership = e_mu
        self.last_delta_membership = de_mu
        self.last_rule_firing = firing

        return output
