#!/usr/bin/env python3
"""
Colorize a Kendrick script or a MATLAB program by concern, for the figures of the paper
(figures/Kcolorized.pdf and figures/Mcolorized.pdf).

Every token is colored with the concern it belongs to: the concern's name, its attribute and
the attribute's values, its parameters, the index variables bound to its attribute, and the
identifiers of the MATLAB program that implement the same notions. Keywords of Kendrick and
built-in functions of MATLAB are grey. Numbers take the color of the name they give a value
to. Everything else (entity names, N, t, punctuation) is black.

Usage:
    colorize.py kendrick "kendrick models/Model3.st" out.html [columns]
    colorize.py matlab "matlab models/M3" out.html [columns]   (concatenates the four .m files)

The HTML is printed to PDF with a headless browser (see make-figures.sh).
"""
import html
import re
import sys
from pathlib import Path

COLORS = {
    "SEIRS": "#ffff66",
    "MultiSpecies": "#ff7a5c",
    "MetaPopulation": "#66e0ff",
    "Isolation": "#b8f0a0",
    "keyword": "#d4d4d4",
}

# ---------------------------------------------------------------------------- Kendrick

K_KEYWORDS = {
    "KModel", "Composition", "Scenario", "Simulation", "Visualization",
    "attribute:", "parameters:", "equations:", "transitions:", "connectionMatrix:",
    "topology:", "ring", "line", "complete", "oneWay", "twoWay", "entry:",
    "transitionRate:", "model:", "on:", "var:", "sum_", "in", "range",
    "solver:", "scenario:", "from:", "to:", "step:",
    "plot:", "for:", "data:", "legendTitle:", "legends:", "xLabel:",
}

K_CONCERNS = {
    "SEIRS": ["SEIRS", "status", "S", "E", "I", "R", "beta", "lambda", "gamma", "mu", "sigma", "nu"],
    "MultiSpecies": ["MultiSpecies", "species", "humans", "birds", "k", "i"],
    "MetaPopulation": ["MetaPopulation", "zone", "rho", "p"] + [str(v) for v in range(1, 16)],
    "Isolation": ["Isolation", "isolation", "free", "isolated", "delta", "epsilon"],
}

# ---------------------------------------------------------------------------- MATLAB

M_BUILTINS = {
    "global", "repmat", "zeros", "cat", "reshape", "for", "end", "sum", "function", "length",
    "plot", "legend", "xlabel", "ylabel", "ode45",
}

# The AlgebraicPetri (Julia) version of Model 3, algebraicpetri models/*.jl, with the same rule: an identifier
# belongs to the concern whose notion it implements. The names of the type system (Pop, infect, disease,
# strata, birth, death) and the library (LabelledPetriNet, oapply_typed, typed_product...) belong to no
# concern, like the MATLAB built-ins; the transition names a concern gives to its own boxes belong to it.
J_CONCERNS = {
    "SEIRS": ["S", "E", "I", "R", "seirs", "seirs_uwd", "infection", "incubation", "recovery", "loss",
              "death_S", "death_E", "death_I", "death_R", "beta", "sigma", "gamma", "nu", "mu", "status", "d"],
    "MultiSpecies": ["humans", "birds", "species", "species_uwd", "infect_BB", "infect_HB", "disease_H", "disease_B",
                     "strata_H", "strata_B", "birth_H", "birth_B", "death_H", "death_B", "species_of", "infectious_of", "k"],
    "MetaPopulation": ["ring_model", "zones", "zone", "zone1", "migration", "np", "rho", "n", "i", "j", "z"],
    "Isolation": [],
}
M_CONCERNS = {
    "SEIRS": ["mu", "gamma", "beta", "nu", "sigma", "lambda", "S", "E", "I", "R",
              "dSdt", "dEdt", "dIdt", "dRdt", "SEIRSInfluenza"],
    "MultiSpecies": ["ns", "s", "Human", "Bird"],
    "MetaPopulation": ["np", "p", "q", "map", "rho", "deltaS", "deltaE", "deltaI", "deltaR"],
    "Isolation": ["IQ", "RQ", "dIQdt", "dRQdt", "delta", "epsilon"],
}


def index(concerns):
    m = {}
    for concern, names in concerns.items():
        for n in names:
            m[n] = concern
    return m


def span(text, concern):
    t = html.escape(text)
    if concern is None:
        return t
    return f'<span style="background:{COLORS[concern]}">{t}</span>'


TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_]*:?|[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|'[^']*'|\S|\s+")


