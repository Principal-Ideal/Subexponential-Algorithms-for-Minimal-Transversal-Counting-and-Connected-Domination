# 007: Linear-size unique-extension cardinality circuit

Proof: [research.tex](../../papers/research.tex), `sec:size` and `eq:adder`. Implementation: [reduction.py](../../code/reduction.py).

[verify.py](../../code/verify.py) checks 511 cardinality inputs and structural bounds through p=256. Out-of-range k is inconsistent; p=0 is handled directly.
