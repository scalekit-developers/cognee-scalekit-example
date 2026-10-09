# 3-minute demo script

Terminal ready, venv active, in the project folder. Cognee UI closed.

## 0:00 Problem (20s)
"Company knowledge is scattered, and some of it is confidential. An agent needs to know the company, but each person should only get what they are authorized to see."

## 0:20 Pull + Remember (40s)
- Show Scalekit dashboard: Connections -> `notion`, Connected Accounts for two identifiers.
- "Scalekit holds each user's OAuth token. My code never sees it."
- Show the ingest result (already run): leadership view 6 docs, engineer view 4 docs, separate Cognee datasets.

## 1:00 Brain (30s)
```bash
python ask.py --user bob@lumen.test "Why did we choose Postgres over MongoDB, and who owns the migration?" 2>/dev/null
```
"Multi-hop answer from the RFC and the decision log."

## 1:30 Access (50s)
Same question, two users:
```bash
Q="What caused the Sept 2 billing outage and how long did it last?"
python ask.py --user jian.han3@gmail.com "$Q" 2>/dev/null
python ask.py --user bob@lumen.test "$Q" 2>/dev/null
```
Then:
```bash
Q="How much is the Series B raise?"
python ask.py --user jian.han3@gmail.com "$Q" 2>/dev/null
python ask.py --user bob@lumen.test "$Q" 2>/dev/null
```
"Leadership gets the root cause and the raise. The new engineer gets nothing confidential."

## 2:20 Eval (30s)
```bash
python eval.py --compare before_no_access_control after_scoped
```
"Without access control the new engineer's answers leak. With per-user brains, zero leaks. LLM calls go through the Respan gateway:"
```bash
respan logs list --limit 3 --all-envs true
```

## 2:50 Limits and next (10s)
"One source today. Next: GitHub as a second source, Cognee backend shares, and separate Notion accounts per user."
