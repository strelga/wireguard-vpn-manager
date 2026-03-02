from vpn_manager.utils import Logger


def validate_client_name(client_name: str) -> bool:
    """Validate client name"""
    if not client_name or not client_name.replace("-", "").replace("_", "").isalnum():
        Logger.error(
            "Client name must contain only alphanumeric characters, hyphens, and underscores"
        )
        return False
    return True
