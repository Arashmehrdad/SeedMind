"""Closure audit for the complete bounded-imagination stage."""

from __future__ import annotations

import ast
import importlib
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from types import ModuleType

import seedmind.research.ndnra as ndnra

_MODULE_NAMES = (
    "bounded_imagination",
    "bounded_imagination_candidates",
    "bounded_imagination_evaluation",
    "bounded_imagination_comparison",
    "bounded_imagination_uncertainty",
    "bounded_imagination_safe_experiment_proposal",
    "bounded_imagination_safe_experiment_permission",
    "bounded_imagination_safe_experiment_review_gate",
)

_FORBIDDEN_IMPORT_PREFIXES = (
    "sqlite3",
    "asyncio",
    "threading",
    "multiprocessing",
    "subprocess",
    "socket",
    "requests",
    "httpx",
    "seedmind.integration",
    "seedmind.environment",
    "seedmind.curiosity",
    "seedmind.research.ndnra.persistence",
    "seedmind.research.ndnra.consolidation",
    "seedmind.research.ndnra.controlled_",
    "seedmind.research.ndnra.growth",
)

_FORBIDDEN_FUNCTION_NAMES = {
    "execute",
    "schedule",
    "persist",
    "recommend",
    "select",
    "promote",
    "optimize",
    "optimise",
    "integrate",
}

_ZERO_FIELDS = {
    "factual_confidence_change",
    "mastery_change",
    "competence_change",
    "growth_pressure_change",
    "replay_evidence_change",
    "real_observation_change",
}

_FALSE_FIELDS = {
    "has_action_selection_authority",
    "has_production_action_authority",
    "authorizes_execution",
    "authorizes_scheduling",
    "authorizes_persistence",
    "authorizes_live_integration",
}


def _modules() -> tuple[ModuleType, ...]:
    return tuple(
        importlib.import_module(f"seedmind.research.ndnra.{name}") for name in _MODULE_NAMES
    )


def _module_source(module: ModuleType) -> str:
    path = Path(module.__file__ or "")
    assert path.is_file()
    return path.read_text(encoding="ascii")


def test_stage_module_inventory_and_package_exports_are_complete() -> None:
    modules = _modules()

    assert tuple(module.__name__.rsplit(".", 1)[-1] for module in modules) == _MODULE_NAMES
    for module in modules:
        public_names = tuple(module.__all__)
        assert public_names
        assert len(public_names) == len(set(public_names))
        for name in public_names:
            assert hasattr(module, name)
            assert getattr(ndnra, name) is getattr(module, name)


def test_stage_modules_exclude_runtime_storage_and_background_dependencies() -> None:
    for module in _modules():
        tree = ast.parse(_module_source(module))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module)

        for forbidden in _FORBIDDEN_IMPORT_PREFIXES:
            assert not any(
                imported == forbidden or imported.startswith(f"{forbidden}.")
                for imported in imported_modules
            ), f"{module.__name__} imports forbidden dependency {forbidden}"


def test_stage_modules_expose_no_execution_or_selection_entry_points() -> None:
    for module in _modules():
        tree = ast.parse(_module_source(module))
        function_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert function_names.isdisjoint(_FORBIDDEN_FUNCTION_NAMES)
        assert not any(isinstance(node, ast.AsyncFunctionDef) for node in ast.walk(tree))

        for public_name in module.__all__:
            assert "Permit" not in public_name
            assert "Executor" not in public_name
            assert "Scheduler" not in public_name


def test_stage_dataclass_authority_and_learning_defaults_remain_zero() -> None:
    checked_fields = 0
    for module in _modules():
        for value in vars(module).values():
            if (
                not isinstance(value, type)
                or value.__module__ != module.__name__
                or not is_dataclass(value)
            ):
                continue
            for item in fields(value):
                if item.name in _ZERO_FIELDS:
                    assert item.default is not MISSING
                    assert item.default == 0.0
                    checked_fields += 1
                elif item.name in _FALSE_FIELDS:
                    assert item.default is not MISSING
                    assert item.default is False
                    checked_fields += 1

    assert checked_fields > 0


def test_stage_sources_define_no_schema_worker_or_timer_surface() -> None:
    forbidden_tokens = (
        "create table",
        "alter table",
        "background worker",
        "threadpool",
        "processpool",
        "call_later(",
        "create_task(",
        "serve_forever(",
    )

    for module in _modules():
        lowered = _module_source(module).lower()
        for token in forbidden_tokens:
            assert token not in lowered
