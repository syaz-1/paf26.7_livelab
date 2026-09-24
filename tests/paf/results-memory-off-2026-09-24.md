# Agent Factory retest — memory disabled

Run: 24 September 2026. Same published flow and same 21 prompts; each used a fresh conversation. Memory was verified disabled before execution.

## Comparison

| Run | Pass | Partial | Fail |
| --- | ---: | ---: | ---: |
| Baseline: shared memory enabled | 7 | 3 | 11 |
| Retest: memory disabled | 12 | 2 | 7 |

All 21 API requests returned HTTP 200. Grades reflect manual final-answer review, not transport status. This single before/after run shows improved answers but is not a controlled proof that every improvement was caused by disabling memory.

## Remaining problems

1. **Routine/tool confusion:** five answers still refused checks while saying the only available tools were PL/SQL discovery and execution. Those are the interfaces intended to invoke the health functions. This strongly suggests an instruction/tool-use issue remains beyond memory.
2. **Incorrect 48-hour job result:** the agent reported no failures. Independent source and deployed-wrapper checks contradicted it, and the failure timestamp predates the answer. The execution trace was unavailable, so a wrong argument/default window is a hypothesis, not a confirmed cause.
3. **Missing final answer:** the typo-heavy performance request returned the server placeholder rather than diagnostic output.
4. **Incomplete guidance:** the SQL answer omitted truncation information; the negative-limit response omitted the maximum allowed value.

## Per-case comparison

| Case | Baseline | Retest | Finding |
| --- | --- | --- | --- |
| dba-01 | PARTIAL | PASS | Returned identity, service and collection time. |
| dba-02 | FAIL | FAIL | Still claimed overview/session tools unavailable; did not list top 10 sessions. |
| dba-03 | FAIL | PASS | Answered the blocking question with database identity and a collection timestamp. |
| dba-04 | PASS | PASS | Returned ordered tablespace percentages, values, identity and collection time. |
| dba-05 | FAIL | FAIL | Claimed no failed jobs in 48 hours, contradicted by independent SQLcl and wrapper checks; the source failure predates the answer. |
| dba-06 | PARTIAL | PARTIAL | Returned five cumulative SQL entries with time, but still omitted the required truncation notice. |
| dba-07 | FAIL | FAIL | Claimed the overview tool was unavailable despite acknowledging PL/SQL discovery/execution tools. |
| nontechnical-01 | FAIL | FAIL | Refused health checks because it only had discovery/execution tools; failed to use them to invoke the routines. |
| nontechnical-02 | PASS | PASS | Answered the blocking question with timestamp and current-session observations. |
| nontechnical-03 | FAIL | PASS | Reported tablespace usage and explicitly distinguished it from service provisioned storage and OCI utilization. |
| nontechnical-04 | FAIL | FAIL | Refused the job check because it only had PL/SQL discovery/execution tools. |
| nontechnical-05 | FAIL | FAIL | Claimed the SQL workload tool unavailable despite acknowledging PL/SQL execution tools. |
| nontechnical-06 | PASS | PASS | Explained that historical yesterday/today comparison is unsupported. |
| nontechnical-07 | PASS | PASS | Maintained the read-only boundary and offered diagnostic checks. |
| gibberish-01 | PASS | PASS | Asked for a clear database request. |
| gibberish-02 | PASS | PASS | Requested a meaningful message instead of inventing results. |
| gibberish-03 | PASS | PASS | Asked for a valid database-health question. |
| gibberish-04 | FAIL | FAIL | Server returned: The flow finished without a user-facing response. |
| gibberish-05 | FAIL | PASS | Recognized session/locking intent and returned a timestamped session summary. |
| gibberish-06 | FAIL | PARTIAL | Rejected the negative limit, but did not state the documented maximum of 100. |
| gibberish-07 | PARTIAL | PASS | Requested a valid integer time window without claiming the tool unavailable. |

## Next change to test

Clarify in the Agent custom instructions that GET_* names are PL/SQL routines, not separate model tool names. Require the model to use the executor discovery tool, then its execution tool with the qualified routine name and named arguments. For a 48-hour request, pass P_HOURS_BACK=48 explicitly and check that the returned note describes that window. Never declare a function unavailable merely because its name is absent from the model tool list.

No live flow instructions or settings were changed during this retest. Memory remains disabled as set by the user. Stored memories were not deleted.

## Evidence and limitations

- Responses and conversation IDs are private local artifacts in `.local/paf-tests/20260924T005315Z/`; full readable responses are in `answers.md`.
- Verified `enabled=false`; the saved sharing flag remains true but durable memory itself is disabled.
- Published API responses contain final text and room IDs, not tool execution traces. PASS means the observed answer met the rubric; it does not certify every internal tool call.
- Independently checked the disputed failed-job result via the required bundled SQLcl; no database changes were made.
- Median response latency 8.46s; maximum 13.52s.
- Prompt, model and tool-selection configuration were left unchanged by the runner. Database observations can change over time.
