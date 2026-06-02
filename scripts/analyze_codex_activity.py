#!/usr/bin/env python3
"""Generate aggregate, privacy-safe Codex activity metrics.

Environment variables:
  CODEX_HOME: Codex data directory. Defaults to ~/.codex.
  CHATGPT_CONVERSATIONS_DIR: optional directory of local ChatGPT .data blobs.
  OUTPUT_PATH: output JSON path. Defaults to data/profile_analysis.json.

This script only emits aggregate counts, keyword category scores, and
metadata-derived profile signals. It does not copy raw prompts, project names,
repository paths, or file contents into the output.
"""

import json
import os
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
STATE_DB = CODEX_HOME / "state_5.sqlite"
SESSION_INDEX = CODEX_HOME / "session_index.jsonl"
HISTORY = CODEX_HOME / "history.jsonl"
SESSIONS_DIR = CODEX_HOME / "sessions"
CHATGPT_CONV_DIR = os.environ.get("CHATGPT_CONVERSATIONS_DIR")
OUTPUT_PATH = Path(os.environ.get("OUTPUT_PATH", "data/profile_analysis.json"))


CATEGORY_KEYWORDS = {
    "Product engineering": [
        "implement",
        "build",
        "feature",
        "scaffold",
        "component",
        "api",
        "backend",
        "frontend",
        "app",
        "mobile",
        "expo",
        "react",
        "swift",
        "typescript",
    ],
    "Debugging and repair": [
        "fix",
        "debug",
        "failure",
        "broken",
        "error",
        "bug",
        "failing",
        "triage",
        "investigate",
    ],
    "Testing and verification": [
        "test",
        "e2e",
        "playwright",
        "verify",
        "validation",
        "lint",
        "ci",
        "coverage",
    ],
    "Architecture and planning": [
        "plan",
        "prd",
        "spec",
        "architecture",
        "review",
        "phase",
        "roadmap",
        "design",
    ],
    "AI and agent systems": [
        "agent",
        "llm",
        "openai",
        "mcp",
        "chat",
        "rag",
        "prompt",
        "embedding",
        "eval",
    ],
    "Data and infrastructure": [
        "database",
        "postgres",
        "supabase",
        "migration",
        "schema",
        "s3",
        "worker",
        "queue",
        "deploy",
        "cloudflare",
        "vercel",
    ],
    "Content and publishing": [
        "docs",
        "documentation",
        "website",
        "publish",
        "profile",
        "landing",
        "copy",
        "seo",
    ],
}


ACTION_KEYWORDS = {
    "implementation": ["implement", "build", "create", "add", "wire", "scaffold"],
    "debugging": ["fix", "debug", "investigate", "triage", "resolve"],
    "review": ["review", "audit", "inspect", "analyze"],
    "verification": ["test", "verify", "validate", "run", "check"],
    "publishing": ["publish", "deploy", "release", "host"],
    "planning": ["plan", "design", "spec", "prd"],
}


AGENT_STACK_SIGNALS = [
    {
        "name": "Superpowers",
        "group": "Workflow layer",
        "terms": [
            "superpowers",
            "test-driven-development",
            "verification-before-completion",
            "systematic-debugging",
            "requesting-code-review",
            "receiving-code-review",
        ],
    },
    {
        "name": "Supabase",
        "group": "Data and backend",
        "terms": ["supabase", "postgres", "migration", "schema"],
    },
    {
        "name": "Cloudflare",
        "group": "Cloud and deploy",
        "terms": ["cloudflare", "wrangler", "workers", "durable objects"],
    },
    {
        "name": "Vercel",
        "group": "Cloud and deploy",
        "terms": ["vercel", "nextjs", "next.js"],
    },
    {
        "name": "GitHub",
        "group": "Repository and CI",
        "terms": ["github", "gh", "pull request", "ci"],
    },
    {
        "name": "Expo",
        "group": "Mobile and native",
        "terms": ["expo", "react native", "mobile"],
    },
    {
        "name": "Browser / Playwright",
        "group": "Browser QA",
        "terms": ["browser", "playwright", "screenshot", "e2e"],
    },
]


