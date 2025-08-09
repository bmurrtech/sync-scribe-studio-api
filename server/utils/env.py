import os

def get_required_env(var_name: str) -> str:
    """
    Get an environment variable, raising a RuntimeError if it's not set.
    This function is designed to be called at request time, not at import time.
    """
    value = os.getenv(var_name)
    if value is None:
        raise RuntimeError(f"{var_name} environment variable is required")
    return value
