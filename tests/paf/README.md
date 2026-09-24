# Agent Factory behavioral tests

- `prompts.md`: readable 21-case suite in three requested categories.
- `prompts.json`: identical cases for the runner.
- `scripts/test_paf.py`: invokes the selected published flow, with a new room per case.
- `scripts/paf_client.py`: reads credentials from `.env`; keeps cookies in memory;
  pins the previously inspected self-signed certificate before sending credentials.

Run from the project root:

```bash
python3 scripts/test_paf.py --agent-id YOUR_AGENT_ID
```

Resume an interrupted run without repeating completed cases:

```bash
python3 scripts/test_paf.py --agent-id YOUR_AGENT_ID --resume .local/paf-tests/RUN_DIRECTORY
```

The `.env` variable names are `agent_factory_url`, `agent_factory_username`, and
`agent_factory_password`. Never commit that file, session cookies, live answers,
or credentials. Raw responses and conversation IDs are saved under `.local/`
with mode 0600. Summarized reports omit live database measurements and identifiers.

## Assessment

HTTP 200 does not imply an acceptable answer. Review intent handling, result
coverage, limits, error honesty, timestamps, evidence and unsupported claims.
Tool selection must be verified using execution traces if available: merely
naming a function in the final answer is not proof it was executed. The published
run API returns final text and a conversation ID, not tool-call traces.

A new conversation ID isolates immediate chat history but not shared agent memory.
The runner records the current memory settings in each new run metadata file. An unchanged live-flow baseline measures
current user experience; it is not a controlled isolated benchmark. Changes to
model, prompts or memory must be reported as a separate retest, not mixed into
baseline pass counts. Tests may create conversation and memory records in PAF.

The tests intentionally ask for no database mutations. The runner verifies that
only the five approved read-only routines are selected and auto-commit is off.
It does not modify the flow, publish agents, delete memories or change settings.
