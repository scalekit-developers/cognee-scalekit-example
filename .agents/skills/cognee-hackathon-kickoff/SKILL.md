---
name: cognee-hackathon-kickoff
description: Use when someone is starting a hackathon project on top of this repo (Book Issue Desk — Scalekit login + Cognee memory) — getting the demo running in under 15 minutes, choosing local vs Cognee Cloud memory, indexing a codebase, and picking a project that uses more of Cognee than one-shot recall.
---

# Cognee hackathon kickoff

This repo is the starting point. It is a FastAPI app with one page. Scalekit
says who is logged in; Cognee stores and answers from that person's memory.
Your job at the hackathon is to make it do something new. This skill gets you
from clone to a working demo fast, then tells you where the interesting Cognee
features are.

The structure and conventions here follow the cognee repo's own skills
(`topoteretes/cognee`, `.agents/skills/`). Read those for depth; this one is
the short path.

## 0. Pick a memory mode (1 minute)

| Mode | Needs | Use when |
|---|---|---|
| `MEMORY_MODE=local` | `LLM_API_KEY` (OpenAI by default) | Hacking. Free of Cloud setup, data stays under `.venv`, you can inspect the graph |
| `MEMORY_MODE=cloud` | `COGNEE_API_KEY` + `COGNEE_BASE_URL` | Demo day. Shared tenant, nothing to keep running |
| local **+** Cloud keys | both | Build locally, then **Push this memory to Cloud** (`cognee.push`, zero LLM calls on Cloud) |

Leave `MEMORY_MODE` empty and the app picks cloud when `COGNEE_BASE_URL` is set, else local.

## 1. Run it (10 minutes)

```bash
git clone https://github.com/scalekit-developers/cognee-scalekit-example.git
cd cognee-scalekit-example
uv venv --python 3.12 .venv            # 3.14 fails; use 3.12
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
```

Fill `.env`:

