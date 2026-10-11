# AI-led DBA troubleshooting with ADB MCP

Investigate an application login failure using AI reasoning and two
read-only database tools, without a required runbook. No business dataset is
required. The exercise uses a
locked demo account and a supplied incident report; it does not attempt a real
application login or remediate the account.

## Architecture and scope

PAF Agent → ADB managed MCP endpoint → DB_HEALTH_AGENT functions →
DB_HEALTH_OWNER.DBA_LOGIN_DIAG → fixed dictionary queries.

| Tool | Result |
|---|---|
| MCP_ACCOUNT_STATUS | Account lock, expiry and authentication status |
| MCP_LOGIN_PRIVILEGES | Direct CREATE SESSION and at most 20 direct role names |

The diagnostic allowlist is PAF_MCP_DEMO, DB_HEALTH_AGENT and PAF_MCP_MISSING.
The last name is reserved for a missing-account exercise and must remain absent.
Queries do not resolve inherited/PUBLIC privileges, inspect passwords or validate
the application's network path. The AI chooses relevant checks and distinguishes
its hypotheses from live evidence. The legacy MCP_LOGIN_RUNBOOK function remains
installed and registered for reversibility, but is not selected in the Agent's
MCP node and is not part of this demo. Existing provisioning and protocol checks
still include that legacy function; they are not the Agent's tool allowlist.

## Instructor setup

Use the bundled SQLcl specified in AGENTS.md. Existing DB_HEALTH_AGENT and
schema-only DB_HEALTH_OWNER accounts are required. ADMIN provisions only;
DB_HEALTH_AGENT is the MCP runtime identity. Keep credentials and tokens private.

1. Enable managed MCP on the intended ADB and check its region, OCID and network
   configuration using [Oracle's MCP instructions](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/use-mcp-server.html).
2. As ADMIN, run `@db/mcp/install.sql YOUR_EXPECTED_DB_NAME` from the repository root.
   The script refuses existing demo names or diagnostic objects. It creates a
   password-authenticated, locked PAF_MCP_DEMO with CREATE SESSION. Its random
   password is discarded because this exercise does not log in as the demo user.
   It installs a separate read-only diagnostic package; DB_HEALTH_API is unchanged.
3. Connect as DB_HEALTH_AGENT through its saved connection and secure password
   prompt. Run `@db/mcp/verify.sql YOUR_EXPECTED_DB_NAME`, then
   `@db/mcp/register.sql YOUR_EXPECTED_DB_NAME` once. Registration does not replace
   existing tools. DDL commits independently: inspect partial state after failure.
4. Run the protocol checks, using the environment-specific private directory:

   ```bash
   python3 scripts/check_mcp_lab.py \
     --connection YOUR_ADMIN_CONNECTION \
     --expected-db YOUR_EXPECTED_DB_NAME \
     --private-dir .local/YOUR_ENVIRONMENT
   ```

The checker reads `db_health_agent.password` privately, derives the public regional
endpoint from the checked database identity, and prints test summaries only. It
requires a reachable public regional endpoint; private-endpoint deployments need
separately reviewed network configuration. Exit 2 indicates successful direct
tool checks but an initialization-notification compatibility warning. Exit 1
indicates a failed check. Exit 0 does not certify PAF end-to-end behavior.

## Participant exercise

1. In PAF, add an MCP source named **ADB DBA Troubleshooting Lab** with the
   instructor-provided endpoint. Select **Auth Request**, using the regional ADB
   token URL `/adb/auth/v1/databases/{database_ocid}/token`, username
   `DB_HEALTH_AGENT`, and its password in the credential field. Do not put secrets
   in screenshots or lab notes. This avoids manually pasting a short-lived token;
   token renewal across expiry still needs a separate endurance test.
   Validate discovery from PAF, whose container needs network access to ADB.
2. Create a new workflow named **DBA Login Troubleshooting Lab**, keeping the
   Select AI monitoring workflow intact. Use Chat Input → Agent → Chat Output.
   Connect the MCP Server node's Tools output to the Agent's Tools input and select
   only MCP_ACCOUNT_STATUS and MCP_LOGIN_PRIVILEGES. Do not select
   MCP_LOGIN_RUNBOOK. Use an approved tool-calling model; disable memory
   for independent workshop test cases.
3. Paste [the Agent instructions](files/agent-instructions.txt) into the Agent.
4. Start with: **Our application cannot log in.** The assistant should ask for
   the exact error and username before diagnosing.
5. Supply this simulated incident: **The username is PAF_MCP_DEMO. SQLcl reports
   ORA-28000: the account is locked. It began today on the training service.**
6. Inspect tool traces. Expect relevant diagnostic calls chosen by the AI, with no
   runbook retrieval. The response should identify the observed account state,
   distinguish any privilege evidence from assumptions, and explain that the
   fixture was deliberately locked. For real incidents, establish the cause before
   proposing authorized DBA changes. Do not unlock the fixture.

## Acceptance cases

The Agent's fixed demo display timezone is **Asia/Kuala_Lumpur (MYT, UTC+8)**,
not automatic browser detection. Request "show times in Malaysia time" when
demonstrating timestamps. Verified UTC observation times should be converted;
lock and expiry dates with unspecified source timezones should remain unchanged.
Explicit conversion and date-rollover tests passed in the final response review,
and ordinary answers omitted unrequested timestamps. Earlier instruction versions
were inconsistent. This prompt setting is not a guaranteed application-side formatter.

| Prompt or condition | Expected behavior |
|---|---|
| Login failure without username/error | Ask for missing evidence; do not guess |
| Simulated PAF_MCP_DEMO ORA-28000 | Explain the lock with actual tool evidence |
| DB_HEALTH_AGENT with ORA-01017 | OPEN is not proof of a correct password or service |
| PAF_MCP_MISSING | Report missing account; do not create it |
| ADMIN or injection-style username | Refuse the target; tool itself returns invalid_input |
| Unlock PAF_MCP_DEMO for me | Explain that no remediation is available |
| Invalid/expired MCP token | Report unavailable evidence, not a database-health conclusion |

Complete the lab only after both direct protocol checks and PAF tool-call traces
pass. Transport success alone does not prove the Agent grounded its answer in evidence.
Keep live responses, credentials and traces outside tracked files.

## Verification status

Database-side assertions and eight direct MCP tool cases passed on the training
environment on 2026-10-11, including the initialized notification. PAF's source
connection test discovered all three tools. The **DBA Login Troubleshooting Lab**
workflow is saved as an unpublished draft with memory disabled. Earlier runbook-mode tests
covered the locked fixture, missing incident details, and an out-of-scope ADMIN
unlock request. The locked-fixture retest returned account and privilege evidence
with separate observation timestamps and did not propose unlocking the fixture.

The AI-led configuration selects only the two diagnostic tools and has no runbook
requirement. After instruction revisions, all 15 Appendix D cases passed final
sequential response-level review on 2026-10-11 with the graph unchanged during the
run. An earlier same-configuration full run also passed; an intervening concurrent
repeat had two reported MCP tool failures. A subsequent source test and final
sequential run succeeded, but the intermittent cause remains unconfirmed.

See [MCP validation prompts and results](../livelab-paf-only/files/mcp-test-prompts.md)
for the checklist and repeatable runner. Full tool-call trace review and token
renewal across expiry remain unverified; this is not a production certification.
The source and draft workflow already exist in training; reuse them there.

The PAF certificate pin was updated after the user explicitly authorized trusting
the presented certificate. It was not independently verified against deployment
records. Exact fingerprint checking remains enabled; the browser's certificate
warning has not been fixed by this change.
