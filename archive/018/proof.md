# Completeness of all nonempty SCC subsets

For every clause of F, add an arc u to v for every negative literal not x_u and positive literal x_v in that clause. Let C range over the strongly connected components of this digraph. Take as the deletion family every nonempty subset of every C. The count is exactly

    ell = sum_C (2^{|C|}-1).

If every SCC has size at most b, then ell <= n 2^b. Isolated variables and clauses containing only one polarity cause no difficulty.

To prove completeness, let D be a nonminimal model and D' a strict submodel. Put S=D minus D', a nonempty set. In the condensation DAG, consider the SCCs intersecting S and choose one C with no incoming edge from another such SCC; such a source exists because the induced graph is acyclic. Let B=S intersect C, a nonempty subset in the proposed family.

Suppose for contradiction that D minus B violates some clause K. Since D satisfies K, a literal that becomes false upon deleting B must be a positive x_v with v in B. Negative literals only become true, so no other kind of literal can explain the loss. Since D' satisfies K and D' is contained in D minus B, some literal becoming true between D minus B and D' must be negative not x_u with u in S minus B. Therefore K gives an arc u to v. The SCC of u intersects S and is different from C, contradicting the choice of C as a source among the S-intersecting SCCs. Thus D minus B is a model and the family is complete.

The direction is source, not sink, for the stated negative-to-positive orientation. Applying [017](../017/proof.md) gives n+ell+max(0,ell-1) variables and width at most max(k+1,3), with its corresponding raw clause bound. For constant b the family is linear in n. If b grows, the explicit factor 2^b must be retained; no generic small directed-FVS substitute follows, as [019](../019/proof.md) demonstrates.
