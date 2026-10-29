# 006: Unique-extension XOR difference-of-counts bridge

Proof: [research.tex](../../papers/research.tex), `eq:xor` and the boundary subsection. Implementation: [reduction.py](../../code/reduction.py).

The bound is 3p+2q-1 when p+q>0; the empty parity chain has a separate constant case. [verify.py](../../code/verify.py) checks gate truth tables and 511 parity inputs.