WORKBENCH_SIGNALS = [
    {"name": "Codex", "group": "Agent interface", "terms": ["codex"]},
    {"name": "ChatGPT", "group": "Agent interface", "terms": ["chatgpt", "chat gpt"]},
    {"name": "React", "group": "Frontend", "terms": ["react", "react native"]},
    {"name": "TypeScript", "group": "Language", "terms": ["typescript", "ts", "tsx"]},
    {"name": "Expo", "group": "Mobile", "terms": ["expo"]},
    {"name": "Swift", "group": "Native", "terms": ["swift", "swiftui"]},
    {"name": "Supabase / Postgres", "group": "Data", "terms": ["supabase", "postgres", "postgresql"]},
    {"name": "Playwright", "group": "Verification", "terms": ["playwright", "e2e"]},
    {"name": "Cloudflare", "group": "Cloud", "terms": ["cloudflare", "wrangler", "workers"]},
    {"name": "Vercel", "group": "Cloud", "terms": ["vercel", "next.js", "nextjs"]},
    {"name": "GitHub", "group": "Repository", "terms": ["github", "pull request", "ci"]},
    {"name": "here.now", "group": "Publishing", "terms": ["here.now", "here now"]},
]


LANGUAGE_SIGNALS = [
    {
        "name": "TypeScript / JavaScript",
        "group": "Primary",
        "terms": ["typescript", "javascript", "react", "tsx", "jsx", "node"],
        "summary": "Frontend, full-stack app work, automation scripts, browser verification, and UI publishing workflows.",
    },
    {
        "name": "Python",
        "group": "Used",
        "terms": ["python", "py", "pytest"],
        "summary": "Data processing, local analysis scripts, workers, automation, and support tooling around AI-assisted workflows.",
    },
    {
        "name": "Swift",
        "group": "Used",
        "terms": ["swift", "swiftui", "xcode"],
        "summary": "Apple-platform work and native app surfaces where local tooling and simulator-oriented workflows are relevant.",
    },
]


OPERATING_STYLE_SIGNALS = [
    {
        "name": "Spec the work",
        "group": "Planning",
        "terms": ["plan", "spec", "prd", "requirements", "architecture", "scope"],
        "summary": "Turn rough ideas into scoped plans, explicit constraints, and concrete acceptance checks before implementation starts.",
    },
    {
        "name": "Build in loops",
        "group": "Implementation",
        "terms": ["implement", "build", "iterate", "loop", "review", "debug", "refactor"],
        "summary": "Use agents for implementation, review, debugging, documentation, and test feedback instead of one-shot generation.",
    },
    {
        "name": "Verify the result",
        "group": "Verification",
        "terms": ["verify", "test", "playwright", "screenshot", "lint", "ci", "coverage", "validation"],
        "summary": "Prefer runnable checks, browser inspection, CI-style validation, and direct artifact review over confidence alone.",
    },
]


CURRENT_DIRECTION_SIGNALS = [
    {
        "name": "Agentic development systems",
        "group": "Exploring",
        "terms": ["agent", "agents", "superpowers", "workflow", "mcp", "codex", "multi-session"],
        "summary": "Workflows where agents help plan, implement, inspect, and maintain software across multiple sessions.",
    },
    {
        "name": "AI-native product interfaces",
        "group": "Building",
        "terms": ["ai-native", "ai", "llm", "chat", "interface", "product", "app"],
        "summary": "Product experiences that use AI as part of the core workflow, not a decorative layer added after the fact.",
    },
    {
        "name": "Useful public artifacts",
        "group": "Sharing",
        "terms": ["publish", "website", "profile", "docs", "documentation", "demo", "landing"],
        "summary": "Profiles, pages, prototypes, docs, and demos that can be safely published without leaking private project context.",
    },
]


def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def read_jsonl(path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def text_from_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("input_text") or ""))
        return "\n".join(parts)
    return ""


def keyword_score(text, groups):
    low = text.lower()
    scores = {}
    for name, words in groups.items():
        score = sum(len(re.findall(r"\b" + re.escape(word) + r"\b", low)) for word in words)
        if score:
            scores[name] = score
    return scores


