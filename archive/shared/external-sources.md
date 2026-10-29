# External sources and algorithmic assumptions

These are the primary sources and exact interfaces used by results 001–020. The OpenAI references identify the October 25, 2026 manuscript revision used by this research.

## OpenAI

- [The Exponential Time Hypothesis is False — manuscript](https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf).
- [Complete manuscript source](https://raw.githubusercontent.com/openai/math/refs/heads/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/build/main_full_version.tex).
- [Lean scope document](https://github.com/openai/math/blob/main/lean/docs/378.md).

[001](../001/index.yaml) imports ordinary fixed-width counting and exact satisfying-set preservation. The manuscript's `thm:main` has exponent proportional to N log log N / sqrt(log N). The conservative `prop:interpolation-bound` and documented Lean scope use N (log log N)^2 / sqrt(log N). The weighted extension uses only the conservative exponent; fixed-density refinements require an actual density bound.

[002](../002/index.yaml) and [011](../011/index.yaml) use more than an ordinary #SAT oracle:

| Source labels | Required interface |
| --- | --- |
| `lem:sparsify`, `app:sparsify` | Disjoint satisfying sets on the same declared variables |
| `lem:greedy-hashes` | Unweighted compression with exact accepting-set equality |
| `subsec:product-interface`, `eq:general-product-sum`, `eq:general-product-degree` | Product sums over a commutative Q-algebra; degree measured in independent factor incidences |
| `lem:measurement-separation`, `lem:boolean-differences`, `eq:hasse-order`, `prop:general-count` | Separation, finite differences, Taylor/Hasse recovery, and the algebra-valued evaluator |
| `lem:layout`, `lem:incidence-parameters` | Scope-dependent layout and incidence bounds |
| `lem:rational-idempotent`, `lem:total-order` | Rational parity lifting and total-order truncation |
| `eq:lifted-factor`, `eq:origin-residue`, `prop:count` | Sparse polynomial-equation evaluation and residue extraction |
| `app:arithmetic`, `subsec:rational-streaming-height`, `subsec:rational-readout`, `eq:exact-readout` | Denominators, coefficient heights, and exact rational interpolation/readout |

The local weighted proof is in [connected_domination.tex](../../papers/connected_domination.tex), `sec:bridge`. Polynomial marker-degree bounds are essential to its bit complexity and space. The external Lean scope does not certify this extension or its connected-domination applications.

## CutCount

Cygan, Nederlof, M. Pilipczuk, M. Pilipczuk, van Rooij, and Wojtaszczyk, *Solving connectivity problems parameterized by treewidth in single exponential time*: [long manuscript](https://arxiv.org/pdf/1103.0534), [journal publication](https://doi.org/10.1145/3506707).

Printed page 9, Lemma 2.5 supplies the Isolation Lemma in [003](../003/index.yaml); Corollary 3.1 gives the one-sided Cut&Count pattern. Page 10, Lemmas 3.3–3.4 give rooted consistent cuts and connectivity parity. Appendix Remark A.9 and Theorem A.11 treat fixed roots and Constrained Connected Dominating Set. These mechanisms are prior work; the treewidth algorithm is not itself an arbitrary-n subexponential algorithm.

## Negative weights

Meert, Vlasselaer, and Van den Broeck, *A Relaxed Tseitin Transformation for Weighted Model Counting*: [author-hosted paper](https://starai.cs.ucla.edu/papers/MeertStarAI16.pdf), “Relaxed Tseitin Transformation,” printed page 2.

Its replacement uses Z and R with clauses Z OR not phi, R OR Z, and R OR not phi; the false R literal has weight -1 and the other displayed literal weights have weight +1. [010](../010/proof.md) recovers the compact edge gadget by specialization and elimination. The supplied unoptimized baseline is not claimed to be the strongest instantiation of this literature.
