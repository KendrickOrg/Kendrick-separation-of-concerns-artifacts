#!/usr/bin/env python3
"""
Metrics of Section 5 (Validation), computed from the models of the paper.

    python3 tools/metrics/metrics.py            (from the root of the repository)

reads  kendrick models/Model1..4.st  and  matlab models/M1..M4/*.m  and writes

    generated/size-metrics.tex        Table: size of the models (LoC, characters, entities)
    generated/change-effort.tex       Table: effort of the three evolution scenarios
    generated/dependency-metrics.tex  Table: Ca, Ce, I of the entities of Model 4
    generated/scattering.tex          Table: trace of each concern of Model 4 (statements, chunks, entities)
    generated/metrics.json            every number, for the text
    generated/attribution-sensitivity.tex  Table: the MATLAB traces of Model 4 with and without the dimensions and index variables
    figures/dependency-graph.pdf      Figure: dependency graphs of Model 4 (MATLAB and Kendrick)

Conventions (stated in the paper):

* A line of code is a non-blank line that is not a comment; characters are counted without
  whitespace and comments. Both languages are laid out one statement per line.
* Kendrick entities are the KModel, Composition, Scenario, Simulation and Visualization
  entities of a script; MATLAB entities are the files of a model (main script and functions).
* A dependency of entity A on entity B is an occurrence, in A, of a name declared by B
  (Kendrick: the entity's name, its attribute and the attribute's values, its parameters;
  index variables are declared by the Scenario that binds them; N and t belong to no entity).
  Ce(A) counts the occurrences in A of names declared elsewhere, Ca(B) the occurrences of B's
  names in other entities, I = Ce / (Ca + Ce).
* MATLAB concerns are not entities: an identifier is attributed to a concern by the same map
  as the colorized figure (tools/colorize/colorize.py) and concern A depends on concern B each
  time an identifier of B occurs in a statement that also mentions A.
* The trace of a concern is the set of statements mentioning one of its names (attributed as in
  the colorized figure); its chunks are the maximal runs of consecutive statements of the trace,
  and it spans the entities that contain at least one of them. A statement mentioning several
  concerns is where they are intertwined.
* Evolution scenario Sn goes from Model n to Model n+1. Entities are matched by name: an entity
  of the new model is *reused* if its text is unchanged (up to whitespace), *changed* if it
  exists in the old model with another text, *added* otherwise. Within a changed entity the
  lines of the two versions are aligned (difflib): lines of the new version that replace old
  lines are *changed*, lines without counterpart are *added*, old lines without counterpart
  *deleted*; the lines of an added entity are added.
"""
import difflib
import json
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "colorize"))
from colorize import K_CONCERNS, M_CONCERNS, J_CONCERNS, COLORS  # noqa: E402

KDIR = ROOT / "kendrick models"
MDIR = ROOT / "matlab models"
JDIR = ROOT / "algebraicpetri models"
OUT = ROOT / "generated"
MODELS = [1, 2, 3, 4]
M_FILES = ["SEIRSInfluenza.m", "modelODEs.m", "resolve.m", "visualization.m"]
J_FILES = ["ontology.jl", "seirs.jl", "species.jl", "ring.jl", "model3.jl"]
# the isolation step S3 applied to the AlgebraicPetri files: the model4 folder, whose assembly is model4.jl
J4_FILES = ["ontology.jl", "seirs.jl", "species.jl", "ring.jl", "isolation.jl", "model4.jl"]
J_ASSEMBLY = {"model3.jl": "assembly", "model4.jl": "assembly"}   # one entity name across the step
TABLES = {"kendrick": K_CONCERNS, "matlab": M_CONCERNS, "julia": J_CONCERNS}

IDENT = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
STRING = re.compile(r"'([^']*)'")


# ------------------------------------------------------------------------------- reading

def strip_comment(line, lang):
    if lang == "matlab":
        line = line.split("%", 1)[0]
    elif lang == "julia":
        line = line.split("#", 1)[0]
    else:  # Kendrick comments are double-quoted strings
        line = re.sub(r'"[^"]*"', "", line)
    return line.rstrip()


