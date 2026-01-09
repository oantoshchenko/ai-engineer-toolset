"""Data models for service configuration and status."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ServiceStatus(Enum):
    """Service runtime status."""

    NOT_INSTALLED = "not_installed"
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    UNHEALTHY = "unhealthy"
    ERROR = "error"

    @property
    def symbol(self) -> str:
        """Return status indicator symbol."""
        symbols = {
            ServiceStatus.NOT_INSTALLED: "◌",
            ServiceStatus.STOPPED: "○",
            ServiceStatus.STARTING: "◐",
            ServiceStatus.RUNNING: "●",
            ServiceStatus.UNHEALTHY: "✕",
            ServiceStatus.ERROR: "✕",
        }
        return symbols[self]

    @property
    def color(self) -> str:
        """Return status color for TUI."""
        colors = {
            ServiceStatus.NOT_INSTALLED: "dim",
            ServiceStatus.STOPPED: "white",
            ServiceStatus.STARTING: "yellow",
            ServiceStatus.RUNNING: "green",
            ServiceStatus.UNHEALTHY: "red",
            ServiceStatus.ERROR: "red",
        }
        return colors[self]


@dataclass
class VendorConfig:
    """Vendor repository configuration."""

    url: str
    ref: str  # tag, branch, or commit


@dataclass
class PortConfig:
    """Port and health endpoint configuration."""

    name: str
    port: int
    health_endpoint: str | None = None


@dataclass
class EnvVarConfig:
    """Environment variable configuration."""

    name: str
    required: bool = False
    secret: bool = False
    default: str | None = None
    description: str | None = None


@dataclass
class LifecycleCommands:
    """Lifecycle management commands."""

    start: str | None = None
    stop: str | None = None
    restart: str | None = None
    install: str | None = None
    logs: str | None = None
    status: str | None = None


@dataclass
class ServiceConfig:
    """Service configuration loaded from service.yaml."""

    name: str
    description: str
    category: str  # core, optional, experimental
    path: Path  # Path to service directory
    vendor: VendorConfig | None = None
    ports: list[PortConfig] = field(default_factory=list)
    env_vars: list[EnvVarConfig] = field(default_factory=list)
    system_dependencies: list[str] = field(default_factory=list)
    service_dependencies: list[str] = field(default_factory=list)
    notes: dict[str, str] = field(default_factory=dict)
    lifecycle: LifecycleCommands = field(default_factory=LifecycleCommands)

    @property
    def dir_name(self) -> str:
        """Return the directory name (used as service ID)."""
        return self.path.name

    @property
    def primary_port(self) -> PortConfig | None:
        """Return the first port with a health endpoint, or first port."""
        for port in self.ports:
            if port.health_endpoint:
                return port
        return self.ports[0] if self.ports else None


@dataclass
class ServiceState:
    """Runtime state of a service."""

    config: ServiceConfig
    status: ServiceStatus = ServiceStatus.NOT_INSTALLED
    container_ids: list[str] = field(default_factory=list)
    error_message: str | None = None

