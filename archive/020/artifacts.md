# 020: Short-edge direct and long-edge cancellation hybrid

Construction, raw clause count, proof, and degenerate cases: [proof.md](proof.md). A conditional runtime corollary additionally uses [001](../001/index.yaml).

This is a hand proof; [reduction.py](../../code/reduction.py) implements all-edge cancellation, not this hybrid. Preserve the zero-sign case instead of using the negative expression 3p+2q_L-1 at p=q_L=0.
