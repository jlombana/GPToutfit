# GPToutfit - Project Brief for Codex

## Welcome
You are the Implementation Engineer for GPToutfit. This document is your onboarding
guide. Read it fully before writing any code.

## What to Read (in order)
1. `CLAUDE.md` — architectural source of truth, hard constraints
2. `docs/ARCHITECTURE.md` — system diagram and component descriptions
3. `docs/DECISIONS.md` — why each architectural choice was made
4. `docs/TASKS.md` — your task list (complete in order)
5. `docs/api-contracts.md` — API endpoint specifications
6. `.env.template` — required environment variables

## How to Work
- Complete tasks in TASKS.md sequentially (unless marked READY independently)
- Each task specifies exact files, function signatures, and acceptance criteria
- Follow the "Do NOT" boundaries strictly
- All code must satisfy the hard constraints in CLAUDE.md
- Use type hints and Google-style docstrings on all public functions
- Run the code after each task to verify it works

## Architecture Summary
```
Image Upload -> Analyze (GPT-4o-mini vision) -> Embed query -> Match (cosine sim)
-> Guardrail (GPT-4o-mini) -> Return validated results
```

## Key Rules
- NEVER hardcode API keys
- NEVER skip the guardrail step
- ALWAYS use the retry wrapper for OpenAI calls
- ALWAYS filter by gender + articleType before matching
- Keep modules independently replaceable
