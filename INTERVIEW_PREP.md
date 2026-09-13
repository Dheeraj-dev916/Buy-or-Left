# Buy or Wait? — Interview Preparation Guide

> This guide helps you explain your project clearly in an AI interview.
> Read each section and practice explaining it in your own words.

---

## 1. How to Introduce Your Project (30-Second Pitch)

**Memorize this and say it naturally:**

> "I built an AI-powered financial agent called **Buy or Wait?** for the HackerRank Orchestrate hackathon. The problem is simple — when someone wants to buy something, the system looks at their entire financial picture — current balance, recurring expenses, future income, pending payments — and tells them the safest way to pay. It can recommend paying in full, using installments, paying partially, waiting for a better date, or not buying at all. The whole system runs in about 30 seconds for 250 requests, costs zero dollars, and uses no external APIs."

---

## 2. The Problem in Simple Words

**Think of it like this:**

Imagine your friend asks you: *"I want to buy a laptop for ₹50,000. Can I afford it?"*

You wouldn't just check their bank balance. You'd think:
- "They have ₹80,000 now, but rent of ₹25,000 is due next week"
- "Their salary of ₹60,000 comes on the 1st"
- "They have a ₹5,000 monthly gym membership they could cancel"
- "They want to keep at least ₹10,000 as emergency money"

That's exactly what this system does — but automatically, for 250 different people with different financial situations.

**The 4 possible answers the system gives:**

| Answer | What it means | Example |
|--------|--------------|---------|
| **Affordable Now** | Pay the full amount today, you'll still be fine | "You have ₹80K, laptop is ₹50K, even after all future bills you'll stay above ₹10K" |
| **Affordable with a Plan** | You can do it, but need installments or spending cuts | "Pay ₹25K in 3 monthly installments of ₹17K" |
| **Affordable Later** | Wait a few weeks when your salary comes in | "Wait until March 5th when your next salary arrives" |
| **Not Affordable** | Even with plans and cuts, it's not safe | "Your expenses are too high for this purchase" |

---

## 3. Tech Stack (Keep It Simple)

**If asked "What technologies did you use?", say:**

> "I used **Python** with **pandas** for data processing and **numpy** for calculations. The system is fully deterministic — meaning it uses rules and math, not AI models. No OpenAI, no APIs, no cloud services. This was a deliberate choice because financial calculations need exact answers, not approximate ones."

| Technology | What it does | Why you chose it |
|-----------|-------------|-----------------|
| **Python** | Main programming language | Best for data processing, quick to build |
| **pandas** | Reading and filtering CSV files | Fast, easy to use, handles large datasets |
| **numpy** | Math calculations | Finding median, averages |
| **No AI/LLM** | — | Financial math must be exact, not approximate |

**If they ask "Why not use an LLM like GPT?", say:**

> "Three reasons: First, LLMs make arithmetic mistakes — they can hallucinate numbers. Second, they're not reproducible — same input can give different outputs. Third, they cost money per request. My rule-based approach is exact, free, and runs in 30 seconds."

---

## 4. How the System Works (Step by Step)

**Think of it as a 5-step assembly line:**

```
Step 1: KNOW THE USER
   ↓  "Who is this person? What's their balance? What do they protect?"
Step 2: UNDERSTAND THE PAST
   ↓  "What do they spend monthly? What's their income pattern?"
Step 3: PREDICT THE FUTURE
   ↓  "What will their balance look like every day for the next 90 days?"
Step 4: CHECK SAFETY
   ↓  "If they pay X today, will they survive the next 90 days?"
Step 5: RECOMMEND
   ↓  "What's the best way to pay — full, installments, wait, or no?"
```

### Step 1: Know the User
Read the user's profile — their currency (₹, $, €, etc.), current balance, minimum balance they want to keep, which expenses they protect (like rent), and which they're willing to cut.

### Step 2: Understand the Past
Look at their transaction history (25,000+ events) and find patterns:
- "Rent of ₹25,000 happens on the 5th of every month"
- "Netflix of ₹649 happens on the 15th"
- "Salary of ₹60,000 comes on the 1st"

Rule: Something is "recurring" only if it appears in **2+ different months**.

### Step 3: Predict the Future (90-Day Simulation)
This is the **heart of the system**. We create a day-by-day balance forecast:

