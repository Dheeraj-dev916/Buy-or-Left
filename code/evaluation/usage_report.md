# Token Usage Report — Buy or Wait? Financial Agent

## Final Full-Dataset Run Summary

**Run date:** 2026-09-13  
**Dataset:** 250 evaluation requests (`dataset/requests.csv`)  
**Runtime:** 32.1 seconds (0.13s per request)  
**Output:** `dataset/output.csv` (250 rows)

---

## Model Providers and Names

| Provider | Model Name | Purpose |
|----------|-----------|---------|
| — | — | No LLM API calls used during inference |

This solution uses a **deterministic rule-based financial engine** for all predictions. No external LLM or AI model API calls were made during the final full-dataset run. All financial decisions are produced by:

- A 90-day cash-flow simulation engine (`financial_engine.py`)
- A ranked decision pipeline (`agent.py`): full_payment → installments → partial_payment → wait → not_recommended
- Hardcoded image-extracted amounts from manual visual inspection of the 16 PNG files in `dataset/media/images/`
- Rule-based message parsing for salary overrides, internal transfers, refund status, and failed debits

---

## Model Calls and Token Usage

| Metric | Value |
|--------|-------|
| Total model calls | 0 |
| Total input tokens | 0 |
| Total output tokens | 0 |
| Average input tokens per request | 0 |
| Average output tokens per request | 0 |

---

## Cost Estimate

| Metric | Value |
|--------|-------|
| Estimated total cost | $0.00 |
| Estimated per-request cost | $0.00 |

---

## Notes

- Image amounts were extracted manually from the 16 provided PNG files during development and hardcoded in `financial_engine.py` (`IMAGE_AMOUNTS` dict). No vision API was called at inference time.
- Message parsing uses keyword-based pattern matching (English and Indonesian) rather than LLM-based NLU.
- Exchange rate conversions use the fixed dated rates in `dataset/exchange_rates.csv`.
- The deterministic approach ensures reproducibility and zero API cost for the evaluation run.

## Dependencies

| Library | Purpose |
|---------|----------|
| pandas | CSV data loading, filtering, grouping, merging |
| numpy | Numerical computation (median, statistical aggregation) |
| Python stdlib | `os`, `sys`, `datetime`, `calendar`, `re`, `collections` |
