# LOANORBIT — Financial Engine & Accounting Architecture

**Compliance Standard:** Strict Decimal & Integer Paise Arithmetic  
**Accounting Standard:** Double-Entry Journaling with Balanced Constraints  
**Currency Unit:** Paise (1 INR = 100 Paise)  

---

## 1. EMI Computation (Reducing Balance)

The monthly EMI for reducing balance interest is given by:

$$EMI = P \times \frac{r(1+r)^n}{(1+r)^n - 1}$$

Where:
- $P$ = Principal amount (converted from paise to `Decimal(Rupees)` for exponentiation).
- $r$ = Monthly interest rate $= \frac{\text{Annual Nominal Rate (Bps)}}{12 \times 100 \times 100} = \frac{\text{Annual Rate \%}}{12 \times 100}$.
- $n$ = Number of monthly instalments.

### Zero-Interest Special Case
If annual rate is $0\%$:
$$EMI = \frac{P}{n}$$

### Precision & Rounding Rules
- All rates are stored in Basis Points (`bps`), where $100\text{ bps} = 1\%$.
- EMI is rounded to the nearest integer paise using `ROUND_HALF_UP`.
- In the amortisation schedule, the final instalment absorbs any minor 1–2 paise rounding residual so that:
$$\sum \text{Principal Components} \equiv \text{Disbursed Principal}$$
$$\text{Final Closing Principal} \equiv 0$$

---

## 2. Repayment Schedule Generation

For each period $k \in [1, n]$:
1. $\text{Interest}_k = \text{round}(\text{OpeningPrincipal}_k \times r)$
2. If $k < n$:
   - $\text{Principal}_k = \text{EMI} - \text{Interest}_k$
   - $\text{ClosingPrincipal}_k = \text{OpeningPrincipal}_k - \text{Principal}_k$
3. If $k = n$ (Final Period):
   - $\text{Principal}_n = \text{OpeningPrincipal}_n$
   - $\text{EMI}_n = \text{Principal}_n + \text{Interest}_n$
   - $\text{ClosingPrincipal}_n = 0$
4. $\text{OpeningPrincipal}_{k+1} = \text{ClosingPrincipal}_k$

---

## 3. Fee & Tax Computation

- **Processing Fee:**
  - *Fixed:* e.g., ₹500 = `50,000 paise`.
  - *Percentage:* e.g., $2\% = 200 \text{ bps} \rightarrow \text{round}(P \times 0.02)$.
- **GST on Fees:**
  - Standard GST @ $18\%$ ($1,800\text{ bps}$) computed *exclusively* on applicable fees (never on principal or loan interest).
  - $\text{GST} = \text{round}(\text{ProcessingFee} \times 0.18)$.
- **Net Disbursement:**
  $$\text{Net Disbursement} = P - (\text{ProcessingFee} + \text{GST})$$

---

## 4. Annual Percentage Rate (APR)

APR reflects the true annual cost of borrowing including fees. It is calculated via the Internal Rate of Return (IRR) on monthly cash flows:
- Time $t = 0$: $-\text{Net Disbursement}$ (Cash inflow to borrower)
- Time $t = 1 \dots n$: $+\text{EMI}_t$ (Cash outflow from borrower)

We solve for the monthly rate $r_m$ such that:
$$\text{NPV} = -\text{NetDisbursement} + \sum_{t=1}^n \frac{\text{EMI}_t}{(1 + r_m)^t} = 0$$

$$\text{APR} = r_m \times 12 \times 100\%$$

Solved numerically using the Newton-Raphson method with guaranteed bounded convergence.

---

## 5. Payment Allocation Waterfall

When a payment of amount $A$ is posted against an active loan:
1. **Tier 1: Overdue Penalties & Charges:**
   $$\text{AllocatedCharges} = \min(A, \text{DueCharges})$$
   $$A \leftarrow A - \text{AllocatedCharges}$$
2. **Tier 2: Accrued / Due Interest:**
   $$\text{AllocatedInterest} = \min(A, \text{DueInterest})$$
   $$A \leftarrow A - \text{AllocatedInterest}$$
3. **Tier 3: Due Principal:**
   $$\text{AllocatedPrincipal} = \min(A, \text{DuePrincipal})$$
   $$A \leftarrow A - \text{AllocatedPrincipal}$$
4. **Tier 4: Future Principal / Excess Balance:**
   Any surplus amount is allocated to reducing future principal or held in borrower overpayment holding liability.

---

## 6. Double-Entry General Ledger

Every financial event creates an immutable, balanced `journal_entry` composed of multiple `journal_lines`:

$$\sum \text{Debits (Paise)} - \sum \text{Credits (Paise)} = 0$$

### Example 1: Loan Disbursement
- Loan Principal: ₹25,000 | Processing Fee: ₹500 | GST: ₹90 | Net Disbursed: ₹24,410
```
Debit:  1101 Loan Principal Receivable        ₹25,000 (2,500,000 paise)
Credit: 1001 Cash / Settlement Account         ₹24,410 (2,441,000 paise)
Credit: 4002 Processing Fee Income               ₹500 (   50,000 paise)
Credit: 2101 GST Payable                          ₹90 (    9,000 paise)
Sum: Debits = 2,500,000 | Credits = 2,500,000 (BALANCED)
```

### Example 2: Monthly EMI Repayment
- EMI Paid: ₹4,388 | Principal: ₹4,013 | Interest: ₹375
```
Debit:  1001 Cash / Settlement Account         ₹4,388 (438,800 paise)
Credit: 1101 Loan Principal Receivable         ₹4,013 (401,300 paise)
Credit: 4001 Interest Income                     ₹375 ( 37,500 paise)
Sum: Debits = 438,800 | Credits = 438,800 (BALANCED)
```

### Example 3: Payment Reversal
A payment reversal creates exact inverse compensating entries with explicit audit linkages; posted records are never hard-deleted.
