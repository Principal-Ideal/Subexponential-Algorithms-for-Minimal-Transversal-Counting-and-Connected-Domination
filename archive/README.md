# Research archive: results 001–020

Browse the [result catalog](catalog.md), [external contracts](shared/external-sources.md), and [verification scope](shared/verification-scope.md). This publication subset contains exactly the first twenty numbered records. Their proof dependencies are closed within the subset.

Every result has a stable quoted numeric ID, an `index.yaml` statement and an `artifacts.md` evidence guide. A local `proof.md` is included where the complete argument is not already in the retained papers. `requires` lists direct mathematical prerequisites; its graph must be acyclic. `motivated_by` records nonessential research connections.

## Status and method

| Status | Meaning |
| --- | --- |
| `imported` | An external theorem or algorithm contract with its actual source and scope; not locally proved or implemented. |
| `established` | The local mathematical claim has a linked proof; its prerequisites remain part of the justification. |
| `conditional` | The conclusion explicitly assumes imported algorithmic results. |

The methods used here are `hand` for mathematical arguments and `external` for imported contracts. A hand proof using an imported result retains that dependence. Supplementary finite tests are not universal proofs, and imported formalization does not certify the local reductions.

Hypergraphs are indexed finite edge families and may have empty or repeated edges and isolated vertices. Graphs are finite, simple and undirected unless explicitly defined as dependency digraphs. Models are identified with their true-variable sets; minimal means inclusion-minimal. Connected dominating sets are nonempty, including for an empty input graph. Boolean variables, clause counts, coefficient degrees and bit arithmetic are distinct parameters.

## Evidence boundaries

The reference counters are exact exponential DPLL and subset enumeration. They do not implement or benchmark the imported subexponential algorithm. The single-log-log and conservative squared-log-log exponents in the external interfaces are not interchangeable. Read [011](011/artifacts.md) for the additional algebra, compression and arithmetic obligations of the weighted extension.

[010](010/proof.md) records that prior relaxed Tseitin transformations recover the compact gadget. Improving a particular unoptimized baseline does not establish novelty or superiority over optimized prior transformations. Results 017–020 have retained hand proofs, but no retained implementation or canonical finite test report.

All local links are relative to their Markdown files. Run commands from the repository root and write new outputs to `workspace/`. Reports are generated on demand and excluded from Git.

```sh
python archive/check_archive.py
```

The checker validates manifests, dependency references, the prerequisite DAG and local links in the repository's Markdown documentation, excluding `.git/` and `workspace/`. It does not check heading fragments, external URL availability, mathematics, solvers or formal proofs. The deliberately small YAML grammar supports the quoted scalars, bare status/method values and inline JSON arrays used here. The JSON/text reports are written under `workspace/`.
