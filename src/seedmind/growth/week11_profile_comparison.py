"""Execute and compare bounded Week 11 candidate profiles."""

from statistics import fmean
from typing import TypedDict

from seedmind.growth.specialist import CandidateSkillExpert
from seedmind.growth.week11_inputs import TRAINING_SEEDS, cube_like_state
from seedmind.growth.week11_rollout import run_specialist
from seedmind.growth.week11_selection import build_candidate, candidate_profiles


class ProfileRow(TypedDict):
    checkpoint_sha256: str
    episodes: list[dict[str, object]]
    mean_steps: float
    profile: dict[str, object]
    success_rate: float


def compare_candidate_profiles() -> tuple[CandidateSkillExpert, dict[str, object]]:
    rows: list[ProfileRow] = []
    selected: CandidateSkillExpert | None = None
    selected_score = (-1.0, 0.0)
    for profile in candidate_profiles():
        candidate = build_candidate(profile)
        episodes = tuple(
            run_specialist(
                cube_like_state(seed),
                seed,
                f"week11-profile-{profile.profile_id}-{seed}",
                candidate,
            )
            for seed in TRAINING_SEEDS
        )
        success_rate = fmean(float(episode.success) for episode in episodes)
        mean_steps = fmean(episode.steps for episode in episodes)
        rows.append(
            {
                "checkpoint_sha256": candidate.checkpoint_sha256,
                "episodes": [episode.to_json() for episode in episodes],
                "mean_steps": mean_steps,
                "profile": profile.to_json(),
                "success_rate": success_rate,
            }
        )
        score = (success_rate, -mean_steps)
        if score > selected_score:
            selected = candidate
            selected_score = score
    if selected is None:
        raise AssertionError("profile comparison produced no candidate")
    report: dict[str, object] = {
        "candidate_id": selected.candidate_id,
        "failure_events": [
            episode["episode_id"]
            for row in rows
            for episode in row["episodes"]
            if not episode["success"]
        ],
        "learning_curve": [
            {
                "epoch": index,
                "profile_id": row["profile"]["profile_id"],
                "success_rate": row["success_rate"],
            }
            for index, row in enumerate(rows)
        ],
        "profiles": rows,
        "selected_checkpoint_sha256": selected.checkpoint_sha256,
        "selected_profile_id": selected.profile.profile_id,
        "training_seeds": list(TRAINING_SEEDS),
    }
    return selected, report