def colorize_kendrick(text):
    lookup = index(K_CONCERNS)
    out = []
    entity = None  # concern of the KModel being read, for its numbers (matrix, range)
    for line in text.splitlines():
        stripped = line.strip()
        m = re.match(r"KModel\s+(\w+)", stripped)
        if m:
            entity = lookup.get(m.group(1))
        elif re.match(r"(Composition|Scenario|Simulation|Visualization)\b", stripped):
            entity = None
        # numbers take the color of the assigned name: the keyword's base, else the entity
        number_color = entity
        km = re.match(r"([A-Za-z][A-Za-z0-9_]*):", stripped)
        if km and km.group(1) + ":" not in K_KEYWORDS:
            number_color = lookup.get(km.group(1).split("_")[0])
        if stripped.startswith(("from:", "to:", "step:")):
            number_color = None
        pieces = []
        for tok in TOKEN.findall(line):
            if tok in K_KEYWORDS:
                pieces.append(span(tok, "keyword"))
            elif tok.startswith("'") and len(tok) >= 2 and tok.endswith("'"):
                inner = tok[1:-1]
                pieces.append("'" + span(inner, lookup.get(inner)) + "'")
            elif re.match(r"[A-Za-z]", tok):
                name, colon = (tok[:-1], ":") if tok.endswith(":") else (tok, "")
                parts = name.split("_")
                rendered = []
                for j, part in enumerate(parts):
                    # a run of index variables (ki, ip) is colored letter by letter
                    if j > 0 and len(part) > 1 and all(c in lookup and len(c) == 1 for c in part):
                        rendered.append("".join(span(c, lookup[c]) for c in part))
                    else:
                        rendered.append(span(part, lookup.get(part)))
                pieces.append("_".join(rendered) + colon)
            elif re.match(r"[0-9]", tok):
                pieces.append(span(tok, number_color))
            else:
                pieces.append(html.escape(tok))
        out.append("".join(pieces))
    return out


def colorize_matlab(text):
    lookup = index(M_CONCERNS)
    out = []
    for line in text.splitlines():
        number_color = None
        lm = re.match(r"\s*([A-Za-z]\w*)\s*(\(.*?\))?\s*=", line)
        if lm:
            number_color = lookup.get(lm.group(1))
        in_comment = False
        pieces = []
        for tok in TOKEN.findall(line):
            if in_comment:
                pieces.append(html.escape(tok))
            elif tok == "%":
                in_comment = True
                pieces.append(html.escape(tok))
            elif tok in M_BUILTINS:
                pieces.append(span(tok, "keyword"))
            elif tok.startswith("'") and len(tok) >= 2 and tok.endswith("'"):
                inner = tok[1:-1]
                pieces.append("'" + span(inner, lookup.get(inner)) + "'")
            elif re.match(r"[A-Za-z]", tok):
                pieces.append(span(tok, lookup.get(tok)))
            elif re.match(r"[0-9]", tok):
                pieces.append(span(tok, number_color))
            else:
                pieces.append(html.escape(tok))
        out.append("".join(pieces))
    return out


def page(lines, title, columns=1):
    """One HTML page; with columns > 1 the numbered lines are laid out in side-by-side columns."""
    per = -(-len(lines) // columns)
    cols = []
    for c in range(columns):
        chunk = lines[c * per:(c + 1) * per]
        cols.append('<div class="col">' + "\n".join(
            f'<div class="l"><span class="n">{c * per + i + 1}</span>{l if l else "&nbsp;"}</div>' for i, l in enumerate(chunk)) + '</div>')
    body = '<div class="cols">' + "\n".join(cols) + '</div>'
    legend = " ".join(f'<span style="background:{COLORS[c]}">&nbsp;{c}&nbsp;</span>' for c in ["SEIRS", "MultiSpecies", "MetaPopulation"])
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>
<style>
 @page {{ size: auto; margin: 6mm; }}
 body {{ margin: 0; font-family: "DejaVu Sans Mono", Consolas, monospace; font-size: 10pt; }}
 .cols {{ display: flex; gap: 2.2em; align-items: flex-start; }}
 .l {{ white-space: pre; line-height: 1.3; }}
 .n {{ display: inline-block; width: 2.2em; color: #777; text-align: right; margin-right: 0.8em; }}
 .legend {{ margin-bottom: 0.6em; font-size: 9pt; }}
</style></head><body><div class="legend">{legend} <span style="background:{COLORS['keyword']}">&nbsp;keywords / built-ins&nbsp;</span></div>
{body}
</body></html>"""


def main():
    kind, src, dst = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    columns = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    if kind == "kendrick":
        lines = colorize_kendrick(src.read_text(encoding="utf-8"))
        title = "Kendrick"
    else:
        text = ""
        for f in ["SEIRSInfluenza.m", "resolve.m", "visualization.m", "modelODEs.m"]:
            text += f"% ---- {f}\n" + (src / f).read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n") + "\n"
        lines = colorize_matlab(text)
        title = "MATLAB"
    dst.write_text(page(lines, title, columns), encoding="utf-8")


if __name__ == "__main__":
    main()
