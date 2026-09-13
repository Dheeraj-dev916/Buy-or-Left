"""
main.py
Entry point for the Buy-or-Wait? financial decision agent.

Usage:
    python main.py

Reads:  dataset/requests.csv  (all evaluation requests)
Writes: dataset/output.csv    (predictions in the required format)
"""

import os
import sys
import time
import pandas as pd

# Ensure the code directory is on the path so imports resolve correctly
CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from agent import run_batch

DATA_DIR = os.path.join(CODE_DIR, '..', 'dataset')
REQUESTS_CSV = os.path.join(DATA_DIR, 'requests.csv')
OUTPUT_CSV   = os.path.join(DATA_DIR, 'output.csv')

# Required output columns in the exact order specified by the challenge
OUTPUT_COLUMNS = [
    'request_id',
    'amount_safe_to_pay',
    'affordability_status',
    'recommended_payment_method',
    'payment_plan',
    'earliest_date_for_full_payment',
    'spending_changes_needed',
    'decision_explanation',
]


def main():
    print("=" * 60)
    print("Buy or Wait? — Financial Decision Agent")
    print("=" * 60)

    # Load requests
    print(f"\nLoading requests from: {REQUESTS_CSV}")
    requests_df = pd.read_csv(REQUESTS_CSV)
    total = len(requests_df)
    print(f"Total requests to process: {total}")

    # Run agent
    print("\nRunning agent on all requests...")
    t0 = time.time()
    results_df = run_batch(requests_df)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s  ({elapsed/total:.2f}s per request)")

    # Ensure all required columns are present and in the right order
    for col in OUTPUT_COLUMNS:
        if col not in results_df.columns:
            results_df[col] = ''
    results_df = results_df[OUTPUT_COLUMNS]

    # Write output
    results_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nOutput written to: {OUTPUT_CSV}")
    print(f"Rows written: {len(results_df)}")

    # Quick status summary
    if 'affordability_status' in results_df.columns:
        print("\nAffordability breakdown:")
        print(results_df['affordability_status'].value_counts().to_string())
    if 'recommended_payment_method' in results_df.columns:
        print("\nPayment method breakdown:")
        print(results_df['recommended_payment_method'].value_counts().to_string())

    print("\nDone!")


if __name__ == '__main__':
    main()
