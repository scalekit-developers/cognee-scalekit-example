"""Pull a user's Notion pages through Scalekit and remember them in Cognee.

Usage:
    .venv/bin/python ingest.py --user alice@acme.com
    .venv/bin/python ingest.py --user bob@acme.com --limit 20

The Scalekit identifier is the user. Each user's pages go into their own
Cognee dataset, so recall for one user never sees another user's pages.
Credentials come from .env (never hard-code them).
"""
try:  # use the OS trust store (needed behind corporate SSL inspection)
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

import argparse
import asyncio
import json
import os
import re

import cognee
from dotenv import load_dotenv
from scalekit import ScalekitClient
from scalekit.common.exceptions import ScalekitServerException

load_dotenv()

NOTION_CONNECTION = os.getenv("NOTION_CONNECTION_NAME", "notion")


def get_actions():
    client = ScalekitClient(
        env_url=os.environ["SCALEKIT_ENVIRONMENT_URL"],
        client_id=os.environ["SCALEKIT_CLIENT_ID"],
        client_secret=os.environ["SCALEKIT_CLIENT_SECRET"],
    )
    return client.actions


def ensure_active(actions, connection: str, identifier: str):
    account = actions.get_or_create_connected_account(
        connection_name=connection, identifier=identifier
    ).connected_account
    if account.status != "ACTIVE":
        link = actions.get_authorization_link(
            connection_name=connection, identifier=identifier
        ).link
        print(f"[{connection}] {identifier} not authorized. Open:\n{link}")
        input("Press Enter after approving...")
        account = actions.get_connected_account_details(
            connection_name=connection, identifier=identifier
        ).connected_account
        if account.status != "ACTIVE":
            raise SystemExit(f"{connection} account is {account.status}")
    return account


def run_tool(actions, account, name: str, tool_input: dict):
    try:
        return actions.execute_tool(
            tool_name=name,
            tool_input=tool_input,
            connected_account_id=account.id,
        ).data
    except ScalekitServerException as e:
        raise SystemExit(f"{name} failed: {e.error_code} {e.message}")


def find_pages(data) -> list[dict]:
    """Search results shape can vary; look for a list of page-like dicts."""
    if isinstance(data, dict):
        for key in ("results", "pages", "items", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    if isinstance(data, list):
        return data
    return []


def page_title(page: dict) -> str:
    if page.get("title"):
        return str(page["title"])
    props = page.get("properties") or {}
    for prop in props.values():
        if isinstance(prop, dict) and prop.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in prop.get("title", [])) or "untitled"
    return "untitled"


def page_text(data) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ("markdown", "content", "text"):
            if isinstance(data.get(key), str):
                return data[key]
    return json.dumps(data, ensure_ascii=False)


def try_tool(actions, account, name: str, tool_input: dict):
    """Like run_tool but returns (ok, data_or_error) instead of exiting."""
    try:
        return True, actions.execute_tool(
            tool_name=name, tool_input=tool_input, connected_account_id=account.id
        ).data
    except Exception as e:  # noqa: BLE001 - we want to try the next variant
        return False, f"{type(e).__name__}: {e}"


