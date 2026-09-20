"""Minimal integration facade for RL training harnesses."""
from pathlib import Path
from config.task import TASK_PROMPT
from environment.api import BusinessEnvironment
from environment.database import build_database
from validator.engine import validate
from config.constants import TASK_ID


def initialize(data_dir: str | Path) -> str:
    """Create deterministic task data and return the SQLite path."""
    db_path = Path(data_dir) / "business.sqlite"
    build_database(db_path).close()
    return str(db_path)


def get_task(db_path: str):
    """Return the task bundle expected by a simple RLVR harness."""
    return {
        "task_id": TASK_ID,
        "prompt": TASK_PROMPT,
        "environment_factory": lambda: BusinessEnvironment(db_path),
        "validator": lambda agent_output: validate(TASK_PROMPT, agent_output, db_path),
    }
