---
id: SAP-FI-001
department: SAP
topic: sap-finance
title: Wrong exchange rate on a foreign-currency posting
updated: '2024-03-19'
served: false
author: S
reviewer: null
legacy: incorrect-exchange-rate-fi
---

## Symptom
A posting in foreign currency was converted to local currency at an unexpected rate, so
the local amount differs from what Finance expected.

## Cause
SAP takes the rate for the posting date from the exchange-rate table, maintained in
OB08. If no rate was entered for that date, SAP uses the most recent earlier rate. A
document type may also use a different rate type (for example the average rate "M")
than the one the user expected.

## Resolution steps
1. Note the document number, posting date, currency pair and the rate used.
2. Check OB08 for the currency pair, rate type and date. See whether the rate was
   missing (an older rate was used) or entered wrongly.
3. If a rate was missing or wrong, Finance enters the correct rate for future postings.
4. Documents already posted with the wrong rate are reversed and reposted by Finance
   (reversal in FB08), never by the helpdesk.

## Warnings
Do not change exchange rates or reverse posted documents. Both are Finance tasks with
approval.

## Key facts
- Exchange rates are maintained in OB08 by currency pair, rate type and date.
- With no rate for the posting date, SAP uses the most recent earlier rate.
- Posted documents with a wrong rate are reversed (FB08) and reposted by Finance only.
