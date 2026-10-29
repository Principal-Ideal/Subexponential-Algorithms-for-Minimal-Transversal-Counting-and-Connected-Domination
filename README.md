# Subexponential Algorithms for Minimal Transversal Counting and Connected Domination

Building on OpenAI's *The Exponential Time Hypothesis is False*, this research derives subexponential algorithms for exact minimal-transversal counting and randomized connected-domination decision, witness recovery, and minimum-size search.

Repository name: `subexponential-minimal-transversal-counting-and-connected-domination`.

## Results

| Results | Content |
| --- | --- |
| 001–003 | External SAT-counting, algebra-valued evaluation, and isolation interfaces |
| 004–010 | Minimal-transversal counting with `3p+2q−1` variables, size distributions, minimal domination and set-cover applications, and prior-art qualification |
| 011–016 | Unary weighted counting bridge, `3n`-variable connected-domination encoding, parity, randomized decision, witnesses, and probabilistic minimum-size search |
| 017–019 | Minimal CNF models through fixed deletion families, SCC completeness, and an exponential family-size obstruction |
| 020 | A hybrid of direct short-edge encoding and long-edge cancellation |

The [catalog](archive/catalog.md) lists all 20 precise statements and dependencies. Complete proofs are in [the minimal-transversal manuscript](papers/research.tex), [the connected-domination manuscript](papers/connected_domination.tex), and the individual archive entries.

The algorithmic bounds use the external assumptions in [the source guide](archive/shared/external-sources.md). The connected-domination algorithms are randomized; their parity encoding does not give exact integer counts of connected dominating sets. The compact transversal gadget is recoverable from prior relaxed Tseitin transformations; [010](archive/010/proof.md) records this qualification.

## Reproduce

Requires Python 3.10+ and only its standard library. Run from the repository root without `python -O`:

```sh
python archive/check_archive.py
python code/verify.py --report workspace/recheck/verification_report.json
python code/verify_connected_domination.py --report workspace/recheck/connected_domination_report.json
```

The checker validates manifests, dependencies, and local Markdown links. The verification suites compare the reductions with independent enumeration on finite instances. **The supplied DPLL counters are exponential reference implementations, not implementations of OpenAI's subexponential algorithm.**

See [code/README.md](code/README.md) for inputs, examples, and export commands, and [verification scope](archive/shared/verification-scope.md) for test coverage. Reports and generated formulas are written to `workspace/` and excluded from Git.

## Contents

- `archive/`: results 001–020, proof guides, and necessary external references.
- `papers/`: two complete English TeX manuscripts.
- `code/`: five implementation and verification scripts.
- `examples/`: two small JSON inputs.

This repository retains the first twenty research results and their original mathematical statements. Later research, audit logs, old reports, proposals, caches, and generated exports are omitted. Source manuscripts received only editorial path and presentation updates. No remote repository has been configured or uploaded.