def loc(text, lang):
    """The lines of code: non-blank, comments removed."""
    return [l for l in (strip_comment(l, lang) for l in text.splitlines()) if l.strip()]


def chars(lines):
    return sum(len(re.sub(r"\s", "", l)) for l in lines)


def kendrick_entities(text):
    """name -> (kind, lines) in script order."""
    entities = OrderedDict()
    current = None
    for line in loc(text, "kendrick"):
        m = re.match(r"(KModel|Composition|Scenario|Simulation|Visualization)\s+(\w+)", line)
        if m:
            current = m.group(2)
            entities[current] = (m.group(1), [])
        entities[current][1].append(line)
    return entities


def julia_entities(folder, files=J_FILES):
    entities = OrderedDict()
    for f in files:
        text = (folder / f).read_text(encoding="utf-8").replace("\r\n", "\n")
        entities[J_ASSEMBLY.get(f, f)] = ("file", loc(text, "julia"))
    return entities


def matlab_entities(folder):
    entities = OrderedDict()
    for f in M_FILES:
        text = (folder / f).read_text(encoding="utf-8").replace("\r\n", "\n")
        entities[f] = ("file", loc(text, "matlab"))
    return entities


def matlab_functions(path):
    """The functions of a single-file MATLAB program, in file order: the entities of Model 4 written in the
    layout of Keeling and Rohani's programs (matlab models/M4-single-file)."""
    entities = OrderedDict()
    current = None
    for line in loc(path.read_text(encoding="utf-8").replace("\r\n", "\n"), "matlab"):
        m = re.match(r"function\s+.*?=\s*(\w+)\s*\(", line)
        if m:
            current = m.group(1)
            entities[current] = ("function", [])
        entities[current][1].append(line)
    return entities


def load(n):
    k = kendrick_entities((KDIR / f"Model{n}.st").read_text(encoding="utf-8"))
    m = matlab_entities(MDIR / f"M{n}")
    return k, m


# ------------------------------------------------------------------------------- size

def size(entities):
    lines = sum(len(v[1]) for v in entities.values())
    c = sum(chars(v[1]) for v in entities.values())
    return {"loc": lines, "chars": c, "entities": len(entities), "avg": round(c / len(entities), 1)}


# ------------------------------------------------------------------------------- change effort

def norm(lines):
    return [re.sub(r"\s+", " ", l.strip()) for l in lines]


def effort(old, new):
    r = {"changed_entities": 0, "added_entities": 0, "reused_entities": 0,
         "changed_lines": 0, "added_lines": 0, "deleted_lines": 0,
         "changed": [], "added": [], "reused": []}
    for name, (kind, lines) in new.items():
        if name not in old:
            r["added_entities"] += 1
            r["added"].append(name)
            r["added_lines"] += len(lines)
            continue
        a, b = norm(old[name][1]), norm(lines)
        if a == b:
            r["reused_entities"] += 1
            r["reused"].append(name)
            continue
        r["changed_entities"] += 1
        r["changed"].append(name)
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if op == "replace":
                common = min(i2 - i1, j2 - j1)
                r["changed_lines"] += common
                r["added_lines"] += (j2 - j1) - common
                r["deleted_lines"] += (i2 - i1) - common
            elif op == "insert":
                r["added_lines"] += j2 - j1
            elif op == "delete":
                r["deleted_lines"] += i2 - i1
    return r


# ------------------------------------------------------------------------------- dependencies

def kendrick_declarations(entities):
    """entity -> set of names it declares."""
    decl = OrderedDict()
    for name, (kind, lines) in entities.items():
        names = {name}
        text = "\n".join(lines)
        if kind == "KModel":
            m = re.search(r"attribute:\s*#\(\s*(\w+)\s+in\s*\((.*?)\)\s*\)", text, re.S)
            if m:
                names.add(m.group(1))
                dom = m.group(2).split()
                if dom and dom[0] == "range":
                    names.update(str(v) for v in range(int(dom[1]), int(dom[2]) + 1))
                else:
                    names.update(dom)
            m = re.search(r"parameters:\s*#\((.*?)\)", text, re.S)
            if m:
                names.update(m.group(1).split())
        elif kind == "Scenario":
            for var in re.findall(r"\(\s*(\w)\s+in\s+\w+\s*\)", text):
                names.add(var)
        decl[name] = names
    return decl


