# 015: Parity-preserving witness self-reduction

Proof: [proof.md](proof.md) and [connected_domination.tex](../../papers/connected_domination.tex), `sec:algorithm`. Implementation and regression: [connected_domination.py](../../code/connected_domination.py), [verifier](../../code/verify_connected_domination.py).

An odd coefficient has exactly one odd child under a selection-bit split. Keep the original graph: deleting excluded vertices changes domination obligations.
