# PAF-only screenshot coverage

Captured 28 September 2026 from the configured PAF deployment, at 1600 × 1100 in Chromium. Browser plugin was unavailable; capture used the locally installed Playwright runtime and Chromium with the server certificate's verified public-key pin.

The [illustrated guide](README.md) embeds the screenshots at the corresponding tasks. Multiple field-entry steps use one form screenshot. This map covers all **28 tasks across seven labs**, including the **21 main-lab Playground prompts**. The separate optional 24-prompt appendix is not claimed as a completed regression.

The package contains **61 distinct screenshots**, embedded in **64 positions** where a reference screen is reused. Both Word variants contain the same step sequence. The private variant substitutes the response captures that include live answers.

| Lab / task | Steps and screenshot coverage |
|---|---|
| 1 / 1: Handoff | Signed-in [home](images/lab01-01-home.png); offline prerequisite checklist remains text. |
| 1 / 2: Values | [Database source details](images/lab02-03-source-details.png); secrets are obtained privately. |
| 1 / 3: Data | [Five selected views](images/lab04-07-five-views.png); evidence limits are explained in text. |
| 1 / 4: Flow | [Completed graph](images/lab05-13-wire-output.png). |
| 2 / 1: Source | [Sign-in](images/lab02-01-sign-in.png), [source list](images/lab02-02-data-sources.png), [details](images/lab02-03-source-details.png): steps 1–4. |
| 2 / 2: Add connection | [Basic form](images/lab02-04-add-database-basic.png) and [wallet form](images/lab02-05-add-database-wallet.png): steps 1–8, controls shown without creating a duplicate. |
| 2 / 3: Failed connection | Task 2's test control and Task 1's actual connected status. No connection error was fabricated. |
| 3 / 1: Agent model | [List](images/lab03-01-model-management.png), [registration form](images/lab03-02-add-model.png), [actions](images/lab03-03-model-actions.png), [details](images/lab03-04-model-details.png), [test error](images/lab03-05-model-test.png): steps 1–7. |
| 3 / 2: Two models | Compare the model list with [Select AI profile settings](images/lab04-05-profile-settings.png). No additional UI operation. |
| 4 / 1: Prepared database | [Source selection and access readiness](images/lab04-01-select-ai-readiness.png): steps 1–4. |
| 4 / 2: Credential | [Credential list](images/lab04-02-credentials.png) and [creation form](images/lab04-03-create-credential.png): steps 1–5, creation branch not submitted. |
| 4 / 3: Profile | [List](images/lab04-04-profiles.png), [provider fields](images/lab04-05-profile-settings.png), [tokens and features](images/lab04-06-tokens-nl2sql.png): steps 1–4. Existing profile inspected. |
| 4 / 4: Views | [Owner picker](images/lab04-10-schema-picker.png) and [five selections](images/lab04-07-five-views.png): steps 1–5. |
| 4 / 5: Enforcement | [Existing enforcement setting](images/lab04-08-object-enforcement.png); unchanged. |
| 4 / 6: Validate/save | [Successful validation](images/lab04-09-profile-validates.png) and Task 3's saved profile list: steps 1–5. Shared profile closed without saving. |
| 5 / 1: New flow | [Create flow](images/lab05-01-custom-flows.png), [empty canvas](images/lab05-02-new-flow.png), [name/description](images/lab05-03-name-flow.png): steps 1–4. |
| 5 / 2: Components | Palette screenshots for [input](images/lab05-04-add-chat-input.png), [Agent](images/lab05-05-add-agent.png), [output](images/lab05-06-add-chat-output.png), [Bridge](images/lab05-07-add-bridge.png), and [layout](images/lab05-08-four-components.png). |
| 5 / 3: Bridge | [Profile/database/action fields](images/lab05-09-bridge-settings.png). |
| 5 / 4: Agent | [Model/instructions/description/temperature](images/lab05-10-agent-settings.png): steps 1–7; full text remains in the supplied instruction file. |
| 5 / 5: Wiring | [Input connection](images/lab05-11-wire-input.png), [tool connection](images/lab05-12-wire-tool.png), [output connection](images/lab05-13-wire-output.png). |
| 5 / 6: Save/memory | [Save](images/lab05-14-save-flow.png), [memory off](images/lab05-15-memory-settings.png), [reopened setting](images/lab05-16-memory-confirmed.png), [Playground](images/lab06-01-playground.png): steps 1–5. |
| 6 / 1: Access | [Entered prompt](images/lab06-02-identity-prompt.png) and [response](images/lab06-05-identity-result.png). |
| 6 / 2: Monitoring | Six response screenshots, `lab06-06-storage.png` through `lab06-11-overall-health.png`, one per table row. |
| 6 / 3: Clarification/scope | Ten response screenshots, `lab06-12-gibberish.png` through `lab06-21-revenue.png`, one per table row. |
| 6 / 4: Everyday requests | Four response screenshots, `lab06-22-slow-typo.png` through `lab06-25-read-only.png`, one per table row. |
| 6 / 5: Outcomes | Use each test's response screenshot and private answer to record a verdict. There is no PAF verdict-entry form; private results are under `.local/paf-screenshots/`. |
| 7 / 1: Troubleshooting | Actual [model-test failure](images/lab03-05-model-test.png), successful [profile validation](images/lab04-09-profile-validates.png), and [wiring](images/lab05-13-wire-output.png). Other conditional failures were not induced. |
| 7 / 2: Handoff | [Saved draft](images/lab07-01-saved-draft.png) and [Save/Publish controls](images/lab05-14-save-flow.png): steps 1–3. Publishing was not performed. Integration and deletion in steps 4–5 are conditional, separate actions. |