K_KEYWORDS = {"KModel", "Composition", "Scenario", "Simulation", "Visualization", "in", "range", "sum_",
              "attribute", "parameters", "equations", "transitions", "connectionMatrix", "transitionRate",
              "topology", "ring", "line", "complete", "oneWay", "twoWay", "entry",
              "model", "on", "var", "solver", "scenario", "from", "to", "step", "plot", "for", "data",
              "legendTitle", "legends", "xLabel", "N", "t", "Empty"}


def kendrick_dependencies(entities):
    """(A, B) -> number of occurrences in A of names declared by B."""
    decl = kendrick_declarations(entities)
    owner = {}
    for e, names in decl.items():
        for n in names:
            owner.setdefault(n, e)
    deps = defaultdict(int)
    for a, (kind, lines) in entities.items():
        own = decl[a]
        for line in lines:
            tokens = []
            for s in STRING.findall(line):
                tokens.append(s)
            code = STRING.sub(" ", line)
            for ident in IDENT.findall(code):
                # an identifier is a base name followed by index tokens: mu_species, I_ip_free, S_birds_1_free
                parts = ident.split("_")
                for j, part in enumerate(parts):
                    if part == "":
                        continue
                    if j > 0 and part not in owner and all(c in owner for c in part):
                        tokens.extend(part)  # a run of index variables: ki, ip
                    else:
                        tokens.append(part)
            for tok in tokens:
                if tok in K_KEYWORDS or tok in own:
                    continue
                b = owner.get(tok)
                if b is not None and b != a:
                    deps[(a, b)] += 1
    return decl, deps


def matlab_dependencies(entities, table=M_CONCERNS):
    """(A, B) -> occurrences of identifiers of concern B in statements that also mention concern A."""
    owner = {}
    for c, names in table.items():
        for n in names:
            owner[n] = c
    deps = defaultdict(int)
    for name, (kind, lines) in entities.items():
        for line in lines:
            idents = [owner[i] for i in IDENT.findall(line) if i in owner]
            present = set(idents)
            if len(present) < 2:
                continue
            for a in present:
                for c in idents:
                    if c != a:
                        deps[(a, c)] += 1
    return deps


def kendrick_table(entities):
    """The attribution of a Kendrick script, computed from its declarations: each KModel owns its name, its
    attribute, the attribute's values and its parameters, and an index variable of the Scenario belongs to the
    concern of the attribute it ranges over. The table that the colorizer shares (K_CONCERNS) must agree."""
    decl = kendrick_declarations(entities)
    kinds = {name: kind for name, (kind, _) in entities.items()}
    table = {c: set(names) for c, names in decl.items() if kinds[c] == "KModel"}
    for name, (kind, lines) in entities.items():
        if kind == "Scenario":
            for var, attr in re.findall(r"\(\s*(\w)\s+in\s+(\w+)\s*\)", "\n".join(lines)):
                for c, names in table.items():
                    if attr in names:
                        names.add(var)
    for c, names in table.items():
        assert names == set(K_CONCERNS[c]), (c, sorted(names ^ set(K_CONCERNS[c])))
    return {c: sorted(names) for c, names in table.items()}


def concern_tokens(line, lang):
    """The concerns mentioned by a statement, one entry per identifier occurrence."""
    lookup = {}
    for c, names in TABLES[lang].items():
        for n in names:
            lookup[n] = c
    found = []
    if lang == "kendrick":
        for st in STRING.findall(line):
            if st in lookup:
                found.append(lookup[st])
        code = STRING.sub(" ", line)
        for ident in IDENT.findall(code):
            for j, part in enumerate(ident.split("_")):
                if part in lookup:
                    found.append(lookup[part])
                elif j > 0 and part and all(c in lookup for c in part):
                    found.extend(lookup[c] for c in part)
        # a number that is an attribute value used as an index (S_birds_1_free) is caught above;
        # the range of a KModel's attribute belongs to that KModel: handled by the entity's own line
    else:
        for ident in IDENT.findall(line):
            if ident in lookup:
                found.append(lookup[ident])
    return found


