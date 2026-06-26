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
    "ShadowComparisonResult",
    "ShadowStepRecord",
    "ShadowSuggestion",
    "export_shadow_comparison_evidence",
    "run_shadow_comparison",
]
