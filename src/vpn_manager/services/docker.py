import subprocess

from vpn_manager.utils import Logger


class DockerManager:
    """Docker management utility"""

    @staticmethod
    def get_compose_command() -> str:
        """Determine available docker-compose command"""
        if DockerManager._command_exists("docker-compose"):
            return "docker-compose"
        elif DockerManager._command_exists("docker"):
            # Check if 'docker compose' works
            try:
                subprocess.run(
                    ["docker", "compose", "version"], capture_output=True, check=True
                )
                return "docker compose"
            except subprocess.CalledProcessError:
                pass

        raise RuntimeError("Neither docker-compose nor 'docker compose' is available")

    @staticmethod
    def _command_exists(command: str) -> bool:
        """Check if command exists"""
        try:
            subprocess.run([command, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def restart_container(container_name: str) -> bool:
        """Restart specific container"""
        try:
            compose_cmd = DockerManager.get_compose_command().split()
            subprocess.run(
                compose_cmd + ["restart", container_name],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to restart container {container_name}: {e}")
            return False

    @staticmethod
    def start_services() -> bool:
        """Start all services"""
        try:
            compose_cmd = DockerManager.get_compose_command().split()
            subprocess.run(compose_cmd + ["up", "-d"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to start services: {e}")
            return False

    @staticmethod
    def stop_services() -> bool:
        """Stop all services"""
        try:
            compose_cmd = DockerManager.get_compose_command().split()
            subprocess.run(compose_cmd + ["down"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to stop services: {e}")
            return False

    @staticmethod
    def run_container(image: str, command: list[str], input_data: str | None = None) -> str:
        """Run a command in a Docker container and return stdout"""
        try:
            cmd = ["docker", "run", "--rm"]
            if input_data is not None:
                cmd.append("-i")
            cmd.extend([image] + command)
            result = subprocess.run(
                cmd, input=input_data, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to run container command: {e}") from e
