"""Exact module-registry restoration for SeedMind Week 11."""

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModuleRegistration:
    module_id: str
    module_type: str
    parent_module: str | None
    active: bool
    checkpoint_sha256: str
    status: str

    def to_json(self) -> dict[str, object]:
        return {
            "active": self.active,
            "checkpoint_sha256": self.checkpoint_sha256,
            "module_id": self.module_id,
            "module_type": self.module_type,
            "parent_module": self.parent_module,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class GrowthRegistry:
    modules: tuple[ModuleRegistration, ...]
    router_registered: bool = False

    def __post_init__(self) -> None:
        ids = tuple(module.module_id for module in self.modules)
        if len(ids) != len(set(ids)):
            raise ValueError("module identifiers must be unique")

    @property
    def digest(self) -> str:
        payload = json.dumps(self.to_json(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("ascii")).hexdigest()

    def to_json(self) -> dict[str, object]:
        return {
            "modules": [module.to_json() for module in self.modules],
            "router_registered": self.router_registered,
            "schema_version": 1,
        }

    def register(self, module: ModuleRegistration) -> "GrowthRegistry":
        if any(item.module_id == module.module_id for item in self.modules):
            raise ValueError("module is already registered")
        modules = tuple(sorted((*self.modules, module), key=lambda item: item.module_id))
        return GrowthRegistry(modules=modules, router_registered=True)

    def discard(self, module_id: str) -> "GrowthRegistry":
        modules = tuple(module for module in self.modules if module.module_id != module_id)
        if len(modules) == len(self.modules):
            raise KeyError(module_id)
        router_registered = any(module.module_type == "skill_expert" for module in modules)
        return GrowthRegistry(modules=modules, router_registered=router_registered)


def initial_growth_registry(general_checkpoint_sha256: str) -> GrowthRegistry:
    return GrowthRegistry(
        modules=(
            ModuleRegistration(
                module_id="general_push_controller",
                module_type="general_controller",
                parent_module=None,
                active=True,
                checkpoint_sha256=general_checkpoint_sha256,
                status="frozen_parent",
            ),
        )
    )
