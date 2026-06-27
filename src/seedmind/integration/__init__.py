"""Typed integration boundaries between validated SeedMind subsystems."""

from seedmind.integration.advice_acceptance import (
    AdviceAcceptanceEvidence,
    AdviceAcceptanceResult,
    AdviceTimelineRecord,
    export_advice_acceptance,
    run_advice_acceptance,
)
from seedmind.integration.bounded_advice import (
    AdviceCode,
    AdviceConfig,
    AdviceDecision,
    AdviceEvidence,
    BoundedAdvicePolicy,
    ConfidenceCalibration,
)
from seedmind.integration.comparison_oracle import (
    CandidateComparison,
    CandidateOutcome,
    NurseryOutcomeOracle,
)
from seedmind.integration.consolidation_acceptance import (
    ConsolidationAcceptanceEvidence,
    ConsolidationAcceptanceResult,
    export_consolidation_acceptance,
    run_consolidation_acceptance,
)
from seedmind.integration.contextual_mastery_acceptance import (
    ContextualMasteryAcceptanceEvidence,
    ContextualMasteryAcceptanceResult,
    export_contextual_mastery_acceptance,
    run_contextual_mastery_acceptance,
)
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
    "AdviceAcceptanceEvidence",
    "AdviceAcceptanceResult",
    "AdviceCode",
    "AdviceConfig",
    "AdviceDecision",
    "AdviceEvidence",
    "AdviceTimelineRecord",
    "BoundedAdvicePolicy",
    "CandidateComparison",
    "CandidateOutcome",
    "ConfidenceCalibration",
    "ConsolidationAcceptanceEvidence",
    "ConsolidationAcceptanceResult",
    "ContextualMasteryAcceptanceEvidence",
    "ContextualMasteryAcceptanceResult",
    "LiveDevelopmentalSignalProvider",
    "LiveDevelopmentalSignals",
    "NDNRALiveShadowAdapter",
    "NDNRAShadowAdapter",
    "NDNRAShadowConfig",
    "NDNRAShadowSession",
    "NDNRAShadowSessionConfig",
    "NDNRAShadowSessionResult",
    "NurseryOutcomeOracle",
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
    "export_advice_acceptance",
    "export_consolidation_acceptance",
    "export_contextual_mastery_acceptance",
    "export_persistent_shadow_evidence",
    "export_shadow_comparison_evidence",
    "export_unified_signal_evidence",
    "run_advice_acceptance",
    "run_consolidation_acceptance",
    "run_contextual_mastery_acceptance",
    "run_persistent_shadow_experiment",
    "run_shadow_comparison",
    "run_unified_signal_experiment",
]
