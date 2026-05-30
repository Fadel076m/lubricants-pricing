"""Configuration constants for data generation."""
from pathlib import Path
from typing import Final

SEED: Final[int] = 42
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "data" / "synthetic"
OUTPUT_FILE: Final[Path] = OUTPUT_DIR / "transactions.parquet"

START_DATE: Final[str] = "2022-01"
END_DATE: Final[str] = "2024-12"
N_MONTHS: Final[int] = 36
EXPECTED_ROWS: Final[int] = 14_400  # 20 SKU × 5 canaux × 4 régions × 36 mois
