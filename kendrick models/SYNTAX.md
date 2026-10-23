# Kendrick syntax used in the paper's model files (decision of 28 Sept 2026)

The four files `Model1.st` .. `Model4.st` use the *new* Kendrick syntax, which the paper
describes in Section 4 and which the Java port (JKendrick, https://github.com/KendrickOrg/JKendrick) implements. The Pharo
implementation and the wiki still use the older spelling (`KendrickModel`, `attribute: #(status -> S E I R)`,
`lambda: #(beta*I_zone/N sum)`, `N: #(species_zone)`, `Simulation X rungeKutta`).

## Entities

    KModel <name> <clause>; ... <clause>.
    Composition <name> model: '<KModel name>'; ... .
    Scenario <name> on: '<Composition name>'; <assignment>; ... .
    Simulation <name> solver: '<solver>'; scenario: '<Scenario name>'; from: <t0>; to: <t1>; step: <dt>.
    Visualization <name> plot: '<kind>'; for: '<Simulation name>'; ... .

## KModel clauses

- `attribute: #(<attr> in (<value> ...))` or `attribute: #(<attr> in (range <a> <b>))`
  -- one attribute per concern; its values name the states of the automaton.
- `parameters: #(<name> ...)`
- `<param>: #(<formula>)` -- optional default value or formula of a parameter (e.g. `lambda: #(beta*I/N)`).
- `equations: #( <compartment>:t=<formula>. ... )` or `transitions: #( <from> -- <rate> --> <to>. ... )`
  or, for a spatial concern, `connectionMatrix: #(#(...) ...)` (adjacency matrix, row = origin, column = destination)
  or `topology: #(<kind> [<direction>])` with `transitionRate: #(<rate>)`. The kinds are `ring` (each value of
  the attribute is linked to the next one, the last to the first), `line` and `complete`; a topology is two-way
  unless `oneWay` is given (`twoWay` is accepted). `connectionMatrix:` and `topology:` are exclusive.
- `entry: #(<value>)` -- the value of the attribute taken by individuals entering the population (births,
  immigration). Without it the attribute is *inherited* (species, zone): an inflow of another concern, such as
  `Empty -- mu*N --> S`, is replicated over its values, each in proportion to its own population. With it the
  attribute is *acquired* (isolation, age, vaccination): the whole inflow lands on the entry value and its rate
  is evaluated with the attribute summed out (`mu*N` counts the whole population). Model 4: `entry: #(free)`.
- A concern never names an attribute, parameter or compartment of another concern
  (heterogeneities are introduced in scenarios, not in concerns).

## Scenario assignments

- `var: #((<v> in <attr>) ...)` binds single-letter index variables to attribute domains.
- Values: `<name>_<attr>...: #(...)` gives one value per value of each listed attribute, in the
  order of the attribute's declaration (`mu_species: #(0.0000365 0.00137)`, `rho_species_isolation: #(#(0.03 0) #(0.1 0))`).
  A name without index is homogeneous. When the same attribute is needed twice, bound variables
  replace attribute names and the order is that of the variables: `beta_ki: #(#(0 0.012) #(0 0.24))`
  is a matrix with row k (species of the susceptible) and column i (species of the infectious).
- Formulas: `<name>_<vars>: #(<expression>)`, where the expression may use `sum_ (<v> in <attr>) <term>`,
  indexed names such as `I_ip`, `N_ip`, and attribute values mixed with variables, e.g. `I_ip_free`.
- `N_<idx>` is the cardinality of the corresponding (sub)compartments of the whole population; it is never declared.
- `t` is the time and may be used in any expression (`beta*(1+cos(t))` for a seasonal transmission rate);
  the functions `sin`, `cos`, `exp`, `log`, `sqrt`, `abs`, `min`, `max` and `pow` are available.
- Compartment sizes: a value assigned to a compartment that is not fully indexed is spread evenly
  over the sub-compartments not mentioned (`S_species: #(75000 750000)` gives 5000 humans and
  50000 birds to each of the 15 zones); `S_birds_1: 49900` then sets one sub-compartment. The last assignment wins.

## Simulation and Visualization

- `Simulation`: `solver:` is `'rungeKutta'`, `'gillespie'`, `'nextReaction'` (Anderson's method, for rates that read `t`) or `'tauLeap'`; `from:`, `to:`, `step:` in days
  (for the stochastic solvers, `step:` is the sampling step of the trajectory); optional `runs:` and `seed:`.
- `Visualization`: `plot: 'diagram'`, `for:` a Simulation, `data: #(<name> ...)`, `legendTitle:`, `legends:`
  (renames the series in order), `xLabel:`, `yLabel:`, `title:`. A data name starts with an attribute value and
  each index is either an attribute name, which splits the series by its values (`I_species`: one series per
  species), or an attribute value, which restricts them (`I_birds_zone`: the infectious birds, one series per
  zone); `I` alone is the total. Without `data:` there is one series per value of the first attribute (the status).

## Settled points (7 Oct 2026)

- `KModel` is the keyword, in the paper (Section 4, Appendix A) and in JKendrick; `KendrickModel` is the Pharo spelling.
- The sum is the prefix keyword `sum_ (i in species) ...` (grammar rule of JKendrick: `'sum_' '(' ID 'in' ID ')' expr`,
  lowest precedence, the body extends to the right); the wiki's postfix `sum` belongs to the old syntax.
- A parameter component that no assignment covers has no default: JKendrick stops with
  "parameter <name> has no value in the scenario" when it is first evaluated. A formula given in a concern
  (`lambda: #(beta*I/N)`) is the default of the whole parameter, which a scenario may override.
