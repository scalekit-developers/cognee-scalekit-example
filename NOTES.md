# Company Brain hackathon notes (2026-10-07)

Permission-aware Company Brain built on the Scalekit + Cognee reference app.
Notion (via Scalekit) -> Cognee knowledge graph per user -> answers scoped to
what each user may see. LLM and embedding calls go through the Respan gateway.

Fictional company data lives in `fixtures/company/` (6 docs). No real company
data and no secrets in this repo; credentials stay in `.env` (git-ignored).

## Files I added

| File | Purpose |
|------|---------|
| `ingest.py` | Pull Notion pages through Scalekit (paginated, `--include` allowlist, `--dry-run`), `cognee.remember` into `<user>-brain`. Optional `--github owner/repo` |
| `ask.py` | Ask as a user; only that user's dataset is searched. `BRAIN_MODE=shared` simulates no access control |
| `eval.py` | 14 scenarios with must / must-not checks (correctness + leakage). `--label`, `--compare` |
| `seed_github.py` | Create demo issues in your own test repo via Scalekit (not run) |
| `respan.env.example` | `.env` lines to route Cognee through the Respan gateway |
| `SUBMISSION.md`, `DEMO_SCRIPT.md` | Hackathon write-up and pitch |
| `eval_results/` | Saved eval runs |

## Everyday commands

Run everything from this folder with the venv active (Cognee reads `.env` from
the current directory; run elsewhere and it silently falls back to defaults).

```bash
cd ~/workspace/github/cognee/hackthon/cognee-scalekit-example
source ~/workspace/github/cognee-env/bin/activate
export GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=$HOME/corp-ca.pem   # corp network only

# ingest (stop the Cognee UI first; it holds the local DB)
python ingest.py --user jian.han3@gmail.com --dry-run
python ingest.py --user jian.han3@gmail.com --include RFC Decision Onboarding Postmortem Leadership
python ingest.py --user bob@lumen.test --include RFC Decision Onboarding

# ask
Q="What caused the Sept 2 billing outage and how long did it last?"
python ask.py --user jian.han3@gmail.com "$Q" 2>/dev/null
python ask.py --user bob@lumen.test "$Q" 2>/dev/null

# eval before/after
BRAIN_MODE=shared python eval.py --label before_no_access_control 2>/dev/null
python eval.py --label after_scoped 2>/dev/null
python eval.py --compare before_no_access_control after_scoped

# wipe a dataset
python -c "import asyncio, cognee; asyncio.run(cognee.forget(dataset='bob-brain'))"

# graph UI (backend :8000, frontend :3000; first start downloads frontend deps)
cognee-cli -ui
```

## Cognee recall search types (v1.6.3)

`SUMMARIES, CHUNKS, RAG_COMPLETION, HYBRID_COMPLETION, TRIPLET_COMPLETION,
GRAPH_COMPLETION, GRAPH_COMPLETION_DECOMPOSITION, GRAPH_SUMMARY_COMPLETION,
CYPHER, NATURAL_LANGUAGE, GRAPH_COMPLETION_COT,
GRAPH_COMPLETION_CONTEXT_EXTENSION, FEELING_LUCKY, TEMPORAL, CODING_RULES,
CHUNKS_LEXICAL, AGENTIC_COMPLETION, CODE, GRAPH_REPORT, SKILLS`

What I observed:

- Default `recall` (it used `HYBRID_COMPLETION`): best for specific and
  multi-hop questions ("why Postgres, who owns it").
- `GRAPH_REPORT`: structural report, mostly graph algorithms (hub nodes by
  degree/PageRank, cross-document links, edge provenance). 6 docs -> 228 nodes,
  741 edges. Top PageRank nodes were generic type nodes (work, technology); the
  real hubs were people (Maya Chen 28, Sofia Alvarez 26, Raj Patel 25).
  Document "Visibility:" lines were extracted as `visible_to` edges.
- `GRAPH_SUMMARY_COMPLETION`: natural-language topic summary. Good for global
  questions ("what does the company discuss"), which default recall handles
  poorly because it only looks at the top-k chunks.

```python
import asyncio, cognee
from cognee import SearchType
async def m():
    r = await cognee.recall("What are the main topics in this knowledge graph?",
                            datasets=["jian_han3-brain"],
                            query_type=SearchType.GRAPH_SUMMARY_COMPLETION)
    for x in r: print(getattr(x, "text", x))
asyncio.run(m())
```

