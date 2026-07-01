#!/usr/bin/env python3
"""
Validate a CDH skill directory for structural correctness.

Usage:
    python scripts/validate_skill.py .agents/skills/cdh-metadata
    python scripts/validate_skill.py .agents/skills/  # validates all skills

Exit codes:
    0  all checks passed (may have warnings)
    1  one or more errors found
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ── ANSI colours ──────────────────────────────────────────────────────────────
RED    = "\033[31m"
YELLOW = "\033[33m"
GREEN  = "\033[32m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

_use_colour = sys.stdout.isatty() and sys.platform != "win32"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore

def _c(code: str, text: str) -> str:
    return f"{code}{text}{RESET}" if _use_colour else text


# ── Issue dataclass ───────────────────────────────────────────────────────────

@dataclass
class Issue:
    level:   str   # "error" | "warning"
    message: str   # what is wrong
    hint:    str   # how to fix it (one sentence, actionable)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_frontmatter(content: str) -> tuple[dict, str, list[Issue]]:
    """Return (frontmatter_dict, body, issues)."""
    issues: list[Issue] = []

    if not content.startswith("---"):
        return {}, content, [Issue(
            "error",
            "SKILL.md must start with YAML frontmatter",
            "Add `---` at the very first line, followed by `name:` and `description:` fields, "
            "then close with another `---`."
        )]

    try:
        end = content.index("---", 3)
    except ValueError:
        return {}, content, [Issue(
            "error",
            "YAML frontmatter block is not closed",
            "Add a closing `---` line after your `name:` and `description:` fields."
        )]

    fm_str = content[3:end].strip()
    body   = content[end + 3:].strip()

    if HAS_YAML:
        try:
            fm = yaml.safe_load(fm_str) or {}
        except yaml.YAMLError as exc:
            issues.append(Issue(
                "error",
                f"Invalid YAML frontmatter: {exc}",
                "Fix the YAML syntax error above. Common causes: missing quotes around special "
                "characters, incorrect indentation, or tabs instead of spaces."
            ))
            fm = {}
    else:
        fm = {}
        for line in fm_str.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip().strip('"').strip("'")

    return fm, body, issues


_LOCAL_PATH = re.compile(
    r'(?<![`\w])'
    r'(?:[A-Za-z]:\\|/home/|/Users/|/root/|C:/|D:/)'
)

_REF_LINK = re.compile(r'`((?:references|assets|scripts)/[^`\s]+)`')


# ── Core validator ────────────────────────────────────────────────────────────

def validate_skill(skill_dir: Path) -> list[Issue]:
    """Return a list of Issues (errors and warnings) for a single skill directory."""
    issues: list[Issue] = []

    # ── 1. SKILL.md presence ──────────────────────────────────────────────────
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        issues.append(Issue(
            "error",
            "SKILL.md not found",
            f"Create a file at `.agents/skills/{skill_dir.name}/SKILL.md` with YAML frontmatter "
            "(`name` and `description`) followed by the skill instructions in Markdown."
        ))
        return issues

    content = skill_md.read_text(encoding="utf-8")
    lines   = content.splitlines()

    # ── 2. Line count ─────────────────────────────────────────────────────────
    if len(lines) > 600:
        issues.append(Issue(
            "warning",
            f"SKILL.md is {len(lines)} lines (recommended maximum: 500)",
            "Move large reference material to a `references/` subdirectory and link to it "
            "from SKILL.md with a sentence like \"Read `references/my-doc.md` for details.\""
        ))

    # ── 3. Frontmatter ────────────────────────────────────────────────────────
    fm, body, fm_issues = _parse_frontmatter(content)
    issues.extend(fm_issues)

    name = fm.get("name", "").strip()
    desc = fm.get("description", "").strip()

    if not name:
        issues.append(Issue(
            "error",
            "frontmatter: 'name' field is missing",
            f"Add `name: {skill_dir.name}` to the YAML frontmatter block."
        ))
    elif name != skill_dir.name:
        issues.append(Issue(
            "error",
            f"frontmatter name '{name}' does not match directory name '{skill_dir.name}'",
            f"Change the `name:` field in frontmatter to `{skill_dir.name}` (must be identical "
            "to the directory name, case-sensitive)."
        ))

    if not desc:
        issues.append(Issue(
            "error",
            "frontmatter: 'description' field is missing",
            "Add a `description:` field explaining what the skill does and when an agent should "
            "invoke it. Include common trigger phrases users are likely to type."
        ))
    else:
        if len(desc) < 60:
            issues.append(Issue(
                "warning",
                f"description is very short ({len(desc)} chars)",
                "Expand the description to include trigger phrases — the words or sentences a "
                "user might type that should activate this skill (e.g. 'Use this skill when the "
                "user asks to download climate data...')."
            ))
        if len(desc) > 3000:
            issues.append(Issue(
                "warning",
                f"description is very long ({len(desc)} chars)",
                "Shorten the description to ~200 words. Only the first ~100 words are shown in "
                "the skill list; move detailed instructions into the SKILL.md body."
            ))

    # ── 4. Referenced bundled files must exist ────────────────────────────────
    for match in _REF_LINK.finditer(body):
        ref_rel  = match.group(1)
        ref_path = skill_dir / ref_rel
        if not ref_path.exists():
            issues.append(Issue(
                "error",
                f"referenced file not found: {ref_rel}",
                f"Either create the file at `.agents/skills/{skill_dir.name}/{ref_rel}` "
                f"or remove the reference to `{ref_rel}` from SKILL.md."
            ))

    # ── 5. No local filesystem paths (portability) ────────────────────────────
    for i, line in enumerate(body.splitlines(), start=1):
        if _LOCAL_PATH.search(line):
            issues.append(Issue(
                "warning",
                f"possible local filesystem path on line {i}",
                "Replace absolute local paths (e.g. C:\\Users\\..., /home/...) with relative "
                "paths or URLs so the skill works on any machine. If it's an example in a code "
                "block, add a comment like `# replace with your path`."
            ))
            break

    # ── 6. evals/evals.json ───────────────────────────────────────────────────
    evals_path = skill_dir / "evals" / "evals.json"
    if not evals_path.exists():
        issues.append(Issue(
            "warning",
            "evals/evals.json not found",
            f"Create `.agents/skills/{skill_dir.name}/evals/evals.json` with at least 2 "
            "realistic test prompts. See CONTRIBUTING.md for the required JSON structure."
        ))
    else:
        try:
            evals_doc = json.loads(evals_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(Issue(
                "error",
                f"evals/evals.json is not valid JSON: {exc}",
                "Fix the JSON syntax error. Use a validator such as jsonlint.com or run "
                "`python -m json.tool evals/evals.json` locally to find the problem."
            ))
            evals_doc = {}

        if evals_doc:
            if evals_doc.get("skill_name", "").strip() != skill_dir.name:
                issues.append(Issue(
                    "warning",
                    f"evals.json skill_name '{evals_doc.get('skill_name')}' does not match "
                    f"directory name '{skill_dir.name}'",
                    f"Set `\"skill_name\": \"{skill_dir.name}\"` at the top of evals.json."
                ))

            evals_list = evals_doc.get("evals", [])
            if not isinstance(evals_list, list) or len(evals_list) == 0:
                issues.append(Issue(
                    "error",
                    "evals.json: 'evals' must be a non-empty array",
                    "Add at least one object to the `evals` array, each with an `id` (integer) "
                    "and a `prompt` (string). See CONTRIBUTING.md for a complete example."
                ))
            else:
                if len(evals_list) < 2:
                    issues.append(Issue(
                        "warning",
                        f"only {len(evals_list)} eval defined (recommended: at least 2)",
                        "Add a second eval that tests a different file type or scenario. "
                        "More diverse evals give reviewers better confidence in the skill."
                    ))
                ids_seen: set = set()
                for idx, ev in enumerate(evals_list):
                    prefix = f"evals[{idx}]"
                    if not ev.get("prompt"):
                        issues.append(Issue(
                            "error",
                            f"{prefix}: 'prompt' field is missing",
                            f"Add a `\"prompt\"` string to evals[{idx}] — write it as a realistic "
                            "user request, not a description of what to test."
                        ))
                    ev_id = ev.get("id")
                    if ev_id is None:
                        issues.append(Issue(
                            "error",
                            f"{prefix}: 'id' field is missing",
                            f"Add `\"id\": {idx + 1}` to evals[{idx}]. IDs must be unique integers."
                        ))
                    elif ev_id in ids_seen:
                        issues.append(Issue(
                            "error",
                            f"{prefix}: duplicate id '{ev_id}'",
                            f"Change the `id` of evals[{idx}] to a unique integer not used by "
                            "any other eval in the file."
                        ))
                    else:
                        ids_seen.add(ev_id)

    return issues


# ── Output modes ──────────────────────────────────────────────────────────────

def _collect_skill_dirs(paths: list[Path]) -> list[Path]:
    dirs: list[Path] = []
    for p in paths:
        if (p / "SKILL.md").exists():
            dirs.append(p)
        else:
            dirs.extend(
                d for d in sorted(p.iterdir())
                if d.is_dir() and not d.name.startswith(".")
            )
    return dirs


def run(paths: list[Path]) -> int:
    """Human-readable terminal output."""
    skill_dirs = _collect_skill_dirs(paths)
    if not skill_dirs:
        print(_c(YELLOW, "No skill directories found."))
        return 0

    total_errors = 0
    for skill_dir in skill_dirs:
        issues = validate_skill(skill_dir)
        errs   = [i for i in issues if i.level == "error"]
        warns  = [i for i in issues if i.level == "warning"]
        total_errors += len(errs)

        status = _c(GREEN, "✓ PASS") if not errs else _c(RED, "✗ FAIL")
        print(f"\n{BOLD}{skill_dir.name}{RESET}  {status}")

        for w in warns:
            print(f"  {_c(YELLOW, 'warn')}  {w.message}")
            print(f"         → {w.hint}")
        for e in errs:
            print(f"  {_c(RED, 'error')} {e.message}")
            print(f"         → {e.hint}")

    print()
    if total_errors:
        print(_c(RED, f"{total_errors} error(s) found — submission blocked."))
        return 1
    print(_c(GREEN, "All skills passed validation."))
    return 0


def run_with_annotations(paths: list[Path]) -> int:
    """Emit GitHub Actions ::error:: / ::warning:: annotations."""
    skill_dirs   = _collect_skill_dirs(paths)
    total_errors = 0
    for skill_dir in skill_dirs:
        issues = validate_skill(skill_dir)
        total_errors += sum(1 for i in issues if i.level == "error")
        skill_md_rel = str(skill_dir / "SKILL.md")
        for issue in issues:
            print(
                f"::{issue.level} file={skill_md_rel}::"
                f"{skill_dir.name}: {issue.message}. Fix: {issue.hint}"
            )
    return 1 if total_errors else 0


def run_as_markdown(paths: list[Path]) -> int:
    """
    Print a Markdown PR comment that tells the author exactly what to fix.
    Errors are grouped separately from warnings, each with an actionable hint.
    """
    skill_dirs   = _collect_skill_dirs(paths)
    total_errors = 0
    sections:  list[str] = []

    for skill_dir in skill_dirs:
        issues = validate_skill(skill_dir)
        errs   = [i for i in issues if i.level == "error"]
        warns  = [i for i in issues if i.level == "warning"]
        total_errors += len(errs)

        icon   = "✅" if not errs else "❌"
        parts: list[str] = [f"### {icon} `{skill_dir.name}`"]

        if errs:
            parts.append(
                "\n**Errors — must fix before this PR can be merged:**\n"
            )
            for i, e in enumerate(errs, 1):
                parts.append(f"{i}. ❌ **{e.message}**  \n   > {e.hint}\n")

        if warns:
            parts.append(
                "\n<details><summary>⚠️ Warnings (do not block merge)</summary>\n"
            )
            for w in warns:
                parts.append(f"- **{w.message}**  \n  {w.hint}")
            parts.append("\n</details>")

        if not errs and not warns:
            parts.append("\n_No issues found._")

        sections.append("\n".join(parts))

    # ── Overall verdict ───────────────────────────────────────────────────────
    if total_errors:
        verdict = (
            f"## ❌ Skill Validation — {total_errors} error(s) to fix\n\n"
            "The automated check found issues that must be resolved before a reviewer can "
            "approve this PR. Each error below includes a description and an exact fix. "
            "Push a new commit to re-run the check.\n\n"
            "> See [CONTRIBUTING.md](../blob/main/CONTRIBUTING.md) for the full skill spec."
        )
    else:
        verdict = (
            "## ✅ Skill Validation — all checks passed\n\n"
            "No structural errors were found. This PR is ready for human review. "
            "A CDH maintainer will check the skill quality and approve or request changes.\n\n"
            "> See [CONTRIBUTING.md](../blob/main/CONTRIBUTING.md) for review criteria."
        )

    print(verdict + "\n\n---\n\n" + "\n\n---\n\n".join(sections))
    return 1 if total_errors else 0


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate CDH skill directories")
    parser.add_argument("paths", nargs="+", type=Path, help="Skill dir(s) or skills root")
    parser.add_argument("--annotations", action="store_true",
                        help="Emit GitHub Actions ::error:: / ::warning:: annotations")
    parser.add_argument("-o", "--output", choices=["text", "markdown"],
                        default="text", help="Output format (default: text)")
    args = parser.parse_args()

    if args.annotations:
        sys.exit(run_with_annotations(args.paths))
    elif args.output == "markdown":
        sys.exit(run_as_markdown(args.paths))
    else:
        sys.exit(run(args.paths))
