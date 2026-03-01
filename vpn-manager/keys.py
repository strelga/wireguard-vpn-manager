#!/usr/bin/env python3
"""
WireGuard Key Generation Module
"""

from pathlib import Path

from utils import KeyGenerator, Logger


class KeyManager:
    """WireGuard key generation utility"""

    def generate(self, output_directory: str | None = None) -> bool:
        """Generate WireGuard key pair"""
        try:
            Logger.info("Generating WireGuard key pair...")
            private_key, public_key = KeyGenerator.generate_keypair()

            if not private_key or not public_key:
                Logger.error("Failed to generate keys")
                return False

            if output_directory:
                output_dir = Path(output_directory)
                output_dir.mkdir(parents=True, exist_ok=True)

                private_file = output_dir / "private.key"
                public_file = output_dir / "public.key"

                # Write private key
                with open(private_file, "w") as f:
                    f.write(private_key)
                private_file.chmod(0o600)

                # Write public key
                with open(public_file, "w") as f:
                    f.write(public_key)
                public_file.chmod(0o644)

                Logger.success("Keys saved to:")
                Logger.info(f"  Private key: {private_file}")
                Logger.info(f"  Public key:  {public_file}")
            else:
                Logger.success("Generated key pair:")
                print(f"Private Key: {private_key}")
                print(f"Public Key:  {public_key}")

            return True

        except Exception as e:
            Logger.error(f"Key generation failed: {e}")
            return False
