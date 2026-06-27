"""Typed integration boundaries between validated SeedMind subsystems."""

from seedmind.integration.ndnra_shadow import (
    NDNRAShadowAdapter,
    NDNRAShadowConfig,
    NDNRAShadowSession,
    NDNRAShadowSessionConfig,
    NDNRAShadowSessionResult,
    ShadowStepRecord,
    ShadowSuggestion,
)
from seedmind.integration.persistent_shadow_experiment import (
    PersistentShadowEvidence,
    PersistentShadowResult,
    export_persistent_shadow_evidence,
    run_persistent_shadow_experiment,
)
from seedmind.integration.shadow_experiment import (
    ShadowComparisonResult,
    export_shadow_comparison_evidence,
    run_shadow_comparison,
)

__all__ = [
    "NDNRAShadowAdapter",
    "NDNRAShadowConfig",
    "NDNRAShadowSession",
    "NDNRAShadowSessionConfig",
    "NDNRAShadowSessionResult",
    "PersistentShadowEvidence",
    "PersistentShadowResult",
    "ShadowComparisonResult",
    "ShadowStepRecord",
    "ShadowSuggestion",
    "export_persistent_shadow_evidence",
    "export_shadow_comparison_evidence",
    "run_persistent_shadow_experiment",
    "run_shadow_comparison",
]
