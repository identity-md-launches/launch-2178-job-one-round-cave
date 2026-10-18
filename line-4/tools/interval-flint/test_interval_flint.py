import json
from fractions import Fraction
from pathlib import Path
import random
import subprocess
import sys
import unittest

import interval_flint as f


def request(expression, variables, within=None, to=None):
    return {"variables": variables, "expression": expression,
            "to": to, "within": within}


class IntervalFlintTests(unittest.TestCase):
    def test_demo_encloses_transfer_time(self):
        result = f.evaluate(f.demo_request())
        self.assertEqual((result["lower"], result["upper"], result["unit"]),
                         ("3.6", "5.5", "s"))
        self.assertEqual(result["base_unit"], "s")
        self.assertTrue(result["within"]["fully_within"])

    def test_exact_dimensions_and_conversion(self):
        result = f.evaluate(request("distance / time",
                                    {"distance": ["9.9 km", "10.1 km"],
                                     "time": ["1.9 h", "2.1 h"]}, to="km/h"))
        self.assertEqual(Fraction(result["lower"]), Fraction(99, 21))
        self.assertEqual(Fraction(result["upper"]), Fraction(101, 19))
        self.assertEqual(result["base_unit"], "m*s^-1")

    def test_dependency_widens_honestly(self):
        result = f.evaluate(request("x-x", {"x": ["1 m", "2 m"]}))
        self.assertEqual((result["lower"], result["upper"]), ("-1", "1"))

    def test_zero_crossing_even_and_odd_powers(self):
        variables = {"x": ["-2 m", "3 m"]}
        self.assertEqual(
            (f.evaluate(request("x^2", variables))["lower"],
             f.evaluate(request("x^2", variables))["upper"]), ("0", "9"))
        self.assertEqual(
            (f.evaluate(request("x^3", variables))["lower"],
             f.evaluate(request("x^3", variables))["upper"]), ("-8", "27"))
        with self.assertRaises(f.engine.UnitError):
            f.evaluate(request("x^-1", variables))

    def test_within_inclusive_and_overlap(self):
        variables = {"x": ["1 m", "2 m"]}
        same = f.evaluate(request("x", variables, ["1 m", "2 m"]))["within"]
        self.assertTrue(same["fully_within"])
        partial = f.evaluate(request("x", variables, ["1.5 m", "3 m"]))["within"]
        self.assertFalse(partial["fully_within"])
        self.assertTrue(partial["overlaps"])
        disjoint = f.evaluate(request("x", variables, ["3 m", "4 m"]))["within"]
        self.assertFalse(disjoint["overlaps"])

    def test_invalid_dimensions_and_limits(self):
        with self.assertRaises(f.IntervalError):
            f.evaluate(request("x", {"x": ["1 m", "2 s"]}))
        with self.assertRaises(f.engine.UnitError):
            f.evaluate(request("x + duration", {"x": ["1 m", "2 m"], "duration": ["1 s", "2 s"]}))
        with self.assertRaises(f.IntervalError):
            f.evaluate(request("x", {"x": ["1 m", "2 m"]}, ["1 s", "2 s"]))
        with self.assertRaises(f.IntervalError):
            f.evaluate(request("x", {"x": ["2 m", "1 m"]}))
        with self.assertRaises(f.IntervalError):
            f.evaluate(request("x", {"m": ["1 m", "2 m"]}))

    def test_random_corner_products_against_fraction_oracle(self):
        rng = random.Random(26)
        for _ in range(200):
            a, b = sorted((rng.randint(-50, 50), rng.randint(-50, 50)))
            c, d = sorted((rng.randint(-50, 50), rng.randint(-50, 50)))
            result = f.evaluate(request("x*y", {"x": [str(a), str(b)],
                                                   "y": [str(c), str(d)]}))
            oracle = [Fraction(x * y) for x in (a, b) for y in (c, d)]
            self.assertEqual((Fraction(result["lower"]), Fraction(result["upper"])),
                             (min(oracle), max(oracle)))

    def test_random_nonzero_divisions_against_fraction_oracle(self):
        rng = random.Random(2601)
        for _ in range(200):
            a, b = sorted((rng.randint(-50, 50), rng.randint(-50, 50)))
            c, d = sorted((rng.randint(1, 50), rng.randint(1, 50)))
            if rng.randrange(2):
                c, d = -d, -c
            result = f.evaluate(request("x/y", {"x": [str(a), str(b)],
                                                   "y": [str(c), str(d)]}))
            oracle = [Fraction(x, y) for x in (a, b) for y in (c, d)]
            self.assertEqual((Fraction(result["lower"]), Fraction(result["upper"])),
                             (min(oracle), max(oracle)))

    def test_json_and_statuses(self):
        with self.assertRaises(f.IntervalError):
            f.decode(b'{"variables":{},"variables":{}}')
        with self.assertRaises(f.IntervalError):
            f.decode(b'{"variables":{"x":[1,2]}}')
        script = Path(__file__).with_name("interval_flint.py")
        for payload, status in [
            (None, 0),
            (request("x", {"x": ["1 m", "2 m"]}, ["1 m", "1.5 m"]), 1),
            (request("x/0", {"x": ["1 m", "2 m"]}), 2),
        ]:
            command = ["demo"] if payload is None else ["run"]
            proc = subprocess.run([sys.executable, "-B", str(script), *command],
                                  input=None if payload is None else json.dumps(payload),
                                  text=True, capture_output=True, check=False)
            self.assertEqual(proc.returncode, status, proc.stderr)
            if status == 2:
                self.assertFalse(proc.stdout)
            else:
                self.assertTrue(proc.stdout)


if __name__ == "__main__":
    unittest.main()
