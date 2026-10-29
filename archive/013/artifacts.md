# 013: Connected-domination parity generating polynomial

Proof: [connected_domination.tex](../../papers/connected_domination.tex), `eq:unsigned`, `eq:parity`, and `eq:signed`. Finite checks: [verify_connected_domination.py](../../code/verify_connected_domination.py).

Roots are evaluated separately. Summing rooted parities multiplies a set by its size and can erase even-size solutions. Consistent-cut parity is [prior work](../shared/external-sources.md#cutcount).
