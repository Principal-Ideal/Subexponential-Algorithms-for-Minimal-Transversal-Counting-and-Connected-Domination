# A bidirected star forces exponentially many deletion sets

Fix t>=1 and use variables c,a_1,b_1,...,a_t,b_t. Define the 3-CNF

    F_t = AND_{i=1}^t [
        (not c OR a_i OR b_i)
        AND (not a_i OR c)
        AND (not b_i OR c)
    ].

In the negative-to-positive dependency graph, the first clause gives arcs c to a_i and c to b_i, and the two binary clauses give the reverse arcs. There are no other arcs. Thus it is the bidirected star centered at c. Deleting c leaves an edgeless graph, so the directed feedback vertex number is at most one; at least one directed 2-cycle exists for t>=1, so the number is exactly one. All variables lie in one SCC.

For each sigma choosing one element of each pair {a_i,b_i}, define

    D_sigma = {c} union {the chosen variable in each pair}.

Every D_sigma is a model: each first clause has its chosen positive literal true, and c satisfies the two implications. The empty set is also a model because all negative literals are then true.

Let D' be any strict submodel of D_sigma. If c is in D', each first clause requires at least one variable from its pair. Only the originally chosen variable is available in D_sigma, so every chosen variable must remain. This forces D'=D_sigma, a contradiction. Hence c is absent from D'. The binary clauses then force all a_i and b_i false, so D' is empty. Therefore empty is the unique strict submodel of D_sigma.

Consider a fixed complete deletion-evidence family as in [017](../017/proof.md). Since D_sigma is nonminimal, some nonempty member B must be contained in D_sigma with D_sigma minus B a model. By the preceding paragraph that remaining model can only be empty, forcing B=D_sigma. All 2^t choices produce different D_sigma. Therefore every complete family has at least 2^t members, despite directed feedback vertex number one and fixed clause width three.

Singleton deletions already fail for these models, since each has t+1>=2 vertices. The stronger lower bound rules out a polynomial-size *fixed deletion family* guaranteed solely by bounded directed FVS. It does not rule out adaptive evidence, different encodings, or unrelated minimal-model algorithms. The proof is universal and needs no computational extrapolation.
