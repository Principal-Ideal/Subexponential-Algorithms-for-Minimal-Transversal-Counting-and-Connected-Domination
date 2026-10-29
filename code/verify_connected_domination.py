"""Independent, reproducible checks of signed and unsigned connected domination."""

from __future__ import annotations

import argparse
from itertools import combinations, product
import json
from pathlib import Path
import platform
import random
import sys
from time import perf_counter

from reduction import CNF, count_models
from connected_domination import (brute_cut_polynomial, brute_unsigned_cut_polynomial,
    build_parity_cnf, build_signed_cnf, find_with_weights, randomized_decide,
    signed_polynomial_count, unsigned_polynomial_count)


def check(condition, details):
    if not condition:
        raise AssertionError(details)


def clean(poly):
    return {key: value for key, value in poly.items() if value}


def parity(poly):
    return {key: value % 2 for key, value in poly.items() if value % 2}


def graph_masks(n, edges):
    neighbors = [1 << v for v in range(n)]
    for u, v in edges:
        neighbors[u] |= 1 << v
        neighbors[v] |= 1 << u
    return neighbors


def direct_properties(n, edges, mask):
    """Independent bitset graph oracle: no calls to production graph helpers."""
    neighbors = graph_masks(n, edges)
    undominated = sum(not (mask & neighbors[v]) for v in range(n))
    remaining = mask
    components = 0
    while remaining:
        reached = remaining & -remaining
        while True:
            grown = reached
            for v in range(n):
                if reached & (1 << v):
                    grown |= neighbors[v] & mask
            if grown == reached:
                break
            reached = grown
        remaining &= ~reached
        components += 1
    return undominated, components


def direct_terms(n, edges, root, weights):
    terms = []
    for mask in range(1 << n):
        if not (mask & (1 << root)):
            continue
        undominated, components = direct_properties(n, edges, mask)
        key = (mask.bit_count(), sum(weights[v] for v in range(n) if mask & (1 << v)))
        terms.append((mask, key, 0 if undominated else 1 << (components - 1),
                      1 << (undominated + components - 1), int(not undominated and components == 1)))
    return terms


def aggregate(terms, restrictions):
    signed, unsigned, connected = {}, {}, {}
    for mask, key, sc, uc, cc in terms:
        if any(bool(mask & (1 << v)) != value for v, value in restrictions.items()):
            continue
        for target, value in ((signed, sc), (unsigned, uc), (connected, cc)):
            target[key] = target.get(key, 0) + value
    return clean(signed), clean(unsigned), clean(connected)


def all_graphs(n):
    possible = list(combinations(range(n), 2))
    for mask in range(1 << len(possible)):
        yield [edge for i, edge in enumerate(possible) if mask & (1 << i)]


def verify_polynomial_oracle():
    rng = random.Random(20261029)
    cases = 0
    for n in range(4):
        weights = [i + 2 for i in range(n)]
        for _ in range(60):
            formula = CNF(names=[f"v{i}" for i in range(3 * n)])
            if n:
                for _ in range(rng.randrange(12)):
                    formula.add(*(rng.choice((-1, 1)) * rng.randrange(1, 3 * n + 1)
                                  for _ in range(rng.randrange(4))))
            expected_signed, expected_unsigned = {}, {}
            for bits in product((False, True), repeat=3 * n):
                if not formula.satisfies(dict(enumerate(bits, 1))):
                    continue
                key = (sum(bits[:n]), sum(weights[v] for v in range(n) if bits[v]))
                expected_signed[key] = expected_signed.get(key, 0) + (-1) ** sum(bits[2 * n:])
                expected_unsigned[key] = expected_unsigned.get(key, 0) + 1
            check(signed_polynomial_count(formula, n, weights) == clean(expected_signed), ("signed generic CNF", n, formula.clauses))
            check(unsigned_polynomial_count(formula, n, weights) == clean(expected_unsigned), ("unsigned generic CNF", n, formula.clauses))
            cases += 1

    formula = CNF(names=["x", "c", "a"])
    signed_stats = {}
    check(signed_polynomial_count(formula, 1, [3], signed_stats) == {}, "free signed helper must cancel")
    check(signed_stats["free_signed_zero_prunes"] > 0, "zero-prune exercised")
    check(unsigned_polynomial_count(formula, 1, [3]) == {(0, 0): 4, (1, 3): 4}, "unsigned free variables")
    formula.add(3)
    formula.add(-2)
    check(signed_polynomial_count(formula, 1, [3]) == {(0, 0): -1, (1, 3): -1}, "assigned negative literal sign")

    formula = CNF(names=[f"v{i}" for i in range(6)])
    for clause in ((-5,), (-6,), (1, 3), (2, 4)):
        formula.add(*clause)
    stats = {}
    actual = signed_polynomial_count(formula, 2, [2, 5], stats)
    check(actual == {(0, 0): 1, (1, 2): 2, (1, 5): 2, (2, 7): 4}, "component polynomial product")
    check(stats["component_splits"] > 0, "component decomposition exercised")
    return {"random_CNF_truth_table_comparisons": cases,
            "both_weight_modes_checked": True, "free_negative_zero_and_assigned_sign_checked": True,
            "variable_disjoint_component_product_checked": True}


def verify_exhaustive_graphs():
    graphs = root_cases = partial_cases = full_cases = parity_calls = 0
    histogram = {}
    for n in range(5):
        number = 0
        weights = [2 * v + 1 for v in range(n)]
        for edges in all_graphs(n):
            graphs += 1
            number += 1
            for root in range(n):
                root_cases += 1
                base = build_signed_cnf(n, edges, root)
                check(base.nvars == 3 * n, "3n base variables")
                check(len(base.clauses) == 2 * n + 4 * len(edges) + 2, "exact base clause count")
                check(all(len(c) <= 3 for c in base.clauses), "base width")
                terms = direct_terms(n, edges, root, weights)
                expected_signed, expected_unsigned, expected_connected = aggregate(terms, {})
                check(brute_cut_polynomial(n, edges, root, weights) == expected_signed, "brute signed interface")
                check(brute_unsigned_cut_polynomial(n, edges, root, weights) == expected_unsigned, "brute unsigned interface")
                for pattern in product((None, False, True), repeat=n):
                    restrictions = {v: value for v, value in enumerate(pattern) if value is not None}
                    signed, unsigned, connected = aggregate(terms, restrictions)
                    formula = build_signed_cnf(n, edges, root, restrictions)
                    got_signed = signed_polynomial_count(formula, n, weights)
                    got_unsigned = unsigned_polynomial_count(formula, n, weights)
                    check(got_signed == signed, ("exhaustive signed", n, edges, root, restrictions))
                    check(got_unsigned == unsigned, ("exhaustive unsigned", n, edges, root, restrictions))
                    check(parity(got_signed) == parity(got_unsigned) == parity(connected), ("Cut&Count parity", n, edges, root, restrictions))
                    partial_cases += 1
                    full_cases += len(restrictions) == n
                even = build_parity_cnf(n, edges, root, 0)
                odd = build_parity_cnf(n, edges, root, 1)
                check(even.nvars == odd.nvars == 4 * n - 1, "parity variable count")
                check(count_models(even) - count_models(odd) == sum(expected_signed.values()), "actual even-odd counts")
                check(count_models(base) == sum(expected_unsigned.values()), "actual unsigned model count")
                parity_calls += 3
        histogram[str(n)] = number
        print(f"PASS all n={n} graphs ({number}), all roots and all partial selection assignments", flush=True)
    return {"graphs_by_n": histogram, "total_graphs": graphs, "rooted_graphs": root_cases,
            "partial_selection_assignments_including_full": partial_cases,
            "fully_fixed_selection_assignments": full_cases, "polynomial_DPLL_calls": 2 * partial_cases,
            "ordinary_DPLL_cross_checks": parity_calls}


def verify_five_vertices():
    n = 5
    rng = random.Random(20261029)
    possible = list(combinations(range(n), 2))
    cases = [[], [(i, i + 1) for i in range(4)], [(i, (i + 1) % 5) for i in range(5)],
             [(0, i) for i in range(1, 5)], possible, [(0, 1), (1, 2), (3, 4)]]
    cases += [[edge for edge in possible if rng.randrange(2)] for _ in range(20)]
    checks = 0
    for edges in cases:
        weights = [rng.randint(1, 2 * n) for _ in range(n)]
        for root in range(n):
            restrictions_list = [{}] + [{v: bool(mask & (1 << v)) for v in range(n)} for mask in range(1 << n)]
            terms = direct_terms(n, edges, root, weights)
            for restrictions in restrictions_list:
                signed, unsigned, connected = aggregate(terms, restrictions)
                formula = build_signed_cnf(n, edges, root, restrictions)
                check(signed_polynomial_count(formula, n, weights) == signed, "n=5 signed")
                check(unsigned_polynomial_count(formula, n, weights) == unsigned, "n=5 unsigned")
                check(parity(signed) == parity(unsigned) == parity(connected), "n=5 parity")
                checks += 1
    return {"representative_graphs": 6, "seeded_random_graphs": 20, "seed": 20261029,
            "root_and_selection_cases": checks, "polynomial_DPLL_calls": 2 * checks}


