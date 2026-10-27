# Part 3 — usability test by a metadata-only agent

The script proves links and data match the record. The adversarial pass checks that authored
fields are true. Neither proves that a person can **use** the record: find the data, query it,
and read the numbers correctly. This part does, by handing the record to a sub-agent that knows
nothing else and logging every place it gets stuck.

## Why it earns its place

On `oecd-dac-crs` (first run, 2026-10-23), the schema check, the link check, the verify script
and a human reviewer all passed the record. A metadata-only agent asked about development finance
to Kenya found that the record and its example used provider `DAC` as "all donors". `DAC` covers
DAC member countries only: USD 1,544 M in 2024, against 3,652 M from all official providers
(`ALLD`). It also found that country was the finest geography, which the record never said; that
the project and climate columns were empty; and that five query dimensions were undocumented.
The score was 6/10. The human review and the agent test caught different problems: run both.

## 1. Build the task

- Take one concrete task from `cdh.usage.intended_uses`, phrased as a user would ask it.
- Add a test geography: a country the record covers, plus a sub-national unit when the record
  claims, or might be assumed to have, sub-national data (e.g. "Kenya, Homa Bay County"). A
  sub-national ask is a good probe even for national data: the agent should discover from the
  metadata that it is not possible.
- Ask for real numbers over a short period, broken down along the record's main dimensions.

## 2. Spawn the agent

Point the agent at the record by URL (raw GitHub or the catalog page) or local path, and give it
a scratch directory. Use this prompt, filling in the `<…>`:

```text
You are a first-time user of the CGIAR Climate Data Hub. Your job is to test whether a dataset's
METADATA RECORD is enough, on its own, for someone to find, download and correctly understand the
data. You are the test instrument: every time you are confused, have to guess, or hit a dead end,
that is a finding.

Record under test: <URL or path of the YAML>

Task (as a user would phrase it): "<task built from intended_uses>, for <country> / <sub-national unit>"
Answer it as far as the data allows, with real numbers, and decide whether the sub-national part
is possible.

Hard rules
- Use ONLY the record and URLs that appear inside it (data endpoints, links, docs, example scripts
  it references), plus pages those link to directly when needed. No web search, no prior knowledge
  of the provider's API, no other code from the repository that produced the record. If you rely
  on something you "just know", log it as GUESSED: the record should have told you.
- Work in <scratch dir>. Keep downloads small (one area, a few years); never pull a whole cube or
  archive. If a request looks huge, stop and log why you could not tell in advance.
- Do not modify the record.

Log as you go in log.md, one entry per thing that matters:
- Step: what you were trying to do
- What the metadata said: quote the field path (e.g. /data/0/description)
- What happened
- Status: OK / GUESSED / BAFFLED / BLOCKED
- Time lost (rough)
- Suggested fix: the concrete change to the record (field, wording or link)
GUESSED = you had to infer something (a code, unit, dimension order, meaning). BAFFLED = you did not
understand. BLOCKED = you could not proceed.

Finish with
1. answer.md: the answer with numbers, units and caveats as you understood them from the metadata,
   and an explicit list of what you are NOT confident about.
2. At the end of log.md: counts of OK/GUESSED/BAFFLED/BLOCKED, the top 5 suggested record changes
   ranked by time they would have saved, and a 1-10 score for "could a first-time user succeed
   with this record alone".
Return a short report (under 300 words) with the counts, the score, the top 5 fixes and the paths.
```

Run it in the background while you do Parts 1 and 2: it takes a few minutes.

## 3. Check the agent's work

The agent is also fallible. Before acting on a finding, confirm it against the source: rerun the
query, open the page. A sub-agent's report is evidence, not a verdict. Watch for:

- **False "missing" claims.** The information was in a field the agent skimmed. That is still worth
  a wording fix if a careful reader missed it, but at lower priority.
- **Out-of-scope expectations.** It asked for something the dataset was never meant to provide.
  Usually the fix is a `not_recommended_for` entry, not new data.

## 4. Act on it

| Status | What to do |
|---|---|
| BLOCKED | Fix in the record (or example) before a person reviews it. |
| BAFFLED | Fix: usually a missing definition, unit, code list or limitation in `note`. |
| GUESSED | Fix when the guess could produce a wrong number (codes, units, aggregates, dimension order); otherwise list for the author. |
| A wrong answer the agent was confident about | Highest priority: the record actively misleads. Add a `not_recommended_for` entry and fix the example. |

Merge the agent's findings into the Part 1/2 table with check `user-test`. Severity: HIGH for
anything that produces a wrong number without warning, MED for BLOCKED/BAFFLED, LOW for the rest.
Re-run the agent after substantive changes and report the score before and after. Attach `log.md`
to the submission PR, next to the AI usage disclosure (cdh-catalog#74).

## Score guide

| Score | Meaning |
|---|---|
| 9-10 | A first-time user gets a correct answer with no guessing that matters. |
| 7-8 | Correct answer, but with guesses a less careful user could get wrong. |
| 5-6 | An answer, but a trap or a missing definition makes a wrong number likely. |
| 1-4 | Blocked, or the record leads to a wrong answer. |

Target: 8 or more before a record is submitted.
