"""Signed and unsigned Cut&Count encoding, with a SMALL exact polynomial oracle.

This standard-library DPLL is exponential in the worst case. It does not
implement the OpenAI algorithm or demonstrate its claimed running time.
Connected sets are nonempty, including when the input graph has zero vertices.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path
import random
from typing import Iterable

from reduction import CNF

Polynomial = dict[tuple[int, int], int]
FrozenPolynomial = tuple[tuple[int, int, int], ...]


def normalize_graph(n: int, edges: Iterable[Iterable[int]]) -> tuple[tuple[int, int], ...]:
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    result = set()
    for edge in edges:
        edge = tuple(edge)
        if len(edge) != 2 or any(type(v) is not int or not 0 <= v < n for v in edge) or edge[0] == edge[1]:
            raise ValueError("Edges must have two distinct endpoints in range(n)")
        result.add(tuple(sorted(edge)))
    return tuple(sorted(result))


def validate_weights(n: int, weights: Iterable[int]) -> tuple[int, ...]:
    weights = tuple(weights)
    if len(weights) != n or any(type(w) is not int or w < 1 for w in weights):
        raise ValueError("Supply one positive integer weight per vertex")
    return weights


def normalize_restrictions(n: int, selected: dict[int, bool] | None) -> dict[int, bool]:
    selected = {} if selected is None else dict(selected)
    if any(type(v) is not int or not 0 <= v < n or type(value) is not bool for v, value in selected.items()):
        raise ValueError("Selection restrictions must map vertices to Boolean values")
    return selected


def build_signed_cnf(n: int, edges: Iterable[Iterable[int]], root: int,
                     selected: dict[int, bool] | None = None) -> CNF:
    """3n variables: x[1:n], c[n+1:2n], a[2n+1:3n].

    True x_v has weight y*z**w_v; true a_v has weight -1. Every other
    literal has weight 1. Restrictions add units on ORIGINAL graph vertices.
    Before these units the formula has exactly 2n+4m+2 clauses, width <=3.
    """
    edges = normalize_graph(n, edges)
    if type(root) is not int or not 0 <= root < n:
        raise ValueError("root must belong to range(n)")
    selected = normalize_restrictions(n, selected)
    formula = CNF()
    x = [formula.variable(f"x_{v}") for v in range(n)]
    c = [formula.variable(f"c_{v}") for v in range(n)]
    a = [formula.variable(f"a_{v}") for v in range(n)]
    for v in range(n):
        formula.add(-c[v], x[v])
        formula.add(-a[v], -x[v])
    formula.require(x[root], True)
    formula.require(c[root], False)
    for u, v in edges:
        formula.add(-c[u], -x[v], c[v])
        formula.add(-c[v], -x[u], c[u])
        formula.add(-a[u], -x[v])
        formula.add(-a[v], -x[u])
    for v, value in sorted(selected.items()):
        formula.require(x[v], value)
    return formula


def build_parity_cnf(n: int, edges: Iterable[Iterable[int]], root: int, parity: int,
                     selected: dict[int, bool] | None = None) -> CNF:
    """Optional ordinary even/odd CNF interface; selection weights still apply."""
    if parity not in (0, 1):
        raise ValueError("parity must be 0 or 1")
    formula = build_signed_cnf(n, edges, root, selected)
    output = False
    for v in range(n):
        output = formula.xor(output, 2 * n + v + 1, f"helper_parity_{v}")
    formula.require(output, bool(parity))
    return formula


def polynomial_count(formula: CNF, n: int, weights: Iterable[int],
                     stats: dict | None = None, *, signed_helpers: bool = True) -> Polynomial:
    """Exact polynomial WMC by cached DPLL and variable-disjoint decomposition.

    Cache entries contain the unassigned variable identities, not merely their
    count. Weights are immutable within this invocation. Assigned literal
    weights are multiplied outside the cached child result. A free a-variable
    contributes 1+(-1)=0, a free c-variable contributes 2, and a free x-variable
    contributes 1+y*z**w. This routine accepts exactly the 3n-variable layout.
    """
    weights = validate_weights(n, weights)
    if formula.nvars != 3 * n:
        raise ValueError("The signed oracle expects exactly the x,c,a layout")
    if any(any(not 1 <= abs(lit) <= 3 * n for lit in clause) for clause in formula.clauses):
        raise ValueError("Invalid literal")
    counters = {"states": 0, "free_signed_zero_prunes": 0, "component_splits": 0}
    zero: FrozenPolynomial = ()
    one: FrozenPolynomial = ((0, 0, 1),)

    def freeze(poly: Polynomial) -> FrozenPolynomial:
        return tuple((k, w, value) for (k, w), value in sorted(poly.items()) if value)

    def add(left: FrozenPolynomial, right: FrozenPolynomial) -> FrozenPolynomial:
        result = {(k, w): value for k, w, value in left}
        for k, w, value in right:
            result[k, w] = result.get((k, w), 0) + value
        return freeze(result)

    def multiply(left: FrozenPolynomial, right: FrozenPolynomial) -> FrozenPolynomial:
        result: Polynomial = {}
        for k, w, value in left:
            for kk, ww, other in right:
                key = (k + kk, w + ww)
                result[key] = result.get(key, 0) + value * other
        return freeze(result)

    def literal_weight(poly: FrozenPolynomial, literal: int) -> FrozenPolynomial:
        if literal <= 0:
            return poly
        if literal <= n:
            return tuple((k + 1, w + weights[literal - 1], value) for k, w, value in poly)
        if literal > 2 * n and signed_helpers:
            return tuple((k, w, -value) for k, w, value in poly)
        return poly

    def free_weight(poly: FrozenPolynomial, variables: int) -> FrozenPolynomial:
        if signed_helpers and variables >> (2 * n):
            counters["free_signed_zero_prunes"] += 1
            return zero
        while variables:
            bit = variables & -variables
            variable = bit.bit_length()
            variables ^= bit
            if variable <= n:
                poly = add(poly, literal_weight(poly, variable))
            else:
                poly = tuple((k, w, 2 * value) for k, w, value in poly)
        return poly

    def canonical(clauses) -> tuple[tuple[int, ...], ...]:
        result = set()
        for clause in clauses:
            literals = frozenset(clause)
            if not any(-literal in literals for literal in literals):
                result.add(tuple(sorted(literals)))
        return tuple(sorted(result))

    def simplify(clauses, literal):
        return canonical(tuple(value for value in clause if value != -literal)
                         for clause in clauses if literal not in clause)

    @lru_cache(maxsize=None)
    def solve(clauses: tuple[tuple[int, ...], ...], unassigned: int) -> FrozenPolynomial:
        counters["states"] += 1
        if () in clauses:
            return zero
        if not clauses:
            return free_weight(one, unassigned)
        unit = next((clause[0] for clause in clauses if len(clause) == 1), None)
        if unit is not None:
            return literal_weight(solve(simplify(clauses, unit), unassigned & ~(1 << (abs(unit) - 1))), unit)
        occurring = 0
        for clause in clauses:
            for literal in clause:
                occurring |= 1 << (abs(literal) - 1)
        free = unassigned & ~occurring
        if free:
            if signed_helpers and free >> (2 * n):
                counters["free_signed_zero_prunes"] += 1
                return zero
            return free_weight(solve(clauses, occurring), free)

        # Components use original variable IDs, which determine literal weights.
        parent = {v: v for v in range(1, 3 * n + 1) if occurring & (1 << (v - 1))}

        def find(v):
            while parent[v] != v:
                parent[v] = parent[parent[v]]
                v = parent[v]
            return v

        for clause in clauses:
            first = find(abs(clause[0]))
            for literal in clause[1:]:
                parent[find(abs(literal))] = first
        groups: dict[int, list] = {}
        masks: dict[int, int] = {}
        for clause in clauses:
            key = find(abs(clause[0]))
            groups.setdefault(key, []).append(clause)
            for literal in clause:
                masks[key] = masks.get(key, 0) | (1 << (abs(literal) - 1))
        if len(groups) > 1:
            counters["component_splits"] += 1
            result = one
            for key in sorted(groups):
                result = multiply(result, solve(tuple(groups[key]), masks[key]))
                if not result:
                    break
            return result
        scores: dict[int, int] = {}
        for clause in clauses:
            for literal in clause:
                variable = abs(literal)
                scores[variable] = scores.get(variable, 0) + (1 << (3 - len(clause)))
        candidates = [v for v in scores if v <= n] or list(scores)
        variable = max(candidates, key=lambda v: (scores[v], -v))
        remaining = unassigned & ~(1 << (variable - 1))
        return add(solve(simplify(clauses, -variable), remaining),
                   literal_weight(solve(simplify(clauses, variable), remaining), variable))

    answer = solve(canonical(formula.clauses), (1 << (3 * n)) - 1)
    if stats is not None:
        stats.update(counters)
        stats.update(cache_hits=solve.cache_info().hits, cache_entries=solve.cache_info().currsize)
    return {(k, w): value for k, w, value in answer}


def signed_polynomial_count(formula: CNF, n: int, weights: Iterable[int],
                            stats: dict | None = None) -> Polynomial:
    """True helper literals have weight -1: nondominating selections cancel."""
    return polynomial_count(formula, n, weights, stats, signed_helpers=True)


def unsigned_polynomial_count(formula: CNF, n: int, weights: Iterable[int],
                              stats: dict | None = None) -> Polynomial:
    """All helper weights are +1: nondominating selections have even counts."""
    return polynomial_count(formula, n, weights, stats, signed_helpers=False)


def selection_properties(n: int, edges: Iterable[Iterable[int]], selected: Iterable[int]) -> tuple[bool, int]:
    """Direct graph definition, independent of the CNF and sign cancellation."""
    edges = normalize_graph(n, edges)
    selected = set(selected)
    if any(type(v) is not int or not 0 <= v < n for v in selected):
        raise ValueError("Selected vertex outside the graph")
    neighbors = [set() for _ in range(n)]
    for u, v in edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    dominates = all(v in selected or bool(neighbors[v] & selected) for v in range(n))
    remaining = set(selected)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            new = neighbors[stack.pop()] & remaining
            remaining -= new
            stack.extend(new)
    return dominates, components


def brute_cut_polynomial(n: int, edges: Iterable[Iterable[int]], root: int,
                         weights: Iterable[int], selected: dict[int, bool] | None = None) -> Polynomial:
    edges = normalize_graph(n, edges)
    weights = validate_weights(n, weights)
    selected = normalize_restrictions(n, selected)
    if type(root) is not int or not 0 <= root < n:
        raise ValueError("Invalid root")
    result: Polynomial = {}
    for mask in range(1 << n):
        vertices = {v for v in range(n) if mask & (1 << v)}
        if root not in vertices or any((v in vertices) != value for v, value in selected.items()):
            continue
        dominates, components = selection_properties(n, edges, vertices)
        if dominates:
            key = (len(vertices), sum(weights[v] for v in vertices))
            result[key] = result.get(key, 0) + (1 << (components - 1))
    return result


def brute_connected_sets(n: int, edges: Iterable[Iterable[int]], size_limit: int | None = None,
                         root: int | None = None) -> list[list[int]]:
    edges = normalize_graph(n, edges)
    limit = n if size_limit is None else size_limit
    result = []
    for mask in range(1, 1 << n):
        vertices = [v for v in range(n) if mask & (1 << v)]
        if len(vertices) > limit or (root is not None and root not in vertices):
            continue
        dominates, components = selection_properties(n, edges, vertices)
        if dominates and components == 1:
            result.append(vertices)
    return result


def brute_unsigned_cut_polynomial(n: int, edges: Iterable[Iterable[int]], root: int,
                                  weights: Iterable[int], selected: dict[int, bool] | None = None) -> Polynomial:
    """Direct fixed-D contribution 2**(undominated(D)+components(D)-1)."""
    edges = normalize_graph(n, edges)
    weights = validate_weights(n, weights)
    selected = normalize_restrictions(n, selected)
    if type(root) is not int or not 0 <= root < n:
        raise ValueError("Invalid root")
    result: Polynomial = {}
    for mask in range(1 << n):
        vertices = {v for v in range(n) if mask & (1 << v)}
        if root not in vertices or any((v in vertices) != value for v, value in selected.items()):
            continue
        _, components = selection_properties(n, edges, vertices)
        undominated = sum(v not in vertices and not any((u in vertices and w == v) or
                         (w in vertices and u == v) for u, w in edges) for v in range(n))
        key = (len(vertices), sum(weights[v] for v in vertices))
        result[key] = result.get(key, 0) + (1 << (undominated + components - 1))
    return result


def recover_witness(n: int, edges: Iterable[Iterable[int]], root: int, weights: Iterable[int],
                    target: tuple[int, int], *, signed_helpers: bool = False) -> list[int]:
    """Parity self-reduction; restrictions always refer to the original graph."""
    edges = normalize_graph(n, edges)
    weights = validate_weights(n, weights)
    initial = polynomial_count(build_signed_cnf(n, edges, root), n, weights, signed_helpers=signed_helpers)
    if initial.get(target, 0) % 2 != 1:
        raise ValueError("Witness recovery requires an odd target coefficient")
    restrictions: dict[int, bool] = {}
    for v in range(n):
        trial = dict(restrictions)
        trial[v] = False
        polynomial = polynomial_count(build_signed_cnf(n, edges, root, trial), n, weights, signed_helpers=signed_helpers)
        restrictions[v] = polynomial.get(target, 0) % 2 != 1
    witness = [v for v, value in restrictions.items() if value]
    dominates, components = selection_properties(n, edges, witness)
    if not (root in witness and dominates and components == 1 and
            len(witness) == target[0] and sum(weights[v] for v in witness) == target[1]):
        raise AssertionError("Recovered witness failed independent original-graph verification")
    return witness


def odd_target_with_weights(n: int, edges: Iterable[Iterable[int]], weights: Iterable[int],
                            size_limit: int, root: int | None = None, *, signed_helpers: bool = False,
                            minimize: bool = False) -> dict | None:
    edges = normalize_graph(n, edges)
    weights = validate_weights(n, weights)
    if type(size_limit) is not int or size_limit < 0:
        raise ValueError("size_limit must be a nonnegative integer")
    if root is not None and (type(root) is not int or not 0 <= root < n):
        raise ValueError("Invalid root")
    best = None
    for candidate_root in range(n) if root is None else (root,):
        polynomial = polynomial_count(build_signed_cnf(n, edges, candidate_root), n, weights, signed_helpers=signed_helpers)
        targets = sorted(key for key, value in polynomial.items() if 1 <= key[0] <= size_limit and value % 2)
        if targets:
            target = targets[0]
            candidate = {"root": candidate_root, "target_coefficient": {"size": target[0], "weight": target[1]},
                         "coefficient": polynomial[target]}
            if not minimize:
                return candidate
            if best is None or target[0] < best["target_coefficient"]["size"]:
                best = candidate
    return best


def find_with_weights(n: int, edges: Iterable[Iterable[int]], weights: Iterable[int],
                      size_limit: int, root: int | None = None, *, signed_helpers: bool = False,
                      minimize: bool = False) -> dict | None:
    edges = normalize_graph(n, edges)
    weights = validate_weights(n, weights)
    found = odd_target_with_weights(n, edges, weights, size_limit, root,
                                   signed_helpers=signed_helpers, minimize=minimize)
    if found is None:
        return None
    target = found["target_coefficient"]
    witness = recover_witness(n, edges, found["root"], weights, (target["size"], target["weight"]),
                              signed_helpers=signed_helpers)
    return found | {"witness": witness, "verified": True}


def randomized_decide(n: int, edges: Iterable[Iterable[int]], size_limit: int | None = None,
                       trials: int = 5, seed: int | None = None, root: int | None = None,
                       mode: str = "unsigned", minimize: bool = False) -> dict:
    edges = normalize_graph(n, edges)
    limit = n if size_limit is None else size_limit
    if type(limit) is not int or limit < 0:
        raise ValueError("size_limit must be a nonnegative integer")
    if type(trials) is not int or trials < 1:
        raise ValueError("trials must be a positive integer")
    if root is not None and (type(root) is not int or not 0 <= root < n):
        raise ValueError("Invalid root")
    if mode not in ("unsigned", "signed"):
        raise ValueError("mode must be unsigned or signed")
    limit = min(limit, n)
    rng = random.SystemRandom() if seed is None else random.Random(seed)
    weight_bits = (2 * n - 1).bit_length() if n else 0
    base = {"n": n, "m": len(edges), "size_limit": limit, "root_constraint": root,
            "seed": seed, "random_source": "system" if seed is None else "seeded_prng",
            "trials_requested": trials, "minimize": minimize,
            "isolation_weight_max": 1 << weight_bits if n else 0,
            "mode": mode, "solver": "Exact exponential polynomial DPLL for validation; not the OpenAI algorithm",
            "connected_set_convention": "nonempty",
            "probability_note": "The 2^-t false-negative bound assumes independent uniform random weights; a fixed PRNG seed gives a reproducible run, not a certificate of nonexistence."}
    if n == 0 or limit == 0:
        return base | {"status": "not_detected", "witness": None, "verified": False,
                       "trials_completed": 0, "isolation_weights": (1,) * n,
                       "interpretation": "The nonempty connected-set convention excludes all sets in this empty search domain.",
                       "false_negative_bound_under_independent_sampling": "0"}
    weights: tuple[int, ...] = ()
    best = None
    for trial in range(1, trials + 1):
        # A power-of-two range needs a fixed number of random bits, no rejection.
        # Its size is >=2n, so the Isolation Lemma still gives success >=1/2.
        weights = tuple(1 + rng.getrandbits(weight_bits) for _ in range(n))
        if minimize:
            candidate = odd_target_with_weights(n, edges, weights, limit, root,
                                                signed_helpers=(mode == "signed"), minimize=True)
            if candidate is not None and (best is None or candidate["target_coefficient"]["size"] < best["target_coefficient"]["size"]):
                best = candidate | {"isolation_weights": weights, "discovered_in_trial": trial}
            continue
        found = find_with_weights(n, edges, weights, limit, root, signed_helpers=(mode == "signed"))
        if found is not None:
            return base | found | {"status": "found", "trials_completed": trial,
                                   "isolation_weights": weights, "false_positive_possible": False}
    if best is not None:
        target = best["target_coefficient"]
        witness = recover_witness(n, edges, best["root"], best["isolation_weights"],
                                  (target["size"], target["weight"]), signed_helpers=(mode == "signed"))
        return base | best | {"status": "found", "witness": witness, "verified": True,
                              "trials_completed": trials, "false_positive_possible": False,
                              "optimality_failure_bound": f"2^-{trials}",
                              "optimality_note": "Feasibility is independently verified. Minimum size is a probabilistic claim under independent uniform weight sampling, not a deterministic optimality certificate."}
    return base | {"status": "not_detected", "witness": None, "verified": False,
                   "trials_completed": trials, "isolation_weights": weights,
                   "interpretation": "No witness detected; this is not a proof that no feasible connected dominating set exists.",
                   "false_negative_bound_under_independent_sampling": f"2^-{trials}"}


def export_encoding(prefix: Path, n: int, edges, root: int, weights: Iterable[int], mode: str = "unsigned") -> list[str]:
    weights = validate_weights(n, weights)
    paths = []
    for name, formula in (("base", build_signed_cnf(n, edges, root)),
                          ("even", build_parity_cnf(n, edges, root, 0)),
                          ("odd", build_parity_cnf(n, edges, root, 1))):
        path = Path(str(prefix) + f".r{root}.{name}.cnf")
        path.parent.mkdir(parents=True, exist_ok=True)
        note = "c See companion metadata for polynomial weights and signed/unsigned interpretations.\n"
        path.write_text(note + formula.dimacs(), encoding="utf-8")
        paths.append(str(path))
    path = Path(str(prefix) + f".r{root}.weights.json")
    metadata = {"n": n, "root": root, "isolation_weights": weights, "primary_mode": mode,
                "signed_variables": 3 * n, "parity_variables": 4 * n - 1,
                "false_literal_weights": "all 1",
                "true_literal_weights_signed": {str(v + 1): f"y*z^{weights[v]}" for v in range(n)} |
                    {str(2 * n + v + 1): "-1" for v in range(n)},
                "other_literal_weights": "1",
                "unsigned_rule": "On base.cnf only true selection literals carry y*z^w; all helper and cut literal weights are 1. Reduce coefficients modulo 2 for connected domination.",
                "even_odd_rule": "For even/odd CNFs all auxiliary literal weights are 1; selection weights y*z^w remain. Subtract their polynomial weighted counts.",
                "size_limit_rule": "No size unit/circuit is exported. Select coefficients y^k with 1 <= k <= the requested limit."}
    path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    paths.append(str(path))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help='JSON {"n": 4, "edges": [[0,1],[1,2],[2,3]]}')
    parser.add_argument("--size-limit", type=int)
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--seed", type=int, help="Use a reproducible PRNG seed; default uses system randomness")
    parser.add_argument("--root", type=int)
    parser.add_argument("--mode", choices=("unsigned", "signed"), default="unsigned")
    parser.add_argument("--minimize", action="store_true", help="Return the smallest detected size; optimality remains probabilistic")
    parser.add_argument("--export-prefix", "--export", dest="export_prefix", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    n, edges = data["n"], normalize_graph(data["n"], data["edges"])
    result = randomized_decide(n, edges, args.size_limit, args.trials, args.seed, args.root, args.mode, args.minimize)
    if args.export_prefix is not None:
        roots = range(n) if args.root is None else (args.root,)
        result["exports"] = [path for root in roots for path in
                             export_encoding(args.export_prefix, n, edges, root, result["isolation_weights"], args.mode)]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
