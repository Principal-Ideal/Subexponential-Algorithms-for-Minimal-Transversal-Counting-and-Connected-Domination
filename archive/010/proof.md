# Recovery from the prior relaxed Tseitin transformation

The source and its literal-weight convention are recorded in [external sources](../shared/external-sources.md#negative-weights). The published transformation replaces a subformula phi by Z and appends

    Z OR not phi;   R OR Z;   R OR not phi,

with weights +1 on both Z literals and on R=true, and -1 on R=false.

To enforce not E, put phi=not E and pin its replacement Z=true. The first two clauses become tautologies and the third becomes R OR E. Rename a=not R. The only remaining relation is a implies E, and the weights are a=false: +1, a=true: -1. Consequently, for every assignment of the original variables,

    sum_{a satisfying (a implies E)} (-1)^a = 1 - [E].

This identity also directly proves the specialization, independently of relying on the general transformation's theorem. If E is a conjunction of clauses E_j, the implication is the conjunction of not a OR E_j; no variable copies are needed.

Now use [005](../005/proof.md). Its exceptional-edge predicate is

    E_e(D,R) = (|e intersect D|<=1) AND (e intersect D subset R).

The first condition is a conjunction of pair clauses not x_v OR not x_w. The second is a conjunction of not x_v OR r_v. Applying the specialized relaxed transformation to the required factor 1-[E_e] gives exactly the two a_e-guarded clause families in the compact formula. Keeping r_v implies x_v and its negative r_v weight gives the same 2p+q base variables and the same signed pointwise sum.

This shows recovery of this compact construction by an old negative-weight rule and elementary simplification. It does not claim that a particular historical software compiler automatically finds the simplification. The saved [baseline code](../../code/prior_art_baseline.py) uses a different, unoptimized instantiation with 2p+3q base variables. Beating that count is not evidence of beating optimized relaxed Tseitin methods, and no novel negative-weight principle or priority claim follows.
