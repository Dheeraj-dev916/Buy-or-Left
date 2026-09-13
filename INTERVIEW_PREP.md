# Buy or Wait? — Complete Project Documentation
## Interview Preparation Guide

---

## 1. Project Overview

**Project Name:** Buy or Wait? — AI-Powered Financial Decision Agent  
**Hackathon:** HackerRank Orchestrate (September 2026, 24-hour challenge)  
**Problem:** Build a system that decides whether a user can safely afford a requested expense, considering their entire financial picture — not just their current balance.

**One-liner:** A deterministic financial agent that simulates a user's cash flow over 90 days and recommends the safest way to pay for a purchase, trip, investment, or other expense.

---

## 2. Problem Statement (What the Agent Solves)

For every purchase/payment request, the agent must answer:
- **Can the user afford it right now?** (full payment today)
- **Can they afford it with a plan?** (installments, partial payment, or spending changes)
- **Can they afford it later?** (wait for a safer date)
- **Can they not afford it at all?** (not recommended)

The recommendation must be **personalized** — two users with the same balance may get different recommendations based on their:
- Recurring expenses and income patterns
- Pending payments and confirmed future transactions
- Protected expense categories (rent, groceries, etc.)
- Willingness to adjust flexible spending
- Payment preferences (full, installments, partial)
- Financial priorities and minimum balance requirements

---

## 3. Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Language** | Python 3 | Fast prototyping, rich data ecosystem |
| **Data Processing** | pandas | CSV loading, filtering, grouping, merging |
| **Numerics** | numpy | Median calculation, statistical aggregation |
| **Standard Library** | `os`, `sys`, `datetime`, `calendar`, `re`, `collections` | File paths, dates, regex parsing, hash maps |
| **AI/ML** | None at inference | 100% deterministic rule-based engine |
| **API Calls** | None | Fully offline, zero cost per request |
| **Runtime** | ~32 seconds for 250 requests | 0.13s per request |

**Key decision:** We chose a **deterministic rule-based approach** over LLM-based reasoning because:
- Reproducible results (same input → same output)
- Zero API cost ($0.00 for the entire run)
- No latency concerns
- No hallucination risk on financial calculations
- Full auditability of every decision

---

## 4. Architecture

### 4.1 Three-Layer Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────┐
│   main.py   │ ──▶ │   agent.py   │ ──▶ │ financial_engine.py │
│  (CLI Entry)│     │  (Decisions) │     │  (Cashflow Sim)    │
└─────────────┘     └──────────────┘     └────────────────────┘
```

**Dependency direction is strictly one-way:** `main.py` → `agent.py` → `financial_engine.py`. The engine layer has no imports back into the agent.

### 4.2 Layer Responsibilities

| Layer | File | Responsibility |
|-------|------|---------------|
| **Entry** | `main.py` | Load `requests.csv`, call `run_batch()`, enforce column order, write `output.csv` |
| **Orchestrator** | `agent.py` | Cache datasets, build financial state, run decision pipeline, generate explanations |
| **Engine** | `financial_engine.py` | 90-day cashflow simulation, recurring pattern detection, exchange rates, message parsing, safety algorithms |

### 4.3 Data Flow

```
dataset/requests.csv ──▶ main.py ──▶ agent.run_batch()
                                          │
                    ┌─────────────────────┘
                    ▼
              For each request:
                    │
                    ├──▶ get_data() (cached CSVs)
                    │     ├── financial_profiles.csv
                    │     ├── financial_events.csv
                    │     ├── messages.csv
                    │     ├── exchange_rates.csv
                    │     └── request_payment_options.csv
                    │
                    ├──▶ financial_engine.get_user_financial_state()
                    │     ├── Apply image amounts to events
                    │     ├── Parse messages for salary/date overrides
                    │     ├── Identify recurring expenses from history
                    │     ├── Identify recurring income from history
                    │     ├── Project 90-day cashflow
                    │     └── Return structured state
                    │
                    ├──▶ compute_amount_safe_to_pay()
                    ├──▶ compute_earliest_full_payment_date()
                    │
                    └──▶ Decision Pipeline (priority order):
                          1. Full payment
                          2. Installments
                          3. Partial payment
                          4. Full payment + spending changes
                          5. Partial payment + spending changes
                          6. Wait
                          7. Not recommended
