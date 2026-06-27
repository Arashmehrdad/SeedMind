"""Typed integration boundaries between validated SeedMind subsystems."""

from seedmind.integration.developmental_signals import (
    LiveDevelopmentalSignalProvider,
    LiveDevelopmentalSignals,
)
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
from seedmind.integration.unified_shadow import (
    NDNRALiveShadowAdapter,
    UnifiedDevelopmentalShadowSession,
    UnifiedShadowConfig,
    UnifiedShadowResult,
    UnifiedShadowStepRecord,
)
from seedmind.integration.unified_signal_experiment import (
    UnifiedSignalEvidence,
    UnifiedSignalExperimentResult,
    export_unified_signal_evidence,
    run_unified_signal_experiment,
)

__all__ = [
    "LiveDevelopmentalSignalProvider",
    "LiveDevelopmentalSignals",
    "NDNRALiveShadowAdapter",
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
    "UnifiedDevelopmentalShadowSession",
    "UnifiedShadowConfig",
    "UnifiedShadowResult",
    "UnifiedShadowStepRecord",
    "UnifiedSignalEvidence",
    "UnifiedSignalExperimentResult",
    "export_persistent_shadow_evidence",
    "export_shadow_comparison_evidence",
    "export_unified_signal_evidence",
    "run_persistent_shadow_experiment",
    "run_shadow_comparison",
    "run_unified_signal_experiment",
]
