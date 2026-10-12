import os

def load_env(env_path: str = None) -> None:
    """
    Loads key-value pairs from a local .env file into os.environ
    without overwriting existing environment variables.
    """
    if env_path is None:
        candidates = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
            os.path.abspath(".env"),
            "/data/.env"
        ]
        for c in candidates:
            if os.path.exists(c):
                env_path = c
                break

    if not env_path or not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    curr = os.environ.get(k, "")
                    # Load if missing, empty, or currently set to placeholder string
                    if k and (not curr or "your_client_id_here" in curr or "your_client_secret_here" in curr or curr == "your_postgres_password_here"):
                        os.environ[k] = v
    except Exception:
        pass

# Automatically run on import
load_env()
