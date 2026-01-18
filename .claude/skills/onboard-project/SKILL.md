---
name: onboard-project
description: Interview to learn about this project's context, criticality, security requirements, and priorities. Results saved to project profile.
---

# Project Onboarding Interview

You are conducting an onboarding interview to understand this project. The goal is to learn what the project is, how critical it is, and what constraints apply.

## Interview Principles

1. **Conversational, not bureaucratic** — This is a dialogue, not a form. Ask naturally, follow up on interesting answers.
2. **One topic at a time** — Don't overwhelm. Ask about one area, listen, then move on.
3. **Adaptive** — Skip questions based on previous answers (side project → skip compliance).
4. **Summarize periodically** — Every 5-6 questions, briefly summarize what you've learned.
5. **Confirm before saving** — At the end, show the full profile and ask if it looks right.

## Question Areas

Work through these areas conversationally. Skip questions if already answered or clearly not relevant.

### 1. The Basics
- What does this project do? Give me the elevator pitch.
- Who is it for? Who are the users?
- What problem does it solve? Why does it exist?

### 2. Stage & Maturity
- What stage is this project at? (idea, prototype, MVP, active development, production, maintenance)
- How old is the codebase?
- Is the architecture stable, or still evolving significantly?
- What's the test coverage situation? (well tested, partially tested, mostly untested)

### 3. Criticality & Risk
- How critical is this project? (side project, internal tool, production with real users, critical infrastructure)
- What happens if it breaks? (nobody notices, inconvenience, people can't work, people lose money)
- Are there real users relying on it right now?
- Roughly how many users or customers?

### 4. Security & Compliance
- What kind of data does this project handle? (public, personal/PII, financial, health, credentials)
- Are there compliance requirements? (GDPR, HIPAA, PCI-DSS, SOC2, other)
- How paranoid should I be about security? (low for internal tools, high for financial/health)
- Any specific security concerns I should know about?

### 5. Team & Organization
- Are you working alone or with a team?
- If team: roughly how many people touch this codebase?
- Is there a code review process? (none, self-review, PR review required)
- Who are the stakeholders beyond the dev team?

### 6. Business Context
- What's the business context? (personal project, startup, enterprise, contract work, open source)
- What's the business model? (none, SaaS, marketplace, internal tool, open source)
- Are there paying customers?
- Is there budget or runway pressure affecting pace?

### 7. Timeline & Priorities
- Is there a deadline or milestone coming up?
- What's the pace of development? (ad-hoc, sprint cycles, continuous delivery)
- What's the current priority? (new features, quality/stability, performance, security, maintenance)
- What would success look like for the next milestone?

### 8. Technical Context
- What's the tech stack? (brief overview)
- Are there technologies you must use? (company mandates, existing integrations)
- Are there technologies you can't use? (licensing, policy, etc.)
- Any specific patterns or architectures required?
- Any approaches that were tried and failed that I should avoid?

### 9. Pain Points & Technical Debt
- What's currently broken or painful?
- What technical debt exists and is accepted?
- What areas of the codebase are fragile?

### 10. Historical Context
- Any key architectural decisions I should know about? (why things are the way they are)
- Any decisions that were contentious or might be revisited?
- Any critical external dependencies I should know about?

## Adaptive Logic

Skip questions based on context:

- **Side project** → Skip compliance, team process, business model, stakeholders
- **Prototype/Idea stage** → Skip maintenance, debt, most security (unless sensitive data)
- **Solo developer** → Skip team process, review process
- **Internal tool** → Skip business model, customer questions
- **Financial/Health data** → Ask detailed security and compliance questions
- **Production with users** → Ask about failure impact, SLAs, on-call
- **Deadline mentioned** → Ask what specifically needs to ship

## Interview Flow

1. **Opening**: "I'd like to understand this project so I can work on it more effectively. This usually takes 10-15 minutes. Ready to start?"

2. **Start with basics**: Always ask what it does, who it's for, what stage it's at.

3. **Branch based on criticality**:
   - Side project → abbreviated interview, skip compliance/process
   - Production → full interview, especially security and reliability

4. **Periodic summaries**: Every 5-6 questions, summarize: "So this is a production fintech app, ~5000 users, PCI compliance required, deadline in 3 weeks. Correct?"

5. **Closing**: Show the complete profile. Ask: "Does this capture the project well? Anything to add or change?"

6. **Save**: Write to `.meridian/project-profile.yaml`

## Output Format

Save to `.meridian/project-profile.yaml`:

```yaml
# Meridian Project Profile
# Generated by project onboarding interview
# Last updated: YYYY-MM-DD

overview:
  name: "<project name>"
  description: "<one sentence description>"
  target_audience: "<who uses this>"
  problem_solved: "<what problem it solves>"

stage:
  maturity: idea | prototype | mvp | active_development | production | maintenance
  codebase_age: "<e.g., 6 months, 2 years>"
  architecture_stability: evolving | stabilizing | stable
  test_coverage: untested | partial | good | comprehensive

criticality:
  level: side_project | internal_tool | production | critical_infrastructure
  failure_impact: none | inconvenience | work_blocked | financial_loss | safety_risk
  has_real_users: true | false
  user_count: "<approximate number or range>"

security:
  data_sensitivity: public | personal | financial | health | credentials
  compliance: [<list of requirements, or "none">]
  paranoia_level: low | medium | high
  specific_concerns:
    - "<any specific security notes>"

team:
  size: solo | small | medium | large
  review_process: none | self_review | pr_required
  stakeholders: [<list of stakeholder types>]

business:
  context: personal | startup | enterprise | contract | open_source
  model: none | saas | marketplace | internal | open_source | other
  has_paying_customers: true | false
  runway_pressure: none | some | high

timeline:
  current_milestone: "<what you're working toward>"
  deadline: "<date if any, or 'none'>"
  pace: adhoc | sprints | continuous
  current_priority: features | quality | performance | security | maintenance

technical:
  stack_summary: "<brief tech stack>"
  required_tech:
    - "<mandated technologies>"
  forbidden_tech:
    - "<technologies to avoid>"
  patterns:
    - "<required architectural patterns>"
  failed_approaches:
    - "<approaches that didn't work>"

pain_points:
  current_issues:
    - "<what's broken or painful>"
  known_debt:
    - "<accepted technical debt>"
  fragile_areas:
    - "<areas to be careful with>"

historical:
  key_decisions:
    - "<important architectural decisions and why>"
  revisitable_decisions:
    - "<decisions that might change>"
  critical_dependencies:
    - "<important external dependencies>"
```

## After Saving

1. **Update config.yaml** if appropriate based on answers:
   - `project_type: production` if criticality is high
   - `plan_review_enabled: true` if security matters
   - `code_review_enabled: true` if it's production

2. Tell the user:
   - "Project profile saved to `.meridian/project-profile.yaml`"
   - "I'll use this context in all our sessions. You can update it anytime with `/onboard-project`."
   - If config was updated: "I also adjusted `.meridian/config.yaml` based on the project's criticality."

3. Return to what the user was doing.
