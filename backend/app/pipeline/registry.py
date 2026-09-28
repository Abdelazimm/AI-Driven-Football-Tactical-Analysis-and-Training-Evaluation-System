"""
Methodology Execution Readiness Registry and Gate.
Distinguishes between methodology metadata existence and production execution readiness.
CRITICAL SCIENTIFIC RULE:
All three methodologies (Method 1, Method 2, Method 3) remain EXPERIMENTAL.
Their production executors are NOT yet installed or validated.
Therefore, all methodologies evaluate to NOT_READY_FOR_EXECUTION.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Union
from enum import Enum

from backend.app.schemas.methodology import MethodologyId


class ExecutionReadinessStatus(str, Enum):
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
    NOT_READY_FOR_EXECUTION = "NOT_READY_FOR_EXECUTION"


class MethodologyExecutor(ABC):
    """Abstract interface for a production methodology pipeline executor."""

    @property
    @abstractmethod
    def methodology_id(self) -> MethodologyId:
        pass

    @abstractmethod
    def execute(self, payload: dict) -> dict:
        pass


class MethodologyExecutorRegistry:
    """
    Registry that inspects whether a validated, production-ready executor
    is installed for a requested computer-vision methodology.
    """

    def __init__(self):
        # Maps methodology_id -> MethodologyExecutor instance when installed
        self._executors: Dict[MethodologyId, MethodologyExecutor] = {}

    def is_ready_for_execution(self, methodology_id: MethodologyId) -> bool:
        """
        Evaluate whether the requested methodology has an installed, validated production executor.
        Currently returns False for all methodologies per scientific readiness rules.
        """
        return methodology_id in self._executors

    def get_readiness_status(
        self, methodology_id: MethodologyId
    ) -> Tuple[ExecutionReadinessStatus, str]:
        """
        Return explicit readiness status and human-readable explanation.
        """
        if methodology_id in self._executors:
            return (
                ExecutionReadinessStatus.READY_FOR_EXECUTION,
                f"Production executor for '{methodology_id.value}' is installed and validated.",
            )

        return (
            ExecutionReadinessStatus.NOT_READY_FOR_EXECUTION,
            (
                f"Methodology '{methodology_id.value}' is currently EXPERIMENTAL in research track. "
                "Production execution is blocked until formal validation and pipeline integration are complete."
            ),
        )

    def get_executor(self, methodology_id: MethodologyId) -> MethodologyExecutor:
        """
        Retrieve executor or raise fail-closed error.
        Production runners are not yet installed in Phase 1.
        """
        resolved = resolve_methodology(methodology_id)
        if resolved not in self._executors:
            raise RuntimeError(
                f"METHODOLOGY_EXECUTOR_NOT_READY: Production runner for '{resolved.value}' "
                "is not yet integrated or validated."
            )
        return self._executors[resolved]

    def register_executor(self, executor: MethodologyExecutor) -> None:
        """Testing / future extension hook to register an executor."""
        self._executors[executor.methodology_id] = executor

    def unregister_executor(self, methodology_id: MethodologyId) -> None:
        """Testing utility."""
        self._executors.pop(methodology_id, None)


def resolve_methodology(requested: Union[MethodologyId, str]) -> MethodologyId:
    """
    Resolve requested methodology.
    AUTO strictly resolves to METHOD_2_RFDETR_GTATRACK per P0 REV2A frozen contract.
    """
    if requested is None:
        return MethodologyId.METHOD_2_RFDETR_GTATRACK
    req_str = str(requested.value if hasattr(requested, "value") else requested).strip()
    if req_str.upper() in ("AUTO", "NONE", ""):
        return MethodologyId.METHOD_2_RFDETR_GTATRACK
    if isinstance(requested, MethodologyId):
        return requested
    return MethodologyId(req_str)


MethodologyRegistry = MethodologyExecutorRegistry
default_executor_registry = MethodologyExecutorRegistry()


def create_production_registry() -> MethodologyExecutorRegistry:
    """
    Construct a production registry populated with validated vision runners.
    Imports runners lazily to preserve fast startup and isolation.
    """
    from backend.app.runners.m1_runner import M1VisionRunner
    from backend.app.runners.m2_runner import M2VisionRunner
    from backend.app.runners.m3_runner import M3VisionRunner

    reg = MethodologyExecutorRegistry()
    reg.register_executor(M1VisionRunner())
    reg.register_executor(M2VisionRunner())
    reg.register_executor(M3VisionRunner())
    return reg

