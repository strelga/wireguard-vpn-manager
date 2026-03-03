import subprocess

from vpn_manager.utils import Logger


class DockerManager:
    """Docker management utility for direct docker commands"""

    @staticmethod
    def _image_exists(image: str) -> bool:
        """Check if Docker image exists locally"""
        try:
            subprocess.run(
                ["docker", "image", "inspect", image],
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def _pull_image(image: str) -> bool:
        """Pull Docker image if it doesn't exist locally"""
        if DockerManager._image_exists(image):
            Logger.info(f"Docker image already exists: {image}")
            return True

        try:
            Logger.info(f"Pulling Docker image: {image}")
            Logger.info("This may take a while on first run...")
            # Allow docker pull to show progress in terminal
            subprocess.run(
                ["docker", "pull", image],
                check=True,
            )
            Logger.success(f"Successfully pulled image: {image}")
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to pull image {image}: {e}")
            return False

    @staticmethod
    def run_container(image: str, command: list[str], input_data: str | None = None, capture_output: bool = True) -> str:
        """Run a command in a Docker container and return stdout

        Args:
            image: Docker image to use
            command: Command to run in the container
            input_data: Optional input data to pipe to the command
            capture_output: If True, capture output and return it. If False, output goes to terminal

        Returns:
            Command output if capture_output=True, empty string otherwise
        """
        # Ensure image exists locally
        Logger.info(f"Preparing to run command in container: {' '.join(command)}")
        if not DockerManager._pull_image(image):
            raise RuntimeError(f"Failed to ensure image {image} is available")

        try:
            cmd = ["docker", "run", "--rm", "-t", "-e", "PUID=1000", "-e", "PGID=1000"]
            if input_data is not None:
                cmd.append("-i")
            cmd.extend([image] + command)
            Logger.info(f"Executing: {' '.join(cmd)}")

            if capture_output:
                result = subprocess.run(
                    cmd, input=input_data, capture_output=True, text=True, check=True
                )
                return result.stdout.strip()
            else:
                # Let output go to terminal
                subprocess.run(
                    cmd, input=input_data, text=True, check=True
                )
                return ""
        except subprocess.CalledProcessError as e:
            Logger.error(f"Command failed with exit code {e.returncode}")
            if capture_output and e.stderr:
                Logger.error(f"Error output: {e.stderr}")
            raise RuntimeError(f"Failed to run container command: {e}") from e


class DockerComposeManager:
    """Docker Compose management utility"""

    _compose_command: list[str] | None

    def __init__(self):
        """Initialize DockerComposeManager"""
        self._compose_command = None

    def _get_compose_command(self) -> list[str]:
        """Determine available docker-compose command (lazy initialization)"""
        if self._compose_command is None:
            if self._command_exists("docker-compose"):
                self._compose_command = ["docker-compose"]
            elif self._command_exists("docker"):
                # Check if 'docker compose' works
                try:
                    subprocess.run(
                        ["docker", "compose", "version"], capture_output=True, check=True
                    )
                    self._compose_command = ["docker", "compose"]
                except subprocess.CalledProcessError:
                    pass

            if self._compose_command is None:
                raise RuntimeError("Neither docker-compose nor 'docker compose' is available")

        return self._compose_command

    @staticmethod
    def _command_exists(command: str) -> bool:
        """Check if command exists"""
        try:
            subprocess.run([command, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _run_command(self, args: list[str], capture_output: bool = False, **kwargs) -> subprocess.CompletedProcess:
        """Run docker-compose command with given arguments"""
        compose_cmd = self._get_compose_command()
        return subprocess.run(compose_cmd + args, check=True, capture_output=capture_output, **kwargs)

    def restart_container(self, container_name: str) -> bool:
        """Restart specific container by recreating it with updated environment"""
        try:
            # Use 'up -d' instead of 'restart' to recreate container with new environment variables
            self._run_command(["up", "-d", container_name])
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to restart container {container_name}: {e}")
            return False

    def pull_services(self) -> bool:
        """Pull all service images"""
        try:
            Logger.info("Pulling Docker images for services...")
            self._run_command(["pull"])
            Logger.success("Successfully pulled all service images")
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to pull service images: {e}")
            return False

    def start_services(self) -> bool:
        """Start all services"""
        try:
            self._run_command(["up", "-d"])
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to start services: {e}")
            return False

    def stop_services(self) -> bool:
        """Stop all services"""
        try:
            self._run_command(["down"])
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to stop services: {e}")
            return False

    def start_container(self, container_name: str) -> bool:
        """Start specific container"""
        try:
            self._run_command(["up", "-d", container_name])
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to start container {container_name}: {e}")
            return False

    def stop_container(self, container_name: str) -> bool:
        """Stop specific container"""
        try:
            self._run_command(["stop", container_name])
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to stop container {container_name}: {e}")
            return False

    def restart_all_services(self) -> bool:
        """Restart all services"""
        try:
            self._run_command(["restart"])
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to restart all services: {e}")
            return False

    def get_container_status(self, container_name: str | None = None) -> str:
        """Get status of specific container or all services"""
        try:
            args = ["ps", container_name] if container_name else ["ps"]
            result = self._run_command(args, capture_output=True, text=True)
            return str(result.stdout)
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get container status: {e}")
            return ""

    def exec_container(self, container_name: str, command: list[str]) -> bool:
        """Execute command in container"""
        try:
            self._run_command(["exec", container_name] + command)
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to execute command in container {container_name}: {e}")
            return False

    def get_container_logs(
        self, container_name: str | None = None, follow: bool = False, tail: int = 100
    ) -> bool:
        """Get logs for specific container or all services"""
        try:
            cmd = ["logs"]
            if follow:
                cmd.append("-f")
            cmd.append(f"--tail={tail}")
            if container_name:
                cmd.append(container_name)
            self._run_command(cmd)
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get container logs: {e}")
            return False
