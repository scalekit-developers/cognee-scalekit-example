# Team Submission

## Team

- Team name: <fill in>
- Participants: Rosso Han
- Company Brain / project name: Permission-Aware Company Brain ("Lumen Pay Brain")

## Company Brain Overview

A Company Brain for an engineering team. It pulls RFCs, a decision log, onboarding docs, an incident postmortem and leadership planning notes from Notion through Scalekit, builds one knowledge graph per user in Cognee, and answers questions using only what that user is allowed to see. A new hire gets onboarding, RFC and decision answers; engineering leadership additionally gets incident root causes, revenue risk and strategy. Same question, different user, different answer.

- Data sources connected through Scalekit (≥ 2 apps): **Notion only (1 app) in this submission.** A GitHub issues/PR ingestion path is written (`seed_github.py`, `ingest.py --github`) but was not run before the deadline.
- Primary use case / team workflow: engineering onboarding and "why did we decide this" questions over RFCs and decision records, with confidential material (postmortem, hiring, financing, churn risk) restricted by role.
- Users in the demo and how their access differs:
  - `jian.han3@gmail.com` (leadership view): all 6 documents (RFC-001, RFC-002, Decision Log, Onboarding, Postmortem PM-2026-09, Leadership priorities)
  - `bob@lumen.test` (new engineer view): 4 engineering documents only (RFC-001, RFC-002, Decision Log, Onboarding)
- What makes it stand out: the access story is measured, not just shown. An eval compares a shared brain with no access control against the per-user brain on questions where leakage is a failure.

## The Three Layers

### Pull — Scalekit

- Connections created (`connection_name` → app): `notion` → Notion (OAuth, per-user); `github-connect` → GitHub (created, not used in the demo)
- Tools called: `notion_page_search` (paginated with `start_cursor`), `notion_page_markdown_get` (fallback `notion_page_content_get`)
- How users are identified (`identifier` ↔ Cognee user): the Scalekit `identifier` is the user's email; the Cognee dataset name is derived from it (`jian_han3-brain`, `bob-brain`)
- Any write-back actions the agent takes: none in this version
- Code entry point: `ingest.py`

### Remember — Cognee

- What goes into the permanent graph: every ingested Notion page as one document via `cognee.remember(doc, dataset_name=..., node_set=[...])`
- What stays in session memory: nothing
- `node_set` tags used for provenance: `source:notion`, `page:<title>`
- Datasets and who owns / can read each: `jian_han3-brain` (leadership view, 6 docs), `bob-brain` (engineering view, 4 docs). Each user only queries their own dataset (`ask.py`).
- Access control: scope is enforced at ingest time by a per-role page allowlist (`--include`) plus one dataset per user. **Limitation, stated plainly:** both demo users authorize with the same Notion account, and Notion tracks page access per user/workspace/integration, not per Scalekit identifier, so Notion-side scoping could not separate them. With separate real Notion accounts the Scalekit consent would scope each user. Cognee-level backend permissions (`ENABLE_BACKEND_ACCESS_CONTROL` users and shares) are the next step and are not used here.
- Anything beyond defaults: Cognee's default `remember` pipeline (includes self-improvement); LLM and embeddings routed through the Respan gateway
- Code entry point: `ingest.py`, `ask.py`

### Act + Evaluate — your agent(s) + Respan

- Agent(s) and the task each performs: a per-user question-answering agent (`ask.py`) that recalls from the user's dataset and answers
- LLM calls routed through the Respan gateway? Yes: Cognee `LLM_*` and `EMBEDDING_*` point to `https://api.respan.ai/api` (model `openai/gpt-5-mini`; embeddings `openai/text-embedding-3-large`). Calls appear in `respan logs list`.
- How the runs are traced: gateway request logs (model, tokens, cost, latency). SDK tracing is wired in `ask.py` but the `respan` Python packages did not install in the hackathon environment (deprecated `sklearn` dependency), so SDK traces are not part of this submission.
- Scenario file / Respan testset: `eval.py`, 14 scenarios (access-sensitive and shared-knowledge questions). Not imported into the Respan platform; scored locally.
- Evaluator: deterministic Python check. Each scenario lists phrases that must appear and phrases that must not (confidential values such as the Series B amount or the outage duration for the new-engineer user).
- Code entry point: `eval.py`

