# User Analytics Pipeline

A small data processing pipeline that loads user activity records,
computes per-user statistics, and generates a summary report.

## Structure

- `models.py` — Data classes and validation helpers
- `data_loader.py` — Loads and parses raw user activity data
- `processor.py` — Computes statistics from loaded user records
- `main.py` — Entry point that ties the pipeline together

## Running

```bash
python main.py
```

## Testing

```bash
python -m pytest test_pipeline.py -v
```

## Overview

The pipeline works in three stages:

1. **Load**: `data_loader.load_user_records()` reads raw activity data and
   returns structured user records.
2. **Process**: `processor.compute_user_stats()` takes the loaded records
   and computes per-user statistics (total activity, average score, etc.).
3. **Report**: `main.generate_report()` formats the statistics into a
   human-readable summary.

Each stage is independently testable. The test suite in `test_pipeline.py`
covers individual functions and the end-to-end pipeline.
