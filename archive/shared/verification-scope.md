# Verification scope

Run the commands in the [repository README](../../README.md) to generate fresh JSON reports and text summaries under `workspace/`. The verifiers use exact exponential DPLL and independent enumeration; they do not implement the imported subexponential algorithm. Do not run with `python -O`.

## Minimal transversals

[verify.py](../../code/verify.py) checks:

- 16 gate truth-table rows and 280 random CNFs against independent model enumeration.
- 511 parity and 511 cardinality input assignments, with circuit bounds through p=256.
- All 278 simple hypergraphs on at most three vertices: actual even/odd CNF counts, totals and size distributions; 2,720 DPLL calls.
- All 65,536 simple four-vertex hypergraphs: independent deletion enumeration versus two factored cancellation identities, including size distributions. This is not actual CNF counting for every four-vertex instance.
- The unoptimized prior baseline on 22 hypergraphs: 74 fixed-selection checks and 192 DPLL calls.
- Boundary and random inputs, all 76 simple graphs on at most four vertices, and set-cover examples.

## Connected domination

[verify_connected_domination.py](../../code/verify_connected_domination.py) checks:

- 240 random CNFs against truth tables, including signed free variables, forced signs, and component products.
- All 76 graphs on at most four vertices, 285 rooted graphs, and 21,423 partial selections including 4,306 complete selections: 42,846 polynomial-DPLL calls and 855 ordinary-DPLL comparisons.
- Six representative and 20 seeded random five-vertex graphs: 4,290 root/selection cases and 8,580 polynomial-DPLL calls.
- 722 graph/size-limit cases, 285 rooted cases, 76 seeded randomized decisions, and 76 seeded minimization cases.
- Witness feasibility and selection restrictions that retain the original graph.

A fixed seed enables reproduction; the probability guarantee assumes independent uniform trials. A returned witness is independently checked, while `not_detected` is generally not a nonexistence certificate and minimum-size optimality is probabilistic.

## Limits

Finite checks do not replace the general proofs. Results 017–020 have hand proofs but no retained implementations or computational reports. The archive checker validates organization and local links, not mathematics, external URLs, solver certificates, or Lean proofs.
