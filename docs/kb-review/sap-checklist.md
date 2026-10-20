# Fact-check checklist: SAP (24 articles, reviewer R)

For each article: open it, click each term, confirm the article uses it correctly.
All correct ➜ set `reviewer: R` in the article. Something wrong ➜ note it here and tell Claude.
Values described as *this organisation's* policy (limits, approvals) are fictional company rules:
they cannot be looked up, only checked for being stated as policy rather than as a vendor default.
⭐ = check first (flagged as risky). ⬜ = not checked. 🤖 = AI-checked only (still needs a human). ✅ = human-reviewed.

## 🤖 SAP-ACC-001: SAP user account locked
File: [data/kb/sap/SAP-ACC-001.md](../../data/kb/sap/SAP-ACC-001.md) · author S

**Look up:** [login/fails_to_user_lock](https://www.google.com/search?q=SAP+login%2Ffails_to_user_lock+site%3Ahelp.sap.com) · [SU01](https://www.google.com/search?q=SAP+SU01+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] The failed-logon limit is set by login/fails_to_user_lock (5 here).
- [ ] Only failed-logon locks may be removed by the helpdesk; administrator locks are escalated to SAP security.
- [ ] Unlocking and setting an initial password are both done in SU01.
- [ ] An initial password must be changed by the user at the next logon.

Notes: 

## 🤖 SAP-ACC-002: Not authorised for a transaction
File: [data/kb/sap/SAP-ACC-002.md](../../data/kb/sap/SAP-ACC-002.md) · author S

**Look up:** [SU53](https://www.google.com/search?q=SAP+SU53+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] SU53 shows the last failed authorization check for the current user.
- [ ] New SAP access always needs manager approval recorded in the request.
- [ ] Role changes are made by the SAP security team, not the helpdesk.
- [ ] The user must log on again before a newly assigned role takes effect.

Notes: 

## 🤖 SAP-ACC-004: Fiori app tile missing from the launchpad
File: [data/kb/sap/SAP-ACC-004.md](../../data/kb/sap/SAP-ACC-004.md) · author S

**Look up:** [PFCG](https://www.google.com/search?q=SAP+PFCG+site%3Ahelp.sap.com) · [SU01](https://www.google.com/search?q=SAP+SU01+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] Fiori tiles come from business catalogs assigned through PFCG roles.
- [ ] A newly assigned role may only appear after signing out and clearing the browser cache.
- [ ] Missing roles are requested through the access process with manager approval, never copied wholesale from a colleague.

Notes: 

## 🤖 SAP-FI-001: Wrong exchange rate on a foreign-currency posting
File: [data/kb/sap/SAP-FI-001.md](../../data/kb/sap/SAP-FI-001.md) · author S

**Look up:** [OB08](https://www.google.com/search?q=SAP+OB08+site%3Ahelp.sap.com) · [FB08](https://www.google.com/search?q=SAP+FB08+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] Exchange rates are maintained in OB08 by currency pair, rate type and date.
- [ ] With no rate for the posting date, SAP uses the most recent earlier rate.
- [ ] Posted documents with a wrong rate are reversed (FB08) and reposted by Finance only.

Notes: 

## 🤖 SAP-INT-001: Background job not starting or stuck
File: [data/kb/sap/SAP-INT-001.md](../../data/kb/sap/SAP-INT-001.md) · author S

**Look up:** [SM37](https://www.google.com/search?q=SAP+SM37+site%3Ahelp.sap.com) · [SM50](https://www.google.com/search?q=SAP+SM50+site%3Ahelp.sap.com) · [SM12](https://www.google.com/search?q=SAP+SM12+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] "Released" means waiting for the start condition; "Ready" means waiting for a free background work process.
- [ ] SM50 shows whether background work processes are busy.
- [ ] The job log in SM37 shows the last step a running job reached.
- [ ] Hung jobs are cancelled by Basis.

Notes: 

## 🤖 SAP-INT-002: IDoc in status 51
File: [data/kb/sap/SAP-INT-002.md](../../data/kb/sap/SAP-INT-002.md) · author S

**Look up:** [WE02](https://www.google.com/search?q=SAP+WE02+site%3Ahelp.sap.com) · [WE05](https://www.google.com/search?q=SAP+WE05+site%3Ahelp.sap.com) · [BD87](https://www.google.com/search?q=SAP+BD87+site%3Ahelp.sap.com) · [status 51](https://www.google.com/search?q=SAP+status+51+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] Status 51 means the application document was not posted.
- [ ] The status record in WE02 names the reason for the failure.
- [ ] Failed IDocs are reprocessed with BD87 after the cause is fixed.
- [ ] Many failures from one partner point to the partner profile or mapping.

Notes: 

## 🤖 SAP-MAT-004: Posting period closed for goods movements
File: [data/kb/sap/SAP-MAT-004.md](../../data/kb/sap/SAP-MAT-004.md) · author S

**Look up:** [MMPV](https://www.google.com/search?q=SAP+MMPV+site%3Ahelp.sap.com) · [MMRV](https://www.google.com/search?q=SAP+MMRV+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] Materials management allows postings only in the current and previous period.
- [ ] MMRV displays the current period; MMPV moves it forward.
- [ ] Postings into older closed periods need Finance approval.

Notes: 

## 🤖 SAP-PO-001: Goods receipt fails because the PO item is blocked
File: [data/kb/sap/SAP-PO-001.md](../../data/kb/sap/SAP-PO-001.md) · author S

**Look up:** [MIGO](https://www.google.com/search?q=SAP+MIGO+site%3Ahelp.sap.com) · [ME22N](https://www.google.com/search?q=SAP+ME22N+site%3Ahelp.sap.com) · [ME23N](https://www.google.com/search?q=SAP+ME23N+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] A blocked PO item cannot be goods-receipted in MIGO until the buyer removes the block.
- [ ] Blocks are removed by the responsible buyer in ME22N, never by the helpdesk.
- [ ] ME23N displays the PO without changing it.
- [ ] An item with a deletion indicator needs a new PO item instead of a receipt.

Notes: 

## 🤖 SAP-PO-002: Purchase order waiting for release
File: [data/kb/sap/SAP-PO-002.md](../../data/kb/sap/SAP-PO-002.md) · author S

**Look up:** [ME23N](https://www.google.com/search?q=SAP+ME23N+site%3Ahelp.sap.com) · [ME29N](https://www.google.com/search?q=SAP+ME29N+site%3Ahelp.sap.com) · [ME28](https://www.google.com/search?q=SAP+ME28+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] The Release Strategy tab in ME23N shows which approvals are outstanding.
- [ ] Approvers release POs in ME29N (individually) or ME28 (collectively).
- [ ] An absent approver is covered by a workflow substitute or another holder of the same release code.
- [ ] The helpdesk never releases a PO on an approver's behalf.

Notes: 

## 🤖 SAP-PO-004: Vendor invoice blocked for payment
File: [data/kb/sap/SAP-PO-004.md](../../data/kb/sap/SAP-PO-004.md) · author S

**Look up:** [MIRO](https://www.google.com/search?q=SAP+MIRO+site%3Ahelp.sap.com) · [MRBR](https://www.google.com/search?q=SAP+MRBR+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] MIRO blocks invoices for payment when they differ from the PO or goods receipt beyond tolerance.
- [ ] MRBR shows why an invoice is blocked and is used to release it.
- [ ] After the missing goods receipt is posted, a quantity block is released by an MRBR run, not automatically.
- [ ] Blocked invoices are released by accounts payable, not the helpdesk.

Notes: 

## 🤖 SAP-SYS-001: SAP GUI cannot connect to the server
File: [data/kb/sap/SAP-SYS-001.md](../../data/kb/sap/SAP-SYS-001.md) · author S

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] Several users unable to connect at once points to a server problem for Basis.
- [ ] SAP GUI connects to the dispatcher on port 32 plus the instance number (3200 for instance 00).
- [ ] Remote users need the VPN connected before SAP GUI can reach the server.

Notes: 

## 🤖 SAP-ACC-003: Forgotten SAP password
File: [data/kb/sap/SAP-ACC-003.md](../../data/kb/sap/SAP-ACC-003.md) · author S

**Look up:** [SU01](https://www.google.com/search?q=SAP+SU01+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] Each SAP system has its own password unless single sign-on is used.
- [ ] Self-service reset needs a verified mobile number in the user's profile.
- [ ] The helpdesk fallback is an initial password set in SU01 after identity verification.

Notes: 

## 🤖 SAP-FI-002: Posting period not open in finance
File: [data/kb/sap/SAP-FI-002.md](../../data/kb/sap/SAP-FI-002.md) · author S

**Look up:** [OB52](https://www.google.com/search?q=SAP+OB52+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] Finance posting periods are controlled per account type in OB52.
- [ ] Postings into a closed period are rejected.
- [ ] Only the Finance close team opens or closes periods.

Notes: 

## 🤖 SAP-FI-003: General ledger account blocked for posting
File: [data/kb/sap/SAP-FI-003.md](../../data/kb/sap/SAP-FI-003.md) · author S

**Look up:** [FS00](https://www.google.com/search?q=SAP+FS00+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] G/L accounts are blocked for posting in the account master (FS00).
- [ ] Blocked accounts usually have a replacement account named by Finance master data.
- [ ] Postings go to the replacement account rather than unblocking the old one.

Notes: 

## 🤖 SAP-FI-004: Vendor not included in the payment run
File: [data/kb/sap/SAP-FI-004.md](../../data/kb/sap/SAP-FI-004.md) · author S

**Look up:** (no technical terms; check the steps make sense)

**Key facts to confirm:**
- [ ] The automatic payment run is F110.
- [ ] Items are paid only if due, not blocked, and the vendor has a payment method and bank details.
- [ ] The payment run exception list explains why items were not paid.

Notes: 

## 🤖 SAP-INT-003: Interface fails with RFC connection error
File: [data/kb/sap/SAP-INT-003.md](../../data/kb/sap/SAP-INT-003.md) · author S

**Look up:** [SM59](https://www.google.com/search?q=SAP+SM59+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] RFC destinations are tested in SM59.
- [ ] A logon failure in the test points to a locked or expired technical user.
- [ ] RFC destinations in production are changed only by Basis.

Notes: 

## 🤖 SAP-INT-004: Scheduled job cancelled because a variant is missing
File: [data/kb/sap/SAP-INT-004.md](../../data/kb/sap/SAP-INT-004.md) · author S

**Look up:** [SM37](https://www.google.com/search?q=SAP+SM37+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] A job using a deleted or invalid variant ends with status Canceled.
- [ ] The SM37 job log names the report, the variant and the error.
- [ ] The job owner corrects the variant before the job is rescheduled.

Notes: 

## 🤖 SAP-MAT-001: Material master locked by another user
File: [data/kb/sap/SAP-MAT-001.md](../../data/kb/sap/SAP-MAT-001.md) · author S

**Look up:** [MM02](https://www.google.com/search?q=SAP+MM02+site%3Ahelp.sap.com) · [SM12](https://www.google.com/search?q=SAP+SM12+site%3Ahelp.sap.com) · [SM04](https://www.google.com/search?q=SAP+SM04+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] A material is locked while another user edits it in MM02.
- [ ] Lock entries are listed in SM12.
- [ ] Basis deletes a lock entry only after confirming in SM04 that the session is gone.

Notes: 

## 🤖 SAP-MAT-002: Number range exhausted
File: [data/kb/sap/SAP-MAT-002.md](../../data/kb/sap/SAP-MAT-002.md) · author S

**Look up:** [FBN1](https://www.google.com/search?q=SAP+FBN1+site%3Ahelp.sap.com) · [MMNR](https://www.google.com/search?q=SAP+MMNR+site%3Ahelp.sap.com) · [SNRO](https://www.google.com/search?q=SAP+SNRO+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] Each document type draws numbers from a number range interval.
- [ ] Year-dependent intervals, such as accounting documents, must be created for every new fiscal year.
- [ ] Number range changes are configuration changes made by the SAP configuration team.

Notes: 

## 🤖 SAP-MAT-003: Material not maintained for the plant
File: [data/kb/sap/SAP-MAT-003.md](../../data/kb/sap/SAP-MAT-003.md) · author S

**Look up:** [MM03](https://www.google.com/search?q=SAP+MM03+site%3Ahelp.sap.com) · [MM01](https://www.google.com/search?q=SAP+MM01+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] A material must be extended to each plant before it can be used there.
- [ ] MM03 shows which plants a material is maintained for.
- [ ] Extensions are made by the master-data team in MM01.

Notes: 

## 🤖 SAP-PO-003: Goods receipt quantity exceeds the PO quantity
File: [data/kb/sap/SAP-PO-003.md](../../data/kb/sap/SAP-PO-003.md) · author S

**Look up:** [MIGO](https://www.google.com/search?q=SAP+MIGO+site%3Ahelp.sap.com) · [ME23N](https://www.google.com/search?q=SAP+ME23N+site%3Ahelp.sap.com) · [ME22N](https://www.google.com/search?q=SAP+ME22N+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] The over-delivery tolerance is set per PO item on its Delivery tab.
- [ ] Receipts above ordered quantity plus tolerance are blocked in MIGO.
- [ ] The buyer decides whether to accept extra quantity by increasing the PO quantity.

Notes: 

## 🤖 SAP-SYS-002: Short dump during a transaction
File: [data/kb/sap/SAP-SYS-002.md](../../data/kb/sap/SAP-SYS-002.md) · author S

**Look up:** [ST22](https://www.google.com/search?q=SAP+ST22+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] ST22 lists short dumps by user and time.
- [ ] TIME_OUT means a dialog step exceeded the allowed runtime; narrowing the selection or running in background avoids it.
- [ ] Dumps in custom Z or Y programs go to the development team.

Notes: 

## 🤖 SAP-SYS-003: Printed SAP document never arrives at the printer
File: [data/kb/sap/SAP-SYS-003.md](../../data/kb/sap/SAP-SYS-003.md) · author S

**Look up:** [SP01](https://www.google.com/search?q=SAP+SP01+site%3Ahelp.sap.com) · [SPAD](https://www.google.com/search?q=SAP+SPAD+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] SP01 lists spool requests and is used to reprint them.
- [ ] A missing spool request means no output was triggered for the document.
- [ ] Output devices are maintained by Basis in SPAD.
- [ ] Printer hardware faults belong to desktop support, not SAP.

Notes: 

## 🤖 SAP-SYS-004: Wrong date or number format in SAP
File: [data/kb/sap/SAP-SYS-004.md](../../data/kb/sap/SAP-SYS-004.md) · author S

**Look up:** [SU3](https://www.google.com/search?q=SAP+SU3+site%3Ahelp.sap.com)

**Key facts to confirm:**
- [ ] Date and decimal formats are set per user in SU3 on the Defaults tab.
- [ ] New formats apply after logging off and on again.
- [ ] Display formats do not change the stored data.

Notes: 