```
Day 0 (today):     ₹80,000  (current balance)
Day 1:             ₹75,000  (electricity bill ₹5,000)
Day 5:             ₹50,000  (rent ₹25,000)
Day 15:            ₹49,351  (Netflix ₹649)
Day 30:            ₹1,09,351 (salary ₹60,000 arrives)
...
Day 90:            ₹XX,XXX
```

We include:
- **Pending payments** (bills that are confirmed but not yet paid)
- **Recurring expenses** (rent, subscriptions, utilities — projected monthly)
- **Confirmed salary** (only when it's certain, never "maybe" income)

We exclude:
- Pending credits (refunds not yet received)
- Bonuses, lottery, commissions (uncertain income)
- Unrealized investment gains (paper profits aren't cash)

### Step 4: Check Safety
Two key calculations:

**"How much is safe to pay today?"**
```
Look at the lowest balance across all 90 days
Subtract the user's minimum required balance
Whatever is left = safe to spend today

Example:
  Lowest future balance: ₹35,000
  User's minimum:        ₹10,000
  Safe to pay:           ₹25,000
```

**"When is the earliest they can pay the full amount?"**
```
Try paying the full amount on Day 0  → balance goes negative? Try Day 1
Try Day 1  → still goes negative? Try Day 2
...
Keep going until all future balances stay above minimum
That day = earliest safe full payment date
```

### Step 5: Recommend (Decision Priority)
The system tries options in this order and picks the first one that works:

1. **Full payment today** — Can they pay the whole thing and stay safe?
2. **Installments** — Can they split it into monthly payments? (Check each available plan)
3. **Partial payment** — Pay some now, rest later?
4. **Spending changes + full payment** — Cut some flexible expenses to afford it?
5. **Spending changes + partial** — Cut expenses and pay in parts?
6. **Wait** — Just wait for a better date?
7. **Not recommended** — Nothing works safely

---

## 5. The Three Code Files (Architecture)

**If asked "Explain your code structure", say:**

> "I have three Python files with a clean one-way dependency. Main loads the data, Agent makes decisions, and Engine does the math."

```
main.py  ──→  agent.py  ──→  financial_engine.py
(Entry)       (Brain)         (Calculator)
```

| File | Lines | What it does | Analogy |
|------|-------|-------------|---------|
| **main.py** | ~83 | Reads requests, writes output | The cashier — takes orders, delivers results |
| **agent.py** | ~577 | Decision pipeline, ranks options | The financial advisor — decides what's best |
| **financial_engine.py** | ~558 | Cash flow simulation, math | The accountant — does all the calculations |

**Key point:** The engine never talks back to the agent. Data flows in one direction only.

---

## 6. Input Data (What the System Reads)

**If asked "What data does your system use?", say:**

> "There are 8 input files. The most important are the user's profile (who they are), their transaction history (what they spend and earn), and payment options (how they can pay)."

| File | What's in it | Why it matters |
|------|-------------|---------------|
| **financial_profiles.csv** | Each user's balance, currency, minimum balance, protected categories, payment preferences | Tells us WHO the user is and what they care about |
| **financial_events.csv** | 25,000+ transactions — salary, rent, groceries, bills | Tells us their SPENDING and EARNING patterns |
| **requests.csv** | 250 purchase requests to evaluate | These are the QUESTIONS we need to answer |
| **request_payment_options.csv** | Installment plans available for each request | These are the OPTIONS we can recommend |
| **exchange_rates.csv** | Currency conversion rates | Handles multi-currency (INR, USD, EUR, ZAR, IDR) |
| **messages.csv** | 216 messages from employers, banks, merchants | Extra info like salary changes, refunds |
| **images.csv** | Links to receipt/payslip images | Provides amounts when CSV has blanks |
| **sample_requests.csv** | 25 example requests with correct answers | Used for testing, NOT for evaluation |

---

## 7. Smart Features to Talk About

### 7.1 Multi-Currency Support
> "Users in India use Rupees, South Africa uses Rand, Indonesia uses Rupiah. When someone in India has a US Dollar expense, the system converts it using the exchange rate from that specific date. If the exact date isn't available, it looks ±7 days around that date."

### 7.2 Message Understanding (English + Indonesian)
> "The system reads messages from employers, banks, and merchants. For example, if an employer says 'Your salary is temporarily reduced to €1,200', the system adjusts the projected salary. It works in both English and Indonesian — recognizing keywords like 'gaji' (salary), 'naik' (increase), 'tanpa gaji' (unpaid leave)."

### 7.3 Image Amounts (Without AI Vision)
> "Some financial events have blank amounts in the CSV but have attached images (receipts, pay slips). Instead of using an expensive vision API at runtime, I manually inspected all 16 images during development and stored the amounts in a dictionary. This makes the system instant and free at runtime."

### 7.4 Spending Changes (The Flexibility System)
> "Every expense has a flexibility type: **fixed** (can't change, like rent), **stoppable** (can cancel, like a gym membership), **reducible** (can lower the amount, like a phone plan), or **reducible_or_stoppable** (either option). When someone can't quite afford something, the system suggests stopping or reducing up to 3 flexible expenses to free up money — but never touches protected categories like rent or groceries."

---

## 8. Challenges You Faced (and How You Solved Them)

**If asked "What challenges did you face?", pick 2-3 of these:**

### Challenge 1: "The Flexibility Bug"
> "Initially, my code looked for expenses labeled 'flexible', but the dataset actually used four specific values: 'stoppable', 'reducible', 'reducible_or_stoppable', and 'fixed'. This meant zero spending changes were generated across all 250 requests. I caught this during testing by checking the output statistics. After fixing it, spending changes went from 0 to 9, and the 'not affordable' rate dropped from 56% to 53%."

**Why this is good to mention:** It shows you test your code, find bugs, and measure impact.

### Challenge 2: "Indonesian Salary Messages"
> "The dataset included messages in Indonesian (Bahasa) from employers about salary changes. A simple keyword search for 'gaji' (salary) would pick up every message mentioning salary, including one-time bonuses. I needed to be more precise — only extracting amounts when paired with change signals like 'naik' (increase) or 'menjadi' (becomes). I also used the first currency match to avoid accidentally picking up a one-time arrears amount mentioned alongside the regular salary."

**Why this is good to mention:** It shows you handle edge cases and think about false positives.

### Challenge 3: "Salary Date Overrides"
> "When an employer message says 'salary will come on March 15th instead of March 1st', the system needs to skip the normal March 1st salary and use March 15th instead. But April's salary should still come on April 1st as normal. My first version accidentally skipped ALL future salaries after the override. I fixed it to only replace the salary in the same month as the override."

**Why this is good to mention:** It shows you think about cascading effects in financial systems.

---

## 9. Common Interview Questions & Natural Answers

### Q1: "Walk me through your project."
> "I built a financial decision agent for a hackathon. It takes 250 purchase requests — each from a different user with different incomes, expenses, and priorities — and decides the safest way to pay. The system simulates each user's cash flow for 90 days, projects all their known expenses and income, then checks if paying for the item would ever drop their balance below their safety minimum. Based on that, it recommends full payment, installments, partial payment, waiting, or not proceeding. The whole thing is deterministic — pure Python and math, no AI models, zero cost."

### Q2: "Why did you choose Python?"
> "Python is the best language for data processing. Pandas makes CSV handling trivial, numpy handles math efficiently, and I can prototype quickly. For a 24-hour hackathon, speed of development matters."

### Q3: "How does the 90-day simulation work?"
> "I start with the user's current balance and go day by day for 90 days. Each day, I add any expected income and subtract any expected expenses. Recurring expenses like rent are projected based on their historical day-of-month. Pending payments are subtracted on their scheduled date. At the end, I have a curve showing the user's projected balance every day. The 'safe amount' is the minimum headroom across all those days."

### Q4: "What makes your solution different from others?"
> "Three things: First, it's fully deterministic — same input always gives the same output, which is critical for financial decisions. Second, it handles 5 currencies with dated exchange rates, not just a single rate. Third, it respects user preferences — protected categories are never cut, installment plans are ranked by total cost, and spending changes are limited to 3 maximum."

### Q5: "How do you handle conflicting data?"
> "I follow a priority hierarchy: explicit cancellations win first, then newer records override older ones, settled transactions override estimates, and when nothing is clear, I choose the financially safer option. For example, if an employer message says salary is reduced, that overrides the historical salary amount."

### Q6: "What would you improve if you had more time?"
> "Four things: (1) Better message understanding using actual NLP instead of keyword matching, (2) A vision API for automatic image amount extraction instead of hardcoding, (3) Weekly and bi-weekly recurring patterns instead of just monthly, (4) Smarter spending change optimization to reduce the 'not affordable' rate from 53%."

### Q7: "How do you know your output is correct?"
> "I built a validation script that checks every output row against the challenge rules: amount bounds, valid enum values, date formats, payment plan arithmetic (do partial payments add up to the total?), and date consistency. All 250 rows pass every check. I also compared my output format against the 25 sample requests provided by the organizers."

### Q8: "Explain your decision pipeline."
> "It's a priority waterfall. I try the best option first — full payment today. If that's not safe, I try installments — evaluating each available plan against the 90-day balance curve. If installments don't work, I try partial payment — some now, rest later. Then I try suggesting spending changes to free up money. If nothing works but a future date is safe, I say 'wait'. If nothing works at all, I say 'not recommended'. The first safe option wins."

### Q9: "How do installments work?"
> "Each request has 2-4 installment options from the seller. For each option, I build the exact payment schedule — say 3 payments of ₹10,000 starting April 1st, monthly. Then I subtract each payment from the projected balance on its due date and check if the balance stays above minimum at every point after. Safe options are ranked by: does it finish by the deadline, lowest total cost including fees, earliest start date, and fewest payments."

### Q10: "Tell me about the dataset."
> "There are 250 requests to evaluate, 276 user profiles, 25,000+ financial events across 5 currencies (INR, ZAR, IDR, USD, EUR). Events have 6 statuses — settled, pending, scheduled, cancelled, failed, unrealized. Expenses have 4 flexibility types. There are also 216 messages in English and Indonesian, and 16 images of receipts and pay slips."

---

## 10. Key Numbers to Remember

| Number | What it represents |
|--------|-------------------|
| **250** | Requests evaluated |
| **276** | User profiles in the system |
| **25,342** | Financial events processed |
| **90 days** | Cash flow forecast window |
| **5** | Currencies supported (INR, ZAR, IDR, USD, EUR) |
| **32 seconds** | Total runtime for all 250 requests |
| **$0.00** | API cost (fully deterministic) |
| **3** | Python files (main, agent, engine) |
| **4** | Affordability statuses |
| **5** | Payment methods |
| **4** | Flexibility types (fixed, stoppable, reducible, reducible_or_stoppable) |

### Output Distribution:
| Status | Count | Percentage |
|--------|-------|-----------|
| Affordable Now | 47 | 19% |
| Affordable with Plan | 49 | 20% |
| Affordable Later | 22 | 9% |
| Not Affordable | 132 | 53% |

---

## 11. Tips for the Interview

1. **Start simple, then go deep.** Give the 30-second pitch first. Only go into technical details when asked.

2. **Use analogies.** "It's like asking a financially smart friend for advice" is better than "it runs a 90-day cash flow simulation with recurring pattern detection."

3. **Admit tradeoffs.** "The deterministic approach sacrifices some flexibility for exactness and zero cost" shows maturity.

4. **Mention the bug you fixed.** Interviewers love hearing about bugs you caught and fixed — it shows real engineering skills.

5. **Know your numbers.** If they ask "how many requests" or "how fast is it", answer immediately. It shows you know your project inside out.

6. **If you don't know, say so.** "That's a good question — I didn't implement that, but here's how I would approach it..." is better than making something up.

7. **Emphasize the deadline.** "This was built in 24 hours" — interviewers understand hackathon constraints and will appreciate what you accomplished.

---

## 12. One-Page Cheat Sheet (Review Right Before Interview)

```
PROJECT: Buy or Wait? — Financial Decision Agent
HACKATHON: HackerRank Orchestrate (24 hours)

WHAT IT DOES:
  For each purchase request → simulates 90-day cash flow → 
  recommends safest payment method

TECH: Python + pandas + numpy (no LLM, no APIs, $0 cost)

3 FILES:
  main.py (entry) → agent.py (decisions) → financial_engine.py (math)

5-STEP PIPELINE:
  1. Load user profile (balance, preferences, protected categories)
  2. Detect recurring patterns from 25K+ events
  3. Simulate balance day-by-day for 90 days
  4. Calculate safe amount and earliest full-payment date
  5. Run decision waterfall: full → installments → partial → wait → no

DECISION PRIORITY:
  full_payment > installments > partial_payment > 
  spending_changes > wait > not_recommended

SMART FEATURES:
  • 5 currencies with dated exchange rates
  • English + Indonesian message parsing
  • 4 flexibility types for spending changes
  • Image amounts extracted at dev time (no runtime API)
  • Installment ranking by cost, deadline, start date

KEY STATS:
  250 requests | 32 seconds | $0 cost | 0 hallucinations
  47 affordable_now | 49 with_plan | 22 later | 132 not_affordable

BIGGEST BUG FIXED:
  Flexibility field mismatch → spending changes went from 0 to 9
```
