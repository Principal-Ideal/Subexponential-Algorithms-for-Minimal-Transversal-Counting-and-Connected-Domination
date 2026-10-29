# Result catalog

See [archive conventions](README.md) for status and dependency meanings. All algorithmic bounds here that invoke OpenAI are conditional imports or conditional transfers.

| ID | Result | Status | Direct prerequisites |
| --- | --- | --- | --- |
| [001](001/index.yaml) | [OpenAI set-preserving compression and ordinary counting](001/artifacts.md) | imported | None |
| [002](002/index.yaml) | [OpenAI algebra-valued product-sum evaluator](002/artifacts.md) | imported | None |
| [003](003/index.yaml) | [Isolation with bounded independent integer weights](003/artifacts.md) | imported | None |
| [004](004/index.yaml) | [Private-edge criterion for minimal transversals](004/artifacts.md) | established | None |
| [005](005/index.yaml) | [Compact pointwise cancellation for minimal transversals](005/artifacts.md) | established | [004](004/index.yaml) |
| [006](006/index.yaml) | [Unique-extension XOR difference-of-counts bridge](006/artifacts.md) | established | None |
| [007](007/index.yaml) | [Linear-size unique-extension cardinality circuit](007/artifacts.md) | established | None |
| [008](008/index.yaml) | [Minimal domination and set-cover correspondences](008/artifacts.md) | established | None |
| [009](009/index.yaml) | [Conditional exact minimal-solution algorithms](009/artifacts.md) | conditional | [001](001/index.yaml), [005](005/index.yaml), [006](006/index.yaml), [007](007/index.yaml), [008](008/index.yaml) |
| [010](010/index.yaml) | [Prior negative-weight transformations recover the compact gadget](010/artifacts.md) | established | [005](005/index.yaml) |
| [011](011/index.yaml) | [Conditional unary signed monomial-weight bridge](011/artifacts.md) | conditional | [001](001/index.yaml), [002](002/index.yaml) |
| [012](012/index.yaml) | [Three-variable-per-vertex connected-domination fibres](012/artifacts.md) | established | None |
| [013](013/index.yaml) | [Connected-domination parity generating polynomial](013/artifacts.md) | established | [012](012/index.yaml) |
| [014](014/index.yaml) | [Conditional randomized connected-domination decision](014/artifacts.md) | conditional | [003](003/index.yaml), [011](011/index.yaml), [013](013/index.yaml) |
| [015](015/index.yaml) | [Parity-preserving witness self-reduction](015/artifacts.md) | established | [013](013/index.yaml) |
| [016](016/index.yaml) | [Conditional probabilistic minimum connected domination](016/artifacts.md) | conditional | [003](003/index.yaml), [011](011/index.yaml), [013](013/index.yaml), [015](015/index.yaml) |
| [017](017/index.yaml) | [Fixed deletion-evidence family compiler](017/artifacts.md) | established | [006](006/index.yaml) |
| [018](018/index.yaml) | [SCC-subset deletion family is complete](018/artifacts.md) | established | [017](017/index.yaml) |
| [019](019/index.yaml) | [Exponential deletion families despite directed FVS one](019/artifacts.md) | established | [017](017/index.yaml) |
| [020](020/index.yaml) | [Short-edge direct and long-edge cancellation hybrid](020/artifacts.md) | established | [005](005/index.yaml), [006](006/index.yaml) |

Only results 001–020 are included. All required and motivation references remain inside this publication subset. Local proof methods and imported algorithm assumptions are described in the [archive conventions](README.md).
