from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExecutionRoute:
    route_name: str
    action_name: str
    backend_name: str
    pre_commands: tuple[tuple[str, ...], ...] = field(default_factory=tuple)
    pre_command_required_commands: tuple[tuple[str, ...], ...] = field(default_factory=tuple)
    command: tuple[str, ...] = ()
    required_commands: tuple[str, ...] = ()
    state_probe_command: tuple[str, ...] = ()
    state_probe_required_commands: tuple[str, ...] = ()
    implemented: bool = False
    requires_privilege_escalation: bool = False
    interactive_passthrough: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)
    execution_surface: str = "host"
    environment_target: str = ""

    @property
    def can_execute_now(self) -> bool:
        return self.implemented and bool(self.command)


@dataclass(frozen=True)
class ExecutionProbe:
    status: str
    command: tuple[str, ...] = ()
    required_commands: tuple[str, ...] = ()
    exit_code: int | None = None
    package_present: bool | None = None
    summary: str = ""


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    attempted: bool = False
    confirmation_supplied: bool = False
    command: tuple[str, ...] = ()
    exit_code: int | None = None
    pre_probe: ExecutionProbe | None = None
    post_probe: ExecutionProbe | None = None
    interactive_passthrough: bool = False
    summary: str = ""
