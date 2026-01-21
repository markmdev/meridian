---
description: Think through a problem on paper before acting
argument-hint: [LINES] [TOPIC]
---

# Think Mode

You have been asked to think through a problem before acting.

**Arguments:** $ARGUMENTS

Parse the arguments:
- First number found = line limit (default: 50 if not specified)
- Remaining text = topic to think about (optional)

**Instructions:**

1. Create a scratch file: `.meridian/.scratch/thinking-YYYY-MM-DD-HH-MM-topic.md`
   - Use current timestamp
   - Slugify the topic for the filename (or use "exploration" if no topic)

2. Write your thoughts to this file. You have **{line_limit} lines** to think.
   - Stream of consciousness — explore angles, question assumptions
   - What could go wrong? What don't you know? What are you assuming?
   - Consider multiple approaches, note tradeoffs
   - Messy is fine. Contradictions are fine. Dead ends are fine.
   - This is exploration, not planning.

3. End with a brief "## Synthesis" section summarizing:
   - Key insights
   - Open questions
   - Recommended next step

4. After writing the thinking file, tell the user what you figured out and ask how to proceed.

**The point:** Thinking on paper catches issues early and produces better solutions than jumping straight to action. Use the line limit — don't stop early, don't exceed it significantly.
