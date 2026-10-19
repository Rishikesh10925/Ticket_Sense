# Incorrect Exchange Rate on FI Posting

**Department:** SAP

## Issue
A financial posting in a foreign currency used the wrong exchange rate,
causing a discrepancy between the SAP-calculated and expected local-currency
amount.

## Resolution
1. Check the exchange rate table (OB08) for the posting date and currency
   pair — confirm whether the rate was missing (defaulted to a stale rate)
   or entered incorrectly.
2. If the rate table was missing an entry for that date, add the correct
   rate and note this may require reversing and reposting any documents
   posted with the fallback rate.
3. If the rate was entered correctly but the document type uses a different
   rate type (average vs. bank buying/selling), confirm the correct rate
   type with Finance before making any correction.
4. Corrections to posted documents require a Finance approval — the
   helpdesk should not reverse FI documents unilaterally.

## Notes
Always escalate exchange-rate discrepancies on documents already posted to
Finance rather than correcting them directly.
