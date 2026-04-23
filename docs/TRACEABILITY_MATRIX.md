> **Portfolio Project** | QA Manual Engineer | 2026  
# Requirements Traceability Matrix

| Field | Value |
|-------|-------|
| **Document ID** | RTM-001 |
| **Version** | 1.0 |
| **Date** | April 2026 |

---

## Purpose

Traces every Use Case → Test Plan Module → Test Cases → Bug Reports.

---

## Full Matrix

| Use Case | Feature | TP Module | Test Cases | Bugs | Status |
|----------|---------|-----------|------------|------|--------|
| UC-01 | Valid login | M-01 | TC-01-01, TC-01-02, TC-01-03 | — | ✅ |
| UC-01 | Session persistence | M-01 | TC-01-09 | — | ✅ |
| UC-01 | RBAC Viewer restrictions | M-01 | TC-01-04, TC-01-05, TC-01-06 | — | ✅ |
| UC-01 | RBAC Editor restrictions | M-01 | TC-01-07, TC-01-08 | — | ✅ |
| UC-01 | Change password | M-01 | TC-01-10 | — | ✅ |
| UC-02 | CSV upload success | M-02 | TC-02-01 | BUG-007 | ✅ |
| UC-02 | Missing board keys | M-02 | TC-02-02 | — | ✅ |
| UC-02 | Subboards=0 | M-02 | TC-02-03 | — | ⚠️ Known |
| UC-02 | Missing columns | M-02 | TC-02-04 | — | ✅ |
| UC-02 | Empty file | M-02 | TC-02-05 | — | ✅ |
| UC-02 | Encoding handling | M-02 | TC-02-06 | — | ✅ |
| UC-02 | OperatorJudgement normalization | M-02 | TC-02-07 | — | ✅ |
| UC-02 | Duplicate upload | M-02 | TC-02-08 | — | ✅ |
| UC-02 | Multi-lot upload | M-02 | TC-02-09 | — | ✅ |
| UC-02 | Session delete | M-02 | TC-02-10 | — | ✅ |
| UC-03 | Add board key | M-04 | TC-04-01 | — | ✅ |
| UC-03 | Duplicate rejected | M-04 | TC-04-02 | — | ✅ |
| UC-03 | Schema migration | M-04 | TC-04-03 | — | ✅ |
| UC-03 | Pair configuration | M-04 | TC-04-04 | — | ✅ |
| UC-03 | has_ict flag | M-04 | TC-04-05 | — | ✅ |
| UC-03 | Validation | M-04 | TC-04-06 | — | ✅ |
| UC-04 | PPY calculation | M-03 | TC-03-01 | — | ✅ |
| UC-04 | FPY calculation | M-03 | TC-03-02 | — | ✅ |
| UC-04 | Scrap Rate | M-03 | TC-03-03 | — | ✅ |
| UC-04 | Gauge color thresholds | M-03 | TC-03-07 | BUG-011 | ✅ |
| UC-04 | Average PPY/FPY | M-03 | TC-03-08 | — | ✅ |
| UC-05 | Unique PCB counting | M-03 | TC-03-04 | BUG-002 | ✅ |
| UC-05 | Percentage base | M-03 | TC-03-05 | BUG-001 | ✅ |
| UC-05 | FalseCall only | M-03 | TC-03-06 | — | ✅ |
| UC-06 | S1∪S2 union | M-05 | TC-05-01, TC-06-01 | BUG-006 | ✅ |
| UC-06 | Table sorting | M-05 | TC-05-05, TC-05-06 | — | ✅ |
| UC-06 | Date filter | M-05 | TC-05-07 | BUG-010 | ⚠️ |
| UC-06 | Pie chart | M-05 | TC-05-08 | BUG-008 | ✅ |
| UC-06 | Consistent with Projects | M-05 | TC-05-09 | BUG-009 | ✅ |
| UC-07 | ICT NG save | M-05 | TC-05-02 | — | ✅ |
| UC-07 | Viewer blocked | M-05 | TC-05-04 | — | ✅ |
| UC-08 | Pairing match | M-06 | TC-06-01 | — | ✅ |
| UC-08 | Pairing mismatch | M-06 | TC-06-02 | — | ✅ |
| UC-08 | S1 only | M-06 | TC-06-03 | — | ✅ |
| UC-08 | Unpaired boards | M-06 | TC-06-04 | — | ✅ |
| UC-09 | Delete lot Admin only | M-05 | TC-05-03 | — | ✅ |
| UC-10 | Variant grouping | M-07 | TC-07-01 | BUG-003 | ✅ |
| UC-10 | Sorted by NG | M-07 | TC-07-02 | — | ✅ |
| UC-10 | TOP 20 limit | M-07 | TC-07-03 | — | ✅ |
| UC-10 | Min 2 lots | M-07 | TC-07-04 | — | ✅ |
| UC-11 | Action from TOP 10 | M-08 | TC-08-01 | — | ✅ |
| UC-11 | Action from Yield | M-08 | TC-08-02 | — | ✅ |
| UC-11 | Viewer blocked | M-08 | TC-08-03 | — | ✅ |
| UC-11 | Persists in DB | M-08 | TC-08-04 | — | ✅ |
| UC-14 | Infinite loop fix | M-05 | TC-05-01 | BUG-004, BUG-005 | ✅ |