```

---

## 5. How It Works — Detailed Workflow

### Step 1: Load User Financial Profile
From `financial_profiles.csv`:
- **home_currency** — user's primary currency (INR, ZAR, IDR, USD, EUR)
- **current_available_balance** — money available right now
- **minimum_balance_to_keep** — floor the user never wants to breach
- **financial_priorities** — what matters most (education, retirement, etc.)
- **expense_categories_to_protect** — categories that can't be cut (rent, groceries)
- **expense_categories_user_is_willing_to_reduce** — flexible categories
- **expense_categories_user_is_willing_to_stop** — stoppable categories
- **payment_methods_user_will_consider** — which methods the user accepts
- **max_installment_months** — maximum installment duration the user allows

### Step 2: Parse Messages
From `messages.csv` — 216 messages from 5 source types:

| Source | What it communicates | How we handle it |
|--------|---------------------|-----------------|
| **employer** | Salary changes, date shifts, unpaid leave | Extract salary override amount and date (English + Indonesian keywords) |
| **bank** | Internal transfers, failed debits | Ignore transfer events (same account holder), track failed retries |
| **merchant** | Pending refunds | Don't count as income until settled |
| **financial_service** | Unrealized investment gains | Don't count as available cash |
| **service_provider** | Pending payouts | Don't count until completed |

**Salary parsing logic:**
- Only triggers on **explicit change signals**: "reduced", "temporary", "unpaid leave" (English) or "gaji sementara", "tanpa gaji", "dikurangi" (Indonesian)
- Takes the **first currency amount** match to avoid picking up one-time adjustments
- Also detects **salary date overrides** when messages say salary is "expected on" or "confirmed for" a specific date

### Step 3: Identify Recurring Patterns
From `financial_events.csv` — 25,342 historical events:

**Recurring Expenses:**
- Group settled debit events by `(description, category, flexibility)`
- Require ≥2 occurrences across ≥2 different months
- Calculate average amount and typical day of month
- Preserve flexibility type: `fixed`, `stoppable`, `reducible`, `reducible_or_stoppable`

**Recurring Income:**
- Group settled salary credit events by day of month
- Use most recent salary amount (or message override)
- Project forward monthly over the 90-day window

### Step 4: 90-Day Cashflow Simulation
The `build_daily_cashflows()` function projects the user's balance day-by-day for 90 days:

```
Day 0:  current_balance
Day 1:  balance + scheduled debits/credits on day 1
Day 2:  balance + scheduled debits/credits on day 2
...
Day 90: balance + recurring expenses + recurring income
```

**What goes into the projection:**
1. **Pending/scheduled debits** — future confirmed payments (reserved)
2. **Scheduled credits** — confirmed salary (counted)
3. **Recurring expenses** — projected monthly from historical patterns
4. **Recurring income** — projected monthly salary from history
5. **Currency conversion** — all amounts converted to home currency using dated exchange rates (with ±7 day fallback)

**What is excluded (per challenge rules):**
- Pending credits (not yet settled)
- Failed/cancelled transactions
- Unrealized investment values
- Bonuses, commissions, lottery proceeds

### Step 5: Safety Algorithms

**`compute_amount_safe_to_pay()`:**
```
baseline_min = minimum balance across all 90 projected days (from payment day onward)
headroom = baseline_min - minimum_balance_to_keep
safe_amount = max(0, min(requested_amount, headroom))
```

**`compute_earliest_full_payment_date()`:**
```
For each day 0 to 90:
  simulated_balances = [projected_balance - requested_amount for all future days]
  if all simulated_balances >= minimum_balance_to_keep:
    return this date as the earliest safe full-payment date
return None (never becomes safe)
```

**`test_plan_safety()`:**
```
Given a payment schedule [(day_offset, amount), ...]:
  subtract each payment from all subsequent projected balances
  if all adjusted balances >= minimum_balance_to_keep:
    plan is safe
```

### Step 6: Decision Pipeline (Priority Order)

```
1. FULL PAYMENT (affordable_now)
   Condition: user accepts full_payment AND safe_amount >= requested_amount
   Result: Pay full amount today

