# 014: Conditional randomized connected-domination decision

Proof: [connected_domination.tex](../../papers/connected_domination.tex), `thm:main` and `sec:algorithm`. Implementation: [connected_domination.py](../../code/connected_domination.py).

Isolation uses the fixed feasible family and independent weights from the least power-of-two interval containing 1,...,2n. The runtime transfer depends on [011](../011/index.yaml). A `not_detected` outcome is generally not a nonexistence certificate.
