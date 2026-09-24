# Storage SQL isolation tests — 2026-09-24

Tested MONITOR_STORAGE_USAGE using the authorized integration endpoint and existing enforced profile. No configuration or privilege changes.

| Query shape | Direct SQLcl as DB_HEALTH_AGENT | Select AI |
|---|---|---|
| COUNT(*) | PASS | ORA-20004 |
| Tablespace names only | PASS | ORA-20004 |
| Names and used percentage | PASS | ORA-20004 |
| Names, used bytes, capacity bytes | PASS | ORA-20004 |
| Filter to DATA tablespace | PASS | ORA-20004 |
| SUM(used_bytes) | PASS | ORA-20004 |
| Order by used percentage | PASS | ORA-20004 in earlier cross-view test |

Direct SQL checks parsed, opened and fetched once from each fixed cursor; values were withheld. SQLcl queries are saved in storage-query-tests.sql. Select AI issued fresh queries for six prompts, returning an error message inside HTTP 200 each time. Error messages include the generated SQL, each referencing only the approved DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE view. Generated SQL variants differ cosmetically in aliases and identifier quoting; the filter variant uses UPPER on both operands.

Even COUNT(*) and a single-column projection fail under Select AI enforcement but work directly. This rules out the explicit date filter, outer ordering, byte calculations in the SELECT list, and missing ordinary SELECT privileges as necessary causes of this storage failure. The view still contains its internal join and underlying dictionary dependencies in all tests. These tests do not isolate which internal dependency or enforcement rule causes rejection.

Private evidence: .local/select-ai-error/storage-tests.json and storage-direct-sql.txt. No API keys or live storage values are included here.
