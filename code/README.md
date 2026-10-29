# Reproducible reductions and verification

These reference implementations cover [archive results 001–020](../archive/catalog.md) and require only the **Python 3.10+ standard library**. The exact DPLL counters may use exponential time and cache space. They do not implement the imported subexponential algorithm.

Run all commands from the repository root. Generated formulas and reports go into `workspace/`.

## Minimal transversals

```sh
python code/verify.py --report workspace/recheck/verification_report.json
python code/reduction.py examples/minimal_transversals.json --count --output-prefix workspace/examples/minimal_transversals
python code/reduction.py examples/minimal_transversals.json --size 1 --count --output-prefix workspace/examples/minimal_transversals_k1
```

Input: `{"p": 3, "edges": [[0,1],[1,2]]}`, with vertices numbered `0..p-1`. Empty hyperedges, empty edge families, repeated edges, isolated vertices, and `p=0` are allowed. Repeated vertices within an edge are deduplicated. `--size k` restricts the solution size; out-of-range sizes make both formulas unsatisfiable. DIMACS `c var` comments record variable names.

The encoding uses `D,R ⊆ U` and `P ⊆ E`, with `R ⊆ D` and, for every `e∈P`, `e∩D⊆R` and `|e∩D|≤1`. Its sign is `(-1)^(|R|+|P|)`. The even CNF model count minus the odd CNF model count equals the number of minimal transversals.

Both CNFs have width at most three and `3p+2q-1` variables when `p+q>0`. Counting by size adds a linear-size balanced binary adder tree with unique extension. See the [manuscript](../papers/research.tex) and [archive proof](../archive/005/proof.md).

The full verifier checks:

- All 278 simple hypergraphs with `p≤3`, including actual even/odd CNF counts for every size, against independent deletion-based enumeration and cancellation identities.
- All 65,536 simple hypergraphs with `p=4`, comparing size distributions from independent enumeration and two factored identities. This part does not count every CNF directly.
- Truth tables for 280 random CNFs, gate and circuit unique extension, variable bounds, boundary cases, graph domination, and set cover.
- The unoptimized negative-weight Skolem baseline on 22 hypergraphs with `p≤2`: 74 fixed-selection checks and 192 actual DPLL calls.

**Prior-art qualification:** the compact gadget can be recovered from the existing relaxed Tseitin transformation by elementary elimination. Fewer variables than the unoptimized baseline do not establish superiority over optimized prior methods or priority for negative-weight cancellation; see [010](../archive/010/proof.md).

## Connected dominating sets

```sh
python code/verify_connected_domination.py --report workspace/recheck/connected_domination_report.json
python code/connected_domination.py examples/connected_domination.json --size-limit 2 --trials 10
python code/connected_domination.py examples/connected_domination.json --minimize --trials 10
python code/connected_domination.py examples/connected_domination.json --minimize --root 0 --trials 4 --seed 20261029 --export-prefix workspace/examples/connected_domination
```

Input: `{"n": 5, "edges": [[0,1],[1,2]]}`, with vertices numbered `0..n-1`; edges are deduplicated as a simple undirected graph. Connected dominating sets must be nonempty, so the empty graph has no solution. The fixed-root encoding has `3n` variables, `2n+4m+2` raw clauses, and width at most three.

With the default `--mode unsigned`, a true selection bit has weight `y*z^w`; all other weights are one. For a fixed selection `D` containing the root, the number of extensions is `2^(u(D)+cc(G[D])-1)`, where `u(D)` counts undominated original vertices. Coefficients modulo two give the parity of connected dominating sets by size and isolation weight. `--mode signed` cancels nondominating sets over the integers and gives the same parity.

System randomness is the default. Weights are independently uniform in `1..R`, where `R` is the smallest power of two at least `2n`. The failure bound `2^-t` assumes independent uniform trials. `--seed` enables reproducibility; a fixed-seed observation is not a probability guarantee.

`found` returns an independently verified set. `not_detected` generally does not prove nonexistence. `--minimize` returns the smallest size detected across the specified roots and trials; optimality is probabilistic. `--root r` requires the solution to contain that root. Witness recovery fixes only selection bits and retains all original vertices and domination requirements.

Exports include `.base.cnf` with `3n` variables, `.even.cnf/.odd.cnf` with `4n-1` variables for signed-identity checks, and `.weights.json` with polynomial weights. Size limits filter coefficients; exported CNFs contain no cardinality circuit. Ordinary model counting or satisfiability of `.base.cnf` alone does not solve connected domination.

The verifier checks all 76 simple graphs on at most four vertices, 285 rooted instances, and 21,423 partial selections, including 4,306 fully fixed sets. It also checks 26 five-vertex instances, 240 random-CNF truth tables, ordinary DPLL counts, decision, minimization, and witnesses. See the [manuscript](../papers/connected_domination.tex) and [archive result](../archive/012/proof.md).

## Reproduction boundaries

Both verifiers create report parent directories and write JSON plus a TXT summary. Without `--report`, output defaults to the repository's `workspace/` directory. No additional dependencies or solvers are required. `verify.py --skip-p4` omits the four-vertex hypergraph check; use the commands above for complete verification.

Historical verification with Python 3.12.14 took about 17.6 seconds for minimal transversals and 11.4 seconds for connected domination. These are small-instance verification times, not evidence for the external algorithm's runtime. See the [verification scope](../archive/shared/verification-scope.md) for coverage and limitations.

Archive entries [017–020](../archive/017/artifacts.md) contain hand proofs without retained implementations or reproducible test reports. Finite verification does not replace general mathematical proofs or constitute local Lean formal verification.
