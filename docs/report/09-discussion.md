# 9. Discussion, limitations and future work

*Owner: Shivaganesh. Draft v1. The final discussion is written after the locked test and the study.*

## 9.1 What the development numbers suggest

- The confidence model ranks drafts better than every single signal on validation, but the
  margin over top-1 retrieval similarity is not yet reliable.
- What helps most is knowing *where* a ticket comes from (category history, routing
  certainty, cross-department ambiguity), not how well the draft is grounded. On a
  benchmark where retrieval almost always finds the right article, grounding varies little.
- The gate is cautious: no fast lane can be certified at a 10% budget yet, so the system
  runs as assisted plus escalate.
- Unseen topics are the main risk; the shift guard removes two thirds of the unacceptable
  drafts that would otherwise reach an engineer, at a small cost on known topics.

## 9.2 Limitations

1. No human labels yet; all numbers use an LLM judge measured against one member on 28 drafts.
2. Synthetic benchmark: paraphrased tickets make retrieval unrealistically easy.
3. Single-split noise: changing only row order moved validation AURC from 0.149 to 0.134.
4. Fast lane closed: the three-lane design currently runs as two lanes.
5. Shift guard tuned and evaluated on three topics each.
6. The output screen blocks some acceptable drafts (47 of 1,484 shown).
7. Knowledge base not yet human-reviewed by a second member.
8. One laptop, one ticket at a time for latency.

## 9.3 Future work

**To be written** after the results: real tickets, more calibration labels to open the fast
lane, topic-aware thresholds, and learning from engineer edits.
