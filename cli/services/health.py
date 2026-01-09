"""Health monitoring for services."""

import asyncio
import subprocess
from pathlib import Path

import httpx

from cli.services.models import PortConfig, ServiceConfig, ServiceStatus


class HealthMonitor:
    """Monitors service health via Docker and HTTP endpoints."""

    def __init__(self, timeout: float = 2.0) -> None:
        """Initialize health monitor.

        Args:
            timeout: HTTP request timeout in seconds.
        """
        self.timeout = timeout

    async def check(self, config: ServiceConfig) -> ServiceStatus:
        """Check the health status of a service.

        Args:
            config: Service configuration.

        Returns:
            Current service status.
        """
        # Use custom status command if specified
        if config.lifecycle.status:
            return await self._check_custom_status(config)

        # Fallback to docker-compose status check
        container_status = await self._check_docker_status(config.path)

        if container_status == ServiceStatus.NOT_INSTALLED:
            return ServiceStatus.NOT_INSTALLED

        if container_status == ServiceStatus.STOPPED:
            return ServiceStatus.STOPPED

        # Containers are running, check health endpoints
        if config.primary_port and config.primary_port.health_endpoint:
            health_ok = await self._check_health_endpoint(config.primary_port)
            if health_ok:
                return ServiceStatus.RUNNING
            else:
                return ServiceStatus.UNHEALTHY

        # No health endpoint, assume running if containers are up
        return ServiceStatus.RUNNING

    async def check_all(
        self, configs: list[ServiceConfig]
    ) -> dict[str, ServiceStatus]:
        """Check health of multiple services concurrently.

        Args:
            configs: List of service configurations.

        Returns:
            Dict mapping service dir_name to status.
        """
        tasks = [self.check(config) for config in configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        statuses: dict[str, ServiceStatus] = {}
        for config, result in zip(configs, results, strict=True):
            if isinstance(result, BaseException):
                statuses[config.dir_name] = ServiceStatus.ERROR
            else:
                statuses[config.dir_name] = result

        return statuses

    async def _check_docker_status(self, service_path: Path) -> ServiceStatus:
        """Check if Docker containers are running for a service.

        Args:
            service_path: Path to service directory with docker-compose.yml

        Returns:
            ServiceStatus based on container state.
        """
        # Find docker-compose file
        compose_file = None
        for name in ["docker-compose.yml", "docker-compose.yaml"]:
            candidate = service_path / name
            if candidate.exists():
                compose_file = candidate
                break

        if compose_file is None:
            return ServiceStatus.NOT_INSTALLED

        try:
            # Run docker compose ps to check container status
            result = await asyncio.to_thread(
                subprocess.run,
                ["docker", "compose", "ps", "--format", "json", "-q"],
                cwd=service_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return ServiceStatus.ERROR

            # If no container IDs returned, service is stopped
            container_ids = result.stdout.strip()
            if not container_ids:
                return ServiceStatus.STOPPED

            return ServiceStatus.RUNNING

        except subprocess.TimeoutExpired:
            return ServiceStatus.ERROR
        except FileNotFoundError:
            # Docker not installed
            return ServiceStatus.ERROR

    async def _check_health_endpoint(self, port: PortConfig) -> bool:
        """Check if a health endpoint responds successfully.

        Args:
            port: Port configuration with health endpoint.

        Returns:
            True if endpoint responds with 2xx status.
        """
        if not port.health_endpoint:
            return True

        url = f"http://localhost:{port.port}{port.health_endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                return response.is_success
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    async def _check_custom_status(self, config: ServiceConfig) -> ServiceStatus:
        """Check status using a custom command.

        Args:
            config: Service configuration with lifecycle.status command.

        Returns:
            Service status based on command exit code.
        """
        import asyncio
        import subprocess
        from functools import partial

        if not config.lifecycle.status:
            return ServiceStatus.ERROR

        try:
            run_cmd = partial(
                subprocess.run,
                config.lifecycle.status,
                shell=True,
                cwd=config.path,
                capture_output=True,
                timeout=10,
            )
            result = await asyncio.to_thread(run_cmd)

            # Exit code 0 = running, non-zero = stopped/error
            if result.returncode == 0:
                return ServiceStatus.RUNNING
            else:
                return ServiceStatus.STOPPED

        except subprocess.TimeoutExpired:
            return ServiceStatus.ERROR
        except Exception:
            return ServiceStatus.ERROR



