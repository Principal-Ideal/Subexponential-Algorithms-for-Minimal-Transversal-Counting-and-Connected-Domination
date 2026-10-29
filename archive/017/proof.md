# Fixed deletion-evidence compiler

Let F be a CNF on the declared vertex set V of n variables. Identify a model with D subset V. A fixed family B_1,...,B_ell of nonempty subsets is complete when every nonminimal model D has some B_i subset D with D minus B_i also a model. Conversely, any such deletion certifies nonminimality. The family depends on F, not on the subsequently chosen model D.

For each B_i introduce z_i with sign (-1)^z_i. Keep F(x), and add the implication

    z_i implies ((AND_{v in B_i} x_v) AND F(x with every x_v, v in B_i, replaced by 0)).

For each v in B_i, the first part uses not z_i OR x_v. For each original clause C, evaluate its literals from B_i at zero and guard the remaining clause by not z_i. A true substituted clause adds nothing; a false one adds the unit not z_i. If the maximum original width is k, guarded clauses have width at most k+1. All substituted formulas share the original x variables: no copy of x is introduced.

For fixed model D, let e_i(D) indicate that B_i is a legal deletion. The signed sum over z is

    product_i (1-e_i(D)).

Completeness makes this product the indicator that D is minimal. For nonmodels, the retained F makes every contribution zero. Thus the base signed CNF uses n+ell variables and at most

    m + sum_i (|B_i|+m)

raw clauses before simplification. [The XOR bridge](../006/index.yaml) adds max(0,ell-1) unique-extension variables and four clauses per XOR, followed by a parity unit when ell>0. The final width is at most max(k+1,3). For ell=0, completeness says all models of F are already minimal; take the even formula F and the odd formula F plus an empty clause.

The assumption on the deletion family is essential. Neither unit deletion nor deleting whole SCCs is universally sufficient. [018](../018/proof.md) supplies a complete family from all nonempty SCC subsets. [019](../019/proof.md) proves that even directed feedback vertex number one cannot guarantee a small family of this unrestricted fixed-family kind.
