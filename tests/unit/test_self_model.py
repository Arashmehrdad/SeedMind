"""Tests for online action-effect evidence and body discovery."""

from pathlib import Path

import pytest

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.environment import DynamicNurseryScenarioFactory, NurseryRuntime
from seedmind.self_model import (
    SelfModelConfig,
    SelfModelRegistry,
    export_action_effects_csv,
    export_self_model_json,
)
from seedmind.training import ExperienceTransition, collect_experience


def create_packet(
    *,
    step_id: int,
    sensor_values: tuple[float, ...],
    episode_id: str = "episode-1",
) -> ObservationPacket:
    """Create one compact packet for synthetic causal evidence."""
    return ObservationPacket(
        timestamp=step_id,
        episode_id=episode_id,
        step_id=step_id,
        sensor_values=sensor_values,
        available_actions=tuple(PrimitiveAction),
    )


def create_experience(
    *,
    action: PrimitiveAction,
    controllable_change: tuple[float, ...],
    external_change: tuple[float, ...],
    episode_id: str = "episode-1",
) -> ExperienceTransition:
    """Create a transition with explicitly separated causal changes."""
    source = tuple(0.0 for _ in controllable_change)
    agent = controllable_change
    final = tuple(
        controllable + external
        for controllable, external in zip(
            controllable_change,
            external_change,
            strict=True,
        )
    )
    return ExperienceTransition(
        observation=create_packet(
            step_id=0,
            sensor_values=source,
            episode_id=episode_id,
        ),
        action=action,
        agent_observation=create_packet(
            step_id=1,
            sensor_values=agent,
            episode_id=episode_id,
        ),
        next_observation=create_packet(
            step_id=1,
            sensor_values=final,
            episode_id=episode_id,
        ),
        terminated=False,
    )


def test_registry_separates_repeatable_body_effect_from_external_change() -> None:
    registry = SelfModelRegistry(
        SelfModelConfig(
            sensor_size=3,
            minimum_samples=4,
            body_probe_actions=(PrimitiveAction.TURN_LEFT,),
        )
    )
    experience = create_experience(
        action=PrimitiveAction.TURN_LEFT,
        controllable_change=(1.0, 0.0, 0.0),
        external_change=(0.0, 0.0, 1.0),
    )

    for _ in range(4):
        registry.observe(experience)

    snapshot = registry.snapshot()
    action_effect = snapshot.action_effects[0]

    assert snapshot.experience_count == 4
    assert snapshot.body_sensor_indices == (0,)
    assert snapshot.mean_body_controllability == pytest.approx(1.0)
    assert snapshot.sensor_estimates[0].best_action is PrimitiveAction.TURN_LEFT
    assert snapshot.sensor_estimates[2].external_effect_frequency == pytest.approx(1.0)
    assert action_effect.mean_controllable_change == pytest.approx((1.0, 0.0, 0.0))
    assert action_effect.controllable_change_variance == pytest.approx((0.0, 0.0, 0.0))
    assert action_effect.controllability_score[0] == pytest.approx(1.0)
    assert action_effect.controllability_score[2] == pytest.approx(0.0)


def test_wait_with_external_motion_does_not_create_body_sensor() -> None:
    registry = SelfModelRegistry(
        SelfModelConfig(
            sensor_size=2,
            minimum_samples=2,
            body_probe_actions=(PrimitiveAction.WAIT,),
        )
    )
    experience = create_experience(
        action=PrimitiveAction.WAIT,
        controllable_change=(0.0, 0.0),
        external_change=(1.0, 0.0),
    )

    registry.observe(experience)
    registry.observe(experience)

    snapshot = registry.snapshot()

    assert snapshot.body_sensor_indices == ()
    assert snapshot.mean_body_controllability == 0.0
    assert snapshot.mean_external_effect_frequency == pytest.approx(0.5)


def test_support_prevents_single_effect_from_becoming_body_evidence() -> None:
    registry = SelfModelRegistry(
        SelfModelConfig(
            sensor_size=1,
            minimum_samples=4,
            body_score_threshold=0.6,
            body_probe_actions=(PrimitiveAction.MOVE_FORWARD,),
        )
    )
    registry.observe(
        create_experience(
            action=PrimitiveAction.MOVE_FORWARD,
            controllable_change=(1.0,),
            external_change=(0.0,),
        )
    )

    snapshot = registry.snapshot()

    assert snapshot.sensor_estimates[0].controllability_score == pytest.approx(0.25)
    assert snapshot.body_sensor_indices == ()


