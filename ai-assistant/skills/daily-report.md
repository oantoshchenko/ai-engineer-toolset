---
type: "agent_requested"
description: "Generate a structured daily report from OpenMemory and write it to the Obsidian daily note."
---

# Daily Report Rule

Generate a structured daily report from OpenMemory and write it to the Obsidian daily note.

## Step 1: Determine the Target Date

1. Run: `date "+Local: %Y-%m-%d %H:%M %Z | UTC: %Y-%m-%d %H:%M UTC"`
2. If the user specifies a different date (e.g., "yesterday"), adjust accordingly.

**Example:**
- Command output: `Local: 2025-12-09 09:12 PST | UTC: 2025-12-09 17:12 UTC`
- Target date: `2025-12-09` (or `2025-12-08` if user said "yesterday")

## Step 2: Query OpenMemory for Activity

1. Query episodic memories for the target date:
   ```
   openmemory_query: "activity work done {target_date}"
   openmemory_list: sector=episodic, limit=20
   ```
2. Filter memories that contain the target date (e.g., "On 2025-12-08, ...")
3. Extract project names from tags (format: `project-<name>` → use `<name>`)

**Example memories:**
```
[episodic] tags=project-DTwin, evaluation, v6-dataset
On 2025-12-08, ran first evaluation on generated_eval_cases_v6 dataset...

[episodic] tags=project-DTwin, evaluation, CLI
On 2025-12-08, implemented 'results' CLI subcommand...
```
→ Project: **DTwin**

## Step 3: Read the Daily Note

1. Read: `Daily/{YYYY-MM-DD}.md`
2. If the note does not exist: **STOP and ask Sasha to create it**. Do not create it yourself.

## Step 4: Cross-Check and Ask for Missing Work

1. Identify all open to-dos (`- [ ]`) in the note
2. Compare with activity from memories
3. **Ask Sasha** which to-dos were completed (unless explicitly stated in memories)
4. Only ask about open items, not already-completed ones
5. **ALWAYS ask:** "What other work did you do that is not in the memories?"
   - This question is **mandatory**, even if there are no open to-dos
   - This captures meetings, discussions, or other work not logged in OpenMemory

**Example interaction:**
```
Open to-dos in note:
- [ ] Have agent Eval PR ready
- [ ] Finish data generation instructions

Work found in memories:
- Implemented eval CLI subcommand
- Ran first evaluation

Questions:
1. Which of these to-dos should I mark complete?
2. What other work did you do that is not in the memories?
   (e.g., meetings, discussions, research, reviews)
```

## Step 5: Write the Daily Report

### Report Format

```markdown
## Daily report

- **ProjectName**
  - High-level action 1
    - Relevant detail
    - Relevant detail
  - High-level action 2
- **ProjectName2**
  - High-level action
```

### Rules
- Project name comes from memory tags: `project-<name>` → use `<name>` as the project name
- Group all actions under their respective project
- High-level actions are the main accomplishments
- Details are optional specifics (metrics, file names, technical choices)

**Example output:**
```markdown
## Daily report

- **DTwin**
  - Built evaluation run history system
    - JSONL format for storage
    - Pydantic models: EvalRunRecord, RunSummary, CaseResult, EvaluatorResult
  - Implemented 'results' CLI subcommand
    - Three modes: summary, compare, show
  - Ran first evaluation on v6 dataset
    - 21 cases, 56.4% pass rate (22/39 assertions)
```

## Step 6: Update the Note

1. Mark completed to-dos as `[x]` (based on Sasha's confirmation)
2. Append the report content after `## Daily report` heading
3. Use `obsidian_search_replace` tool for updates