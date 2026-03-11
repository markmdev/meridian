![Logo](https://github.com/user-attachments/assets/9eb140c8-b938-4e77-ab94-0461a6d919fd)

# Meridian

Meridian makes Claude Code more reliable on real projects.

It adds persistent project context, smarter session handoff, and lightweight workflow enforcement so Claude is less likely to lose the plot halfway through a long task.

## What problem it solves

Claude Code is great at short bursts. It gets shakier when work stretches across a big repo, multiple sessions, or a lot of moving pieces.

Common failure modes:

- Context gets lost after compaction or a fresh session
- Important project docs exist, but Claude does not read the right ones at the right time
- Instructions in `CLAUDE.md` drift out of focus during long runs
- Work stops in an awkward half-finished state with missing docs, review, or cleanup
- The same mistakes repeat because nothing turns session learnings into project memory

Meridian closes those gaps without asking you to completely change how you work.

## What Meridian gives you

- Better session continuity: important project context is re-injected when a session starts or compacts
- A real project workspace: `WORKSPACE.md`, project docs, and supporting prompts stay available across sessions
- Smarter doc routing: docs in `.meridian/docs/` can advertise when they should be read
- Instruction reinforcement: Meridian can remind Claude to follow your local guidance during long sessions
- End-of-task quality pressure: the stop checklist nudges Claude to finish the boring but important parts
- Session learning: a background learner can update workspace/docs based on what actually happened

Meridian is intentionally opinionated, but it stays behind the scenes. You still talk to Claude normally.

## Best fit

Meridian is most useful if you use Claude Code for:

- multi-hour or multi-day implementation work
- medium or large repositories
- tasks where losing decisions or next steps is expensive
- projects that benefit from structured docs and a running workspace file

If you mostly use Claude Code for tiny one-off edits, Meridian is probably overkill.

## Quick start

### 1. Install the plugin

```bash
/plugin marketplace add markmdev/claude-plugins
/plugin install meridian@markmdev
```

### 2. Scaffold the project files

Inside the repo you want to use with Meridian:

```bash
curl -fsSL https://raw.githubusercontent.com/markmdev/meridian/main/install.sh | bash
```

That creates a `.meridian/` folder with the project-side files Meridian uses.

### 3. Restart or reload Claude Code

Meridian hooks are provided by the plugin. The scaffolded `.meridian/` directory gives the plugin project-specific files to read from.

## Updating

Update the project scaffolding:

```bash
meridian-update
```

Or:

```bash
curl -fsSL https://raw.githubusercontent.com/markmdev/meridian/main/install.sh | bash
```

Update the plugin itself:

```bash
/plugin update meridian@markmdev
```

Check the installed project version:

```bash
cat .meridian/.version
```

## What gets installed

Meridian has two halves:

### Plugin-managed runtime

Installed through Claude Code's plugin system:

- hooks
- agents
- commands
- skills
- Python helper scripts

These live with the plugin and are updated with `/plugin update`.

### Project scaffolding

Installed into your repo by `install.sh`:

```text
.meridian/
├── SOUL.md
├── WORKSPACE.md
├── config.yaml
├── docs/
├── prompts/
├── scripts/
└── lib/
```

The installer preserves project state on update, including:

- `WORKSPACE.md`
- `.meridian/workspace/`
- `.meridian/plans/`
- `.meridian/config.yaml`

## How it works

Meridian hooks into Claude Code lifecycle events and adds a little structure at the moments where Claude usually drifts.

Current behavior includes:

- Session start: inject relevant project context
- User prompt submit: track activity, watch for planning mode, reinforce instructions
- Stop: run checklist-style reminders before Claude wraps up
- Pre-compact: checkpoint transcript and session learnings before compaction
- Session end: write last-session context and run the learner

The goal is not to micromanage Claude. The goal is to keep it oriented.

## Core files you will care about

### `.meridian/WORKSPACE.md`

The running handoff for the project. Keep it current, short, and operational.

### `.meridian/docs/`

Put durable project docs here. Meridian scans these docs and can steer Claude toward the right one when a task matches its frontmatter hints.

Minimal frontmatter:

```yaml
---
summary: What this doc covers
read_when:
  - keyword or situation
  - another keyword
---
```

### `.meridian/config.yaml`

Project-level behavior toggles.

Current built-in options include:

```yaml
pebble_enabled: false
stop_hook_min_actions: 15
session_learner_mode: project
```

Recent versions also support extra stop-checklist items and custom instruction reminders.

## Typical workflow

1. Install the plugin once.
2. Run the scaffold installer in a repo.
3. Keep `WORKSPACE.md` and `.meridian/docs/` useful.
4. Use Claude Code normally.
5. Let Meridian keep context, docs, and session hygiene from falling apart.

## Worktrees

Meridian stores ephemeral session state in `~/.meridian/state/<hash>/`, not inside the repo. That means `.meridian/` can be shared across worktrees while each worktree still gets isolated runtime state.

If you work heavily with git worktrees, this is a very nice quality-of-life improvement.

## FAQ

### Does this replace `CLAUDE.md`?

No. `CLAUDE.md` is still your core instruction file. Meridian helps those instructions stay alive in practice during longer sessions.

### Does Meridian change how I prompt Claude?

Not much. It is designed to improve behavior without forcing a whole new user workflow.

### Is Meridian only for huge repos?

No, but the payoff is much bigger once tasks are large enough that session continuity and docs routing matter.

### Can I customize it?

Yes. The main entry points are:

- `.meridian/config.yaml`
- `.meridian/docs/`
- `.meridian/prompts/`
- your normal `CLAUDE.md`

## Contributing

Issues and PRs are welcome.

If you are making a meaningful behavior change, update the docs and [CHANGELOG.md](CHANGELOG.md) in the same PR.
