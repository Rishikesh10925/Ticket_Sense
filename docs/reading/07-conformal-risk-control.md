# Reading note: Conformal Risk Control

- Paper: A. N. Angelopoulos, S. Bates, A. Fisch, L. Lei and T. Schuster, ICLR 2024
  (Blueprint ref. [7])
- Presented by: Rishikesh, Week 1 design session (10 minutes)

## The idea in one paragraph

Conformal prediction guarantees that a prediction set misses the truth at most α of the
time. Conformal risk control (CRC) generalises "misses" to any bounded loss that is
monotone (non-increasing) in a parameter λ. Given n calibration examples with losses
L_i(λ) ∈ [0, B], choose

λ̂ = inf { λ : (n / (n + 1)) · R̂_n(λ) + B / (n + 1) ≤ α },

where R̂_n is the empirical mean loss. Then the **expected** loss on a new exchangeable
example is at most α, and it is not much below α (within about B/(n+1)). So the
guarantee is tight, not merely safe.

## CRC versus Learn then Test, for our gate

| | Conformal risk control | Learn then Test (what we use) |
|---|---|---|
| Guarantee | E[loss] ≤ α, averaged over calibration draws | P(risk ≤ α) ≥ 1 − δ for the selected threshold |
| Loss shape | Must be monotone in λ | Any; uses p-values |
| Strength | Tight, simple closed form | High-probability statement the admin can read as a promise |
| Our risk | The fast-lane risk is a *ratio* (bad / shown), which is not a per-ticket monotone loss | Binomial test handles the ratio directly |

## Why we chose LTT for the main gate

The administrator's question is "how sure are we that *this* threshold keeps errors under
10%?" That is a high-probability statement about one deployed threshold, which is LTT's
form. CRC promises the error rate *on average over calibrations*, so a single unlucky
calibration set can still give a threshold that is too lenient. Also, selective risk
(errors among shown drafts) is not a monotone per-example loss, so CRC does not apply
directly. CRC would fit a per-ticket loss like "an unacceptable draft reached the fast
lane", which controls a different quantity (unacceptable and shown, over all tickets).

## What we keep from it

- A possible ablation for the Discussion chapter: CRC controlling
  P(unacceptable and fast lane) ≤ α versus LTT controlling the fast-lane risk, so the
  report can explain which promise each one makes.
- The same honesty about exchangeability. Both fail under topic shift; H3 measures it.
