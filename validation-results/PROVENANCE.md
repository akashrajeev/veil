# Check provenance (2026-10-14 IST)

Server code for all "final tree" results: mcp_server.py sha256 357d4c67bb19bccc57b2388dd1ba64dcde408a1d7b9c0e19119ac386cf1895d6 (unchanged since 21:10).
Whole-tree content hash including the judge-script UI: 05f5e70ad9a5689cd6ef02e1690336bbc870b747e812286385fec71d24344b7b (22:22); alexa.html changed once after (22:25 judge-script fix) - UI only, no server/transcript impact.

| result file | check | started | tree |
|---|---|---|---|
| main3-uniform-final-tree.json | mcp_independence_check.py 3 (approvals + length-3 sweep, uniform default) | 22:10:16 | final |
| composition2-uniform-final-tree.json | mcp_independence_check.py composition (up to 2 approved disclosures, uniform default) | 22:23 | final |
| weighted-prior13-final-tree.json | mcp_independence_check.py weighted (length-3, declared prior [1,3]) | 21:28 | final |
| weighted-composition-prior13-final-tree.json | mcp_independence_check.py weighted-composition (up to 2 approvals, prior [1,3]) | 21:41 | final |
| composition3-uniform-tree-2040.json | mcp_independence_check.py composition3 (up to 3 approved disclosures, uniform default) | 20:40 | tree as of 20:40, BEFORE the declared-prior feature existed; uniform-default code paths unchanged since |

verify_all (221 unit one job = 191 non-MCP + 30 MCP; 12 correctness-spike tests as a separate job): passed on the final tree 21:49, and passed again on a clean extract of the loop-12 package 22:07-22:09. Results are recomputed per tree; attach numbers to the tree they ran on.
