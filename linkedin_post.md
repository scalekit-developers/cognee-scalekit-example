Same question. Different user. Different answer.

For the Cognee × Scalekit hackathon I built a permission-aware "Company Brain" for an engineering team.

An agent needs to know the company, but each person should only get what they're allowed to see. So:

→ Pull: Scalekit connects Notion with per-user OAuth (RFCs, decision log, onboarding, an incident postmortem, leadership notes)
→ Remember: Cognee builds one knowledge graph per user
→ Act: the agent answers only from that user's graph
→ Evaluate: all LLM calls go through the Respan gateway, and an eval checks for leaks

Ask "What caused the September billing outage?" and leadership (6 documents) gets the root cause. A new engineer (4 documents) gets nothing confidential.

The part I like most: access is measured, not just demoed. The eval compares a shared brain with no access control against the per-user brain on questions where leakage counts as a failure.

Honest limits: only Notion is connected so far (GitHub ingestion is written but not run), and both demo users share one Notion account, so scoping happens at ingest time. Next: GitHub as a second source, Cognee backend shares, and separate Notion accounts per user.

#AI #AIAgents #KnowledgeGraph #RAG #Cognee #Scalekit #Respan #AccessControl #AIGovernance #Hackathon #BuildInPublic
