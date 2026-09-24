# Phase 1 verification — 2026-09-23

Status: database backend deployed and live SQLcl verification passed.

| Component | Observed result |
| --- | --- |
| SQLcl | Bundled Oracle SQL Developer SQLcl 26.2.1 |
| Target | User-selected demo Autonomous Database, OLTP service |
| Database release | Oracle AI Database 26ai, 23.26.3.3.0 |
| Owner | DB_HEALTH_OWNER; NO AUTHENTICATION; no roles or system privileges |
| Runtime user | DB_HEALTH_AGENT; PASSWORD authentication; OPEN |
| Runtime system grant | CREATE SESSION only |
| Owner object grants | SELECT on five approved SYS monitoring views; no grant option |
| Runtime object grant | EXECUTE on DB_HEALTH_OWNER.DB_HEALTH_API only; no grant option |
| Package | Specification and body VALID; five public AUTHID DEFINER functions |
| SQLcl runtime connection | demo adb sg health agent; no stored password |

Successful checks:

- Actual password login as DB_HEALTH_AGENT; no admin impersonation.
- All five functions returned successful, bounded JSON results with identity and time.
- SQL workload truncation was exercised with a one-row limit.
- Zero, excessive, fractional and null inputs were rejected.
- Direct session, SQL-statistics and Scheduler-history view access was denied.
- Runtime could discover all five functions and CLOB return signatures.
- No create, administration or broad read system privileges were present.
- Storage byte values matched independent blocks-times-block-size queries.
- SQL seconds/executions agreed with live source counters; average units were checked.
- The empty 24-hour failed-job result matched an independent source query.
- Credential directory/file permissions were 0700/0600.
- Python deployment helper passed syntax compilation.

The first non-interactive runtime test hit a SQLcl masked-password-prompt issue.
The helper now passes the password through private SQLcl stdin with history
and echo disabled. The rerun passed. No password is supplied in process arguments.

Not yet verified:

- Agent Factory container network access, private endpoint routing and model configuration.
- PL/SQL Executor discovery and JSON CLOB handling inside Agent Factory itself.
- Natural-language routing, answer accuracy, timeout behavior and trace destinations.
- Controlled fixtures for known blocking sessions and failed jobs, or simulated outages.

No Scheduler jobs, blocking workloads, business tables or corrective database
operations were created for these tests. No Agent Factory flow has been published.

## 2026-09-24: Agent Factory discovery compatibility

The user confirmed the executor dropdown shows the same-schema overview wrapper.
Deployed DB_HEALTH_AGENT.DB_HEALTH_API with all five delegating functions. Runtime
SQLcl checks now call these wrappers and all passed, including USER_PROCEDURES
visibility, parameter limits, caller identity and denied monitoring-view access.
The administrator grant audit and independent measurement checks passed again.
No new privileges were granted. Agent Factory execution of the five tools is
still awaiting the user's flow configuration and chat test.
