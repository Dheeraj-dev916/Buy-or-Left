"""
agent.py
Main affordability decision agent.
Orchestrates financial_engine.py and produces the required output fields.

Decision pipeline (ranked priority):
  full_payment > installments > partial_payment > wait > not_recommended
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from financial_engine import (
    get_user_financial_state,
    compute_amount_safe_to_pay,
    compute_earliest_full_payment_date,
    test_plan_safety,
    apply_image_amounts,
)


# ─── Data directory ────────────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'dataset')

_CACHE = {}


def get_data():
    if not _CACHE:
        _CACHE['profiles'] = pd.read_csv(os.path.join(DATA_DIR, 'financial_profiles.csv'))
        _CACHE['events']   = pd.read_csv(os.path.join(DATA_DIR, 'financial_events.csv'))
        _CACHE['messages'] = pd.read_csv(os.path.join(DATA_DIR, 'messages.csv'))
        _CACHE['rates']    = pd.read_csv(os.path.join(DATA_DIR, 'exchange_rates.csv'))
        _CACHE['options']  = pd.read_csv(os.path.join(DATA_DIR, 'request_payment_options.csv'))
    return (
        _CACHE['profiles'],
        _CACHE['events'],
        _CACHE['messages'],
        _CACHE['rates'],
        _CACHE['options'],
    )


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _parse_list(value: str | float | None) -> list:
    """Parse a pipe-separated string into a list of stripped strings."""
    if not value or (isinstance(value, float) and pd.isna(value)):
        return []
    return [v.strip() for v in str(value).split('|') if v.strip()]


def _date(s) -> datetime | None:
    try:
        return datetime.strptime(str(s).strip(), '%Y-%m-%d')
    except Exception:
        return None


def _fmt_money(val: float) -> str:
    """Format an amount: no decimals if whole number, else 2 decimal places."""
    val = round(float(val), 2)
    if val == int(val):
        return str(int(val))
    return f"{val:.2f}"


# ─── Installment plan evaluator ───────────────────────────────────────────────

def _evaluate_installment_option(
    option: pd.Series,
    balances: list,
    dates: list,
    min_balance: float,
    max_installment_months: int | None,
) -> dict | None:
    """
    Check if a supplied payment option is safe given the 90-day balance curve.
    Returns a result dict or None if the option is not safe / not eligible.
    """
    n_payments = int(option['number_of_payments'])
    per_payment = float(option['payment_amount'])
    first_date  = _date(option['first_payment_date'])
    freq_days   = int(option['payment_frequency_days']) if pd.notna(option.get('payment_frequency_days')) else 30

    if first_date is None:
        return None

    # Respect max_installment_months
    if max_installment_months is not None and n_payments > max_installment_months:
        return None

    req_date = dates[0]

    # Build payment schedule
    payment_schedule = []
    payment_plan_parts = []
    for k in range(n_payments):
        pay_dt = first_date + timedelta(days=k * freq_days)
        day_idx = (pay_dt - req_date).days
        if day_idx < 0:
            day_idx = 0
        payment_schedule.append((day_idx, per_payment))
        payment_plan_parts.append(f"{pay_dt.strftime('%Y-%m-%d')}:{_fmt_money(per_payment)}")

    # Safety check
    if not test_plan_safety(min_balance, balances, dates, payment_schedule):
        return None

    return {
        'option_id': option['payment_option_id'],
        'n_payments': n_payments,
        'per_payment': per_payment,
        'total_payable': float(option['total_payable_amount']),
        'first_date': first_date,
        'payment_plan': '|'.join(payment_plan_parts),
        'completes_by': first_date + timedelta(days=(n_payments - 1) * freq_days),
    }


# ─── Spending change advisor ───────────────────────────────────────────────────

def get_spending_changes(
    recurring_expenses: list,
    shortfall: float,
    home_currency: str,
    profile: pd.Series,
) -> dict:
    """
    Suggest spending cuts from flexible, non-protected recurring expenses.
    Only categories the user is willing to reduce/stop are eligible.
    Returns {'required': bool, 'adjustments': list}
    """
    if shortfall <= 0:
        return {'required': False, 'adjustments': [], 'total_savings': 0.0, 'residual_shortfall': 0.0}

    protected    = set(_parse_list(profile.get('expense_categories_to_protect', '')))
    can_reduce   = set(_parse_list(profile.get('expense_categories_user_is_willing_to_reduce', '')))
    can_stop     = set(_parse_list(profile.get('expense_categories_user_is_willing_to_stop', '')))
    eligible_cats = can_reduce | can_stop

    flex_exps = []
    for e in recurring_expenses:
        flex = e['flexibility']
        cat = e['category']
        if cat in protected or cat not in eligible_cats:
            continue
        # Determine possible actions based on flexibility type
        can_stop_this = False
        can_reduce_this = False
        min_allowed = e.get('min_allowed') or 0

        if flex == 'stoppable':
            can_stop_this = cat in can_stop
        elif flex == 'reducible':
            can_reduce_this = cat in can_reduce
        elif flex == 'reducible_or_stoppable':
            can_stop_this = cat in can_stop
            can_reduce_this = cat in can_reduce

        if not (can_stop_this or can_reduce_this):
            continue

        if can_stop_this:
            min_allowed = 0
        max_cut = e['avg_amount'] - min_allowed
        if max_cut <= 0:
            continue

        flex_exps.append({
            **e,
            'min_allowed': min_allowed,
            'max_cut': max_cut,
            'can_stop': can_stop_this,
        })

    flex_exps.sort(key=lambda x: x['max_cut'], reverse=True)

    adjustments = []
    remaining = shortfall

    for exp in flex_exps:
        if len(adjustments) >= 3:
            break
        max_cut = exp['max_cut']
        cut = min(max_cut, remaining)
        if cut > 0:
            new_amount = round(exp['avg_amount'] - cut, 2)
            if new_amount == 0 and exp.get('can_stop', False):
                action = 'stop'
            else:
                action = 'reduce_to'
            adjustments.append({
                'category':        exp['category'],
                'description':     exp['description'],
                'event_id':        exp.get('event_id', ''),
                'current_amount':  exp['avg_amount'],
                'suggested_amount': new_amount,
                'monthly_saving':  round(cut, 2),
                'min_allowed':     exp.get('min_allowed', 0),
                'action':          action,
            })
            remaining -= cut
            if remaining <= 0:
                break

    return {
        'required':           True,
        'adjustments':        adjustments,
        'total_savings':      round(shortfall - remaining, 2),
        'residual_shortfall': round(max(0.0, remaining), 2),
    }


def _spending_changes_str(spending_changes: dict) -> str:
    """Format spending changes into the required stop/reduce_to format."""
    if not spending_changes.get('required') or not spending_changes.get('adjustments'):
        return 'none'
    parts = []
    for adj in spending_changes['adjustments'][:3]:
        ev_id = adj.get('event_id', '')
        if adj['action'] == 'stop':
            parts.append(f"stop:{ev_id}")
        else:
            sug_str = _fmt_money(adj['suggested_amount'])
            parts.append(f"reduce_to:{ev_id}:{sug_str}")
    return '|'.join(parts) if parts else 'none'


# ─── Explanation generator ────────────────────────────────────────────────────

def build_explanation(
    home_currency: str,
    current_balance: float,
    min_balance: float,
    requested_amount: float,
    amount_safe_today: float,
    affordability_status: str,
    payment_method: str,
    payment_plan: str,
    earliest_full_date: str,
    spending_changes: dict,
    daily_delta: dict,
    messages_adj: dict,
) -> str:
    curr = home_currency
    lines = []

    headroom = current_balance - min_balance
    lines.append(
        f"Balance: {curr} {current_balance:,.2f} (min required: {curr} {min_balance:,.2f}; "
        f"headroom: {curr} {headroom:,.2f})."
    )

    near_debits = sum(abs(v) for k, v in daily_delta.items() if 1 <= k <= 30 and v < 0)
    near_credits = sum(v for k, v in daily_delta.items() if 1 <= k <= 30 and v > 0)
    if near_debits > 0:
        lines.append(f"Committed outflows next 30 days: {curr} {near_debits:,.2f}.")
    if near_credits > 0:
        lines.append(f"Expected income next 30 days: {curr} {near_credits:,.2f}.")

    if messages_adj.get('salary_override'):
        lines.append(
            f"Salary temporarily reduced to {curr} {messages_adj['salary_override']:,.2f}/month per employer message."
        )
    if messages_adj.get('salary_date_override'):
        lines.append(f"Next salary expected on {messages_adj['salary_date_override']}.")

    if affordability_status == 'affordable_now':
        lines.append(
            f"Decision: Full payment of {curr} {requested_amount:,.2f} is safe today. "
            f"Balance remains above minimum throughout the 90-day forecast."
        )
    elif affordability_status == 'affordable_with_plan':
        if payment_method == 'installments':
            lines.append(
                f"Decision: Full payment is not safe today (safe amount: {curr} {amount_safe_today:,.2f}). "
                f"Installment plan: {payment_plan}."
            )
        elif payment_method == 'partial_payment':
            lines.append(
                f"Decision: Pay {curr} {amount_safe_today:,.2f} today; "
                f"remaining balance due on {earliest_full_date}. Plan: {payment_plan}."
            )
        else:
            lines.append(f"Decision: Affordable with plan. Payment plan: {payment_plan}.")
        if spending_changes.get('required') and spending_changes.get('adjustments'):
            savings = spending_changes.get('total_savings', 0)
            lines.append(f"Spending changes required to cover shortfall (saves {curr} {savings:,.2f}/month).")
    elif affordability_status == 'affordable_later':
        lines.append(
            f"Decision: Cannot safely pay {curr} {requested_amount:,.2f} today "
            f"(safe amount now: {curr} {amount_safe_today:,.2f}). "
            f"Full payment becomes safe on {earliest_full_date}."
        )
    else:
        lines.append(
            f"Decision: Not affordable. Safe to pay only {curr} {amount_safe_today:,.2f} today, "
            f"and the full {curr} {requested_amount:,.2f} does not become safe within the 90-day horizon."
        )

    return ' '.join(lines)


# ─── Main agent function ───────────────────────────────────────────────────────

def run_agent(request: dict, options_df: pd.DataFrame = None) -> dict:
    """
    Process one affordability request and return the full required output dict.
    """
    profiles_df, events_df, messages_df, rates_df, all_options_df = get_data()
    if options_df is None:
        options_df = all_options_df

    user_id         = str(request['user_id'])
    request_id      = str(request['request_id'])
    requested_amount = float(request['requested_amount'])
    request_date_str = str(request['request_date'])
    allows_partial  = str(request.get('allows_partial_payment', 'False')).strip().lower() in ('true', '1', 'yes')
    desired_completion_date_str = str(request.get('desired_completion_date', '')).strip()

    try:
        req_date = datetime.strptime(request_date_str, '%Y-%m-%d')
    except ValueError:
        req_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    desired_completion_dt = _date(desired_completion_date_str)

    # ── Build financial state ──────────────────────────────────────────────
    state = get_user_financial_state(
        user_id=user_id,
        request_id=request_id,
        req_date=req_date,
        profiles_df=profiles_df,
        events_df=events_df,
        rates_df=rates_df,
        messages_df=messages_df,
    )

    current_balance  = state['current_balance']
    min_balance      = state['min_balance']
    home_currency    = state['home_currency']
    dates            = state['dates']
    balances         = state['balances']
    daily_delta      = state['daily_delta']
    recurring_expenses = state['recurring_expenses']
    recurring_income   = state['recurring_income']
    messages_adj       = state['messages_adj']
    profile            = state['profile']

    # ── User payment preferences ───────────────────────────────────────────
    user_methods = set(_parse_list(profile.get('payment_methods_user_will_consider', 'full_payment')))
    max_inst_months_raw = profile.get('max_installment_months', None)
    max_installment_months = (
        int(max_inst_months_raw)
        if max_inst_months_raw and not (isinstance(max_inst_months_raw, float) and pd.isna(max_inst_months_raw))
        else None
    )

    # ── Amount safe to pay today ───────────────────────────────────────────
    amount_safe_today = compute_amount_safe_to_pay(
        current_balance=current_balance,
        min_balance=min_balance,
        requested_amount=requested_amount,
        dates=dates,
        balances=balances,
        payment_date_idx=0,
    )

    # ── Earliest full payment date ─────────────────────────────────────────
    earliest_full_date = compute_earliest_full_payment_date(
        current_balance=current_balance,
        min_balance=min_balance,
        requested_amount=requested_amount,
        dates=dates,
        balances=balances,
    )

    # ── Payment options for this request ──────────────────────────────────
    req_options = options_df[options_df['request_id'] == request_id].copy()
    req_options = req_options.sort_values('payment_option_id')  # tie-break by lowest option_id

    # ─────────────────────────────────────────────────────────────────────
    # DECISION PIPELINE  (priority: full > installments > partial > wait > not_recommended)
    # ─────────────────────────────────────────────────────────────────────

    chosen_method      = None
    chosen_status      = None
    chosen_plan        = 'none'
    chosen_explanation = ''
    spending_changes   = {'required': False, 'adjustments': [], 'total_savings': 0.0, 'residual_shortfall': 0.0}

    # 1 ── FULL PAYMENT (affordable now) ───────────────────────────────────
    if 'full_payment' in user_methods and amount_safe_today >= requested_amount:
        chosen_method = 'full_payment'
        chosen_status = 'affordable_now'
        # Find supplied full_payment option for plan string (use first available)
        fp_opts = req_options[req_options['payment_method'] == 'full_payment']
        if not fp_opts.empty:
            opt = fp_opts.iloc[0]
            chosen_plan = f"{opt['first_payment_date']}:{_fmt_money(float(opt['payment_amount']))}"
        else:
            chosen_plan = f"{req_date.strftime('%Y-%m-%d')}:{_fmt_money(requested_amount)}"

    # 2 ── INSTALLMENTS (no spending changes) ──────────────────────────────
    if chosen_method is None and 'installments' in user_methods:
        inst_opts = req_options[req_options['payment_method'] == 'installments']
        safe_inst_plans = []

        for _, opt in inst_opts.iterrows():
            result = _evaluate_installment_option(
                option=opt,
                balances=balances,
                dates=dates,
                min_balance=min_balance,
                max_installment_months=max_installment_months,
            )
            if result is None:
                continue
            # Check completion deadline
            completes_by_deadline = (
                desired_completion_dt is None or result['completes_by'] <= desired_completion_dt
            )
            safe_inst_plans.append({**result, 'completes_by_deadline': completes_by_deadline})

        if safe_inst_plans:
            # Rank: deadline first, then min total cost, then earliest start, fewer payments, lowest option_id
            safe_inst_plans.sort(key=lambda x: (
                not x['completes_by_deadline'],
                x['total_payable'],
                x['first_date'],
                x['n_payments'],
                x['option_id'],
            ))
            best = safe_inst_plans[0]
            chosen_method = 'installments'
            chosen_status = 'affordable_with_plan'
            chosen_plan   = best['payment_plan']

    # 3 ── PARTIAL PAYMENT (no spending changes) ───────────────────────────
    if chosen_method is None and 'partial_payment' in user_methods and allows_partial:
        if 0 < amount_safe_today < requested_amount and earliest_full_date is not None:
            earliest_full_dt = _date(earliest_full_date)
            deadline_ok = (
                desired_completion_dt is None
                or earliest_full_dt is None
                or earliest_full_dt <= desired_completion_dt
            )
            if deadline_ok:
                second_amt = round(requested_amount - amount_safe_today, 2)
                chosen_method = 'partial_payment'
                chosen_status = 'affordable_with_plan'
                chosen_plan = (
                    f"{req_date.strftime('%Y-%m-%d')}:{_fmt_money(amount_safe_today)}"
                    f"|{earliest_full_date}:{_fmt_money(second_amt)}"
                )

    # 4 ── PLANS WITH SPENDING CHANGES ────────────────────────────────────
    # 4a: Full payment with spending changes
    if chosen_method is None and 'full_payment' in user_methods:
        shortfall = requested_amount - amount_safe_today
        if shortfall > 0:
            sc = get_spending_changes(recurring_expenses, shortfall, home_currency, profile)
            if sc['required'] and sc['residual_shortfall'] == 0:
                chosen_method = 'full_payment'
                chosen_status = 'affordable_with_plan'
                chosen_plan   = f"{req_date.strftime('%Y-%m-%d')}:{_fmt_money(requested_amount)}"
                spending_changes = sc

    # 4b: Partial payment with spending changes
    if chosen_method is None and 'partial_payment' in user_methods and allows_partial:
        shortfall = requested_amount - amount_safe_today
        sc = get_spending_changes(recurring_expenses, shortfall, home_currency, profile)
        if sc['required'] and sc['residual_shortfall'] == 0 and earliest_full_date is not None:
            earliest_full_dt = _date(earliest_full_date)
            deadline_ok = (
                desired_completion_dt is None
                or earliest_full_dt is None
                or earliest_full_dt <= desired_completion_dt
            )
            if deadline_ok:
                second_amt = round(requested_amount - amount_safe_today, 2)
                chosen_method = 'partial_payment'
                chosen_status = 'affordable_with_plan'
                chosen_plan = (
                    f"{req_date.strftime('%Y-%m-%d')}:{_fmt_money(amount_safe_today)}"
                    f"|{earliest_full_date}:{_fmt_money(second_amt)}"
                )
                spending_changes = sc

    # 5 ── WAIT (full_payment accepted, safe later by deadline) ────────────
    if chosen_method is None and 'full_payment' in user_methods and earliest_full_date is not None:
        earliest_full_dt = _date(earliest_full_date)
        deadline_ok = (
            desired_completion_dt is None
            or earliest_full_dt is None
            or earliest_full_dt <= desired_completion_dt
        )
        if deadline_ok:
            chosen_method = 'wait'
            chosen_status = 'affordable_later'
            chosen_plan   = f"{earliest_full_date}:{_fmt_money(requested_amount)}"

    # 6 ── NOT RECOMMENDED ─────────────────────────────────────────────────
    if chosen_method is None:
        chosen_method = 'not_recommended'
        chosen_status = 'not_affordable'
        chosen_plan   = 'none'

    # ── earliest_date_for_full_payment (spec requirement) ──────────────────
    if chosen_status == 'affordable_now':
        eff_earliest = req_date.strftime('%Y-%m-%d')   # MUST equal request_date
    elif chosen_method == 'not_recommended':
        eff_earliest = ''
    elif earliest_full_date:
        eff_earliest = earliest_full_date
    else:
        eff_earliest = ''

    # ── Spending changes string ────────────────────────────────────────────
    spending_changes_str = _spending_changes_str(spending_changes)

    # ── Explanation ───────────────────────────────────────────────────────
    explanation = build_explanation(
        home_currency=home_currency,
        current_balance=current_balance,
        min_balance=min_balance,
        requested_amount=requested_amount,
        amount_safe_today=amount_safe_today,
        affordability_status=chosen_status,
        payment_method=chosen_method,
        payment_plan=chosen_plan,
        earliest_full_date=eff_earliest,
        spending_changes=spending_changes,
        daily_delta=daily_delta,
        messages_adj=messages_adj,
    )

    return {
        'request_id':                   request_id,
        'amount_safe_to_pay':           amount_safe_today,
        'affordability_status':         chosen_status,
        'recommended_payment_method':   chosen_method,
        'payment_plan':                 chosen_plan,
        'earliest_date_for_full_payment': eff_earliest,
        'spending_changes_needed':      spending_changes_str,
        'decision_explanation':         explanation,
    }


# ─── Batch runner ─────────────────────────────────────────────────────────────

def run_batch(requests_df: pd.DataFrame) -> pd.DataFrame:
    """Process a DataFrame of requests and return a results DataFrame."""
    _, _, _, _, options_df = get_data()
    results = []
    for _, row in requests_df.iterrows():
        try:
            result = run_agent(row.to_dict(), options_df=options_df)
        except Exception as exc:
            result = {
                'request_id':                   row.get('request_id', '?'),
                'amount_safe_to_pay':            0.0,
                'affordability_status':          'not_affordable',
                'recommended_payment_method':    'not_recommended',
                'payment_plan':                  'none',
                'earliest_date_for_full_payment': '',
                'spending_changes_needed':        'none',
                'decision_explanation':           f'Error: {exc}',
            }
        results.append(result)
    return pd.DataFrame(results)