2. INSTALLMENTS (affordable_with_plan)
   Condition: user accepts installments
   Process: Evaluate each installment option from request_payment_options.csv
            - Build payment schedule from first_payment_date + frequency
            - Test safety against 90-day balance curve
            - Respect max_installment_months from profile
   Ranking: Deadline compliance → lowest total cost → earliest start → 
            fewer payments → lowest option_id

3. PARTIAL PAYMENT (affordable_with_plan)
   Condition: user accepts partial_payment AND request allows it AND
              0 < safe_amount < requested_amount AND
              earliest_full_date <= desired_completion_date
   Plan: Pay safe_amount today + remainder on earliest_full_date

4. SPENDING CHANGES — Full Payment
   Condition: shortfall exists AND flexible expenses can cover it
   Process: Find stoppable/reducible recurring expenses in categories 
            user is willing to adjust (not protected)
   Max 3 changes: stop:<event_id> or reduce_to:<event_id>:<new_amount>

5. SPENDING CHANGES — Partial Payment
   Same as above but for partial payment scenario

6. WAIT (affordable_later)
   Condition: user accepts full_payment AND earliest_full_date exists
              AND earliest_full_date <= desired_completion_date
   Result: Wait and pay full amount on earliest_full_date

7. NOT RECOMMENDED (not_affordable)
   Fallback: No safe plan found within the forecast period
