# Select AI object-list validation investigation — 2026-09-24

## Confirmed

- The saved monitoring flow uses Run SQL, the expected ADB connection and profile DB_HEALTH_AGENT.
- The profile lists all five intended DB_HEALTH_AGENT monitoring views with enforcement=true and object-list mode=all.
- Direct SQL as DB_HEALTH_AGENT works for every wrapper, including the exact job query supplied by the user and seven storage query shapes.
- Under Select AI enforcement, database overview, sessions and SQL workload return results. Storage and job history reject even COUNT(*) with ORA-20004.
- Multiple storage errors contain the generated query. They reference only the approved MONITOR_STORAGE_USAGE view, demonstrating an object-list rejection despite the expected top-level object reference.
- Storage still fails when the generated SQL visibly preserves a NO_MERGE hint. A corresponding job prompt also fails, but its error does not expose the generated SQL, so hint retention is unverified there.

## Dependency comparison

| Wrapper | Dependencies | Select AI result |
|---|---|---|
| MONITOR_DATABASE_OVERVIEW | SYS.DUAL | Works |
| MONITOR_SESSIONS | SYS.GV_$SESSION -> SYS.GV$SESSION | Works |
| MONITOR_SQL_WORKLOAD | SYS.GV_$SQLSTATS -> SYS.GV$SQLSTATS | Works |
| MONITOR_STORAGE_USAGE | SYS.DBA_TABLESPACES and SYS.DBA_TABLESPACE_USAGE_METRICS | Fails |
| MONITOR_JOB_RUNS | SYS.DBA_SCHEDULER_JOB_RUN_DETAILS and SYS.DBMS_SCHEDULER | Fails |

DBA_TABLESPACES depends on internal SYS tables including TS$, IMSVCTS$ and X$KCFISTSA. DBA_TABLESPACE_USAGE_METRICS depends on separate data/temp/undo metrics views. Scheduler run details depend on internal SCHEDULER$_* tables and DBMS_SCHEDULER.

This supports a dictionary-view validation compatibility hypothesis, not a proven rule that underlying objects must be added to the profile. No extra SYS objects were allowlisted or granted.

## Independent SQL expansion diagnostic

DBMS_UTILITY.EXPAND_SQL_TEXT results:

- Overview: succeeds.
- Sessions, SQL workload and storage: ORA-24256 wrapping ORA-28113 (VPD predicate error).
- Job runs: ORA-24256 wrapping ORA-01039 (insufficient privileges on underlying view objects).

These are diagnostic expansion failures, not normal query failures. Since sessions and workload still work in Select AI, expansion errors alone do not explain the Select AI rejection. It would be incorrect to claim these errors prove a missing grant or to grant internal dictionary table access to resolve them.

## Conclusion and limits

The reproducible failure is localized to object-list validation of the storage/job wrappers in this environment. Query syntax, ordinary view SELECT access, the 48-hour predicate, sort order and wrong configured profile do not explain the observed storage cases. The exact internal validation behavior remains unconfirmed. Only the DBMS_CLOUD_AI package specification is exposed through ALL_SOURCE to the runtime user; no supported standalone validator was identified there. Public documentation establishes object-list enforcement semantics but does not explain this specific rejection.

No database objects, grants, production profile attributes or flow settings were changed during this investigation. All model tests used the user-authorized integration endpoint with enforcement enabled. API keys were not saved in artifacts.

## Next controlled investigation / workaround

Prepare an isolated minimal reproduction for Oracle support comparing an ordinary read-only query over the wrapper, SHOWSQL, and RUNSQL with enforcement enabled. Include cloud package build identifier DBMS_CLOUD$PDBCS_260904_0, exact profile object list, wrapper DDL, generated SQL and failure correlation IDs. Avoid exposing credentials or live results.

If a practical workaround is needed first, test an explicitly approved snapshot-table design for storage and job history in an isolated profile. Snapshot tables remove live dictionary dependencies from model-facing SQL but add refresh scheduling and freshness semantics. This is a proposed experiment, not a validated fix. Existing fixed-query health functions remain a working live-query path outside Select AI.

## Private evidence

- .local/select-ai-error/storage-tests.json
- .local/select-ai-error/storage-direct-sql.txt
- .local/select-ai-error/cross-view-tests.json
- .local/select-ai-error/expansion-tests.txt
- .local/select-ai-error/no-merge-tests.json

Storage NO_MERGE failure reference: 4feea49d-c542-4580-ba74-f8f221f50d1e.
Job NO_MERGE prompt failure reference: 38d33ff9-d47d-4dab-a918-52b3bd854ba0.

## Direct SQLcl Select AI reproduction

After explicit user approval for the configured OCI model destination and schema-metadata payload, ran as DB_HEALTH_AGENT:

```sql
execute DBMS_CLOUD_AI.SET_PROFILE('DB_HEALTH_AGENT');
SELECT AI RUNSQL show storage usage;
```

Result: reproduced ORA-20004 in the RESPONSE text. The returned generated SQL selects TABLESPACE_NAME, COLLECTED_AT_UTC, CAPACITY_BYTES, USED_BYTES and USED_PERCENT solely from DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE. Object-list enforcement remained enabled; no persistent profile attributes changed.

SQLcl process exit code was 0 because the failure was returned as response text; this is a failed Select AI test, not successful query execution. This reproduction bypasses Agent Factory and establishes that its UI/integration endpoint is not required for the failure. The remaining issue is in the database-side Select AI validation/execution path. Exact internal cause remains unconfirmed.

Private output: .local/select-ai-error/sqlcl-select-ai-storage.txt.

## User-authorized enforcement-off test

The user explicitly requested disabling enforce_object_list. SQLcl verified the stored attribute was true, set it to false with DBMS_CLOUD_AI.SET_ATTRIBUTE, and verified false. The object list and database grants were not changed.

Fresh integration chats then succeeded for both previously failing prompts:

- Show storage usage: returned six tablespace rows.
- Show failed job runs in the last 48 hours: returned a failed Scheduler run.

This confirms disabling the enforcement setting resolves the two reproduced failures in this test. It isolates the failing behavior to the enforced path but does not identify the validator's exact internal defect. Model-generated SQL can vary across calls. Enforcement remains false at the user's request. The object list continues to provide metadata context, while actual database grants govern access; it is no longer an enforced object allowlist.

Private evidence: .local/select-ai-error/enforcement-off-tests.json. No API key was saved.
