# Datasets Folder

Paste your Kaggle CSV files into `datasets/raw/`.

## Current status

- Raw source used: `datasets/raw/amazon.csv`
- Processed outputs generated in: `datasets/processed/`

## Recommended filenames

- `catalog.csv`
- `reviews.csv`
- `pricing.csv`
- `competitors.csv`
- `performance_signals.csv`

## Minimum required columns

### `catalog.csv`
- `sku`
- `category`
- `price`
- `stock`
- `features`

### `reviews.csv`
- `sku`
- `rating`
- `review_text`

### `pricing.csv`
- `sku`
- `our_price`
- `competitor`
- `competitor_price`
- `tier` (optional but recommended)

### `competitors.csv`
- `competitor`
- `competitor_sku`
- `category`
- `price`
- `features`

### `performance_signals.csv`
- `sku`
- `views`
- `conversions`
- `returns`

## Next step

After pasting files, tell me and I will map/clean them into the exact format your agent expects.

## Auto-process command

Run this from project root:

```bash
python3 src/prepare_datasets.py --raw datasets/raw/amazon.csv --out-dir datasets/processed --limit 8000
```

Generated files:

- `datasets/processed/catalog.json`
- `datasets/processed/reviews.json`
- `datasets/processed/pricing.json`
- `datasets/processed/competitors.json`
- `datasets/processed/performance_signals.json`
- `datasets/processed/summary.json`
- `datasets/processed/brief_deep_kaggle.json`

## Important data-quality note

- `competitors.json` and `performance_signals.json` are derived for schema compatibility.
- Replace them with true competitor/performance feeds for production-grade accuracy.
