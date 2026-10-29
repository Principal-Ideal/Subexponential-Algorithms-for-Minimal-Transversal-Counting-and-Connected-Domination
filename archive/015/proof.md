# Deterministic search from one odd coefficient

Fix the graph, root r, integer vertex weights, and a known odd coefficient indexed by (k,W). Also retain any existing selection restrictions. For each not-yet-fixed selection bit x_v, let C_0 and C_1 be the integer coefficient after adjoining respectively not x_v and x_v as a unit. Satisfying assignments partition by x_v, including all auxiliary assignments and their weights. Therefore C=C_0+C_1. If C is odd, exactly one child coefficient is odd. Query C_0, retain that child if odd, and otherwise retain the x_v=1 child.

After at most n such queries, all selection bits are fixed to D and the retained coefficient is still odd. The [parity fibre identity](../013/index.yaml) says D contains r, dominates the original graph, is connected, and has size k and total weight W. Independent direct checking of those properties provides a practical final witness check. No new randomness or isolated-weight promise is needed once the first odd coefficient is known.

All calls use the unchanged original graph and units on x only. Removing an excluded vertex from the graph would erase its domination requirement and break the partition argument. This proof gives the number of coefficient-oracle queries; the [conditional unary bridge](../011/index.yaml) supplies their asymptotic cost when that imported route is assumed.