## What `cognee.remember` does

`remember` = `add` + `cognify` + `improve`:

1. add: store raw text, classify the document, record dataset metadata (SQLite).
2. cognify: chunk, LLM-extract entities and relationships (graph DB), embed
   chunks and entities (LanceDB).
3. improve: self-improvement pass and vector-store compaction.

Local storage: `cognee-env/lib/python3.11/site-packages/cognee/.cognee_system/`.
`node_set=["source:notion", "page:<title>"]` tags nodes with provenance.

## Respan

- Gateway: set `LLM_*` / `EMBEDDING_*` to `https://api.respan.ai/api` (see
  `respan.env.example`). Every call shows up in Logs.
- CLI: `npm install -g @respan/cli`; reads `RESPAN_API_KEY` from `.env` in the
  current directory.

```bash
respan logs list --all-envs true --limit 15 --start-time 2026-10-07T00:00:00Z --sort-by -timestamp
respan logs list --all-envs true --filter status_code:not:200 --start-time "$(date -u -v-3H +%Y-%m-%dT%H:%M:%SZ)"
respan logs get <id>      # replace <id> with a real id; no angle brackets in zsh
```

- `logs list` default window is short; pass `--start-time` explicitly.
  Timestamps are UTC (`Z`); PDT = UTC-7.
- One question = 2-3 embedding calls (retrieval) + 1 answer call + session
  memory analysis calls.
- SDK tracing (`respan`, `respan-tracing`, `respan-instrumentation-openai`) did
  not install (deprecated `sklearn` dependency). Gateway logs were enough.

## Gotchas

1. Corporate SSL inspection: `uv venv --native-tls`; Python `requests`:
   `pip install truststore` + `truststore.inject_into_ssl()`; gRPC (Scalekit SDK)
   ignores both: export keychain certs to a PEM and set
   `GRPC_DEFAULT_SSL_ROOTS_FILE_PATH`; npm: `npm config set cafile ~/corp-ca.pem`.
2. Never `pip install` Cognee into the global env (huggingface-hub <1 vs
   transformers/gradio >=1). Use a venv.
3. Cognee dataset names cannot contain dots or spaces.
4. `notion_page_search` returns 10 results per call; paginate with `start_cursor`.
5. The Notion grant covers whatever pages you tick, including personal notes;
   dry-run first.
6. Notion page access is per Notion account + integration, not per Scalekit
   identifier. Two simulated users on one Notion account share the grant, so
   scope was enforced with the ingest-time `--include` allowlist.
7. Approve the authorization link in the browser before pressing Enter, or the
   account stays `PENDING_AUTH`.
8. Stop `cognee-cli -ui` before ingesting (DB lock).
9. Changing the embedding model invalidates existing vectors: forget and re-ingest.
10. Cognee session-memory analysis (`SessionTurnAnalysis`) fails under OpenAI
    strict JSON schema (`oneOf` not permitted, HTTP 400); Cognee retries in
    non-strict mode, answers are unaffected. `CACHING=false` in `.env` turns it
    off. This is what prints `LiteLLM.Info: ... Give Feedback`.
11. Run Cognee scripts from this folder; elsewhere `.env` is not loaded and LLM
    calls fail (silently empty results with `2>/dev/null`).
12. Cognee fetches the embedding tokenizer from huggingface.co; behind corp SSL
    that fails and it falls back to TikToken (approximate token counts). Ad-hoc
    scripts need `truststore.inject_into_ssl()` like `ask.py`; or set
    `HF_HUB_OFFLINE=1` to skip the download.
13. Links inside a permitted page leak titles of restricted pages. In our case
    the 06 Leadership page sat under the 04 Onboarding page in Notion, so 04's
    markdown ended with `<page url=...>[06-leadership-...]</page>`; Bob's graph
    got a `06-leadership-...` node and his topic summary listed "Leadership /
    hiring / priorities" (title only, no content). Parent / index pages do the
    same. `ingest.py` now strips `<page>` child-page links before `remember`.
    Debug tip: `respan logs get <id>` shows the exact context the LLM saw.

## Limits / next

- Only one source (Notion). GitHub path is written but not run.
- Enforce access in Cognee itself (`ENABLE_BACKEND_ACCESS_CONTROL`, users and
  dataset shares) instead of dataset naming.
- Separate real Notion accounts per user.
- Write-back actions through Scalekit (Slack, issues).
- Import `eval.py` scenarios into Respan evals with an LLM judge.
