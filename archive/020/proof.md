# Hybrid encoding and exact parameter counts

Fix an integer d>=2. Split the indexed edges into short edges E_S of size at most d and long edges E_L of size greater than d. Write q_L=|E_L| and s=p+q_L. Use x_v,r_v for every vertex and a_e only for long edges.

For every v add not r_v OR x_v. For each short edge e add the hitting clause OR_{v in e} x_v and, for each v in e, the clause

    not r_v OR (OR_{w in e minus {v}} x_w).

For each long edge e use the two guarded clause families of [005](../005/proof.md):

    not a_e OR not x_v OR r_v                     (v in e),
    not a_e OR not x_v OR not x_w                 ({v,w} subset e).

The sign is (-1)^(sum_v r_v + sum_{e in E_L} a_e). There are 2p+q_L base variables and

    C_base = p + sum_{e in E_S}(1+|e|)
               + sum_{e in E_L}(|e|+binom(|e|,2))

raw clauses; their width is at most max(d,3). These are generated counts before deduplication or constant simplification.

Fix D. If it misses a short edge, the formula is inconsistent. If it misses a long edge, that a_e is free and its signed sum is zero. Hence only transversals contribute. For a transversal, the short-edge clauses exclude from R exactly the owners of private short edges. Summing the long-edge a variables, by the argument of [005](../005/proof.md), excludes from R exactly the owners of private long edges. The remaining sum is over R contained in D minus W(D), and equals [W(D)=D], the minimal-transversal indicator. The reasoning is pointwise and so survives restrictions on x.

There are s sign bits. Applying [006](../006/index.yaml) gives exactly

    N = 2p+q_L+max(0,s-1)

declared variables in each formula. If s>0, this is 3p+2q_L-1, and each final formula has C_base+4(s-1)+1 raw clauses. If s=0, the even formula has C_base clauses and the odd formula has C_base+1 clauses, the latter being an empty clause. In all cases, a unified final clause expression is C_base+4 max(0,s-1)+u_epsilon, with u_epsilon=1 when s>0 and u_epsilon=epsilon when s=0 (epsilon=0 even, 1 odd).

For s=0, p=q_L=0. All remaining indexed edges, if any, are empty short edges and already make the base formula inconsistent. If there are no edges, the base formula on zero variables has one assignment, yielding difference one. This is why the expression 3p+2q_L-1 must not be used at s=0. A short singleton edge gives x_v and not r_v. Repeated edges remain valid, and q_L=0 with p>0 is an ordinary nonempty parity-chain case.

For fixed d the width is constant. Therefore the ordinary external algorithm in [001](../001/index.yaml), if assumed, yields the corresponding conditional subexponential bound in p+q_L with polynomial input overhead. The present manifest states the unconditional algebraic reduction; it does not claim an implemented hybrid generator, a new priority result, or reproducible evidence from unretained tests.
