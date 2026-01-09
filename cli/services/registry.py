"""Service discovery and registry."""

from pathlib import Path

import yaml

from cli.services.models import (
    EnvVarConfig,
    LifecycleCommands,
    PortConfig,
    ServiceConfig,
    VendorConfig,
)


class ServiceRegistry:
    """Discovers and manages service configurations."""

    def __init__(self, services_dir: Path | None = None) -> None:
        """Initialize registry with services directory.

        Args:
            services_dir: Path to services directory. Defaults to ./services
        """
        if services_dir is None:
            # Find services dir relative to this file or cwd
            services_dir = Path(__file__).parent.parent.parent / "services"
            if not services_dir.exists():
                services_dir = Path.cwd() / "services"
        self.services_dir = services_dir
        self._cache: dict[str, ServiceConfig] = {}

    def discover(self) -> list[ServiceConfig]:
        """Scan services directory for service.yaml files.

        Returns:
            List of discovered service configurations.
        """
        services: list[ServiceConfig] = []

        if not self.services_dir.exists():
            return services

        for service_path in sorted(self.services_dir.iterdir()):
            if not service_path.is_dir():
                continue

            config_file = service_path / "service.yaml"
            if not config_file.exists():
                continue

            try:
                config = self._load_config(config_file, service_path)
                services.append(config)
                self._cache[config.dir_name] = config
            except Exception as e:
                # Log but don't fail on individual service errors
                print(f"Warning: Failed to load {config_file}: {e}")

        return services

    def get(self, name: str) -> ServiceConfig | None:
        """Get a specific service by directory name.

        Args:
            name: Service directory name (e.g., 'openmemory')

        Returns:
            ServiceConfig if found, None otherwise.
        """
        if name in self._cache:
            return self._cache[name]

        # Try to load directly
        service_path = self.services_dir / name
        config_file = service_path / "service.yaml"

        if config_file.exists():
            config = self._load_config(config_file, service_path)
            self._cache[name] = config
            return config

        return None

    def _load_config(self, config_file: Path, service_path: Path) -> ServiceConfig:
        """Load and parse a service.yaml file.

        Args:
            config_file: Path to service.yaml
            service_path: Path to service directory

        Returns:
            Parsed ServiceConfig
        """
        with open(config_file) as f:
            data = yaml.safe_load(f)

        # Parse vendor config
        vendor = None
        if data.get("vendor"):
            vendor = VendorConfig(
                url=data["vendor"]["url"],
                ref=data["vendor"]["ref"],
            )

        # Parse ports
        ports = [
            PortConfig(
                name=p["name"],
                port=p["port"],
                health_endpoint=p.get("health_endpoint"),
            )
            for p in data.get("ports", [])
        ]

        # Parse env vars
        env_vars = [
            EnvVarConfig(
                name=e["name"],
                required=e.get("required", False),
                secret=e.get("secret", False),
                default=e.get("default"),
                description=e.get("description"),
            )
            for e in data.get("env_vars", [])
        ]

        # Parse dependencies
        deps = data.get("dependencies", {})
        system_deps = deps.get("system", [])
        service_deps = deps.get("services", [])

        # Parse lifecycle commands
        lifecycle_data = data.get("lifecycle", {})
        lifecycle = LifecycleCommands(
            start=lifecycle_data.get("start"),
            stop=lifecycle_data.get("stop"),
            restart=lifecycle_data.get("restart"),
            install=lifecycle_data.get("install"),
            logs=lifecycle_data.get("logs"),
            status=lifecycle_data.get("status"),
        )

        return ServiceConfig(
            name=data["name"],
            description=data["description"],
            category=data.get("category", "optional"),
            path=service_path,
            vendor=vendor,
            ports=ports,
            env_vars=env_vars,
            system_dependencies=system_deps,
            service_dependencies=service_deps,
            notes=data.get("notes", {}),
            lifecycle=lifecycle,
        )

