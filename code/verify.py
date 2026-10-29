"""Reproducible tests of the reduction; run with Python >=3.10, no dependencies."""

from __future__ import annotations

import argparse
from itertools import combinations, product
import json
from pathlib import Path
import platform
import random
import sys
from time import perf_counter

from reduction import (CNF, add_binary_count, brute_minimal_counts,
                       closed_neighborhood_hypergraph, count_models, encode,
                       impose_size, original_signed_counts_factored,
                       set_cover_hypergraph, signed_counts_factored)
from prior_art_baseline import known_skolem_baseline


def check(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def formulas_count(p: int, edges: list | tuple, size: int | None = None) -> tuple[int, int]:
    formulas = [encode(p, edges, parity, size) for parity in (0, 1)]
    for formula in formulas:
        check(all(len(c) <= 3 for c in formula.clauses), "clause width")
    if size is None:
        check(formulas[0].nvars == 2 * p + len(edges) + max(0, p + len(edges) - 1), "variable bound")
        base_clauses = p + sum(len(set(e)) + len(set(e)) * (len(set(e)) - 1) // 2 for e in edges)
        parity_variables = max(0, p + len(edges) - 1)
        # Empty input: even has no clauses; odd has one empty clause.
        expected_clauses = base_clauses + 4 * parity_variables + (1 if p + len(edges) else 0)
        check(len(formulas[0].clauses) == expected_clauses, "exact clause bound")
    return tuple(count_models(formula) for formula in formulas)


def verify_gates_and_oracle() -> dict:
    rows = 0
    for operation, arity in (("xor", 2), ("conjunction", 2), ("majority", 3)):
        for bits in product((False, True), repeat=arity):
            formula = CNF()
            variables = [formula.variable(f"x{i}") for i in range(arity)]
            output = getattr(formula, operation)(*variables, "output")
            expected = sum(bits) == 1 if operation == "xor" else all(bits) if operation == "conjunction" else sum(bits) >= 2
            for variable, bit in zip(variables, bits, strict=True):
                formula.require(variable, bit)
            check(count_models(formula) == 1, (operation, bits, "unique extension"))
            formula.require(output, expected)
            check(count_models(formula) == 1, (operation, bits, "correct output"))
            formula.require(output, not expected)
            check(count_models(formula) == 0, (operation, bits, "wrong output"))
            rows += 1

    rng = random.Random(20261029)
    random_cnf_cases = 0
    for n in range(7):
        for _ in range(40):
            formula = CNF(names=[f"x{i}" for i in range(n)])
            if n:
                for _ in range(rng.randrange(12)):
                    formula.add(*(rng.choice((-1, 1)) * rng.randrange(1, n + 1) for _ in range(rng.randrange(4))))
            expected = sum(formula.satisfies(dict(enumerate(bits, 1))) for bits in product((False, True), repeat=n))
            check(count_models(formula) == expected, ("DPLL cross-check", formula.dimacs()))
            random_cnf_cases += 1
    return {"gate_truth_table_rows": rows, "random_cnf_oracle_cross_checks": random_cnf_cases}


def verify_circuits() -> dict:
    parity_rows = 0
    for n in range(9):
        for bits in product((False, True), repeat=n):
            formula = CNF()
            variables = [formula.variable(f"x{i}") for i in range(n)]
            parity = False
            for i, variable in enumerate(variables):
                parity = formula.xor(parity, variable, f"parity{i}")
            for variable, value in zip(variables, bits, strict=True):
                formula.require(variable, value)
            check(count_models(formula) == 1, ("parity unique extension", bits))
            formula.require(parity, bool(sum(bits) % 2))
            check(count_models(formula) == 1, ("parity value", bits))
            formula.require(parity, not bool(sum(bits) % 2))
            check(count_models(formula) == 0, ("parity wrong value", bits))
            parity_rows += 1

    size_rows = 0
    for p in range(9):
        for bits in product((False, True), repeat=p):
            formula = CNF()
            variables = [formula.variable(f"x{i}") for i in range(p)]
            outputs = add_binary_count(formula, variables)
            assignment = formula.extend(dict(zip(variables, bits, strict=True)))
            count = sum((wire if type(wire) is bool else assignment[wire]) << i for i, wire in enumerate(outputs))
            check(count == sum(bits), ("count circuit", bits))
            check(formula.satisfies(assignment), ("count circuit satisfaction", bits))
            for variable, value in zip(variables, bits, strict=True):
                formula.require(variable, value)
            check(count_models(formula) == 1, ("count circuit unique extension", bits))
            size_rows += 1

    bound_cases = 0
    for p in range(1, 257):
        formula = CNF()
        variables = [formula.variable(f"x{i}") for i in range(p)]
        add_binary_count(formula, variables)
        h = (p - 1).bit_length()
        b = 1 << h
        check(formula.nvars - p <= 5 * b - 3 * h - 5 < 10 * p, ("linear variables", p))
        check(len(formula.clauses) <= 21 * b - 14 * h - 21 < 42 * p, ("linear clauses", p))
        check(all(len(c) <= 3 for c in formula.clauses), "count circuit width")
        bound_cases += 1
    for p in range(5):
        for k in range(-1, p + 2):
            formula = CNF()
            variables = [formula.variable(f"x{i}") for i in range(p)]
            impose_size(formula, variables, k)
            expected = sum(sum(bits) == k for bits in product((False, True), repeat=p))
            check(count_models(formula) == expected, ("size circuit total", p, k))
    return {"parity_input_assignments": parity_rows, "count_input_assignments": size_rows,
            "linear_bound_sizes_checked": bound_cases}


def all_hypergraphs(p: int):
    possible_edges = [tuple(v for v in range(p) if mask & (1 << v)) for mask in range(1 << p)]
    for family in range(1 << len(possible_edges)):
        yield [edge for i, edge in enumerate(possible_edges) if family & (1 << i)]


def verify_exhaustive_small() -> dict:
    histogram = {}
    formula_calls = 0
    for p in range(4):
        number = 0
        for edges in all_hypergraphs(p):
            expected = brute_minimal_counts(p, edges)
            check(signed_counts_factored(p, edges) == expected, ("factored", p, edges))
            check(original_signed_counts_factored(p, edges) == expected, ("original", p, edges))
            even, odd = formulas_count(p, edges)
            check(even - odd == sum(expected), ("CNF", p, edges, even, odd, expected))
            formula_calls += 2
            for size in range(p + 1):
                even, odd = formulas_count(p, edges, size)
                check(even - odd == expected[size], ("size CNF", p, edges, size))
                formula_calls += 2
            number += 1
        histogram[str(p)] = number
        print(f"All p={p} simple hypergraphs: {number}; all sizes and actual CNF counts passed.", flush=True)
    check(sum(histogram.values()) == 278, "Expected 278 including p=0")
    return {"hypergraphs_by_p": histogram, "total_hypergraphs": 278, "actual_dpll_calls": formula_calls}


def verify_exhaustive_four() -> dict:
    number = 0
    for edges in all_hypergraphs(4):
        expected = brute_minimal_counts(4, edges)
        check(signed_counts_factored(4, edges) == expected, ("p=4 factored", edges))
        check(original_signed_counts_factored(4, edges) == expected, ("p=4 original", edges))
        number += 1
    return {"hypergraphs": number, "comparison": "factored D,R,P and original D,T,P,Q sums versus independent deletion enumeration, all sizes",
            "actual_cnf_counts_for_all_p4": False}


def verify_boundary_random_and_applications() -> dict:
    cases = [(0, []), (0, [()]), (0, [(), ()]), (3, []), (3, [()]),
             (3, [(0,), (0,)]), (4, [(0, 1), (0, 1), (1, 2)]),
             (4, [(0, 0, 1), (0, 1)]), (4, [(0,), (1, 2)])]
    rng = random.Random(20261029)
    for _ in range(20):
        p = rng.randrange(4, 7)
        edges = [tuple(v for v in range(p) if rng.randrange(2)) for _ in range(rng.randrange(1, 7))]
        cases.append((p, edges))
    samples = []
    calls = 0
    for p, edges in cases:
        expected = brute_minimal_counts(p, edges)
        check(signed_counts_factored(p, edges) == expected, ("boundary/random factored", p, edges))
        check(original_signed_counts_factored(p, edges) == expected, ("boundary/random original", p, edges))
        even, odd = formulas_count(p, edges)
        check(even - odd == sum(expected), ("boundary/random CNF", p, edges))
        calls += 2
        for size in range(-1, p + 2):
            counts = formulas_count(p, edges, size)
            check(counts[0] - counts[1] == (expected[size] if 0 <= size <= p else 0), ("boundary/random size", p, edges, size))
            calls += 2
        samples.append({"p": p, "edges": edges, "even": even, "odd": odd, "minimal_counts_by_size": expected})

    graph_count = 0
    graph_calls = 0
    for n in range(5):
        possible = list(combinations(range(n), 2))
        for subset in range(1 << len(possible)):
            graph = [e for i, e in enumerate(possible) if subset & (1 << i)]
            edges = closed_neighborhood_hypergraph(n, graph)
            expected = [0] * (n + 1)
            # Direct graph semantics; no private-neighbor characterization.
            def dominates(selected):
                return all(v in selected or any((u, v) in graph or (v, u) in graph for u in selected) for v in range(n))
            for mask in range(1 << n):
                selected = {v for v in range(n) if mask & (1 << v)}
                if dominates(selected) and all(not dominates(selected - {v}) for v in selected):
                    expected[len(selected)] += 1
            check(brute_minimal_counts(n, edges) == expected, ("graph dual", n, graph))
            even, odd = formulas_count(n, edges)
            check(even - odd == sum(expected), ("graph CNF", n, graph))
            graph_calls += 2
            graph_count += 1

    cover_examples = [(0, []), (0, [(), ()]), (3, [(0, 1), (1, 2), (0, 2)]),
                      (3, [(0,), (0,), (1, 2)]), (3, [(0, 1)])]
    for universe_size, sets in cover_examples:
        p, edges = set_cover_hypergraph(universe_size, sets)
        expected = [0] * (p + 1)
        def covers(chosen):
            return set().union(*(set(sets[i]) for i in chosen)) == set(range(universe_size))
        for mask in range(1 << p):
            chosen = {i for i in range(p) if mask & (1 << i)}
            if covers(chosen) and all(not covers(chosen - {i}) for i in chosen):
                expected[len(chosen)] += 1
        check(brute_minimal_counts(p, edges) == expected, ("set cover", universe_size, sets))
    return {"boundary_and_seeded_random_cases": len(cases), "random_seed": 20261029,
            "actual_dpll_calls": calls + graph_calls, "all_simple_graphs_n_0_through_4": graph_count,
            "set_cover_cases": len(cover_examples), "examples": samples}


def verify_known_skolem_baseline() -> dict:
    instances = 0
    fixed_x_cases = 0
    oracle_calls = 0
    for p in range(3):
        for edges in all_hypergraphs(p):
            totals = [known_skolem_baseline(p, edges, parity) for parity in (0, 1)]
            for formula in totals:
                check(formula.nvars == 2 * p + 3 * len(edges) + max(0, p + 2 * len(edges) - 1), "baseline variable bound")
                check(all(len(c) <= 3 for c in formula.clauses), "baseline clause width")
            even, odd = [count_models(formula) for formula in totals]
            oracle_calls += 2
            check(even - odd == sum(brute_minimal_counts(p, edges)), ("known Skolem baseline total", p, edges))
            for mask in range(1 << p):
                selected = {v for v in range(p) if mask & (1 << v)}
                hits = lambda candidate: all(any(v in candidate for v in edge) for edge in edges)
                expected = int(hits(selected) and all(not hits(selected - {v}) for v in selected))
                counts = []
                for parity in (0, 1):
                    formula = known_skolem_baseline(p, edges, parity)
                    for v in range(p):
                        formula.require(v + 1, v in selected)
                    counts.append(count_models(formula))
                    oracle_calls += 1
                check(counts[0] - counts[1] == expected, ("known Skolem baseline fixed x", p, edges, selected))
                fixed_x_cases += 1
            instances += 1
    check(instances == 22, "Expected 22 p<=2 hypergraphs")
    return {"all_simple_hypergraphs_p_0_through_2": instances,
            "fixed_x_contribution_checks": fixed_x_cases, "actual_dpll_calls": oracle_calls,
            "base_variables": "2p+3q", "total_variables_nonempty": "3p+5q-1",
            "interpretation": "Known negative-weight Skolem method already gives an O(p+q)-variable baseline; this is not a new-main-result claim."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path,
                        default=Path(__file__).resolve().parents[1] / "workspace" / "verification_report.json")
    parser.add_argument("--skip-p4", action="store_true", help="Skip 65,536-hypergraph factored check")
    args = parser.parse_args()
    start = perf_counter()
    report = {"status": "running", "python": sys.version.split()[0], "platform": platform.platform(),
              "command": "python code/verify.py", "oracle": "Exact small-instance cached DPLL; not OpenAI's algorithm",
              "sections": {}}
    tasks = [("gate_and_oracle_checks", verify_gates_and_oracle), ("circuit_checks", verify_circuits),
             ("all_simple_hypergraphs_p_le_3", verify_exhaustive_small)]
    if not args.skip_p4:
        tasks.append(("all_simple_hypergraphs_p_eq_4", verify_exhaustive_four))
    tasks.append(("boundary_random_and_applications", verify_boundary_random_and_applications))
    tasks.append(("known_skolem_prior_art_baseline", verify_known_skolem_baseline))
    for name, task in tasks:
        section_start = perf_counter()
        report["sections"][name] = task()
        report["sections"][name]["elapsed_seconds"] = round(perf_counter() - section_start, 3)
        print(f"PASS {name} ({report['sections'][name]['elapsed_seconds']:.3f}s)", flush=True)
    report["status"] = "passed"
    report["elapsed_seconds"] = round(perf_counter() - start, 3)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    text_path = args.report.with_suffix(".txt")
    lines = ["PASS: linear-variable minimal-transversal reduction", f"Python: {report['python']}",
             "278 simple hypergraphs for p=0,1,2,3: actual even/odd 3-CNF counts, total and every size.",
             "Counts by p: 2, 4, 16, 256; empty edges and empty families included."]
    if not args.skip_p4:
        lines.append("65,536 simple hypergraphs for p=4: both factored signed sums versus independent deletion enumeration; all sizes.")
    lines += ["DPLL cross-checked against brute truth tables on 280 random small CNFs.",
              "XOR, AND, majority truth tables; unique extension and linear counting-circuit bounds checked.",
              "Duplicate edges, isolated vertices, invalid sizes, all 76 simple graphs n<=4, and set-cover cases checked.",
              "Known negative-weight Skolem baseline: all 22 p<=2 hypergraphs, including all 74 fixed-x contributions, checked with actual CNF counts.",
              "The test oracle is exponential and does not implement the OpenAI algorithm.",
              "Finite tests support error detection; the mathematical proof is a separate artifact.",
              f"Elapsed seconds: {report['elapsed_seconds']}"]
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ALL PASSED; saved {args.report} and {text_path}", flush=True)


if __name__ == "__main__":
    main()