def traces(entities, lang):
    """Per concern: statements mentioning it, chunks (maximal runs of such statements), entities spanned;
    plus the share of statements mentioning several concerns."""
    concerns = list(K_CONCERNS)
    stats = {c: {"statements": 0, "chunks": 0, "entities": 0} for c in concerns}
    total = mixed = 0
    for name, (kind, lines) in entities.items():
        seen = set()
        prev = set()
        for line in lines:
            present = set(concern_tokens(line, lang))
            if lang == "kendrick":
                m = re.match(r"KModel\s+(\w+)", line)
                if m and m.group(1) in stats:
                    present.add(m.group(1))
            total += 1
            if len(present) > 1:
                mixed += 1
            for c in present:
                stats[c]["statements"] += 1
                if c not in prev:
                    stats[c]["chunks"] += 1
                seen.add(c)
            prev = present
        for c in seen:
            stats[c]["entities"] += 1
    for c in concerns:
        stats[c]["share"] = round(100.0 * stats[c]["statements"] / total, 1) if total else 0
    return {"concerns": stats, "statements": total, "mixed": mixed, "mixed_share": round(100.0 * mixed / total, 1) if total else 0}


# The attribution without the dimensions and index variables (Section 5.1, "The disputable entries"):
# the species and metapopulation concerns of the MATLAB code then exist only through the species names,
# the adjacency matrix, the migration rate and the migration terms.
M_DIMENSIONS = {"ns", "s", "np", "p", "q"}
M_CONCERNS_WITHOUT_DIMENSIONS = {c: [n for n in names if n not in M_DIMENSIONS] for c, names in M_CONCERNS.items()}


def traces_with(entities, lang, table):
    """traces() under another attribution table."""
    saved = TABLES[lang]
    TABLES[lang] = table
    try:
        return traces(entities, lang)
    finally:
        TABLES[lang] = saved


def tex_sensitivity(mt, mt_without):
    """The MATLAB traces of Model 4 under the two attributions, side by side."""
    out = [r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{|l|r|r|r|r|r|r|}", r"\cmidrule{2-7}",
           r"\multicolumn{1}{c|}{} & \multicolumn{3}{c|}{With dimensions and index variables} & \multicolumn{3}{c|}{Without} \\",
           r"\hline", r"Concern & Statements & Share (\%) & Chunks & Statements & Share (\%) & Chunks \\", r"\hline"]
    for c in mt["concerns"]:
        a, b = mt["concerns"][c], mt_without["concerns"][c]
        out.append(f"{c} & {a['statements']} & {a['share']} & {a['chunks']} & {b['statements']} & {b['share']} & {b['chunks']} \\\\")
    out.append(r"\hline")
    out.append(r"Intertwined statements (\%%) & \multicolumn{3}{c|}{%s} & \multicolumn{3}{c|}{%s} \\"
               % (mt["mixed_share"], mt_without["mixed_share"]))
    out.append(r"\hline")
    out.append(r"\end{tabular}")
    return "\n".join(out) + "\n"


def tex_traces(kt, mt):
    out = [r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{|l|r|r|r|r|}", r"\hline",
           r"Concern & Statements & Share (\%) & Chunks & Entities \\", r"\hline"]
    for label, t in (("MATLAB", mt), (r"\textsc{Kendrick}", kt)):
        out.append(r"\multicolumn{5}{|l|}{\emph{%s}} \\" % label)
        out.append(r"\hline")
        for c, r in t["concerns"].items():
            out.append(f"{c} & {r['statements']} & {r['share']} & {r['chunks']} & {r['entities']} \\\\")
        out.append(r"\hline")
    out.append(r"\end{tabular}")
    return "\n".join(out) + "\n"


