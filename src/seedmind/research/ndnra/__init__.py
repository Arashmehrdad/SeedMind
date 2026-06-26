"""Need-Driven Neural Recruitment Architecture research prototype."""

from seedmind.research.ndnra.composition import (
    CompositionCandidate,
    CompositionResult,
    ExperienceAssembly,
    MultidimensionalExperienceGraph,
    NeedDrivenComposer,
)
from seedmind.research.ndnra.effects import (
    EffectEstimate,
    EffectNeed,
    EffectObservation,
    LocalEffectLink,
    NeedDimension,
    SparseEffectMemory,
)
from seedmind.research.ndnra.experiment import (
    NDNRAExperimentResult,
    RecallEpisodeResult,
    RecallStepRecord,
    TeacherTrainingResult,
    evaluate_recall,
    export_ndnra_evidence,
    run_ndnra_heat_fan_experiment,
    train_teacher_demonstrations,
)
from seedmind.research.ndnra.heat_world import (
    HeatFanWorld,
    HeatTransition,
    HeatWorldState,
)
from seedmind.research.ndnra.models import (
    GrowthPressure,
    HeatAction,
    HeatContext,
    LocalNeuron,
    LocalSynapse,
    ModulationSummary,
    NeedPulse,
    NeuronKind,
    RecallResult,
)
from seedmind.research.ndnra.multieffect_experiment import (
    MultieffectExperimentResult,
    build_intended_effect_only_baseline,
    build_multieffect_graph,
    cleanliness_need,
    cooling_need,
    export_multieffect_evidence,
    run_ndnra_multieffect_experiment,
)
from seedmind.research.ndnra.network import (
    LocalNeuralGraph,
    LocalNeuralGraphConfig,
)

__all__ = [
    "CompositionCandidate",
    "CompositionResult",
    "EffectEstimate",
    "EffectNeed",
    "EffectObservation",
    "ExperienceAssembly",
    "GrowthPressure",
    "HeatAction",
    "HeatContext",
    "HeatFanWorld",
    "HeatTransition",
    "HeatWorldState",
    "LocalEffectLink",
    "LocalNeuralGraph",
    "LocalNeuralGraphConfig",
    "LocalNeuron",
    "LocalSynapse",
    "ModulationSummary",
    "MultidimensionalExperienceGraph",
    "MultieffectExperimentResult",
    "NDNRAExperimentResult",
    "NeedDimension",
    "NeedDrivenComposer",
    "NeedPulse",
    "NeuronKind",
    "RecallEpisodeResult",
    "RecallResult",
    "RecallStepRecord",
    "SparseEffectMemory",
    "TeacherTrainingResult",
    "build_intended_effect_only_baseline",
    "build_multieffect_graph",
    "cleanliness_need",
    "cooling_need",
    "evaluate_recall",
    "export_multieffect_evidence",
    "export_ndnra_evidence",
    "run_ndnra_heat_fan_experiment",
    "run_ndnra_multieffect_experiment",
    "train_teacher_demonstrations",
]
