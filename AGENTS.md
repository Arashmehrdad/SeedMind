# SeedMind project instructions

## Canonical specification

Follow the SeedMind Master Implementation Plan v0.1.

## Locked MVP boundaries

- Use a deterministic 2D symbolic Nursery environment.
- Do not place an LLM inside the SeedMind seed.
- Do not provide task-specific knowledge at birth.
- Use symbolic human teaching signals.
- Keep the protected safety supervisor outside normal learning.
- Allow only policy or skill specialists to grow during the MVP.
- Do not add internet access, shell access, or source self-modification.
- Preserve deterministic evaluation and checkpoint reproducibility.

## Implementation order

Environment -> prediction -> body discovery -> curiosity -> ambition ->
human apprenticeship -> memory -> skill -> contribution -> diagnosis ->
growth -> consolidation -> evidence.

Do not implement a later subsystem before the preceding pass gate succeeds.

## Engineering rules

- Prefer small, focused changes.
- Use explicit typed contracts at subsystem boundaries.
- Add tests whenever behaviour changes.
- Keep safety and permission checks outside learned controllers.
- Never commit secrets, credentials, generated checkpoints, or large artifacts.
- Run Ruff, Mypy, Pytest, and pip check before completion.
- Report every validation command and its result.