def tex_traces3(kt, mt, jt):
    out = [r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{|l|r|r|r|r|}", r"\hline",
           r"Concern & Statements & Share (\%) & Chunks & Entities \\", r"\hline"]
    for label, t in (("MATLAB", mt), ("AlgebraicPetri", jt), (r"\textsc{Kendrick}", kt)):
        out.append(r"\multicolumn{5}{|l|}{\emph{%s} (%d statements)} \\" % (label, t["statements"]))
        out.append(r"\hline")
        for c, r in t["concerns"].items():
            if r["statements"]:
                out.append(f"{c} & {r['statements']} & {r['share']} & {r['chunks']} & {r['entities']} \\\\")
        out.append(r"\hline")
    out.append(r"\end{tabular}")
    return "\n".join(out) + "\n"


def coupling(nodes, deps):
    rows = OrderedDict()
    for n in nodes:
        ce = sum(v for (a, b), v in deps.items() if a == n)
        ca = sum(v for (a, b), v in deps.items() if b == n)
        rows[n] = {"Ca": ca, "Ce": ce, "I": round(ce / (ca + ce), 2) if ca + ce else 0.0}
    return rows


# ------------------------------------------------------------------------------- outputs

def tex_size(sizes):
    out = [r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{|c|c|r|r|r|r|}", r"\cmidrule{3-6}",
           r"\multicolumn{2}{c|}{} & \multicolumn{2}{c|}{Model size} & Avg. entity & \multirow{2}{*}{\texttt{\#Ent.}} \\",
           r"\multicolumn{2}{c|}{} & \texttt{\#LoC} & \texttt{\#Chars} & \texttt{\#Chars} & \\", r"\hline"]
    for n in MODELS:
        for lang, key in (("M", "matlab"), ("K", "kendrick")):
            s = sizes[n][key]
            first = r"\multirow{2}{*}{M%d}" % n if lang == "M" else ""
            out.append(f"{first} & {lang} & {s['loc']} & {s['chars']} & {s['avg']} & {s['entities']} \\\\")
            out.append(r"\cmidrule{2-6}" if lang == "M" else r"\hline")
    out.append(r"\end{tabular}")
    return "\n".join(out) + "\n"


def tex_effort(efforts):
    out = [r"\begin{tabular}{|c|rr|rr|rr|rr|rr|rr|}", r"\cmidrule{2-13}",
           r"\multicolumn{1}{c|}{} & \multicolumn{2}{c|}{Changed} & \multicolumn{2}{c|}{Added} & \multicolumn{2}{c|}{Reused} & \multicolumn{2}{c|}{Changed} & \multicolumn{2}{c|}{Added} & \multicolumn{2}{c|}{Deleted} \\",
           r"\multicolumn{1}{c|}{} & \multicolumn{2}{c|}{entities} & \multicolumn{2}{c|}{entities} & \multicolumn{2}{c|}{entities} & \multicolumn{2}{c|}{statements} & \multicolumn{2}{c|}{statements} & \multicolumn{2}{c|}{statements} \\",
           r"\cmidrule{2-13}",
           r"\multicolumn{1}{c|}{} & M & K & M & K & M & K & M & K & M & K & M & K \\", r"\hline"]
    for i, n in enumerate(MODELS[:-1]):
        e = efforts[n]
        m, k = e["matlab"], e["kendrick"]
        cells = []
        for key in ("changed_entities", "added_entities", "reused_entities", "changed_lines", "added_lines", "deleted_lines"):
            cells += [str(m[key]), str(k[key])]
        out.append("S%d\\tnote{%s} & " % (n, "abc"[i]) + " & ".join(cells) + r" \\")
        out.append(r"\hline")
    out.append(r"\end{tabular}")
    return "\n".join(out) + "\n"


def tex_dependencies(kc, mc):
    out = [r"\begin{tabular}{|l|l|r|r|r|}", r"\hline",
           r"& Entity / concern & \texttt{Ca} & \texttt{Ce} & \texttt{I} \\", r"\hline"]
    first = True
    for name, r in mc.items():
        out.append((r"\multirow{%d}{*}{MATLAB}" % len(mc) if first else "") + f" & {name} & {r['Ca']} & {r['Ce']} & {r['I']:.2f} \\\\")
        first = False
    out.append(r"\hline")
    first = True
    for name, r in kc.items():
        out.append((r"\multirow{%d}{*}{\textsc{Kendrick}}" % len(kc) if first else "") + f" & {name} & {r['Ca']} & {r['Ce']} & {r['I']:.2f} \\\\")
        first = False
    out += [r"\hline", r"\end{tabular}"]
    return "\n".join(out) + "\n"