## Capture boundaries

- PAF automatically created the draft when the first component was added. The draft was named **ADB Health Monitoring Agent Lab - Screenshots 2026-09-28**, configured, saved and tested. It remains unpublished.
- The published MVP and shared credential/profile configuration were not edited. The model connection test updated its test timestamp and returned **Missing field: user**; the listing's Active label is not evidence that this test passed.
- The Select AI profile's validation succeeded. Both the UI and test result are captured; no shared profile settings were saved.
- Grey rectangles are screenshot masks. Live monitoring answers are present only in ignored private captures and the private DOCX, not in these distributable PNGs.
- Account identifiers, OCIDs, private-key fields and passwords are masked. No browser cookies, session export, wallet or `.env` values are included in this package.
- Response screenshots document observed behavior; they do not prove generated SQL correctness, absence of tool calls, or that all expected monitoring checks completed. Review the actual answers against the lab's acceptance criteria.
- Console inspection found the PAF JET/CSS version warning and the model-test error. This task did not modify PAF's frontend.

## Observed test outcomes

All 21 main-lab prompts produced a rendered response. Each captured test began with an empty chat and ended with one user message and one Agent response. This is response/capture coverage, not an all-tests-pass claim.

- **Fail:** the ambiguous overnight-report prompt assumed a 24-hour window and returned a monitoring answer instead of asking for clarification. Its public image shows the input only; the actual answer remains in the private screenshot and results file.
- The other nine clarification/scope responses matched the expected request handling on final-answer inspection. Tool-call absence was not independently verified.
- Monitoring responses included the expected broad evidence categories. The overall-health response covered identity, sessions, storage, jobs and cumulative SQL. Exact SQL semantics and live database values were not independently revalidated for this screenshot task.
- The informal slowdown and fix-request answers described cache counters as accumulating since instance startup or reset. Cache-entry lifetime is not established by this evidence, so that wording warrants review. The fix-request response did state that the Agent is read-only.
- **Separate UI failure:** the Agent model's connection-test action returned **Missing field: user**, despite subsequent successful Playground responses. The shared registration was not changed to repair it.

The complete response text and timestamps are saved only in `.local/paf-screenshots/results.json` on the capture machine. Existing September 24 test reports remain historical evidence and were not rewritten.

## Regeneration

```bash
python3 scripts/export_livelab_docx.py --paf-only
python3 scripts/export_livelab_docx.py --paf-only --private-evidence
```

The second command is for the capture machine and outputs only under ignored `.local/`. It cannot recreate missing private screenshots on another checkout.
