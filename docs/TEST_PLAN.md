> **Portfolio Project** | QA Manual Engineer | 2026  
# Test Plan — SMT AOI Quality Dashboard

| Field | Value |
|-------|-------|
| **Document ID** | TP-001 |
| **Version** | 1.0 |
| **Date** | April 2026 |
| **Author** | QA Manual Engineer |

---

## 1. Scope

**In scope:** Authentication/RBAC, CSV upload/parsing, KPI calculations (PPY/FPY/Scrap), S1∪S2 union logic, Board Master CRUD, Yield tab, Recurring defects, Action Plan, Visualizations.

**Out of scope:** Performance testing, mobile, export functionality, SAKI API integration.

---

## 2. Test Objectives

1. Verify KPI calculations match SAKI AOI machine output
2. Confirm S1∪S2 union logic produces correct physical PCB counts
3. Validate RBAC — each role can only access permitted features
4. Ensure CSV upload handles edge cases without crashing
5. Verify data integrity — no corruption on CRUD operations
6. Confirm schema migration runs without data loss

---

## 3. Test Approach

| Type | Approach |
|------|----------|
| Functional | Manual black-box testing |
| Calculation | Cross-validate with SAKI AOI output |
| Negative | Invalid inputs, boundary values, unauthorized access |
| Regression | Re-run affected TCs after each bug fix |
| API | Postman collection — 34 requests, positive + negative |

---

## 4. Test Environment

| Component | Details |
|-----------|---------|
| OS | Windows 10/11 |
| Browser | Chrome 120+, Edge 120+ |
| Python | 3.10+ |
| URL | http://localhost:5000 |
| API Testing | Postman — see `/postman/` folder |

### Test Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| smt_eng | smt123 | Editor |
| viewer | view123 | Viewer |

---

## 5. Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| KPI mismatch with SAKI machine | Medium | High | Cross-validate with real CSV |
| S1∪S2 logic incorrect for edge cases | Medium | High | Test S1-only, S2-only, mismatched counts |
| Data loss on delete | Low | Critical | Verify DB state before/after |
| RBAC bypass via direct API | Medium | High | Test endpoints directly with wrong session |
| Schema migration corrupts data | Low | Critical | Test on DB with existing records |
| date_str empty for pre-migration records | High | Medium | Document as known limitation |

---

## 6. Test Modules

| ID | Module | Priority | TCs |
|----|--------|----------|-----|
| M-01 | Authentication & RBAC | Critical | 10 |
| M-02 | CSV Upload & Parsing | Critical | 10 |
| M-03 | KPI Calculations | Critical | 8 |
| M-04 | Board Master | High | 6 |
| M-05 | Yield Tab | High | 9 |
| M-06 | S1/S2 Pairing | High | 4 |
| M-07 | Recurring Defects | High | 4 |
| M-08 | Action Plan | High | 4 |
| **Total** | | | **55** |

---

## 7. Severity Levels

| Level | Definition |
|-------|-----------|
| **Critical** | App crash, data loss, security breach |
| **High** | Wrong KPI values, core feature broken |
| **Medium** | Feature works incorrectly but has workaround |
| **Low** | UI/UX cosmetic issue |

---

## 8. Exit Criteria

- All Critical TCs: PASS
- All High TCs: PASS or documented Known Issue
- 0 open Critical/High bugs without workaround
- Postman collection: 100% pass rate
