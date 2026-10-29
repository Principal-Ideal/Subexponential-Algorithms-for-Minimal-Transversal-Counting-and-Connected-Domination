# 011: Conditional unary signed monomial-weight bridge

Proof: [connected_domination.tex](../../papers/connected_domination.tex), `prop:weighted` and `sec:bridge`. Imported interfaces: [001](../001/index.yaml), [002](../002/index.yaml), and the [source labels](../shared/external-sources.md#openai).

For a fixed number r of markers, replace the two-marker algebra by Q[V,Y_1,...,Y_r]/(V^ell,Y_1^(A_1+1),...,Y_r^(A_r+1)); its dimension is ell times the product of (A_j+1), still polynomial. Zero unary weights only decrease coefficient bounds. The same compression, incidence, denominator, and centered-recovery arguments apply.

Compression remains unweighted until accepting-set equality. The extension uses the conservative squared-log-log exponent and does not cover arbitrary assignment weights or a growing number of markers.
