"""Linear-variable signed reduction from minimal transversals to two #3SATs.

Python standard library only. The included exact DPLL is a small validation
oracle, NOT an implementation of any claimed subexponential #SAT algorithm.
Vertices are numbered 0,...,p-1. Duplicate hyperedges are deliberately retained.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import combinations
import json
from pathlib import Path
from typing import Iterable

Wire = int | bool


@dataclass
class CNF:
    names: list[str] = field(default_factory=list)
    clauses: list[tuple[int, ...]] = field(default_factory=list)
    # (output variable, operation, input wires), in topological order.
    gates: list[tuple[int, str, tuple[Wire, ...]]] = field(default_factory=list)

    @property
    def nvars(self) -> int:
        return len(self.names)

    def variable(self, name: str) -> int:
        self.names.append(name)
        return self.nvars

    def add(self, *literals: int) -> None:
        if any(type(x) is not int or x == 0 or abs(x) > self.nvars for x in literals):
            raise ValueError("Invalid CNF literal")
        if len(literals) > 3:
            raise ValueError("This encoder emits clauses of width at most 3")
        self.clauses.append(tuple(literals))

    def require(self, wire: Wire, value: bool) -> None:
        if type(wire) is bool:
            if wire != value:
                self.add()
        else:
            self.add(wire if value else -wire)

    def xor(self, a: Wire, b: Wire, name: str) -> Wire:
        if a is False:
            return b
        if b is False:
            return a
        if type(a) is bool and type(b) is bool:
            return a != b
        # True constants occur only through public API use, not this encoder.
        if a is True or b is True:
            v = b if a is True else a
            z = self.variable(name)
            self.add(v, z)
            self.add(-v, -z)
            self.gates.append((z, "xor", (a, b)))
            return z
        if a == b:
            return False
        z = self.variable(name)
        self.add(a, b, -z)
        self.add(-a, -b, -z)
        self.add(a, -b, z)
        self.add(-a, b, z)
        self.gates.append((z, "xor", (a, b)))
        return z

    def conjunction(self, a: Wire, b: Wire, name: str) -> Wire:
        if a is False or b is False:
            return False
        if a is True:
            return b
        if b is True or a == b:
            return a
        z = self.variable(name)
        self.add(-z, a)
        self.add(-z, b)
        self.add(z, -a, -b)
        self.gates.append((z, "and", (a, b)))
        return z

    def majority(self, a: Wire, b: Wire, c: Wire, name: str) -> Wire:
        if a is False:
            return self.conjunction(b, c, name)
        if b is False:
            return self.conjunction(a, c, name)
        if c is False:
            return self.conjunction(a, b, name)
        # Inputs to the counting circuit are variables or False, never True.
        if a is True or b is True or c is True:
            raise ValueError("Majority True constants are not needed here")
        if a == b or a == c:
            return a
        if b == c:
            return b
        z = self.variable(name)
        for u, v in ((a, b), (a, c), (b, c)):
            self.add(-u, -v, z)
            self.add(u, v, -z)
        self.gates.append((z, "majority", (a, b, c)))
        return z

    def extend(self, base_assignment: dict[int, bool]) -> dict[int, bool]:
        result = dict(base_assignment)

        def value(wire: Wire) -> bool:
            return wire if type(wire) is bool else result[wire]

        for z, operation, inputs in self.gates:
            values = [value(x) for x in inputs]
            if operation == "xor":
                result[z] = values[0] != values[1]
            elif operation == "and":
                result[z] = all(values)
            elif operation == "majority":
                result[z] = sum(values) >= 2
            else:
                raise AssertionError(operation)
        return result

    def satisfies(self, assignment: dict[int, bool]) -> bool:
        return all(any(assignment[abs(x)] == (x > 0) for x in c) for c in self.clauses)

    def dimacs(self) -> str:
        comments = ["c Small exact validation encoding; width at most 3."]
        comments.extend(f"c var {i} {name}" for i, name in enumerate(self.names, 1))
        lines = comments + [f"p cnf {self.nvars} {len(self.clauses)}"]
        lines.extend(" ".join(map(str, clause)) + (" 0" if clause else "0") for clause in self.clauses)
        return "\n".join(lines) + "\n"


def normalize_hypergraph(p: int, edges: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
    if type(p) is not int or p < 0:
        raise ValueError("p must be a nonnegative integer")
    result = []
    for edge in edges:
        values = list(edge)
        if any(type(v) is not int or not 0 <= v < p for v in values):
            raise ValueError("Every vertex must be an integer in range(p)")
        result.append(tuple(sorted(set(values))))
    return tuple(result)


def add_binary_count(cnf: CNF, variables: list[int]) -> list[Wire]:
    """Return little-endian bits of their Hamming weight, with unique extension.

    Pad to b=2**h leaves. A level-j adder uses <=3j-1 fresh variables,
    <=14j-7 clauses: one half adder, then j-1 full adders. Thus p>=2 uses
    <=5b-3h-5 < 10p auxiliaries, <=21b-14h-21 < 42p gate clauses.
    Constant simplification can only decrease these bounds.
    """
    p = len(variables)
    if p == 0:
        return [False]
    b = 1 << (p - 1).bit_length()
    numbers: list[list[Wire]] = [[v] for v in variables] + [[False] for _ in range(b - p)]
    level = 0
    while len(numbers) > 1:
        level += 1
        next_numbers = []
        for i in range(0, len(numbers), 2):
            left, right = numbers[i], numbers[i + 1]
            carry: Wire = False
            output: list[Wire] = []
            for bit, (a, b_wire) in enumerate(zip(left, right, strict=True)):
                prefix = f"count_l{level}_a{i // 2}_b{bit}"
                pair = cnf.xor(a, b_wire, prefix + "_xor")
                output.append(cnf.xor(pair, carry, prefix + "_sum"))
                carry = cnf.majority(a, b_wire, carry, prefix + "_carry")
            output.append(carry)
            next_numbers.append(output)
        numbers = next_numbers
    return numbers[0]


def impose_size(cnf: CNF, variables: list[int], k: int) -> None:
    if type(k) is not int:
        raise ValueError("size must be an integer")
    if k < 0 or k > len(variables):
        cnf.add()
        return
    for i, wire in enumerate(add_binary_count(cnf, variables)):
        cnf.require(wire, bool((k >> i) & 1))


def encode(p: int, edges: Iterable[Iterable[int]], parity: int, size: int | None = None) -> CNF:
    """Encode even (0) or odd (1) signed sum using D,R,P variables.

    R subset D; selected edge e forces D intersect e subset R and |D intersect e|<=1.
    The sign is (-1)**(|R|+|P|). Empty parity list has even parity.
    Without size restriction N=2p+q+max(0,p+q-1); for p+q>0 this is 3p+2q-1.
    """
    if parity not in (0, 1):
        raise ValueError("parity must be 0 or 1")
    edges = normalize_hypergraph(p, edges)
    cnf = CNF()
    d = [cnf.variable(f"D_{v}") for v in range(p)]
    r = [cnf.variable(f"R_{v}") for v in range(p)]
    a = [cnf.variable(f"P_{i}") for i in range(len(edges))]
    for v in range(p):
        cnf.add(-r[v], d[v])
    for selected, edge in zip(a, edges, strict=True):
        for v in edge:
            cnf.add(-selected, -d[v], r[v])
        for v, w in combinations(edge, 2):
            cnf.add(-selected, -d[v], -d[w])
    parity_bits = r + a
    total: Wire = False
    for i, bit in enumerate(parity_bits):
        total = cnf.xor(total, bit, f"parity_{i}")
    cnf.require(total, bool(parity))
    if size is not None:
        impose_size(cnf, d, size)
    return cnf


def count_models(cnf: CNF) -> int:
    """Exact cached DPLL #SAT oracle for SMALL tests; exponential worst case."""
    def canonical(clauses: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
        unique = set()
        for clause in clauses:
            literals = frozenset(clause)
            if not any(-x in literals for x in literals):
                unique.add(tuple(sorted(literals)))
        return tuple(sorted(unique))

    def simplify(clauses: tuple[tuple[int, ...], ...], literal: int) -> tuple[tuple[int, ...], ...]:
        return canonical(tuple(x for x in c if x != -literal) for c in clauses if literal not in c)

    @lru_cache(maxsize=None)
    def solve(clauses: tuple[tuple[int, ...], ...], unassigned: int) -> int:
        if () in clauses:
            return 0
        while True:
            unit = next((c[0] for c in clauses if len(c) == 1), None)
            if unit is None:
                break
            clauses = simplify(clauses, unit)
            unassigned -= 1
            if () in clauses:
                return 0
        if not clauses:
            return 1 << unassigned
        scores: dict[int, int] = {}
        for clause in clauses:
            for lit in clause:
                scores[abs(lit)] = scores.get(abs(lit), 0) + (1 << (3 - len(clause)))
        variable = max(scores, key=scores.get)
        return solve(simplify(clauses, variable), unassigned - 1) + solve(simplify(clauses, -variable), unassigned - 1)

    return solve(canonical(cnf.clauses), cnf.nvars)


def edge_masks(p: int, edges: Iterable[Iterable[int]]) -> tuple[int, ...]:
    return tuple(sum(1 << v for v in edge) for edge in normalize_hypergraph(p, edges))


def brute_minimal_counts(p: int, edges: Iterable[Iterable[int]]) -> list[int]:
    """Independent definition: test hitting, then every single-vertex deletion."""
    masks = edge_masks(p, edges)
    result = [0] * (p + 1)
    for d in range(1 << p):
        if not all(d & e for e in masks):
            continue
        minimal = True
        for v in range(p):
            if d & (1 << v) and all((d ^ (1 << v)) & e for e in masks):
                minimal = False
                break
        if minimal:
            result[d.bit_count()] += 1
    return result


def signed_counts_factored(p: int, edges: Iterable[Iterable[int]]) -> list[int]:
    """Sum D,R literally, factoring each independent P-bit as 1-1 or 1.

    This avoids constructing CNF and is independent of the #SAT oracle.
    No private-edge minimality characterization is used to decide the result.
    """
    masks = edge_masks(p, edges)
    result = [0] * (p + 1)
    for d in range(1 << p):
        intersections = tuple(d & e for e in masks)
        if 0 in intersections:
            continue  # One free P-bit contributes 1-1.
        singletons = tuple(x for x in intersections if x.bit_count() == 1)
        subtotal = 0
        r = d
        while True:
            if not any(x & r for x in singletons):
                subtotal += -1 if r.bit_count() % 2 else 1
            if r == 0:
                break
            r = (r - 1) & d
        result[d.bit_count()] += subtotal
    return result


def original_signed_counts_factored(p: int, edges: Iterable[Iterable[int]]) -> list[int]:
    """Check proposal's original D,T,P,Q formula by factoring P,Q separately."""
    masks = edge_masks(p, edges)
    result = [0] * (p + 1)
    for d in range(1 << p):
        if any(d & e == 0 for e in masks):
            continue  # Sum over Q vanishes.
        t = d
        while True:
            eligible_p = any((d & e).bit_count() <= 1 and t & e == 0 for e in masks)
            if not eligible_p:
                result[d.bit_count()] += -1 if (d.bit_count() + t.bit_count()) % 2 else 1
            if t == 0:
                break
            t = (t - 1) & d
    return result


def closed_neighborhood_hypergraph(n: int, graph_edges: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
    neighbors = [{v} for v in range(n)]
    for edge in graph_edges:
        values = tuple(edge)
        if len(values) != 2 or values[0] == values[1] or any(type(v) is not int or not 0 <= v < n for v in values):
            raise ValueError("Expected a simple undirected edge with endpoints in range(n)")
        u, v = values
        neighbors[u].add(v)
        neighbors[v].add(u)
    return tuple(tuple(sorted(s)) for s in neighbors)


def set_cover_hypergraph(universe_size: int, sets: Iterable[Iterable[int]]) -> tuple[int, tuple[tuple[int, ...], ...]]:
    """Selectable sets become vertices; original elements become hyperedges."""
    sets = normalize_hypergraph(universe_size, sets)
    return len(sets), tuple(tuple(i for i, s in enumerate(sets) if v in s) for v in range(universe_size))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help='JSON {"p": 3, "edges": [[0,1],[1,2]]}')
    parser.add_argument("--output-prefix", type=Path, help="Export .even.cnf and .odd.cnf")
    parser.add_argument("--size", type=int, help="Restrict |D| to this value")
    parser.add_argument("--count", action="store_true", help="Run exponential small-instance DPLL validation")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    p, edges = data["p"], normalize_hypergraph(data["p"], data["edges"])
    formulas = [encode(p, edges, parity, args.size) for parity in (0, 1)]
    result = {"p": p, "q": len(edges), "size": args.size,
              "variables": formulas[0].nvars, "clauses_even": len(formulas[0].clauses),
              "clauses_odd": len(formulas[1].clauses), "width_at_most": 3}
    if args.output_prefix:
        for name, formula in zip(("even", "odd"), formulas, strict=True):
            destination = Path(str(args.output_prefix) + f".{name}.cnf")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(formula.dimacs(), encoding="utf-8")
    if args.count:
        even, odd = [count_models(f) for f in formulas]
        counts = brute_minimal_counts(p, edges)
        expected = sum(counts) if args.size is None else counts[args.size] if 0 <= args.size <= p else 0
        if even - odd != expected:
            raise AssertionError("Reduction and direct enumeration disagree")
        result.update(even=even, odd=odd, difference=even - odd, independent_count=expected,
                      counts_by_size=counts, upper_size=max((k for k, count in enumerate(counts) if count), default=None))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
