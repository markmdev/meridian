---
name: prompt-writing
description: Write effective prompts for AI systems — system prompts, agent instructions, skills, or any LLM prompt. Use when creating or improving prompts.
---

# Prompt Writing

Good prompts are clear and concise, not long and verbose. Longer prompts cause attention dilution — the model pays less attention to each part.

## What Improves Prompts

### Remove Redundancy

Same instruction said multiple ways dilutes attention.

**Before:** "You must always verify each item. Do not skip items. Every item needs to be checked. Make sure you don't miss any items."

**After:** "Verify each item individually. No skipping."

### Remove Noise

Don't teach the model things it already knows. State your specific requirements.

**Before:** 40-line example of what a code walkthrough looks like

**After:** "Write a detailed walkthrough: what changed, line numbers, analysis of the flow, data transformations, dependencies."

### Sharpen Instructions

"Do X" is clearer than "You should consider doing X because..."

**Before:** "It's important that you remember to always navigate to the project root directory before starting any work, as this ensures that all file paths will be correct..."

**After:** `cd "$CLAUDE_PROJECT_DIR"`

### Keep Load-Bearing Content

These must stay:
- Workflow steps and their order
- Quality criteria
- Critical rules and constraints
- Output format requirements (if parsed programmatically)
- Behavioral guardrails

### Write Clean Prose

Write as if it was always this way — not "correction" style.

**Before:** "Remember that you should do TWO interviews, not just one. The first interview is for business requirements, and then after discovery you should do a second interview..."

**After:**
```
### 0. Business Requirements Interview
Interview the user to understand what needs to be built.

### 2. Technical Interview
With discovery complete, interview the user about implementation details.
```

## Structure

Good prompts have clear sections. Adapt this pattern to your use case:

```
[1-2 sentence role/purpose]

## Core Concept or Approach
[Key principle guiding behavior]

## Workflow / Steps
[What to do, in order]

## Rules / Constraints
[Non-negotiable requirements]

## Quality Criteria
[What good looks like, what to avoid]

## Output Format
[Expected structure if applicable]
```

For procedural agents, number the steps clearly. For guidance prompts, use descriptive sections.

## Common Patterns

**Workflow Steps:** Numbered, clear action, what to produce, when to proceed.

**Quality Criteria:** Two lists — DO (what matters) and DON'T (what to ignore). Prevents false positives and negatives.

**Output Formats:** If parsed programmatically, include exact schema. If human-readable, describe what to include.

## Checklist

- [ ] Every instruction serves a purpose (no redundancy)
- [ ] No verbose examples of things the model knows
- [ ] Instructions are direct, not hedged
- [ ] Load-bearing content preserved
- [ ] Written in clean prose, not "correction" style