## Evaluation Evidence

### Baseline Run (no access control)

- Respan trace / eval run link: gateway logs only
- Scenarios run: 14, with `BRAIN_MODE=shared` (every user reads the leadership dataset)
- Mean score: <fill from `eval_results/before_no_access_control.json`>
- Worst scenario and why it failed: <fill: e.g. `series-bob` leaked the raise amount>

```text
question: How much is the Series B raise?
expected: no confidential amount in the new engineer's answer
got:      <fill>
score:    FAIL
```

### Improved Run (per-user brain)

- Respan trace / eval run link: gateway logs only
- What changed in the brain or agent between runs: each user queries only their own role-scoped dataset instead of a shared one.
- Mean score: <fill>

```text
Before:  passed = ___ / 14   (shared brain, no access control)
After:   passed = ___ / 14   (per-user brain)
```

## Access Story

- User A (`jian.han3@gmail.com`): Notion via Scalekit; dataset `jian_han3-brain` with all 6 documents
- User B (`bob@lumen.test`): Notion via Scalekit; dataset `bob-brain` with 4 engineering documents
- Question asked by both: "What are the Q4 priorities?"
- Result for A: Instant Payouts by 2026-11-30, reduce card-network risk, close the $40M Series B by 2026-12-15
- Result for B: "The provided context does not specify the Q4 priorities." No confidential data.
- The grant: not implemented in this version (no cross-user sharing)
- Result for B after the share: n/a

## Architecture

```text
[ Notion via Scalekit connection "notion", per-user identifier ]
        |
        | execute_tool(notion_page_search, notion_page_markdown_get)
        v
[ ingest.py: role allowlist ] -> cognee.remember(node_set=[source:notion, page:*],
        |                                         dataset_name=<user>-brain)
        v
[ Cognee: one knowledge graph per user dataset ]
        |
        | recall(question, datasets=[<user>-brain])
        v
[ ask.py agent; LLM + embeddings through the Respan gateway ] -> answer
        |
        v
[ eval.py: 14 scenarios, must / must-not checks ] -> before / after
```

## Reproduction

```bash
python -m venv cognee-env && source cognee-env/bin/activate   # Python 3.11 worked
pip install cognee scalekit-sdk-python python-dotenv truststore
cp respan.env.example .env   # then add the Scalekit values below
python ingest.py --user jian.han3@gmail.com --include RFC Decision Onboarding Postmortem Leadership
python ingest.py --user bob@lumen.test --include RFC Decision Onboarding
python ask.py --user jian.han3@gmail.com "What caused the Sept 2 billing outage?"
python ask.py --user bob@lumen.test "What caused the Sept 2 billing outage?"
BRAIN_MODE=shared python eval.py --label before_no_access_control
python eval.py --label after_scoped
python eval.py --compare before_no_access_control after_scoped
```

Environment variables required:

```text
RESPAN_API_KEY
LLM_PROVIDER / LLM_ENDPOINT / LLM_API_KEY / LLM_MODEL
EMBEDDING_PROVIDER / EMBEDDING_ENDPOINT / EMBEDDING_API_KEY / EMBEDDING_MODEL / EMBEDDING_DIMENSIONS
SCALEKIT_ENVIRONMENT_URL
SCALEKIT_CLIENT_ID
SCALEKIT_CLIENT_SECRET
```

Judges without our Notion: the source documents are in `fixtures/company/` (6 markdown files). Import them into a Notion page, authorize the `notion` connection in Scalekit, then run the commands above. Behind a corporate TLS proxy also set `GRPC_DEFAULT_SSL_ROOTS_FILE_PATH` to a CA bundle that includes the proxy root.

## Demo

- 3-minute pitch outline:

```text
1. Problem: company knowledge is scattered and confidential; agents need role-aware access
2. Pull: Scalekit connects Notion per user (identifier = email), no tokens in our code
3. Brain: Cognee builds a knowledge graph; show a multi-hop answer (why Postgres, who owns it)
4. Access: same question, two users - outage root cause / Q4 priorities / Series B
5. Eval: before (shared brain) vs after (per-user brain) scores
6. Honest limits and next: second source (GitHub), Cognee backend shares, separate Notion accounts
```

## Links

- Repo: <fill in>
- Respan traces / eval runs: Respan gateway logs (platform.respan.ai)
