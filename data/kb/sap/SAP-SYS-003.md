---
id: SAP-SYS-003
department: SAP
topic: sap-system
title: Printed SAP document never arrives at the printer
updated: '2026-02-26'
served: true
author: S
reviewer: Claude
legacy: print-output-missing-sp01
---

## Symptom
A user printed an invoice, purchase order or delivery note from SAP but nothing came out
of the printer.

## Cause
SAP creates a spool request and passes it to the output device. The request can fail
(wrong output device), wait for a printer that is offline, or never be created because
no output was triggered for the document.

## Resolution steps
1. Open SP01 and search for spool requests by the user's ID and the time of printing.
2. If a request exists with an error status, open its log. The most common cause is an
   output device that points to the wrong or a retired printer.
3. If the request is fine, reprint it from SP01 to the correct output device.
4. If no spool request exists, the print was never triggered from SAP. Check the
   document's output messages; an output type may be missing.
5. If the printer is offline or out of paper, hand over to desktop support.

## Warnings
Do not change output device definitions in SPAD; that is a Basis task.

## Key facts
- SP01 lists spool requests and is used to reprint them.
- A missing spool request means no output was triggered for the document.
- Output devices are maintained by Basis in SPAD.
- Printer hardware faults belong to desktop support, not SAP.