def verify_decision_and_recovery():
    cases = rooted_cases = randomized_cases = randomized_misses = minimum_cases = 0
    for n in range(5):
        # Superincreasing weights make all subsets distinct for a deterministic test.
        weights = [1 << v for v in range(n)]
        for edges in all_graphs(n):
            feasible = [mask for mask in range(1, 1 << n) if direct_properties(n, edges, mask) == (0, 1)]
            for limit in range(n + 1):
                expected = [mask for mask in feasible if mask.bit_count() <= limit]
                for signed in (False, True):
                    found = find_with_weights(n, edges, weights, limit, signed_helpers=signed, minimize=True)
                    check((found is not None) == bool(expected), ("decision unique weights", n, edges, limit))
                    if found:
                        mask = sum(1 << v for v in found["witness"])
                        check(mask in expected, "original-graph witness")
                        check(mask.bit_count() == min(x.bit_count() for x in expected), "minimum under unique weights")
                    cases += 1
            for root in range(n):
                expected = [mask for mask in feasible if mask & (1 << root)]
                found = find_with_weights(n, edges, weights, n, root, minimize=True)
                check((found is not None) == bool(expected), "rooted unique-weight decision")
                if found:
                    check(sum(1 << v for v in found["witness"]) in expected, "rooted witness")
                rooted_cases += 1
            result = randomized_decide(n, edges, n, trials=3, seed=20261029)
            randomized_cases += 1
            if result["status"] == "found":
                check(sum(1 << v for v in result["witness"]) in feasible, "random decision false positive")
            elif feasible:
                randomized_misses += 1
            optimized = randomized_decide(n, edges, n, trials=3, seed=20261029, minimize=True)
            minimum_cases += 1
            if optimized["status"] == "found":
                check(sum(1 << v for v in optimized["witness"]) in feasible, "random minimum feasibility")
                check(optimized["optimality_failure_bound"] == "2^-3", "probabilistic optimality label")
                check(optimized["trials_completed"] == 3, "optimization uses all trials")
    # Regression: deleting vertex 2 would make {0} dominate the remaining path,
    # but restrictions must keep vertex 2 in the ORIGINAL domination obligations.
    edges = [(0, 1), (1, 2)]
    restrictions = {0: True, 1: False, 2: False}
    formula = build_signed_cnf(3, edges, 0, restrictions)
    check(signed_polynomial_count(formula, 3, [1, 2, 4]) == {}, "original-graph restriction regression signed")
    check(unsigned_polynomial_count(formula, 3, [1, 2, 4]) == {(1, 1): 2}, "original-graph restriction regression unsigned")
    return {"all_graph_size_limits_both_modes_unique_weights": cases,
            "rooted_unique_weight_cases": rooted_cases, "randomized_decision_cases": randomized_cases,
            "observed_randomized_false_negatives": randomized_misses,
            "randomized_minimization_cases": minimum_cases,
            "original_graph_restriction_regression": "passed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path,
                        default=Path(__file__).resolve().parents[1] / "workspace" / "connected_domination_report.json")
    args = parser.parse_args()
    start = perf_counter()
    report = {"status": "running", "python": sys.version.split()[0], "platform": platform.platform(),
              "command": "python code/verify_connected_domination.py", "seed": 20261029,
              "oracle_scope": "Exponential exact polynomial DPLL; no implementation or runtime verification of OpenAI's algorithm",
              "empty_graph_convention": "Connected dominating sets must be nonempty",
              "sections": {}}
    for name, task in (("signed_unsigned_oracle", verify_polynomial_oracle),
                       ("all_graphs_n_le_4", verify_exhaustive_graphs),
                       ("representative_random_n_5", verify_five_vertices),
                       ("decision_optimization_witness", verify_decision_and_recovery)):
        then = perf_counter()
        report["sections"][name] = task()
        report["sections"][name]["elapsed_seconds"] = round(perf_counter() - then, 3)
        print(f"PASS {name}: {report['sections'][name]['elapsed_seconds']:.3f}s", flush=True)
    report["status"] = "passed"
    report["elapsed_seconds"] = round(perf_counter() - start, 3)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = ["PASS: connected domination signed/unsigned polynomial encodings",
               "All 76 simple graphs n=0..4; all 285 valid rooted graphs.",
               "All 21,423 partial selection assignments, including 4,306 fully fixed selections; both polynomial identities and mod-2 equality checked.",
               "26 representative/seeded random five-vertex graphs, all roots and all fully fixed selections checked.",
               "Generic signed and unsigned DPLL cross-checked with brute truth tables on 240 CNFs.",
               "Free signed variables, negative forced weights, and component products checked.",
               "Decision, probabilistic minimization labels, and independently verified witnesses checked.",
               "Selection restrictions retain every vertex and edge of the original graph.",
               "This exponential validation oracle does not implement the OpenAI algorithm.",
               "A not_detected result is not a general certificate of nonexistence; minimum-size optimality is probabilistic.",
               f"Elapsed seconds: {report['elapsed_seconds']}"]
    args.report.with_suffix(".txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"ALL PASSED: {args.report}", flush=True)


if __name__ == "__main__":
    main()