def flatten_blocks(data) -> str:
    """Collect every plain_text / text content found anywhere in a block tree."""
    out: list[str] = []

    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get("plain_text"), str):
                out.append(x["plain_text"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(data)
    return "\n".join(s for s in out if s.strip())


def fetch_page_text(actions, account, page_id: str) -> str:
    """Try several tool/param variants until one returns text."""
    attempts = [
        ("notion_page_markdown_get", {"page_id": page_id}),
        ("notion_page_markdown_get", {"id": page_id}),
        ("notion_page_content_get", {"block_id": page_id}),
        ("notion_page_content_get", {"page_id": page_id}),
    ]
    errors = []
    for name, tool_input in attempts:
        ok, data = try_tool(actions, account, name, tool_input)
        if ok:
            text = page_text(data) if name.endswith("markdown_get") else flatten_blocks(data)
            if text.strip():
                return text
            errors.append(f"{name} {list(tool_input)}: empty")
        else:
            errors.append(f"{name} {list(tool_input)}: {data[:160]}")
    print("  all variants failed:\n    " + "\n    ".join(errors))
    return ""


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True, help="Scalekit identifier (e.g. email)")
    ap.add_argument("--limit", type=int, default=100, help="Max pages to fetch in total")
    ap.add_argument("--query", default="", help="Notion search text (server-side filter)")
    ap.add_argument(
        "--include",
        nargs="+",
        default=[],
        help="Only ingest pages whose title contains one of these words (case-insensitive)",
    )
    ap.add_argument("--github", default="", help="owner/repo whose issues and PRs to ingest")
    ap.add_argument("--dry-run", action="store_true", help="List pages, ingest nothing")
    args = ap.parse_args()

    actions = get_actions()
    account = ensure_active(actions, NOTION_CONNECTION, args.user)
    local = args.user.split("@")[0]
    dataset = re.sub(r"[^A-Za-z0-9_-]", "_", local) + "-brain"  # no dots/spaces allowed

    # notion_page_search defaults to 10 results per call: paginate with start_cursor.
    pages: list[dict] = []
    cursor = None
    while len(pages) < args.limit:
        tool_input = {"page_size": min(100, args.limit - len(pages))}
        if args.query:
            tool_input["query"] = args.query
        if cursor:
            tool_input["start_cursor"] = cursor
        found = run_tool(actions, account, "notion_page_search", tool_input)
        batch = find_pages(found)
        pages.extend(batch)
        cursor = None
        if isinstance(found, dict):
            cursor = found.get("next_cursor") or found.get("next_page_token")
        if not batch or not cursor:
            break
    print(f"{args.user}: {len(pages)} Notion pages visible -> dataset '{dataset}'")

    for page in pages:
        page_id = page.get("id")
        title = page_title(page)
        if not page_id:
            continue
        if args.include and not any(w.lower() in title.lower() for w in args.include):
            print(f"  skipped: {title}")
            continue
        if args.dry_run:
            print(f"  would ingest: {title}")
            continue
        text = fetch_page_text(actions, account, page_id)
        # Drop embedded child-page links: a permitted page can link to a page the
        # user may not see, which would leak its title into their graph.
        text = re.sub(r"<page\b[^>]*>.*?</page>", "", text, flags=re.S)
        if not text.strip():
            print(f"  skipped (no text): {title}")
            continue
        doc =f"# {title}\n(source: notion, page_id: {page_id})\n\n{text}"
        await cognee.remember(
            doc,
            dataset_name=dataset,
            node_set=["source:notion", f"page:{title[:40]}"],
        )
        print(f"  remembered: {title}")

    if args.github:
        gh_conn = os.getenv("GITHUB_CONNECTION_NAME", "github-connect")
        ensure_active(actions, gh_conn, args.user)
        resp = actions.request(
            connection_name=gh_conn,
            identifier=args.user,
            method="GET",
            path=f"/repos/{args.github}/issues",
            query_params={"state": "all", "per_page": "100"},
        )
        if resp.status_code != 200:
            raise SystemExit(f"GitHub issues fetch failed: {resp.status_code} {resp.text[:200]}")
        issues = resp.json()
        print(f"{args.user}: {len(issues)} GitHub issues/PRs in {args.github}")
        for it in issues:
            kind = "PR" if it.get("pull_request") else "issue"
            title = it.get("title", "")
            if args.dry_run:
                print(f"  would ingest {kind} #{it['number']}: {title}")
                continue
            doc = (
                f"# GitHub {kind} #{it['number']}: {title}\n"
                f"(source: github, repo: {args.github}, state: {it.get('state')}, "
                f"author: {(it.get('user') or {}).get('login')})\n\n{it.get('body') or ''}"
            )
            await cognee.remember(
                doc,
                dataset_name=dataset,
                node_set=["source:github", f"repo:{args.github}"],
            )
            print(f"  remembered {kind} #{it['number']}: {title}")

    print("Done. Now recall with the same dataset, e.g.:")
    print(f"  cognee.recall('Why did we choose Postgres?', datasets=['{dataset}'])")


if __name__ == "__main__":
    asyncio.run(main())