def count_signal_mentions(corpus, signals):
    joined = "\n".join(corpus).lower()
    result = []
    for signal in signals:
        score = 0
        matched_terms = []
        for term in signal["terms"]:
            term_score = len(re.findall(r"\b" + re.escape(term.lower()) + r"\b", joined))
            if term_score:
                score += term_score
                matched_terms.append(term)
        if score:
            result.append(
                {
                    "name": signal["name"],
                    "group": signal["group"],
                    "score": score,
                    "matched_terms": matched_terms,
                    **({"summary": signal["summary"]} if signal.get("summary") else {}),
                }
            )
    return sorted(result, key=lambda item: item["score"], reverse=True)


def signal_names(items, limit=3):
    return [item["name"] for item in items[:limit]]


def unique_nonempty(values):
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def generate_public_positioning(category_scores, operating_style, agent_stack, current_direction):
    top_categories = [name for name, _score in category_scores.most_common(3)]
    top_operating = signal_names(operating_style)
    top_agent_stack = signal_names(agent_stack)
    top_direction = signal_names(current_direction)

    candidates = []
    if "Agentic development systems" in top_direction:
        candidates.append("Software builder using agents to plan, ship, and verify.")
    if "Spec the work" in top_operating and "Verify the result" in top_operating:
        candidates.append("AI-assisted builder with a spec-driven, verification-heavy workflow.")
    if top_agent_stack:
        candidates.append(f"Software builder turning {top_agent_stack[0]} workflows into working products.")
    if top_categories:
        candidates.append(f"Product builder strongest in {top_categories[0].lower()} and agent-assisted delivery.")
    if "Useful public artifacts" in top_direction:
        candidates.append("Builder turning agent-assisted work into useful public artifacts.")
    candidates.append("AI-assisted software builder operating with agents in the loop.")

    candidates = unique_nonempty(candidates)
    return {
        "source": "metadata-derived aggregate signals",
        "approval_required": True,
        "selected_headline": candidates[0],
        "headline_candidates": candidates[:5],
        "source_signals": {
            "work_mix": top_categories,
            "operating_style": top_operating,
            "agent_stack": top_agent_stack,
            "current_direction": top_direction,
        },
        "notes": [
            "Generated from aggregate signal names and scores, not raw prompts.",
            "The selected headline is a default candidate and should be approved before publishing.",
            "Identity, location, and contact details remain user-provided.",
        ],
    }


