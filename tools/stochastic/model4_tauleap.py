#!/usr/bin/env python3
"""
Runs Model 4 once with its own solver (the ODEs, Runge-Kutta) and ten times by tau-leaping, one run per
seed from 1 to 10, and summarizes each run: the infectious humans per zone (their peak over the run and
their number on day 1500) and the infectious birds on day 1500 (in all, the number of zones where they
persist, the smallest zone). This is the stochastic reading of Section 5.2 of the paper.

    python3 tools/stochastic/model4_tauleap.py [JAR]
        (from any directory; JAR defaults to ../JKendrick/target/jkendrick.jar beside this repository;
         needs Java 23, from JAVA_HOME or the PATH)

Writes generated/model4-tauleap.json and prints a summary.
"""
import csv
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL4 = os.path.join(ROOT, "kendrick models", "Model4.st")
DEFAULT_JAR = os.path.join(os.path.dirname(ROOT), "JKendrick", "target", "jkendrick.jar")
JAVA = os.path.join(os.environ["JAVA_HOME"], "bin", "java") if "JAVA_HOME" in os.environ else "java"
OUTPUT = os.path.join(ROOT, "generated", "model4-tauleap.json")

ODE_SOLVER_CLAUSE = "    solver: 'rungeKutta';\n"
ZONES = range(1, 16)
SEEDS = range(1, 11)


def tau_leap_clause(seed):
    return f"    solver: 'tauLeap';\n    runs: 1;\n    seed: {seed};\n"


def model4_source():
    with open(MODEL4, encoding="utf-8") as f:
        source = f.read().replace("\r\n", "\n")
    assert ODE_SOLVER_CLAUSE in source, "Model4.st no longer has the solver clause this script replaces"
    return source


def run_model4(source, solver_clause, name, jar, workdir):
    """Runs Model 4 with its solver clause replaced and returns the rows of its trajectory."""
    script = os.path.join(workdir, name + ".st")
    with open(script, "w", encoding="utf-8") as f:
        f.write(source.replace(ODE_SOLVER_CLAUSE, solver_clause))
    trajectory = os.path.join(workdir, name + ".csv")
    subprocess.run([JAVA, "-cp", jar, "jKendrick.Kendrick", script, "--csv", trajectory], check=True,
                   stdout=subprocess.DEVNULL)
    with open(trajectory, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def count_in_zone(row, status, species, zone_number):
    """Individuals of the given status and species in the zone, summed over the isolation attribute.

    The columns are named status_species_zone_isolation (I_humans_3_free); the trailing underscore of the
    prefix keeps zone 1 apart from zone 10."""
    prefix = f"{status}_{species}_{zone_number}_"
    return sum(float(value) for column, value in row.items() if column.startswith(prefix))


def summary(rows):
    last = rows[-1]
    peak_humans = [max(count_in_zone(row, "I", "humans", zone) for row in rows) for zone in ZONES]
    day1500_humans = [count_in_zone(last, "I", "humans", zone) for zone in ZONES]
    day1500_birds = [count_in_zone(last, "I", "birds", zone) for zone in ZONES]
    return {
        "day": float(last["t"]),
        "infectious_humans_per_zone_peak": [min(peak_humans), max(peak_humans)],
        "infectious_humans_per_zone_on_day": [min(day1500_humans), max(day1500_humans)],
        "infectious_birds_on_day": sum(day1500_birds),
        # at least one infectious bird: tau-leaping counts are integers, and the ODE values are all far
        # above it (100 in the smallest zone)
        "zones_with_infectious_birds": sum(birds > 0.5 for birds in day1500_birds),
        "infectious_birds_smallest_zone": min(day1500_birds),
    }


def print_summary(label, result):
    peak = result["infectious_humans_per_zone_peak"]
    on_day = result["infectious_humans_per_zone_on_day"]
    print(f"{label:8} infectious humans per zone: peak {peak[0]:.2f} to {peak[1]:.2f}, "
          f"day {result['day']:.0f} {on_day[0]:.2f} to {on_day[1]:.2f} | "
          f"infectious birds on day {result['day']:.0f}: {result['infectious_birds_on_day']:.0f}, "
          f"in {result['zones_with_infectious_birds']} zones, "
          f"smallest zone {result['infectious_birds_smallest_zone']:.0f}")


def main():
    if len(sys.argv) > 2:
        sys.exit(__doc__)
    jar = sys.argv[1] if len(sys.argv) == 2 else DEFAULT_JAR
    source = model4_source()
    with tempfile.TemporaryDirectory() as workdir:
        ode = summary(run_model4(source, ODE_SOLVER_CLAUSE, "ode", jar, workdir))
        print_summary("ODE", ode)
        tau_leaping = []
        for seed in SEEDS:
            result = {"seed": seed, **summary(run_model4(source, tau_leap_clause(seed), f"seed{seed}", jar, workdir))}
            print_summary(f"seed {seed}", result)
            tau_leaping.append(result)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"model": "Model4", "ode": ode, "tau_leaping": tau_leaping}, f, indent=2)
        f.write("\n")
    print(f"written to {os.path.relpath(OUTPUT, ROOT)}")


if __name__ == "__main__":
    main()