def test_dynamic_world_body_candidates_remain_in_anonymous_body_channels() -> None:
    scenario = DynamicNurseryScenarioFactory().create(seed=4)
    initial_runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id="interface",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    registry = SelfModelRegistry(
        SelfModelConfig(
            sensor_size=initial_runtime.sensor_size,
            minimum_samples=4,
            body_probe_actions=(PrimitiveAction.TURN_LEFT,),
        )
    )

    for episode_index in range(4):
        runtime = NurseryRuntime(
            initial_state=scenario.initial_state,
            episode_id=f"dynamic-{episode_index}",
            resource_state_provider=scenario.resource_state,
            world_processes=scenario.world_processes,
        )
        registry.observe(collect_experience(runtime, PrimitiveAction.TURN_LEFT))

    snapshot = registry.snapshot()

    assert snapshot.body_sensor_indices
    assert all(sensor_index < 6 for sensor_index in snapshot.body_sensor_indices)
    assert any(
        estimate.external_effect_frequency > 0.0
        for estimate in snapshot.sensor_estimates[6:]
    )
    assert not any(
        estimate.is_body_candidate for estimate in snapshot.sensor_estimates[6:]
    )


def test_snapshot_reports_action_coverage() -> None:
    registry = SelfModelRegistry(
        SelfModelConfig(
            sensor_size=1,
            minimum_samples=1,
            body_probe_actions=(PrimitiveAction.TURN_LEFT,),
        )
    )
    registry.observe(
        create_experience(
            action=PrimitiveAction.TURN_LEFT,
            controllable_change=(1.0,),
            external_change=(0.0,),
        )
    )
    registry.observe(
        create_experience(
            action=PrimitiveAction.WAIT,
            controllable_change=(0.0,),
            external_change=(0.0,),
        )
    )

    snapshot = registry.snapshot()

    assert snapshot.action_coverage == pytest.approx(2 / len(PrimitiveAction))
    assert [effect.action for effect in snapshot.action_effects] == [
        PrimitiveAction.TURN_LEFT,
        PrimitiveAction.WAIT,
    ]


def test_registry_rejects_different_sensor_width() -> None:
    registry = SelfModelRegistry(SelfModelConfig(sensor_size=2))

    with pytest.raises(ValueError, match="sensor width"):
        registry.observe(
            create_experience(
                action=PrimitiveAction.WAIT,
                controllable_change=(0.0,),
                external_change=(0.0,),
            )
        )


def test_self_model_exports_are_ascii_and_inspectable(tmp_path: Path) -> None:
    registry = SelfModelRegistry(
        SelfModelConfig(
            sensor_size=1,
            minimum_samples=1,
            body_probe_actions=(PrimitiveAction.TURN_RIGHT,),
        )
    )
    registry.observe(
        create_experience(
            action=PrimitiveAction.TURN_RIGHT,
            controllable_change=(1.0,),
            external_change=(0.0,),
        )
    )
    snapshot = registry.snapshot()
    json_path = tmp_path / "self_model.json"
    csv_path = tmp_path / "action_effects.csv"

    export_self_model_json(snapshot, json_path)
    export_action_effects_csv(snapshot, csv_path)

    json_text = json_path.read_text(encoding="ascii")
    csv_text = csv_path.read_text(encoding="ascii")
    assert '"body_sensor_indices": [' in json_text
    assert '"turn_right"' in json_text
    assert csv_text.startswith("action,sample_count,sensor_index")
    assert "turn_right,1,0" in csv_text


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"sensor_size": 0}, "sensor_size"),
        ({"sensor_size": 1, "minimum_samples": 0}, "minimum_samples"),
        ({"sensor_size": 1, "effect_threshold": -1.0}, "effect_threshold"),
        ({"sensor_size": 1, "body_score_threshold": 1.1}, "body_score_threshold"),
        ({"sensor_size": 1, "body_probe_actions": ()}, "body_probe_actions"),
        (
            {
                "sensor_size": 1,
                "body_probe_actions": (
                    PrimitiveAction.TURN_LEFT,
                    PrimitiveAction.TURN_LEFT,
                ),
            },
            "unique",
        ),
        (
            {
                "sensor_size": 1,
                "body_probe_actions": (PrimitiveAction.STOP,),
            },
            "stop",
        ),
    ],
)
def test_self_model_config_rejects_invalid_values(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        SelfModelConfig(**kwargs)  # type: ignore[arg-type]
