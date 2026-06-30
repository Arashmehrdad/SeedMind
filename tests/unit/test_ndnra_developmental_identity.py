"""Tests for NDNRA v0.2 Stage 0 identity and lifecycle contracts."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research import ndnra
from seedmind.research.ndnra import (
    BRAIN_SCHEMA,
    DEVELOPMENTAL_NETWORK_NAMESPACE,
    DEVELOPMENTAL_NETWORK_SCHEMA,
    DEVELOPMENTAL_TRACE_SCHEMA,
    LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA,
    STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA,
    DevelopmentalEvidenceTrace,
    DevelopmentalIdentity,
    DevelopmentalIdentityKind,
    DevelopmentalLifecycleState,
    DevelopmentalLifecycleTransition,
    DevelopmentalSchemaIdentity,
    DevelopmentalTraceEvent,
    StageZeroIdentityCatalog,
    V01AcceptanceBaselineReference,
    default_stage_zero_identity_catalog,
    make_developmental_identity,
    run_stage_zero_contract_acceptance,
)


def _identity(
    kind: DevelopmentalIdentityKind = DevelopmentalIdentityKind.NEURON,
) -> DevelopmentalIdentity:
    return make_developmental_identity(kind, f"test:{kind.value}")


def _transition() -> DevelopmentalLifecycleTransition:
    return DevelopmentalLifecycleTransition(
        structure_identity=_identity(),
        from_state=DevelopmentalLifecycleState.ACTIVE,
        to_state=DevelopmentalLifecycleState.RESTING,
        reason_code="test:rest",
    )


def test_stage_zero_acceptance_matrix_is_complete_and_zero_authority() -> None:
    evidence = run_stage_zero_contract_acceptance()

    assert set(evidence.pass_gate_matrix().values()) == {True}
    assert set(evidence.completion_matrix().values()) == {"implemented_and_evidenced"}
    assert evidence.production_action_authority_violations == 0
    assert evidence.evidence_trace.authority_count == 0
    assert not evidence.evidence_trace.runtime_adapter_connected
    assert not evidence.evidence_trace.action_gateway_connected
    assert evidence.snapshot_json_ascii() == evidence.snapshot_json_ascii()
    assert evidence.snapshot_json_ascii().decode("ascii")


def test_v0_2_schema_identity_cannot_be_confused_with_v0_1_schemas() -> None:
    schema_identity = DevelopmentalSchemaIdentity()
    baseline = V01AcceptanceBaselineReference()
    v01_schemas = {
        BRAIN_SCHEMA,
        STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA,
        LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA,
    }

    assert schema_identity.namespace == DEVELOPMENTAL_NETWORK_NAMESPACE
    assert schema_identity.schema == DEVELOPMENTAL_NETWORK_SCHEMA
    assert schema_identity.trace_schema == DEVELOPMENTAL_TRACE_SCHEMA
    assert schema_identity.schema not in v01_schemas
    assert schema_identity.trace_schema not in v01_schemas
    assert not baseline.proof_store_mutation_allowed

    with pytest.raises(ValueError, match=r"v0.2 schema"):
        DevelopmentalSchemaIdentity(schema=BRAIN_SCHEMA)
    with pytest.raises(ValueError, match=r"v0.2 namespace"):
        DevelopmentalSchemaIdentity(namespace="seedmind.ndnra.brain")
    with pytest.raises(ValueError, match="proof-store mutation"):
        replace(baseline, proof_store_mutation_allowed=True)


def test_identity_catalog_has_exact_canonical_kind_coverage() -> None:
    catalog = default_stage_zero_identity_catalog()

    assert {identity.kind for identity in catalog.identities} == set(DevelopmentalIdentityKind)
    assert catalog.snapshot_json_ascii() == catalog.snapshot_json_ascii()
    assert all(
        identity.identity_id.startswith("developmental-identity:")
        for identity in catalog.identities
    )
    with pytest.raises(ValueError, match="exactly one identity per kind"):
        StageZeroIdentityCatalog(
            identities=(
                *catalog.identities,
                replace(catalog.identities[0], local_code="duplicate:action_proposal"),
            )
        )
    with pytest.raises(ValueError, match="canonical sorted order"):
        StageZeroIdentityCatalog(identities=tuple(reversed(catalog.identities)))
    with pytest.raises(ValueError, match=r"v0.2 namespace"):
        DevelopmentalIdentity(
            kind=DevelopmentalIdentityKind.NEURON,
            local_code="bad:namespace",
            namespace=BRAIN_SCHEMA,
        )


def test_lifecycle_transitions_are_explicit_deterministic_and_non_authoritative() -> None:
    transition = _transition()

    assert transition.transition_id == transition.transition_id
    assert transition.snapshot_json_ascii() == transition.snapshot_json_ascii()
    assert transition.authority_count_delta == 0
    assert not transition.has_production_action_authority

    with pytest.raises(ValueError, match="invalid lifecycle transition"):
        DevelopmentalLifecycleTransition(
            structure_identity=_identity(DevelopmentalIdentityKind.OUTCOME),
            from_state=DevelopmentalLifecycleState.VERIFIED_OUTCOME,
            to_state=DevelopmentalLifecycleState.PENDING_OUTCOME,
            reason_code="bad:verified_reopens_to_pending",
        )
    with pytest.raises(ValueError, match="invalid lifecycle transition"):
        DevelopmentalLifecycleTransition(
            structure_identity=_identity(DevelopmentalIdentityKind.NEURON),
            from_state=DevelopmentalLifecycleState.ACTIVE,
            to_state=DevelopmentalLifecycleState.MATURE_SKILL,
            reason_code="bad:cross_domain_transition",
        )
    with pytest.raises(ValueError, match="authority_count_delta"):
        replace(transition, authority_count_delta=1)
    with pytest.raises(ValueError, match="production action authority"):
        replace(transition, has_production_action_authority=True)


def test_trace_contract_rejects_runtime_gateway_and_sequence_mutations() -> None:
    schema_identity = DevelopmentalSchemaIdentity()
    transition = _transition()
    event = DevelopmentalTraceEvent(
        sequence_index=0,
        event_code="trace:rest",
        subject_identity=transition.structure_identity,
        lifecycle_transition=transition,
    )
    trace = DevelopmentalEvidenceTrace(schema_identity=schema_identity, events=(event,))

    assert trace.trace_id == trace.trace_id
    assert trace.snapshot_json_ascii() == trace.snapshot_json_ascii()

    with pytest.raises(ValueError, match="consecutive"):
        DevelopmentalEvidenceTrace(
            schema_identity=schema_identity,
            events=(replace(event, sequence_index=1),),
        )
    with pytest.raises(ValueError, match="runtime adapter"):
        replace(trace, runtime_adapter_connected=True)
    with pytest.raises(ValueError, match="action gateway"):
        replace(trace, action_gateway_connected=True)
    with pytest.raises(ValueError, match="zero"):
        replace(trace, authority_count=1)
    with pytest.raises(ValueError, match="subject identity"):
        DevelopmentalTraceEvent(
            sequence_index=0,
            event_code="trace:mismatch",
            subject_identity=_identity(DevelopmentalIdentityKind.REGION),
            lifecycle_transition=transition,
        )


def test_public_exports_cover_stage_zero_contracts() -> None:
    exported = set(ndnra.__all__)

    assert "DevelopmentalIdentityKind" in exported
    assert "DevelopmentalLifecycleState" in exported
    assert "StageZeroContractEvidence" in exported
    assert "run_stage_zero_contract_acceptance" in exported
    assert "DEVELOPMENTAL_NETWORK_SCHEMA" in exported


def test_developmental_identity_has_no_runtime_adapter_or_gateway_imports() -> None:
    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "seedmind"
        / "research"
        / "ndnra"
        / "developmental_identity.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_roots = {"asyncio", "concurrent", "queue", "sqlite3", "threading", "time"}
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module.split(".")[0])

    assert imports.isdisjoint(forbidden_roots)
    assert "seedmind.integration" not in source
    assert "ActionGateway" not in source
