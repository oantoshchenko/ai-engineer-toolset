"""Service lifecycle management - start, stop, restart, install."""

import asyncio
import subprocess
from collections.abc import AsyncIterator
from pathlib import Path

from cli.services.models import ServiceConfig


class ServiceLifecycle:
    """Manages service lifecycle operations."""

    def __init__(self, services_dir: Path | None = None) -> None:
        """Initialize lifecycle manager.

        Args:
            services_dir: Path to services directory.
        """
        if services_dir is None:
            services_dir = Path(__file__).parent.parent.parent / "services"
        self.services_dir = services_dir

    async def start(self, config: ServiceConfig) -> tuple[bool, str]:
        """Start a service.

        Args:
            config: Service configuration.

        Returns:
            Tuple of (success, message).
        """
        if config.lifecycle.start:
            return await self._run_shell_command(config.path, config.lifecycle.start)
        # Fallback to docker-compose
        return await self._run_compose_command(config.path, ["up", "-d"])

    async def stop(self, config: ServiceConfig) -> tuple[bool, str]:
        """Stop a service.

        Args:
            config: Service configuration.

        Returns:
            Tuple of (success, message).
        """
        if config.lifecycle.stop:
            return await self._run_shell_command(config.path, config.lifecycle.stop)
        # Fallback to docker-compose
        return await self._run_compose_command(config.path, ["down"])

    async def restart(self, config: ServiceConfig) -> tuple[bool, str]:
        """Restart a service.

        Args:
            config: Service configuration.

        Returns:
            Tuple of (success, message).
        """
        if config.lifecycle.restart:
            return await self._run_shell_command(config.path, config.lifecycle.restart)

        # Fallback to stop + start
        stop_ok, stop_msg = await self.stop(config)
        if not stop_ok:
            return False, f"Failed to stop: {stop_msg}"

        start_ok, start_msg = await self.start(config)
        if not start_ok:
            return False, f"Failed to start: {start_msg}"

        return True, "Restarted successfully"

    async def install(self, config: ServiceConfig) -> AsyncIterator[str]:
        """Run the service's install/update script, streaming output.

        Args:
            config: Service configuration.

        Yields:
            Lines of output from the install script.
        """
        # Use custom install command if specified
        if config.lifecycle.install:
            process = await asyncio.create_subprocess_shell(
                config.lifecycle.install,
                cwd=config.path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        else:
            # Fallback to update.sh
            update_script = config.path / "update.sh"
            if not update_script.exists():
                yield f"Error: {update_script} not found and no lifecycle.install command"
                return

            process = await asyncio.create_subprocess_exec(
                str(update_script),
                cwd=config.path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

        if process.stdout is None:
            yield "Error: Could not capture output"
            return

        async for line in process.stdout:
            yield line.decode().rstrip()

        await process.wait()

        if process.returncode == 0:
            yield "✅ Install completed successfully"
        else:
            yield f"❌ Install failed with code {process.returncode}"

    async def logs(
        self, config: ServiceConfig, follow: bool = False, tail: int = 50
    ) -> AsyncIterator[str]:
        """Stream logs from a service.

        Args:
            config: Service configuration.
            follow: Whether to follow logs in real-time.
            tail: Number of lines to show initially.

        Yields:
            Log lines from the service.
        """
        # Use custom logs command if specified
        if config.lifecycle.logs:
            cmd = config.lifecycle.logs
            if follow:
                cmd = f"{cmd} -f"
            if tail:
                cmd = f"{cmd} --tail={tail}"

            process = await asyncio.create_subprocess_shell(
                cmd,
                cwd=config.path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        else:
            # Fallback to docker-compose logs
            cmd_list = ["docker", "compose", "logs", f"--tail={tail}"]
            if follow:
                cmd_list.append("-f")

            process = await asyncio.create_subprocess_exec(
                *cmd_list,
                cwd=config.path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

        if process.stdout is None:
            yield "Error: Could not capture logs"
            return

        async for line in process.stdout:
            yield line.decode().rstrip()

    async def _run_shell_command(
        self, service_path: Path, command: str
    ) -> tuple[bool, str]:
        """Run a shell command.

        Args:
            service_path: Path to service directory (working directory).
            command: Shell command to execute.

        Returns:
            Tuple of (success, output).
        """
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                cwd=service_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                return True, result.stdout or "Success"
            else:
                return False, result.stderr or result.stdout or "Unknown error"

        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    async def _run_compose_command(
        self, service_path: Path, args: list[str]
    ) -> tuple[bool, str]:
        """Run a docker compose command.

        Args:
            service_path: Path to service directory.
            args: Arguments to pass to docker compose.

        Returns:
            Tuple of (success, output).
        """
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["docker", "compose", *args],
                cwd=service_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                return True, result.stdout or "Success"
            else:
                return False, result.stderr or result.stdout or "Unknown error"

        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except FileNotFoundError:
            return False, "Docker not found"
        except Exception as e:
            return False, str(e)

