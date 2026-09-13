"""
financial_engine.py
Reconstructs each user's financial state and simulates 90-day balance curves.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict


# ─── Image / amounts resolved from visual inspection ─────────────────────────
IMAGE_AMOUNTS = {
    'event_253':   4365000.0,   # Pay slip Aug-2019 IDR net pay
    'event_1442':  100000.0,    # Rent receipt INR balance due
    'event_1545':  41272.0,     # Bill of Supply INR net amount
    'event_1700':  2854.0,      # Blinkit delivery INR item bill
    'event_1786':  704.05,      # Airtel bill INR amount due
    'event_3051':  1995.0,      # Blinkit grocery receipt INR
    'event_3231':  8528.0,      # Nagarjuna food INR grand total
    'event_4535':  15339.0,     # Maintenance receipt INR total
    'event_5170':  723.0,       # Water bill receipt INR total
    'event_6033':  79679.26,    # Grocery invoice INR total
    'event_6859':  3650.0,      # Hospital provisional bill INR
    'event_7307':  33.50,       # CityCab taxi receipt USD total
    'event_7941':  2298.0,      # DailyObjects order INR total paid
    'event_9421':  4543.0,      # Pharmacy handwritten bill INR total
    'event_9806':  9968.0,      # Flight invoice INR grand total
    'event_10521': 393.22,      # EV charging station INR total
}


def apply_image_amounts(events: pd.DataFrame) -> pd.DataFrame:
    """Fill blank amounts from known image-extracted values."""
    events = events.copy()
    for ev_id, amt in IMAGE_AMOUNTS.items():
        mask = events['event_id'] == ev_id
        if mask.any():
            events.loc[mask, 'amount'] = amt
    return events


def get_exchange_rate(rates_df: pd.DataFrame, from_curr: str, to_curr: str,
                      date_str: str) -> float:
    """Return the rate for the given direction and settlement date."""
    if from_curr == to_curr:
        return 1.0
    # try exact date
    row = rates_df[
        (rates_df['rate_date'] == date_str) &
        (rates_df['from_currency'] == from_curr) &
        (rates_df['to_currency'] == to_curr)
    ]
    if not row.empty:
        return float(row['rate'].iloc[0])
    # try nearby dates (within ±7 days)
    target = pd.to_datetime(date_str)
    filtered = rates_df[
        (rates_df['from_currency'] == from_curr) &
        (rates_df['to_currency'] == to_curr)
    ].copy()
    filtered['rate_date_dt'] = pd.to_datetime(filtered['rate_date'])
    filtered['diff'] = (filtered['rate_date_dt'] - target).abs()
    if not filtered.empty:
        return float(filtered.loc[filtered['diff'].idxmin(), 'rate'])
    return 1.0


def convert_to_home(amount: float, from_curr: str, to_curr: str,
                    settlement_date: str, rates_df: pd.DataFrame) -> float:
    """Convert amount from from_curr to to_curr using fixed dated rates."""
    if from_curr == to_curr:
        return amount
    rate = get_exchange_rate(rates_df, from_curr, to_curr, settlement_date)
    return amount * rate


def parse_messages(messages_df: pd.DataFrame, user_id: str,
                   request_id: str, req_date: datetime):
    """
    Parse messages for salary updates, rent changes, internal transfers,
    refund status, etc. Returns a dict of adjustments.
    """
    adjustments = {
        'salary_override': None,           # (amount, date) if salary changed
        'salary_date_override': None,      # date override for next salary
        'ignore_event_ids': set(),         # events to ignore (internal transfers, etc.)
        'ignore_pending_credit_event_ids': set(),  # pending credits to ignore
        'pending_debit_failed': set(),     # failed debit event_ids
    }

    # Filter messages relevant to this user/request
    um = messages_df[
        (messages_df['user_id'] == user_id) |
        (messages_df['request_id'] == request_id)
    ].copy()

    if um.empty:
        return adjustments

    um['sent_at_dt'] = pd.to_datetime(um['sent_at'], utc=True, errors='coerce')
    um = um.sort_values('sent_at_dt')

    for _, msg in um.iterrows():
        text = str(msg.get('message_text', '')).lower()
        source = str(msg.get('source_type', '')).lower()
        related_ev = msg.get('related_event_id', None)

        # Employer messages - salary updates
        if source == 'employer':
            import re
            msg_text_raw = str(msg.get('message_text', ''))

            # --- Salary amount override ---
            # Only extract when the message describes a salary change
            # (reduction, temporary pay, or confirmed new amount)
            is_reduction = (
                'temporary monthly pay' in text
                or 'reduced amount' in text
                or 'reduced to' in text
                or 'unpaid leave' in text
                # Indonesian reduction keywords
                or 'tanpa gaji' in text
                or 'gaji sementara' in text
                or 'dikurangi' in text
                or 'cuti' in text
            )
            # Salary increase or confirmed new salary (not just a mention)
            is_salary_change = (
                'naik' in text and 'gaji' in text  # Indonesian: salary increase
                or ('gaji' in text and 'menjadi' in text)  # Indonesian: salary becomes
                or ('salary' in text and ('now' in text or 'new' in text or 'updated' in text))
                or ('gaji' in text and 'dikonfirmasi' in text)  # Indonesian: confirmed salary
                or ('salary' in text and 'confirmed' in text)
            )

            if is_reduction or is_salary_change:
                # Take the FIRST currency amount (the primary salary figure)
                for match in re.finditer(
                    r'(?:eur|usd|inr|idr|zar)\s*([\d,]+\.?\d*)', text
                ):
                    try:
                        adjustments['salary_override'] = float(
                            match.group(1).replace(',', '')
                        )
                        break  # Use first match only
                    except ValueError:
                        pass

            # --- Salary date override ---
            date_matches = re.findall(r'(\d{4}-\d{2}-\d{2})', msg_text_raw)
            has_date_keyword = (
                'salary' in text or 'payroll' in text
                or 'expected on' in text or 'revised date' in text
                or 'confirmed credit date' in text or 'resumes on' in text
                or 'diperkirakan pada' in text or 'tanggal yang direvisi' in text
                or 'tanggal penggajian' in text or 'penggajian berikutnya' in text
                or 'slip gaji berikutnya' in text or 'replaces' in text
                or 'confirmed' in text or 'dikonfirmasi' in text
            )
            if date_matches and has_date_keyword:
                adjustments['salary_date_override'] = date_matches[0]

        # Bank messages - internal transfers (both debit & credit are same holder)
        if source == 'bank':
            if 'transfer between your two accounts' in text and related_ev and not pd.isna(related_ev):
                adjustments['ignore_event_ids'].add(str(related_ev))

        # Merchant messages - refund pending (don't count as income yet)
        if source == 'merchant':
            if 'refund' in text and ('not reached' in text or 'initiated' in text):
                if related_ev and not pd.isna(related_ev):
                    adjustments['ignore_pending_credit_event_ids'].add(str(related_ev))

        # Financial service - unrealized investment gains / pending prize
        if source == 'financial_service':
            if ('no units have been sold' in text or 'no cash proceeds' in text or
                    'not been credited' in text or 'payment processing' in text):
                if related_ev and not pd.isna(related_ev):
                    adjustments['ignore_pending_credit_event_ids'].add(str(related_ev))

        # Service provider - pending payouts
        if source == 'service_provider':
            if 'pending' in text and ('payout' in text or 'balance' in text):
                if related_ev and not pd.isna(related_ev):
                    adjustments['ignore_pending_credit_event_ids'].add(str(related_ev))

        # Bank - failed debit retry
        if source == 'bank':
            if 'failed' in text or 'previous debit attempt failed' in text:
                if related_ev and not pd.isna(related_ev):
                    adjustments['pending_debit_failed'].add(str(related_ev))

    return adjustments


def identify_recurring_expenses(events_df: pd.DataFrame, req_date: datetime,
                                  user_id: str):
    """
    Identify recurring monthly expense patterns from historical settled events.
    Returns list of (category, description, avg_amount, day_of_month, flexibility, min_allowed, event_id).
    """
    historical = events_df[
        (events_df['user_id'] == user_id) &
        (events_df['event_date'] < req_date.strftime('%Y-%m-%d')) &
        (events_df['direction'] == 'debit') &
        (events_df['status'] == 'settled') &
        (events_df['amount'].notna())
    ].copy()

    if historical.empty:
        return []

    historical['event_date_dt'] = pd.to_datetime(historical['event_date'])
    historical['month'] = historical['event_date_dt'].dt.to_period('M')
    historical['day'] = historical['event_date_dt'].dt.day
    historical['month_year'] = historical['event_date_dt'].dt.to_period('M')

    recurring = []

    # Group by description+category+flexibility to detect patterns
    for (desc, cat, flex), grp in historical.groupby(['description', 'category', 'flexibility']):
        if len(grp) < 2:
            continue
        months = grp['month'].nunique()
        if months < 2:
            continue

        # Check if it appears approximately monthly (within a window)
        days = sorted(grp['day'].tolist())
        avg_day = int(np.median(days))
        avg_amount = float(grp['amount'].mean())
        min_allowed = None
        ev_id = grp['event_id'].iloc[-1]  # most recent event_id for spending changes

        if grp['minimum_allowed_amount'].notna().any():
            min_allowed = float(grp['minimum_allowed_amount'].dropna().iloc[-1])

        recurring.append({
            'category': cat,
            'description': desc,
            'avg_amount': avg_amount,
            'day_of_month': avg_day,
            'flexibility': flex,
            'min_allowed': min_allowed,
            'event_id': ev_id,
            'count': len(grp),
            'months': months,
        })

    return recurring


def identify_recurring_income(events_df: pd.DataFrame, req_date: datetime,
                               user_id: str, messages_adj: dict):
    """
    Identify recurring salary/income from settled history.
    Returns list of income records with (amount, day_of_month, event_id).
    """
    historical = events_df[
        (events_df['user_id'] == user_id) &
        (events_df['direction'] == 'credit') &
        (events_df['status'] == 'settled') &
        (events_df['amount'].notna()) &
        (events_df['category'] == 'salary')
    ].copy()

    if historical.empty:
        return []

    historical['event_date_dt'] = pd.to_datetime(historical['event_date'])
    historical = historical.sort_values('event_date_dt')
    historical['day'] = historical['event_date_dt'].dt.day

    incomes = []
    for (cat, day), grp in historical.groupby(['category', 'day']):
        months = grp['event_date_dt'].dt.to_period('M').nunique()
        if months < 1:
            continue
        latest_amount = float(grp['amount'].iloc[-1])
        # Override from messages
        if messages_adj.get('salary_override') is not None:
            latest_amount = messages_adj['salary_override']
        incomes.append({
            'amount': latest_amount,
            'day_of_month': day,
            'category': cat,
        })

    return incomes


def build_daily_cashflows(
    user_id: str,
    req_date: datetime,
    current_balance: float,
    min_balance: float,
    events_df: pd.DataFrame,
    rates_df: pd.DataFrame,
    home_currency: str,
    messages_adj: dict,
    forecast_days: int = 90,
) -> tuple:
    """
    Build 90-day forward cashflow projection.
    Returns (dates_list, projected_balances, committed_future_events).
    """
    events_df = events_df.copy()

    # Apply image amounts
    events_df = apply_image_amounts(events_df)

    dates = [req_date + timedelta(days=i) for i in range(forecast_days + 1)]
    # daily_delta[i] = sum of net credits/debits on day i
    daily_delta = defaultdict(float)

    # 1. Handle already-scheduled / pending debits that settle during the window
    future_confirmed = events_df[
        (events_df['user_id'] == user_id) &
        (events_df['status'].isin(['pending', 'scheduled'])) &
        (events_df['direction'] == 'debit') &
        (events_df['amount'].notna())
    ].copy()

    for _, ev in future_confirmed.iterrows():
        if str(ev['event_id']) in messages_adj.get('pending_debit_failed', set()):
            continue
        settle_date_str = str(ev.get('settlement_date', ev['event_date']))
        try:
            settle_dt = datetime.strptime(settle_date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            try:
                settle_dt = datetime.strptime(str(ev['event_date']), '%Y-%m-%d')
            except Exception:
                continue
        if settle_dt < req_date:
            continue
        day_idx = (settle_dt - req_date).days
        if 0 <= day_idx <= forecast_days:
            amt = float(ev['amount'])
            curr = str(ev.get('currency', home_currency))
            if curr != home_currency:
                amt = convert_to_home(amt, curr, home_currency, settle_date_str, rates_df)
            daily_delta[day_idx] -= amt

    # 2. Handle next confirmed salary (scheduled income)
    future_income = events_df[
        (events_df['user_id'] == user_id) &
        (events_df['status'] == 'scheduled') &
        (events_df['direction'] == 'credit') &
        (events_df['amount'].notna())
    ].copy()

    for _, ev in future_income.iterrows():
        ev_id = str(ev['event_id'])
        if ev_id in messages_adj.get('ignore_pending_credit_event_ids', set()):
            continue
        settle_date_str = str(ev.get('settlement_date', ev['event_date']))
        try:
            settle_dt = datetime.strptime(settle_date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            continue
        if settle_dt < req_date:
            continue
        day_idx = (settle_dt - req_date).days
        if 0 <= day_idx <= forecast_days:
            amt = float(ev['amount'])
            if messages_adj.get('salary_override') is not None:
                amt = messages_adj['salary_override']
            curr = str(ev.get('currency', home_currency))
            if curr != home_currency:
                amt = convert_to_home(amt, curr, home_currency, settle_date_str, rates_df)
            daily_delta[day_idx] += amt

    # 3. Identify recurring expenses and income from history
    recurring_expenses = identify_recurring_expenses(events_df, req_date, user_id)
    recurring_income = identify_recurring_income(events_df, req_date, user_id, messages_adj)

    # 4. Project recurring expenses over the 90-day window
    for exp in recurring_expenses:
        day_of_month = exp['day_of_month']
        avg_amt = exp['avg_amount']
        # Project for each month in the window
        for month_offset in range(4):  # up to 3 full months ahead
            # Find the date for day_of_month in req_date + month_offset months
            try:
                target_month = (req_date.month + month_offset - 1) % 12 + 1
                target_year = req_date.year + (req_date.month + month_offset - 1) // 12
                import calendar
                max_day = calendar.monthrange(target_year, target_month)[1]
                actual_day = min(day_of_month, max_day)
                exp_dt = datetime(target_year, target_month, actual_day)
            except Exception:
                continue
            if exp_dt < req_date:
                continue
            day_idx = (exp_dt - req_date).days
            if 0 <= day_idx <= forecast_days:
                daily_delta[day_idx] -= avg_amt

    # 5. Project recurring income over the 90-day window
    for inc in recurring_income:
        day_of_month = inc['day_of_month']
        amt = inc['amount']
        # Check if salary date was overridden
        override_month_skip = False
        if messages_adj.get('salary_date_override'):
            try:
                ovr_dt = datetime.strptime(messages_adj['salary_date_override'], '%Y-%m-%d')
                if ovr_dt >= req_date:
                    day_idx = (ovr_dt - req_date).days
                    if 0 <= day_idx <= forecast_days:
                        daily_delta[day_idx] += amt
                    # If override is in the same month as request,
                    # it replaces the normal cycle for that month
                    if (ovr_dt.year == req_date.year and
                            ovr_dt.month == req_date.month):
                        override_month_skip = True
            except Exception:
                pass

        for month_offset in range(4):
            # Skip the normal cycle in the override's month
            if month_offset == 0 and override_month_skip:
                continue
            try:
                target_month = (req_date.month + month_offset - 1) % 12 + 1
                target_year = req_date.year + (req_date.month + month_offset - 1) // 12
                import calendar
                max_day = calendar.monthrange(target_year, target_month)[1]
                actual_day = min(day_of_month, max_day)
                inc_dt = datetime(target_year, target_month, actual_day)
            except Exception:
                continue
            if inc_dt < req_date:
                continue
            day_idx = (inc_dt - req_date).days
            if 0 <= day_idx <= forecast_days:
                daily_delta[day_idx] += amt

    # 6. Build running balance
    running_balance = current_balance
    balances = []
    for i in range(forecast_days + 1):
        running_balance += daily_delta[i]
        balances.append(running_balance)

    return dates, balances, daily_delta, recurring_expenses, recurring_income


def compute_amount_safe_to_pay(
    current_balance: float,
    min_balance: float,
    requested_amount: float,
    dates: list,
    balances: list,
    payment_date_idx: int = 0,
) -> float:
    """
    Compute the largest amount that can be safely paid on payment_date_idx
    without the balance ever falling below min_balance over the full window.
    """
    # baseline min balance over the 90-day window (excluding the payment itself)
    baseline_min = min(balances[payment_date_idx:]) if payment_date_idx < len(balances) else balances[-1]
    # How much headroom do we have at that minimum point?
    headroom = baseline_min - min_balance
    safe = max(0.0, min(requested_amount, headroom))
    return round(safe, 2)


def compute_earliest_full_payment_date(
    current_balance: float,
    min_balance: float,
    requested_amount: float,
    dates: list,
    balances: list,
) -> str | None:
    """
    Find the earliest date when paying requested_amount still keeps
    balance >= min_balance throughout the remaining 90-day window.
    """
    n = len(dates)
    for i, dt in enumerate(dates):
        # If we pay on day i, remaining balances from day i onward are shifted down
        simulated_remaining = [b - requested_amount for b in balances[i:]]
        if all(b >= min_balance for b in simulated_remaining):
            return dt.strftime('%Y-%m-%d')
    return None  # Never becomes safe


def test_plan_safety(
    min_balance: float,
    balances: list,
    dates: list,
    payments: list,  # list of (day_idx, amount)
) -> bool:
    """
    Check if a payment plan is safe: balance never below min_balance after payments.
    payments: list of (day_offset, amount) tuples.
    """
    adjusted = list(balances)
    for day_idx, amount in payments:
        if day_idx >= len(adjusted):
            return False
        for j in range(day_idx, len(adjusted)):
            adjusted[j] -= amount
    return all(b >= min_balance for b in adjusted)


def get_user_financial_state(
    user_id: str,
    request_id: str,
    req_date: datetime,
    profiles_df: pd.DataFrame,
    events_df: pd.DataFrame,
    rates_df: pd.DataFrame,
    messages_df: pd.DataFrame,
    forecast_days: int = 90,
) -> dict:
    """
    Full financial state for a user at request_date.
    Returns structured state dict.
    """
    events_df = apply_image_amounts(events_df)

    prof = profiles_df[profiles_df['user_id'] == user_id].iloc[0]
    home_currency = str(prof['home_currency'])
    current_balance = float(prof['current_available_balance'])
    min_balance = float(prof['minimum_balance_to_keep'])

    # Parse messages
    messages_adj = parse_messages(messages_df, user_id, request_id, req_date)

    # Build daily cashflows
    dates, balances, daily_delta, recurring_expenses, recurring_income = build_daily_cashflows(
        user_id=user_id,
        req_date=req_date,
        current_balance=current_balance,
        min_balance=min_balance,
        events_df=events_df,
        rates_df=rates_df,
        home_currency=home_currency,
        messages_adj=messages_adj,
        forecast_days=forecast_days,
    )

    return {
        'profile': prof,
        'home_currency': home_currency,
        'current_balance': current_balance,
        'min_balance': min_balance,
        'dates': dates,
        'balances': balances,
        'daily_delta': daily_delta,
        'recurring_expenses': recurring_expenses,
        'recurring_income': recurring_income,
        'messages_adj': messages_adj,
    }
