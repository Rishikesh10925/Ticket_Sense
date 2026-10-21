# Error analysis: worst gate cases (judge labels)

PROVISIONAL: labels are the LLM judge's.

Unacceptable drafts the gate would still show (validation + unseen, guard on): **77**.

| Group | Counts |
|---|---|
| Split | {'unseen': 58, 'val': 19} |
| Ticket type | {'C1': 58, 'A': 16, 'C2': 2, 'B': 1} |
| Department | {'SAP': 22, 'Networking': 21, 'Cloud': 20, 'Database': 13, 'HR': 1} |
| Topic | {'net-switching': 19, 'sap-finance': 15, 'cloud-provisioning': 14, 'db-replication': 8, 'sap-access': 4, 'sap-system': 3, 'net-performance': 2, 'cloud-storage': 2, 'db-storage': 2, 'cloud-cost': 2, 'cloud-compute': 2, 'none': 2, 'hr-payroll': 1, 'db-locking': 1} |

## The 15 highest-scoring

### 1. T-00771 · A · Networking / net-performance · val
- Ticket: File copies slow over VPN
- Gate: assisted, score 0.830; reasons: unusual number of claims, low reranker score, a weakly supported claim
- Claims supported 0.8333, min support 0.0033, routing certainty 0.946, probe margin 0.5561
- Label R: The draft is partly correct but missing key steps and contains wrong steps; rewriting is faster.

### 2. T-00447 · A · Cloud / cloud-storage · val
- Ticket: Expired download link
- Gate: assisted, score 0.828; reasons: ticket asks several questions, ticket also matches another department, weak best retrieval match
- Claims supported 0.6667, min support 0.4512, routing certainty 0.8914, probe margin 0.3161
- Label R: The draft is partly correct but missing key steps and contains no wrong steps, however, rewriting is faster to include the necessary information from the reference.

### 3. T-00463 · A · HR / hr-payroll · val
- Ticket: Missed timesheet deadline
- Gate: assisted, score 0.816; reasons: uncertain routing, a weakly supported claim, keyword and dense results differ
- Claims supported 0.3333, min support 0.0002, routing certainty 0.743, probe margin 0.3963
- Label R: The draft is partly correct but missing key steps and containing wrong steps; rewriting is faster.

### 4. T-00162 · A · Cloud / cloud-storage · val
- Ticket: Expired download link
- Gate: assisted, score 0.810; reasons: uncertain routing, no clear best passage, ticket asks several questions
- Claims supported 1.0, min support 0.9383, routing certainty 0.7652, probe margin 0.3368
- Label R: The draft is partly correct but missing key steps and contains no wrong steps, however, it is faster to rewrite it to include the correct key facts.

### 5. T-00487 · A · Networking / net-performance · val
- Ticket: File copies slow over VPN
- Gate: assisted, score 0.804; reasons: uncertain routing, low reranker score, a weakly supported claim
- Claims supported 0.5, min support 0.0003, routing certainty 0.8267, probe margin 0.5281
- Label R: The draft is partly correct but missing key steps and contains wrong steps; rewriting is faster.

### 6. T-01540 · C1 · SAP / sap-finance · unseen
- Ticket: Posting period issue
- Gate: assisted, score 0.804; reasons: topic often needs rework, old evidence, keyword and dense results differ
- Claims supported 1.0, min support 0.9585, routing certainty 0.9045, probe margin 0.2275
- Label W: The draft confidently answers despite missing key facts and contradicting others, which could mislead or cause harm.

### 7. T-01470 · C1 · SAP / sap-finance · unseen
- Ticket: Posting period issue
- Gate: assisted, score 0.791; reasons: uncertain routing, topic often needs rework, old evidence
- Claims supported 0.75, min support 0.1073, routing certainty 0.8439, probe margin 0.3094
- Label W: The draft confidently answers despite lacking critical information, relying on guesswork that could mislead or cause harm.

### 8. T-01255 · C1 · Networking / net-switching · unseen
- Ticket: Desk phone not turning on
- Gate: assisted, score 0.790; reasons: a weakly supported claim, flat reranker scores, uncertain routing
- Claims supported 0.0, min support 0.003, routing certainty 0.8262, probe margin 0.151
- Label W: The draft confidently answers with incorrect information, relying on irrelevant sources and missing key facts.

### 9. T-01421 · C1 · Cloud / cloud-provisioning · unseen
- Ticket: Managed db connections full
- Gate: assisted, score 0.787; reasons: low reranker score, uncertain routing, topic often needs rework
- Claims supported 1.0, min support 0.9453, routing certainty 0.6623, probe margin 0.2378
- Label W: The draft confidently answers the question despite lacking the necessary information to do so, and some of the steps provided are incorrect or irrelevant.

### 10. T-01398 · C1 · SAP / sap-finance · unseen
- Ticket: Finance posting issue
- Gate: assisted, score 0.784; reasons: topic often needs rework, unusual ticket length, uncertain routing
- Claims supported 1.0, min support 0.9585, routing certainty 0.9027, probe margin 0.2441
- Label W: The draft confidently answers the question despite lacking the necessary information to do so, which is a critical problem.

### 11. T-01494 · C1 · Cloud / cloud-provisioning · unseen
- Ticket: Managed DB connections overloaded
- Gate: assisted, score 0.781; reasons: uncertain routing, topic often needs rework, unusual ticket length
- Claims supported 0.8, min support 0.1145, routing certainty 0.8184, probe margin 0.2468
- Label W: The draft confidently answers the ticket despite lacking the necessary information to do so, and includes an action (restart the application instance) that could potentially cause more harm than good.

### 12. T-01468 · C1 · SAP / sap-finance · unseen
- Ticket: Posting period issue
- Gate: assisted, score 0.780; reasons: uncertain routing, topic often needs rework, unusual ticket length
- Claims supported 1.0, min support 0.9655, routing certainty 0.873, probe margin 0.2982
- Label W: The draft confidently answers the ticket despite lacking the necessary information to do so, which is a critical problem.

### 13. T-01258 · C1 · SAP / sap-finance · unseen
- Ticket: Posting period closed
- Gate: assisted, score 0.779; reasons: uncertain routing, low reranker score, topic often needs rework
- Claims supported 0.8, min support 0.0712, routing certainty 0.7934, probe margin 0.2787
- Label W: The draft confidently answers the ticket despite lacking the necessary information to do so, relying on guessed steps that may not be correct.

### 14. T-01277 · C1 · Cloud / cloud-provisioning · unseen
- Ticket: New cloud environment needed
- Gate: assisted, score 0.778; reasons: a weakly supported claim, topic often needs rework, low reranker score
- Claims supported 0.0, min support 0.0031, routing certainty 0.9777, probe margin 0.1928
- Label W: The draft confidently answers despite lacking the necessary information, which is a critical problem.

### 15. T-01257 · C1 · SAP / sap-finance · unseen
- Ticket: Posting period closed
- Gate: assisted, score 0.777; reasons: uncertain routing, topic often needs rework, old evidence
- Claims supported 1.0, min support 0.9585, routing certainty 0.8485, probe margin 0.2951
- Label W: The draft confidently answers despite lacking the necessary information to do so, relying on guesswork.