```

### Step 7: Generate Output
For each request, produce one row with:

| Field | Description |
|-------|------------|
| `amount_safe_to_pay` | Max safe amount today (0 ≤ x ≤ requested_amount) |
| `affordability_status` | `affordable_now`, `affordable_with_plan`, `affordable_later`, `not_affordable` |
| `recommended_payment_method` | `full_payment`, `installments`, `partial_payment`, `wait`, `not_recommended` |
| `payment_plan` | Chronological `YYYY-MM-DD:amount` entries separated by `\|`, or `none` |
| `earliest_date_for_full_payment` | First safe date for full payment (equals request_date if affordable_now) |
| `spending_changes_needed` | Up to 3 `stop:` / `reduce_to:` actions, or `none` |
| `decision_explanation` | Human-readable summary of balance, headroom, and recommendation |

---

## 6. Dataset Schema

### 6.1 Input Files

| File | Rows | Key Columns | Purpose |
|------|------|-------------|---------|
| `requests.csv` | 250 | request_id, user_id, request_date, requested_amount, desired_completion_date, allows_partial_payment | Payment requests to evaluate |
| `financial_profiles.csv` | 276 | user_id, home_currency, current_available_balance, minimum_balance_to_keep, payment_methods_user_will_consider | User financial preferences |
| `financial_events.csv` | 25,342 | event_id, user_id, direction, amount, currency, event_date, status, flexibility | Historical and future transactions |
| `exchange_rates.csv` | ~500 | rate_date, from_currency, to_currency, rate | Fixed dated conversion rates |
| `request_payment_options.csv` | 791 | request_id, payment_method, payment_amount, number_of_payments, financing_fee | Available payment plans |
| `messages.csv` | 216 | user_id, request_id, source_type, message_text | Notifications from employers/banks/merchants |
| `images.csv` | 17 | image_id, user_id, related_event_id | Links images to events |
| `sample_requests.csv` | 25 | Same as requests + all output columns | Golden examples for format reference |

### 6.2 Event Types and Classifications

**Statuses:** settled (25,148), pending (71), scheduled (70), cancelled (22), failed (21), unrealized (10)

**Directions:** debit (23,609), credit (1,723), non_cash (10)

**Flexibility values:** fixed (21,138), reducible (2,682), stoppable (1,297), reducible_or_stoppable (225)

**Currencies:** INR, ZAR, IDR, USD, EUR

---

## 7. Key Design Decisions

### 7.1 Why Deterministic Over LLM?

| Factor | Deterministic | LLM-based |
|--------|-------------|-----------|
| Reproducibility | Same input → same output | Non-deterministic |
| Cost | $0.00 | $5-50 per run |
| Speed | 32 seconds | Minutes |
| Auditability | Every decision traceable | Black box |
| Hallucination | Impossible | Risk of invented facts |
| Accuracy on math | Exact | Can miscalculate |

### 7.2 Image Amount Handling
Instead of calling a vision API at runtime, we **manually inspected all 16 images** during development and hardcoded the extracted amounts in a dictionary:
```python
IMAGE_AMOUNTS = {
    'event_253': 4365000.0,   # Pay slip: IDR net pay
    'event_1442': 100000.0,   # Rent receipt: INR balance due
    'event_1545': 41272.0,    # Bill of Supply: INR net amount
    # ... 13 more entries
}
```
This ensures zero latency and zero cost while maintaining accuracy.

### 7.3 Spending Change Logic
The flexibility field has **4 values**, not a generic "flexible":
- **`stoppable`** → can be cut to zero (e.g., delivery membership)
- **`reducible`** → can be reduced to `minimum_allowed_amount` (e.g., streaming plan)
- **`reducible_or_stoppable`** → either option available
- **`fixed`** → cannot be changed (e.g., rent, utilities)

Spending changes only apply to:
- Non-protected categories (not in user's `expense_categories_to_protect`)
- Categories the user is willing to reduce or stop
- Recurring expenses with ≥2 historical occurrences across ≥2 months

### 7.4 Installment Ranking
When multiple installment options are safe, we rank by:
1. **Completes by deadline** — does the last payment land before `desired_completion_date`?
2. **Lowest total cost** — minimize `total_payable_amount` (includes financing fees)
3. **Earliest start** — prefer plans that begin sooner
4. **Fewer payments** — fewer installments is simpler
5. **Lowest option_id** — deterministic tie-breaker

---

## 8. Challenges Faced & Solutions

### Challenge 1: Multi-Currency Handling
**Problem:** Users have balances in INR, ZAR, IDR, USD, EUR. Events may be in different currencies.
**Solution:** Use `exchange_rates.csv` with exact date matching and ±7 day fallback. All amounts are converted to the user's `home_currency` before any safety calculation.

### Challenge 2: Detecting Recurring Patterns
**Problem:** Need to distinguish rent (monthly, fixed) from one-time purchases.
**Solution:** Group settled debit events by `(description, category, flexibility)`. Require ≥2 occurrences in ≥2 different months. Use median day-of-month and mean amount for projection.

### Challenge 3: Message Interpretation
**Problem:** Messages in English AND Indonesian (Bahasa) contain salary changes, transfer notifications, refund status.
**Solution:** Keyword-based pattern matching for both languages. Conservative extraction (first currency match only) to avoid false positives from one-time adjustments mentioned alongside regular salary.

### Challenge 4: Image Data Without Vision API
**Problem:** Some financial events have blank amounts that must be extracted from attached images.
**Solution:** Manual visual inspection of all 16 PNG files during development, with amounts hardcoded in a lookup dictionary. This avoids runtime API costs while maintaining accuracy.

### Challenge 5: Salary Date Overrides
**Problem:** When an employer message shifts the salary date, the projection must replace the normal cycle for that month but continue normally afterward.
**Solution:** If the override date is in the same month as the request, skip the normal cycle for that month only. Subsequent months use the regular monthly pattern.

---

## 9. Output Statistics

| Metric | Value |
|--------|-------|
| Total requests | 250 |
| `affordable_now` | 47 (19%) |
| `affordable_with_plan` | 49 (20%) |
| `affordable_later` | 22 (9%) |
| `not_affordable` | 132 (53%) |
| `full_payment` | 56 |
| `installments` | 35 |
| `partial_payment` | 5 |
| `wait` | 22 |
| `not_recommended` | 132 |
| Spending changes generated | 9 |

---

## 10. Interview Q&A Preparation

### Q: "How does your agent decide if someone can afford something?"
**A:** We simulate the user's cash flow for 90 days. Starting from their current balance, we project all known future debits (pending payments, recurring expenses) and credits (confirmed salary). At every point in that 90-day window, the balance must stay above the user's minimum required balance. The "amount safe to pay" is the headroom at the tightest point in the forecast — the minimum balance across all 90 days minus the user's minimum requirement.

### Q: "Why didn't you use an LLM?"
**A:** Financial calculations require exact arithmetic. LLMs can hallucinate numbers, make arithmetic errors, and produce non-deterministic outputs. Our deterministic approach gives exact, reproducible results at zero cost and 32-second runtime for 250 requests. We also avoid the risk of the LLM inventing unsupported financial facts.

### Q: "How do you handle foreign currencies?"
**A:** We use fixed dated exchange rates from `exchange_rates.csv`. For each foreign-currency event, we look up the rate for the settlement date and currency pair. If the exact date isn't available, we use the nearest rate within ±7 days. All amounts are converted to the user's home currency before any safety calculation.

### Q: "How do you detect recurring expenses?"
**A:** We group all settled debit events by description, category, and flexibility type. If a pattern appears in at least 2 different calendar months, we consider it recurring. We use the median day-of-month and mean amount for forward projection.

### Q: "What are spending changes and when do you recommend them?"
**A:** Spending changes suggest stopping or reducing flexible recurring expenses to free up money. They're only recommended when the user can't afford the request without cuts. We respect the user's protected categories and only modify expenses in categories they've explicitly agreed to adjust. Maximum 3 changes, prioritized by savings potential.

### Q: "How do you handle installment plans?"
**A:** We evaluate each installment option from `request_payment_options.csv` against the 90-day balance curve. We build the exact payment schedule using the option's first payment date, frequency, and number of payments. Then we test whether subtracting each payment keeps the balance above the minimum at every point. Safe options are ranked by deadline compliance, total cost, start date, and number of payments.

### Q: "What happens when records conflict?"
**A:** We follow a resolution hierarchy: (1) explicit cancellation/settlement/amendment wins, (2) newer records from the same source override older ones, (3) settled events override estimates, (4) when unresolved, we choose the financially safer interpretation.

### Q: "How do messages and images affect decisions?"
**A:** Messages can override salary amounts, shift salary dates, flag internal transfers to ignore, and mark pending credits as unsettled. Images provide amounts for events where the CSV has blank values — we extracted these manually from receipts, pay slips, and bills. Both are treated as untrusted data — they can clarify financial facts but never override the challenge rules.

### Q: "What's the flexibility system?"
**A:** Every expense has a flexibility classification: `fixed` (can't change, like rent), `stoppable` (can eliminate entirely, like a delivery membership), `reducible` (can reduce to a minimum amount, like a streaming plan), or `reducible_or_stoppable` (either option). This determines which expenses can be cut when recommending spending changes.

### Q: "Walk me through the code architecture."
**A:** Three files with strict one-way dependencies. `main.py` is the CLI entry point — it loads requests and writes output. `agent.py` is the orchestrator — it caches all CSV datasets, builds financial state for each user, and runs the decision pipeline. `financial_engine.py` is the pure computation layer — it handles cashflow simulation, pattern detection, exchange rates, and message parsing with no file I/O of its own.

### Q: "What would you improve?"
**A:** 
- More sophisticated NLU for message interpretation (currently keyword-based)
- Vision API integration for dynamic image amount extraction
- More granular recurring expense detection (weekly, bi-weekly patterns)
- Better handling of linked events (investment lifecycles, refund chains)
- Reducing the `not_affordable` rate (currently 53%) with smarter spending change optimization

---

## 11. File Structure

```
hackerrank-orchestrate/
├── code/
│   ├── main.py                    # Entry point (python main.py)
│   ├── agent.py                   # Decision orchestrator (548 lines)
│   ├── financial_engine.py        # Cashflow simulation (558 lines)
│   └── evaluation/
│       └── usage_report.md        # Token/cost report
├── dataset/
│   ├── requests.csv               # 250 evaluation requests
│   ├── financial_profiles.csv     # 276 user profiles
│   ├── financial_events.csv       # 25,342 transactions
│   ├── exchange_rates.csv         # Currency conversion rates
│   ├── request_payment_options.csv # 791 payment plans
│   ├── messages.csv               # 216 notifications
│   ├── images.csv                 # 17 image-event links
│   ├── sample_requests.csv        # 25 golden examples
│   ├── output.csv                 # 250 predictions (generated)
│   └── media/images/              # 16 PNG files
├── AGENTS.md                      # Agent instructions
├── README.md                      # Project documentation
└── log.txt                        # Development chat transcript
```

---

## 12. Submission Deliverables

| Deliverable | Description | Status |
|------------|-------------|--------|
| **code.zip** | Full runnable solution with `evaluation/usage_report.md` | Ready |
| **output.csv** | 250 predictions for all evaluation requests | Ready (250 rows, all validations pass) |
| **chat_transcript** | Development conversation log | Ready (log.txt, 10 entries) |

**Submission URL:**  
https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission
