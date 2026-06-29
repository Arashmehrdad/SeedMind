# ADR: Bounded Imagination Stage Closure

Date: 29 June 2026
Status: accepted
Scope: SeedMind bounded imagination

## Closure decision

The bounded-imagination stage is closed at Batch 8 as a deterministic, finite, in-memory, provenance-preserving, non-evidentiary, and non-authoritative subsystem.

The accepted stage can:

- produce caller-supplied exact-source imagined traces;
- enumerate exact-record candidates in deterministic breadth-first order;
- annotate every route step against every explicit need dimension;
- compare caller-ordered routes pairwise without a global utility;
- expose exact unresolved comparison reasons;
- preserve one caller-nominated safe-experiment proposal;
- record optional training-time human approve, reject, or defer review evidence;
- resolve either training review status or one explicit configured non-training bypass.

The stage cannot create factual evidence, alter learned confidence or mastery, rank routes globally, select a winner, recommend an action, schedule or execute an experiment, persist imagination state, integrate with the live Nursery loop, promote a proposal autonomously, or control production actions.

## Completion evidence

| Batch | Accepted capability | Primary implementation |
| --- | --- | --- |
| 1 | Exact caller-sequence imagined traces | `bounded_imagination.py` |
| 2 | Exact-record deterministic candidate generation | `bounded_imagination_candidates.py` |
| 3 | Per-step and per-dimension need alignment | `bounded_imagination_evaluation.py` |
| 4 | Caller-order pairwise route relations | `bounded_imagination_comparison.py` |
| 5 | Exact unresolved-comparison uncertainty audit | `bounded_imagination_uncertainty.py` |
| 6 | Caller-nominated proposal semantics | `bounded_imagination_safe_experiment_proposal.py` |
| 7 | Optional training-time human review evidence | `bounded_imagination_safe_experiment_permission.py` |
| 8 | Explicit training-review or non-training bypass resolution | `bounded_imagination_safe_experiment_review_gate.py` |

The closure audit in `tests/unit/test_ndnra_bounded_imagination_stage_closure.py` verifies the complete module inventory, package exports, exclusion of storage, live-integration, background-worker, timer, execution, scheduling, and selection dependencies, absence of execution-oriented public entry points, and zero learning and authority defaults across stage dataclasses.

## Review-gate boundary

Batch 7 remains optional outside training. Batch 8 permits bypass only when non-training mode, an enabled bypass policy, an explicit bypass request, and an ASCII `runtime-policy:` identity are all present. Missing, rejected, or deferred review evidence never acts as implicit bypass.

Review or bypass resolution remains policy evidence only. It does not authorize an experiment permit, scheduling, execution, persistence, live integration, recommendation, selection, promotion, or production action.

## Validation evidence

The closure baseline is:

```text
ruff format --check .: 226 files already formatted
ruff check .: passed
mypy: no issues in 226 source files
pytest -q: 896 passed
pip check: no broken requirements
git diff --check: passed
```

One first full-suite invocation encountered a transient Windows `PermissionError` while replacing a temporary persistence test file. An immediate unchanged rerun passed all 896 tests. No bounded-imagination test failed.

## Deferred boundaries

The following remain outside this closure and require separate architecture approval:

- experiment permits;
- experiment scheduling or execution;
- imagination persistence;
- live Nursery integration;
- autonomous proposal promotion;
- production recommendation or action authority;
- any route optimiser that collapses explicit trade-offs into an unapproved utility.

The expanded developmental architecture marker remains 82%.
