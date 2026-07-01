"""Deterministic candidate-profile selection for Week 11."""

from seedmind.growth.specialist import CandidateSkillExpert, SpecialistProfile
from seedmind.growth.week11_profiles import CANDIDATE_ID, PARENT_MODULE


def candidate_profiles() -> tuple[SpecialistProfile, ...]:
    return (
        SpecialistProfile("direct_axis", (1.0, 0.0, 0.03, 2.0, 0.5, -10.0)),
        SpecialistProfile("clearance_strong", (1.0, 5.0, 0.02, 0.25, 1.5, -10.0)),
    )


def build_candidate(profile: SpecialistProfile) -> CandidateSkillExpert:
    return CandidateSkillExpert(
        candidate_id=CANDIDATE_ID,
        parent_module=PARENT_MODULE,
        profile=profile,
    )