def draw(kdeps, knodes, mdeps, mnodes, path):
    """The two dependency graphs, with matplotlib only (nodes are boxes, arcs are labelled arrows)."""
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    def color(n):
        return COLORS.get(n, "#e8e8e8")

    BW, BH = 1.15, 0.55  # box size in data units

    def boundary(p, q):
        """The point of the box centred at p on the segment from p to q."""
        dx, dy = q[0] - p[0], q[1] - p[1]
        if dx == 0 and dy == 0:
            return p
        tx = abs(BW / 2 / dx) if dx else math.inf
        ty = abs(BH / 2 / dy) if dy else math.inf
        t = min(tx, ty)
        return (p[0] + dx * t, p[1] + dy * t)

    def graph(ax, deps, nodes, pos, title, rad):
        for n in nodes:
            x, y = pos[n]
            ax.add_patch(FancyBboxPatch((x - BW / 2, y - BH / 2), BW, BH, boxstyle="round,pad=0.02",
                                        fc=color(n), ec="#444", lw=0.8))
            ax.text(x, y, n, ha="center", va="center", fontsize=8)
        # sorted: the MATLAB counts are accumulated over sets, whose order varies from run to run
        for (a, b), w in sorted(deps.items()):
            p, q = pos[a], pos[b]
            start, end = boundary(p, q), boundary(q, p)
            arrow = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11, lw=0.9, color="#333",
                                    connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=1)
            ax.add_patch(arrow)
            # label at 35% of the way, offset to the side of the arc
            t = 0.35
            mx, my = start[0] + t * (end[0] - start[0]), start[1] + t * (end[1] - start[1])
            dx, dy = end[0] - start[0], end[1] - start[1]
            norm = math.hypot(dx, dy) or 1
            off = rad * norm * 0.5 * 2 * t * (1 - t) * 2  # displacement of the arc at t (approx.)
            ax.text(mx - dy / norm * off - dy / norm * 0.06, my + dx / norm * off + dx / norm * 0.06, str(w),
                    fontsize=7, ha="center", va="center", bbox={"fc": "white", "ec": "none", "alpha": 0.8, "pad": 0.6})
        xs = [pos[n][0] for n in nodes]
        ys = [pos[n][1] for n in nodes]
        ax.set_xlim(min(xs) - 1.0, max(xs) + 1.0)
        ax.set_ylim(min(ys) - 0.7, max(ys) + 0.7)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=10)
        ax.set_axis_off()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), gridspec_kw={"width_ratios": [1.15, 1.5]})
    # (a) MATLAB concerns on a circle, arcs curved so that both directions show
    mpos = {}
    for i, n in enumerate(mnodes):
        ang = math.pi / 2 - 2 * math.pi * i / len(mnodes)
        mpos[n] = (2.4 * math.cos(ang), 2.0 * math.sin(ang))
    graph(axes[0], mdeps, mnodes, mpos, "(a) MATLAB: concern co-occurrences", 0.25)
    # (b) Kendrick entities: concerns on a row at the bottom, the others above (arrows point down or sideways)
    kpos = {"SEIRS": (-3, 0), "MultiSpecies": (-1, 0), "MetaPopulation": (1, 0), "Isolation": (3, 0),
            "Influenza": (3.2, 1.7), "Scr1": (-1, 1.8), "InfluenzaSim": (0.2, 3.3), "InfluenzaViz": (-3, 3.3)}
    for i, n in enumerate(n for n in knodes if n not in kpos):
        kpos[n] = (i * 1.5 - 3, 4.5)
    graph(axes[1], kdeps, knodes, kpos, "(b) Kendrick: entity references", 0.0)
    fig.tight_layout()
    # no creation date in the PDF, so that a rerun on unchanged models leaves the file unchanged
    fig.savefig(path, metadata={"CreationDate": None})
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    models = {n: load(n) for n in MODELS}
    sizes = {n: {"kendrick": size(k), "matlab": size(m)} for n, (k, m) in models.items()}
    efforts = {}
    for n in MODELS[:-1]:
        k0, m0 = models[n]
        k1, m1 = models[n + 1]
        efforts[n] = {"kendrick": effort(k0, k1), "matlab": effort(m0, m1)}
    k4, m4 = models[4]
    kdecl, kdeps = kendrick_dependencies(k4)
    mdeps = matlab_dependencies(m4)
    knodes = list(k4.keys())
    mnodes = [c for c in M_CONCERNS if any(c in e for e in mdeps)]
    kc, mc = coupling(knodes, kdeps), coupling(mnodes, mdeps)
    kt, mt = traces_with(k4, "kendrick", kendrick_table(k4)), traces(m4, "matlab")
    (OUT / "scattering.tex").write_text(tex_traces(kt, mt), encoding="utf-8")
    mt_without = traces_with(m4, "matlab", M_CONCERNS_WITHOUT_DIMENSIONS)
    (OUT / "attribution-sensitivity.tex").write_text(tex_sensitivity(mt, mt_without), encoding="utf-8")
    # Model 3 in the three languages (the AlgebraicPetri version exists for Model 3 only)
    k3, m3 = models[3]
    j3 = julia_entities(JDIR)
    kt3, mt3, jt3 = traces_with(k3, "kendrick", kendrick_table(k3)), traces(m3, "matlab"), traces(j3, "julia")
    jdeps = matlab_dependencies(j3, J_CONCERNS)
    jnodes = [c for c in J_CONCERNS if any(c in e for e in jdeps)]
    jc = coupling(jnodes, jdeps)
    (OUT / "scattering3.tex").write_text(tex_traces3(kt3, mt3, jt3), encoding="utf-8")
    # the isolation step S3 in AlgebraicPetri: Model 3 folder -> model4 folder, with the assembly matched by role
    j4 = julia_entities(JDIR / "model4", J4_FILES)
    jeffort = effort(j3, j4)
    # Model 4 in MATLAB, in the layout of Keeling and Rohani's programs: one file, two functions
    m4s = matlab_functions(MDIR / "M4-single-file" / "Model_4.m")
    m4s_deps = matlab_dependencies(m4s)
    m4s_coupling = coupling([c for c in M_CONCERNS if any(c in e for e in m4s_deps)], m4s_deps)

    (OUT / "size-metrics.tex").write_text(tex_size(sizes), encoding="utf-8")
    (OUT / "change-effort.tex").write_text(tex_effort(efforts), encoding="utf-8")
    (OUT / "dependency-metrics.tex").write_text(tex_dependencies(kc, mc), encoding="utf-8")
    draw(kdeps, knodes, mdeps, mnodes, ROOT / "figures" / "dependency-graph.pdf")
    result = {
        "sizes": sizes, "efforts": efforts,
        "kendrick": {"declarations": {e: sorted(s) for e, s in kdecl.items()},
                     "dependencies": {f"{a} -> {b}": v for (a, b), v in sorted(kdeps.items())}, "coupling": kc},
        "matlab": {"dependencies": {f"{a} -> {b}": v for (a, b), v in sorted(mdeps.items())}, "coupling": mc},
        "traces": {"kendrick": kt, "matlab": mt, "matlab_without_dimensions": mt_without},
        "model3": {"sizes": {"kendrick": size(k3), "matlab": size(m3), "algebraicpetri": size(j3)},
                   "traces": {"kendrick": kt3, "matlab": mt3, "algebraicpetri": jt3},
                   "algebraicpetri": {"dependencies": {f"{a} -> {b}": v for (a, b), v in sorted(jdeps.items())}, "coupling": jc}},
        "algebraicpetri_step": {"sizes": {"model3": size(j3), "model4": size(j4)}, "effort": jeffort},
        "matlab_single_file": {"size": size(m4s), "traces": traces(m4s, "matlab"),
                               "dependencies": {f"{a} -> {b}": v for (a, b), v in sorted(m4s_deps.items())},
                               "coupling": m4s_coupling},
    }
    (OUT / "metrics.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
