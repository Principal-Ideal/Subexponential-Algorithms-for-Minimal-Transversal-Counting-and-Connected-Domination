# Pointwise cancellation and the compact formula

Let H=(U,E), with indexed edges, p=|U| and q=|E|. Variables x_v encode D, variables r_v encode R, and a_e encode P. Require

- not r_v OR x_v, for every v;
- not a_e OR not x_v OR r_v, for every v in e;
- not a_e OR not x_v OR not x_w, for every unordered distinct pair v,w in e.

There are 2p+q declared variables and p+sum_e |e|+sum_e binom(|e|,2) raw clauses. All clauses have width at most three. For fixed D and R contained in D, a_e=1 is permitted exactly when

    E_e(D,R): |e intersect D| <= 1 and e intersect D is contained in R.

Summing a_e with weight (-1)^a_e gives 1-[E_e(D,R)]. If D misses an edge, E_e is true for all R and that edge makes the product zero. If D is a transversal, E_e holds exactly when e intersect D={v} for some v in R. Thus the product over edges is one exactly for R contained in D minus W(D), where W(D) is the set of private-edge owners. The remaining signed sum is

    sum_{R subset D minus W(D)} (-1)^|R| = [W(D)=D].

By the [private-edge criterion](../004/index.yaml), the right side is precisely the minimal-transversal indicator. This argument is pointwise in D, so cardinality restrictions or selection-variable units preserve it. Repeated edges repeat a zero/one factor and do not affect the conclusion. An empty edge makes the sum zero; an empty edge family has exactly the empty minimal transversal. When p=q=0, the empty assignment contributes one.

This identity is a sum in the integers. It does not say that positive assignments alone are in bijection with minimal transversals. [The XOR bridge](../006/index.yaml) turns the sum into a difference of two ordinary counts.
