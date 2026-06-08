---
title: OpenAI Codex
description: Set up OpenAI Codex with the CDH skills system prompt for climate data workflows.
sidebar:
  order: 3
---

**Audience:** Users running OpenAI Codex (or similar agents without a `read_url_content`
tool). No programming experience required after the one-time setup.

Unlike Antigravity, Codex may not automatically follow internal cross-references in skill
files, so all five URLs are provided upfront in the system prompt.

## Prerequisites

| Requirement | How to get it |
|-------------|---------------|
| OpenAI Codex access | [platform.openai.com](https://platform.openai.com) |
| Python 3.10+ with `aggeodata` | See below |
| Internet access | Required to fetch skill files |

```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git" s3fs zarr
```

## Step 0 — System prompt

Each skill page includes the system prompt to paste into Codex. Find it in the **Codex** tab of the skill you want to use — for example, [GCF Pipeline → Codex](../skills/gcf-pipeline/).

## Antigravity vs Codex

| | Antigravity | Codex |
|--|-------------|-------|
| URL fetch tool | `read_url_content` (built-in) | `curl` / `wget` / web tool |
| URLs in system prompt | 5 (all skills upfront) | 5 (all skills upfront) |
| Sub-skill loading | Pre-fetched at task start | Pre-fetched at task start |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Codex cannot access URLs | Enable internet access in Codex settings |
| `ModuleNotFoundError: aggeodata` | Run the pip install command above |
| Agent invents code instead of following the skill | Verify the system prompt was saved and the fetch succeeded |