def read_thread_db():
    result = {
        "count": 0,
        "months": Counter(),
        "active_days": set(),
        "distinct_workspaces": set(),
        "texts": [],
    }
    if not STATE_DB.exists():
        return result

    conn = sqlite3.connect(STATE_DB)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            select created_at, title, cwd, first_user_message
            from threads
            """
        ).fetchall()
    finally:
        conn.close()

    result["count"] = len(rows)
    for row in rows:
        if row["created_at"]:
            dt = datetime.fromtimestamp(row["created_at"], tz=timezone.utc)
            result["months"].update([dt.strftime("%Y-%m")])
            result["active_days"].add(dt.strftime("%Y-%m-%d"))
        if row["cwd"]:
            result["distinct_workspaces"].add(row["cwd"])
        if row["title"]:
            result["texts"].append(row["title"])
        if row["first_user_message"]:
            result["texts"].append(row["first_user_message"])
    return result


def main():
    thread_db = read_thread_db()
    session_index_count = 0
    history_count = 0
    prompt_texts = []
    observed_dates = []

    for row in read_jsonl(SESSION_INDEX):
        session_index_count += 1
        prompt_texts.append(row.get("thread_name", ""))
        dt = parse_iso(row.get("updated_at", ""))
        if dt:
            observed_dates.append(dt)

    for row in read_jsonl(HISTORY):
        history_count += 1
        prompt_texts.append(row.get("text", ""))
        if row.get("ts"):
            observed_dates.append(datetime.fromtimestamp(row["ts"], tz=timezone.utc))

    session_files = list(SESSIONS_DIR.glob("**/*.jsonl")) if SESSIONS_DIR.exists() else []
    rollout_user_events = 0
    rollout_assistant_events = 0
    tool_events = 0
    first_user_texts = []
    tool_signal_texts = []

    for path in session_files:
        saw_first_user = False
        for row in read_jsonl(path):
            ts = parse_iso(row.get("timestamp", ""))
            if ts:
                observed_dates.append(ts)
            payload = row.get("payload") or {}
            if row.get("type") != "response_item":
                continue
            role = payload.get("role")
            ptype = payload.get("type")
            if role == "user":
                rollout_user_events += 1
                if not saw_first_user:
                    text = text_from_content(payload.get("content"))
                    if text:
                        first_user_texts.append(text)
                    saw_first_user = True
            elif role == "assistant":
                rollout_assistant_events += 1
            elif ptype in {"function_call", "tool_call", "function_call_output", "tool_call_output"}:
                tool_events += 1
                name = payload.get("name") or payload.get("tool_name") or payload.get("server")
                if name:
                    tool_signal_texts.append(str(name).replace("_", " ").replace("-", " "))

    corpus = prompt_texts + thread_db["texts"] + first_user_texts + tool_signal_texts
    category_scores = Counter()
    action_scores = Counter()
    for text in corpus:
        category_scores.update(keyword_score(text, CATEGORY_KEYWORDS))
        action_scores.update(keyword_score(text, ACTION_KEYWORDS))
    agent_stack = count_signal_mentions(corpus, AGENT_STACK_SIGNALS)
    workbench_tools = count_signal_mentions(corpus, WORKBENCH_SIGNALS)
    languages = count_signal_mentions(corpus, LANGUAGE_SIGNALS)
    operating_style = count_signal_mentions(corpus, OPERATING_STYLE_SIGNALS)
    current_direction = count_signal_mentions(corpus, CURRENT_DIRECTION_SIGNALS)
    public_positioning = generate_public_positioning(
        category_scores,
        operating_style,
        agent_stack,
        current_direction,
    )

    active_days = set(thread_db["active_days"])
    active_days.update(dt.strftime("%Y-%m-%d") for dt in observed_dates)

    chatgpt_blob_count = 0
    if CHATGPT_CONV_DIR:
        chatgpt_path = Path(CHATGPT_CONV_DIR)
        if chatgpt_path.exists():
            chatgpt_blob_count = len(list(chatgpt_path.glob("*.data")))

    output = {
        "sources_used": {
            "codex_session_index_records": session_index_count,
            "codex_history_prompts": history_count,
            "codex_session_files": len(session_files),
            "codex_state_threads": thread_db["count"],
            "chatgpt_local_binary_conversation_blobs_count_only": chatgpt_blob_count,
        },
        "date_range_utc": {
            "first_seen": min(observed_dates).isoformat() if observed_dates else None,
            "last_seen": max(observed_dates).isoformat() if observed_dates else None,
            "active_days": len(active_days),
        },
        "volume": {
            "threads_or_sessions_indexed": max(thread_db["count"], session_index_count),
            "session_files": len(session_files),
            "rollout_user_events_seen": rollout_user_events,
            "rollout_assistant_events_seen": rollout_assistant_events,
            "tool_events_seen_in_rollouts": tool_events,
            "distinct_workspaces": len(thread_db["distinct_workspaces"]),
            "chatgpt_conversations_count_only": chatgpt_blob_count,
        },
        "cadence": {
            "by_month": dict(sorted(thread_db["months"].items())),
        },
        "workbench_tools": workbench_tools,
        "public_positioning": public_positioning,
        "agent_stack": agent_stack,
        "agent_stack_notes": [
            "Conservative keyword scan over public-safe metadata text.",
            "Structured event extraction from tool namespaces and skill references is the preferred next step when records expose it safely.",
            "Scores are directional, not exhaustive proof of every plugin or skill loaded in a session.",
        ],
        "languages": languages,
        "operating_style": operating_style,
        "current_direction": current_direction,
        "derived_profile_notes": [
            "Workbench, languages, operating style, and current direction are derived from metadata keyword and tool-signal scores.",
            "Identity, location, and contact details remain user-provided or template-provided.",
            "Public copy is summarized from aggregate signals and should be reviewed before publishing.",
        ],
        "work_mix": category_scores.most_common(),
        "action_mix": action_scores.most_common(),
        "privacy_notes": [
            "No raw project names, repository paths, prompts, titles, or file contents are included.",
            "ChatGPT conversation blobs are counted only when CHATGPT_CONVERSATIONS_DIR is provided.",
            "Counts are approximate because some sessions can be indexed in more than one Codex store.",
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
