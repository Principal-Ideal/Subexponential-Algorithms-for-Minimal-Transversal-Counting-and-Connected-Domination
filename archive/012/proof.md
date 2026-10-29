# Exact rooted fibres

Let G=(V,E) be simple and undirected, n>=1, with root r. Use x_v for membership in D, c_v for the second cut side, and a_v for a domination flag. The CNF consists of

- not c_v OR x_v for every v;
- units x_r and not c_r;
- not c_u OR not x_v OR c_v, and not c_v OR not x_u OR c_u, for every edge {u,v};
- not a_v OR not x_w for every v and w in the closed neighborhood N[v].

There are 3n declared variables. The clause count is n+2+2m+sum_v |N[v]|=2n+4m+2; maximum width is three. The count is of generated clauses, before optional simplification.

Fix D. If r is absent, the root unit fails. Otherwise c is zero outside D, constant on each connected component of G[D], and zero on the component containing r. Hence there are 2^{cc(G[D])-1} colorings, including 1 when D is a singleton.

For a vertex v dominated by D, some selected x_w forces a_v=0. For an undominated original vertex v, all its neighbors' x_w are zero and a_v is free. If u(D) is the number of such undominated vertices, ordinary counting contributes 2^{u(D)} from flags. Giving a_v=1 weight -1 instead contributes (1-1)^{u(D)}, interpreted as one when u(D)=0. Multiplying proves the two fibre formulas in [012](index.yaml).

For unsigned parity, the contribution is odd exactly when both u(D)=0 and cc(G[D])=1. For signed parity the same conclusion holds. Selection restrictions add units to these same formulas; they never change G or its original domination requirements. If n=0 there is no root and no nonempty connected dominating set, so callers return no detection without creating this rooted formula.