- Memory: `LLM_API_KEY` (local) **or** `COGNEE_API_KEY` + `COGNEE_BASE_URL`
  (cloud, from https://platform.cognee.ai → API Keys).
- Scalekit (always required, the app refuses to start without it):
  `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET`
  from https://app.scalekit.com → Developers → Settings → API Credentials, and
  `COOKIE_ENCRYPTION_SECRET=$(openssl rand -base64 32)`.
- In the Scalekit dashboard: Authentication → Redirect URLs →
  callback `http://localhost:5001/callback`, initiate `http://localhost:5001/login`,
  post-logout `http://localhost:5001/`. Enable Magic Link & OTP (Verification
  Code). Environment settings → Test users: `alice+sktest@demo.com`,
  `bob+sktest@demo.com`, static code `424242`.

Start:

```bash
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 5001
```

Smoke test without any login: open http://localhost:5001 → **Try Bob without
login** → **Save this customer's notes** → click the reorder question. The
answer must mention the failed payment. Then **Index this repo** → **Draw the
module map of this app** renders a Mermaid diagram of `app.py` routes.

CLI equivalents (same `.env`):

```bash
.venv/bin/python loop.py --user bob            # seed + recall
.venv/bin/python loop.py --user alice --push   # local → Cloud
.venv/bin/python loop.py --index-code          # build the code graph
.venv/bin/python loop.py --code impact         # architecture|impact|path|insights|facts
```

## 2. Where the Cognee calls are

All of them live in `loop.py`; `app.py` is routes and cookies.

| Function | Cognee call | Note |
|---|---|---|
| `connect()` | `cognee.serve(url, api_key)` | Once per process (FastAPI lifespan). After this every SDK call goes to Cloud |
| `seed_user()` | `cognee.remember(text, dataset_name=…)` then `cognee.improve(…)` | On Cloud, `remember` returns `status: running` before the note is stored. The seed then polls `GET /api/v1/datasets/{id}/data` until a document appears, or returns a timeout. It does not claim the note is saved before that. |
| `recall_user()` | `cognee.recall(q, query_type=HYBRID_COMPLETION, datasets=[name])` | Pinned type so item 0 is always the LLM answer. Retries HTTP 409 with backoff |
| `push_user()` | `cognee.push(name, url=…, api_key=…, mode="preserve")` | Exports the local graph (COGX) and imports it on Cloud |
| `index_code()` | `cognee.remember(path_or_git_url, content_type="code", dataset_name="desk_code")` | enola code graph, deterministic, no LLM. Cloud clones a URL; a local path only works locally |
| `ask_code()` | `cognee.recall("", scope=["code"], code_query={…}, datasets=["desk_code"])` | `code_query` needs `scope=["code"]` or it raises |

Dataset = isolation boundary. `datasets=["bob"]` never sees `alice`.

## 3. Hackathon ideas, ordered by effort

Each one uses something the demo does not yet.

1. **Real conversations (session memory).** Replace the fixed buttons with a
   text box. Store each turn with `remember(QAEntry(question=…, answer=…),
   session_id=f"desk-{customer}")` and read with `recall(q, session_id=…,
   datasets=[customer])`. Follow-ups ("ok, jump to #53") start working. Run
   `improve(customer, session_ids=[…])` to fold the conversation into the
   permanent graph. Skill in the cognee repo: `cognee-improve-sessions`.
2. **Show your evidence.** `recall(…, include_references=True)` returns which
   chunk supports each edge used; `only_context=True` returns the exact prompt
   Cognee sent to the LLM. Both fit the "How this reply is built" panel.
3. **Structured answers instead of substring matching.** `/api/ask` sets
   `matched` by searching the answer for "51"/"payment". Use
   `recall(…, response_schema={…})` to get `{"current_issue": 51,
   "requested_issue": 53}` and assert on it.
4. **Real data.** Four lines per customer is a prompt, not a memory. Drop an
   order-history CSV or a folder of support emails into `fixtures/` and
   `remember()` the folder (`cognee-ingestion` skill lists every input type).
   Then try `SearchType.GRAPH_REPORT` for "what does the shop know about Alice?".
5. **Let Cognee enforce isolation.** Today both datasets sit under one API
   key; the app picks the right name. Create one Cognee user per Scalekit
   `sub` and call with that user's credentials; `recall(datasets=["bob"])`
   from Alice then raises `PermissionDeniedError`. Skill: `cognee-permissions`.
6. **Code graph for your own repo.** Set `CODE_REPO_URL` to any GitHub URL,
   click **Index this repo**, then write new `code_query` buttons in
   `loop.py:CODE_QUESTIONS` (`explore`, `traverse`, `query_facts` with
   `kind="dependency"`, `delta`). Diagrams: add `"diagram": "mermaid"` to
   any operation. Example: `examples/guides/code_graph_example.py` in cognee.
7. **Act on memory.** The Slack post is static text. Build it from
   `recall()` ("summarize what Bob still owes") and send through Scalekit's
   connected account so the token stays out of your app.
8. **Agentic answers.** `cognee.search(query_type=AGENTIC_COMPLETION,
   skills=[…], tools=[…])` runs a bounded tool loop; ingest a `SKILL.md`
   playbook with `remember(folder, content_type="skills")` and let the desk
   follow it.

## 4. Pitfalls that cost people an hour

- **Python 3.14** breaks the install. `uv venv --python 3.12`.
- **Cloud `remember` returns before the graph is queryable.** `improve()`
  can skip every stage. `seed_user()` polls the dataset data endpoint and
  returns an error on timeout. Do not treat the click as saved until the
  page says the notes are saved.
- **HTTP 409 on recall** = a pipeline still holds the dataset lock.
  `recall_user()` backs off 1s, 2s, 4s. Do not hammer it.
- **Local mode is slow per answer?** `AUTO_FEEDBACK=false` in `.env` removes
  one LLM call per answered turn. Keep `CACHING=true`.
- **`code_query` without `scope=["code"]` raises.** The code lane is never
  implied.
- **Code indexing on Cloud needs a git URL.** A local path means the server's
  filesystem, not yours. Local mode indexes the live checkout.
- **`push` fails with "did not perform a COGX archive import".** The Cloud
  tenant runs an older cognee; use cloud mode and `remember()` the raw notes.
- **Scalekit redirect mismatch.** The dashboard callback URL and
  `SCALEKIT_REDIRECT_URI` must be byte-identical.
- **Unrecognized login lands on "Continue as Alice".** The default token has
  `sub` but no `email`. Copy `sub` into `SCALEKIT_ALICE_SUB` /
  `SCALEKIT_BOB_SUB` to skip the click.
- **Wipe local state** between experiments: `.venv/bin/python -c
  "import asyncio, cognee; asyncio.run(cognee.forget(everything=True))"`.

## 5. Read next

In the cognee repo (`.agents/skills/`): `cognee-install`, `cognee-ingestion`,
`cognee-recall`, `cognee-improve-sessions`, `cognee-permissions`,
`cognee-performance`. Docs: https://docs.cognee.ai. Scalekit:
https://docs.scalekit.com/authenticate/fsa/quickstart/.
