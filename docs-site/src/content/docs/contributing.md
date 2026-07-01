---
title: Contributing a skill
description: How to submit a new skill to the CDH Skills Hub via a GitHub pull request, including local validation and the automated review process.
sidebar:
  order: 2
---

Skills are short instruction files that guide an AI agent through a specific geospatial or
climate-data workflow. When a skill is installed, the agent reads it automatically and follows
its staged workflow instead of improvising. Skills are **agent-agnostic** — the same skill works
across any compatible runtime (Claude Code, Antigravity, OpenAI Codex, and others).

## What makes a good skill

A skill is worth submitting when it encapsulates a **repeatable, multi-step workflow** that
benefits from structured guidance — data download pipelines, format conversions, metadata
authoring, spatial processing chains. One-shot tasks (e.g. "convert a single file") don't
need a skill.

Before you start, check whether an existing skill can be extended rather than replaced.

---

## Skill structure

Every skill lives in its own directory under `.agents/skills/`:

```
.agents/skills/<skill-name>/
├── SKILL.md                  required — instructions the agent follows
├── evals/
│   └── evals.json            required — at least 2 test prompts
└── references/               optional — docs, templates, vocab files
    └── *.md
```

### SKILL.md

Must begin with YAML frontmatter:

```yaml
---
name: skill-name          # must match the directory name exactly
description: >
  One paragraph. What the skill does and when an agent should invoke it.
  Include trigger phrases users are likely to type.
---
```

The body is plain Markdown. Keep it under 500 lines. If you need large reference material,
put it in `references/` and link to it from the body.

### evals/evals.json

```json
{
  "skill_name": "skill-name",
  "evals": [
    {
      "id": 1,
      "prompt": "A realistic user prompt that should trigger this skill",
      "expected_output": "Plain-language description of what a correct response looks like"
    },
    {
      "id": 2,
      "prompt": "A second realistic prompt, different scenario or file type"
    }
  ]
}
```

Prompts should read like something a real user would type — casual language, actual file
paths or variable names, enough context to be unambiguous. Avoid toy examples.

---

## Submission process

### 1. Fork and branch

```bash
git checkout -b skill/my-skill-name
```

### 2. Create your skill directory

```
.agents/skills/my-skill-name/
├── SKILL.md
└── evals/evals.json
```

### 3. Test it locally

Run the validator to catch structural issues before pushing:

```bash
python scripts/validate_skill.py .agents/skills/my-skill-name
```

Test the skill manually at least once with a real dataset and your agent of choice before
opening a PR.

### 4. Open a pull request

Push your branch and open a PR against `main`. The PR template will appear automatically —
fill it in. GitHub Actions runs the validator and posts a report as a comment within about
30 seconds.

### 5. Address validation errors

If the check fails, fix the errors listed in the PR comment and push again. The comment
updates automatically on each push.

### 6. Human review

Once checks pass, a CDH maintainer reviews:

- Does the skill solve a real, recurring workflow?
- Are the instructions clear, agent-agnostic, and safe to follow?
- Do the evals represent realistic usage?
- Are there portability issues (local paths, hardcoded credentials, agent-specific syntax)?

### 7. Merge

After approval the PR is merged and the skill becomes available to all users and agents
connected to this repository.

---

## Writing agent-agnostic instructions

Skills must work regardless of which agent runtime executes them:

| Do | Don't |
|----|-------|
| Write instructions in the imperative: "inspect the file", "ask the user", "write the output to…" | Reference a specific agent by name (e.g. "ask Claude to…") |
| Use standard tool verbs any runtime can implement: read a file, run a script, write a file, ask a question | Rely on agent-specific features, tools, or APIs inside `SKILL.md` |

---

## Automated checks

The following checks run on every PR that touches `.agents/skills/`:

| Check | Blocks merge? |
|-------|--------------|
| `SKILL.md` exists | yes |
| Frontmatter has `name` and `description` | yes |
| `name` matches directory name | yes |
| All files referenced in `SKILL.md` exist | yes |
| `evals/evals.json` is valid JSON with ≥ 1 prompt per eval | yes |
| `evals.json` has at least 2 evals | warning only |
| `SKILL.md` is under 500 lines | warning only |
| No local filesystem paths in skill body | warning only |

Errors block the merge. Warnings are shown in the PR comment but do not prevent approval.

---

## Updating an existing skill

Open a PR that modifies files inside the existing skill directory. The same validation
and review process applies. In the PR description, explain what changed and why.

---

## Contact

Open a GitHub Discussion or reach one of the maintainers directly:

| GitHub | Role |
|--------|------|
| [@anaguilarar](https://github.com/anaguilarar) | Reviewer |
| [@bjyberg](https://github.com/bjyberg) | Reviewer |
| [@peetmate](https://github.com/peetmate) | Reviewer |
| [@dagudelo30](https://github.com/dagudelo30) | Reviewer |
