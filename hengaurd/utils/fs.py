from pathlib import Path

def safe_mkdir(path: Path):
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Failed to create directory {path}: {e}")