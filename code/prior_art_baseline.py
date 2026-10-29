"""Validation baseline instantiating negative-weight Skolemization.

This is a comparison encoding suggested by the research audit, not a claim of
a new technique. It uses more variables than reduction.encode, but already
demonstrates a linear-variable route from the known signed method.
"""

from itertools import combinations

from reduction import CNF, normalize_hypergraph


def known_skolem_baseline(p: int, edges, parity: int) -> CNF:
    """Two unweighted #3SAT formulas for a negative-weight Skolem encoding.

    Base variables: x[p],u[p],b[q],s[q],t[q], hence 2p+3q.
    Every false u, s, or t has weight -1; all remaining literal weights are +1.
    A parity chain converts these weights into even/odd ordinary #SAT calls.
    N=2p+3q+max(0,p+2q-1), i.e. 3p+5q-1 when p+q>0.
    """
    if parity not in (0, 1):
        raise ValueError("parity must be 0 or 1")
    edges = normalize_hypergraph(p, edges)
    cnf = CNF()
    x = [cnf.variable(f"x_{v}") for v in range(p)]
    u = [cnf.variable(f"u_{v}") for v in range(p)]
    b = [cnf.variable(f"b_{i}") for i in range(len(edges))]
    s = [cnf.variable(f"s_{i}") for i in range(len(edges))]
    t = [cnf.variable(f"t_{i}") for i in range(len(edges))]
    for i, edge in enumerate(edges):
        for v, w in combinations(edge, 2):
            cnf.add(b[i], -x[v], -x[w])
            cnf.add(s[i], -x[v], -x[w])
        cnf.add(s[i], b[i])
        for v in edge:
            cnf.add(t[i], -x[v])
            cnf.add(u[v], b[i])
    for v in range(p):
        cnf.add(u[v], x[v])
    weighted_variables = u + s + t
    total = False
    for i, variable in enumerate(weighted_variables):
        total = cnf.xor(total, variable, f"baseline_parity_{i}")
    # Number of false weighted variables = len(weighted_variables) - sum(bits).
    cnf.require(total, bool(parity ^ (len(weighted_variables) % 2)))
    return cnf
