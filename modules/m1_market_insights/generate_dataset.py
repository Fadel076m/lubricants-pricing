"""
Synthetic dataset generator — Lubricants Portfolio & Pricing Management System.

USAGE:
    python modules/m1_market_insights/generate_dataset.py
"""
from loguru import logger
from modules.m1_market_insights.data_generation import (
    generate_dataset,
    validate_dataset,
    print_summary,
    SEED,
    OUTPUT_DIR,
    OUTPUT_FILE,
)

def main() -> None:
    """Entry point: generate, validate, and save the dataset."""
    logger.info("Starting synthetic dataset generation")
    df = generate_dataset(seed=SEED)
    validate_dataset(df)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_FILE, index=False, engine="pyarrow")
    logger.success("Saved to {}", OUTPUT_FILE)
    
    print_summary(df)

if __name__ == "__main__":
    main()