---

## Bug → Test Case Mapping

| Bug | Severity | Failing TC | Fix Summary |
|-----|----------|------------|-------------|
| BUG-001 | 🟠 High | TC-03-05 | Changed % denominator to total NG PCBs |
| BUG-002 | 🟠 High | TC-03-04 | Sort by unique boards not events |
| BUG-003 | 🟠 High | TC-07-01 | Added variant to grouping key |
| BUG-004 | 🔴 Critical | TC-05-01 | Early-return if lots unchanged |
| BUG-005 | 🟠 High | TC-05-01 | Removed stale JS code |
| BUG-006 | 🟠 High | TC-05-01 | Compute Set locally not in shared state |
| BUG-007 | 🔴 Critical | TC-02-01 | Added link_id to tuple unpack |
| BUG-008 | 🟠 High | TC-05-09 | Single formula: ng/total×100 everywhere |
| BUG-009 | 🟠 High | TC-05-09 | Both views use calcYieldRows() |
| BUG-010 | 🔵 Low | TC-05-07 | Known limitation — re-upload CSV |
| BUG-011 | 🔵 Low | TC-03-07 | Gradient segments + needle design |

---

## Coverage Summary

| Module | UCs | TCs | Bugs | Pass Rate |
|--------|-----|-----|------|-----------|
| M-01 Auth | UC-01 | 10 | 0 | 100% |
| M-02 Upload | UC-02 | 10 | 1 | 90%* |
| M-03 KPI | UC-04, UC-05 | 8 | 3 | 100% |
| M-04 Board Master | UC-03 | 6 | 0 | 100% |
| M-05 Yield | UC-06..09, UC-14 | 9 | 6 | 100% |
| M-06 Pairing | UC-08 | 4 | 0 | 100% |
| M-07 Recurring | UC-10 | 4 | 1 | 100% |
| M-08 Actions | UC-11 | 4 | 0 | 100% |
| **Total** | **15/15** | **55** | **11** | **98.2%** |

*TC-02-03 is known limitation

---

## Document Flow

```
TEST_PLAN.md  →  defines scope and modules
     ↓
USE_CASES.md  →  defines features (UC-01..UC-15)
     ↓
TEST_SUITE.md →  test cases (TC-01-01..TC-08-04)
     ↓ TC fails
BUG_REPORTS.md → root cause + fix (BUG-001..BUG-011)
     ↓ after fix
TC re-run → PASS
     ↓
TRACEABILITY_MATRIX.md ← (this document)
```
