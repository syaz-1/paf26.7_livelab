# Select AI full-suite retest — enforcement disabled

Run: 24 September 2026, 04:21–04:24 UTC. Tested the existing direct Chat Input → Select AI Run SQL → Chat Output flow through its integration endpoint. Same 21 prompts as the original suite, across DBA, nontechnical and gibberish categories. No prompt, flow, grant or profile changes during the run.

Memory was verified disabled. Profile enforcement was verified false and max_tokens=4096. Every request used a distinct room. GET_* tool names in the old test file do not apply to this flow; grades evaluate the original user-facing behaviors, not literal function calls.

## Results

- 21/21 HTTP 200 responses.
- Zero database-error messages, object-list rejections or no-user-facing-response placeholders.
- 6 responses returned an empty list, without explanation.
- Full behavioral rubric: 1 PASS, 11 PARTIAL, 9 FAIL.

These grades are stricter than SQL execution success. A direct NL2SQL node returns query results but does not reliably provide the clarifications, multi-step investigation and explanations expected of the original conversational agent. Prior scores used different flow designs, so this is not a controlled numerical comparison between equivalent agents.

## Material findings

1. Storage and 48-hour job checks execute with enforcement disabled; earlier ORA-20004 failures did not recur.
2. The ordered-tablespaces request returned name order rather than usage order.
3. An overnight-report question returned older failures rather than a recent diagnostic scope.
4. A yesterday-versus-today question produced a definitive NO without demonstrated historical evidence. This is not a supported comparison using the configured current/cumulative monitoring views. Cached-SQL lookup did not recover the actual comparison query, so its precise construction remains unverified.
5. Nonsense, negative limits and invalid hours did not elicit clarification.
6. Empty result sets were exposed without explanation.

## Per-case review

| Case | Verdict | Finding |
|---|---|---|
| dba-01 | PASS | Returned database identity and service. |
| dba-02 | PARTIAL | Returned sessions; omitted collection time/truncation context. Exact generated limit was not captured. |
| dba-03 | PARTIAL | Returned [] without explaining no matching blockers or snapshot scope; internal SQL not captured. |
| dba-04 | FAIL | Returned tablespace percentages ordered by name rather than usage; omitted service-capacity distinction. |
| dba-05 | PARTIAL | Returned the independently verified failure within 48 hours; omitted retained-log coverage caveat. |
| dba-06 | PARTIAL | Returned five SQL entries in decreasing elapsed time; did not explain cumulative scope or truncation. |
| dba-07 | PARTIAL | Returned several aggregate health metrics but omitted workload and interpretation. Failed-job count matches all retained failures; time scope was not stated. |
| nontechnical-01 | FAIL | Returned only []; no usable slowdown investigation or explanation. |
| nontechnical-02 | PARTIAL | Returned [] without explaining blocking evidence or snapshot limits. |
| nontechnical-03 | PARTIAL | Returned usage percentages without explaining service storage limits. |
| nontechnical-04 | FAIL | Returned 50 older failures from previous weeks for an overnight-report question; no recent-window explanation or clarification. |
| nontechnical-05 | PARTIAL | Returned SQL counters but no session findings or explanation of cumulative scope. |
| nontechnical-06 | FAIL | Returned WAS_YESTERDAY_SLOWER=NO and a today-labelled average without historical evidence. Available monitoring views cannot establish that comparison. |
| nontechnical-07 | PARTIAL | Returned diagnostic SQL statistics and made no fix claim; did not explain the read-only boundary. No independent audit of mutations was performed. |
| gibberish-01 | FAIL | Returned database overview for nonsense instead of clarification. |
| gibberish-02 | FAIL | Returned database overview for punctuation instead of clarification. |
| gibberish-03 | FAIL | Returned [] instead of clarification. |
| gibberish-04 | PARTIAL | Recognized slowdown intent and returned SQL counters, but no session findings or explanatory scope. |
| gibberish-05 | PARTIAL | Returned [] without explaining possible locking or no matches. |
| gibberish-06 | FAIL | Returned sessions without rejecting or explaining the negative row limit. |
| gibberish-07 | FAIL | Returned [] rather than requesting a valid time window. |

## Verification and limits

A fixed independent SQLcl query confirmed the 48-hour failed-job result and that the overall-health failed-job aggregate matched all retained failures, not a stated recent window. Dynamic session/storage/workload values change over time and were not checked for exact equality against later snapshots. Integration responses do not contain full SQL execution traces. Output rows alone cannot certify correct filtering, all required source queries, or absence of every possible side effect.

Live responses and supporting checks remain private in `.local/paf-tests/select-ai-20260924T042155Z/`; API keys are not stored. `scripts/test_select_ai.py` reproduces the suite with an API key supplied via stdin. No email, messaging or external publication occurred.

## Recommended next step

Use the direct Select AI flow for explicit query tests. For the original conversational assistant behavior, add an Agent layer that clarifies invalid requests, rejects unsupported historical comparisons, completes required checks and explains result scope. This is a proposed next change, not completed work. The user's chosen enforcement setting remains false; the object list is no longer an enforced access boundary.
