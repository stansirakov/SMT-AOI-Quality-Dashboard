# SMT-AOI Quality Dashboard
> **Portfolio Project** | QA Manual Engineer | 2026  
> Quality Analysis project for SMT (Surface Mount Technology) production lines

---

##  Project at a Glance

- 55 manual test cases designed and executed
- 34 API tests (Postman collection)
- 11 real bugs documented with root cause analysis
- Full QA lifecycle: Test Plan → Test Cases → Execution → Bug Reporting → RTM
- Industrial domain: SMT / AOI production quality systems

---

##  Business Problem

Most SMT production environments rely on spreadsheets for quality tracking. This leads to:

- manual calculation errors
- missing traceability
- incorrect KPI reporting (FPY, PPY, Scrap Rate)
- delayed defect detection

This project replaces that workflow with a structured, testable QA system that ensures **data integrity and production reliability**.

---

##  Project Purpose

This system simulates a real SMT production environment and processes AOI (Automated Optical Inspection) data.

It handles:

- AOI defect ingestion (CSV-based)
- KPI calculations (FPY, PPY, Scrap Rate)
- S1/S2 dual-side PCB logic (union handling)
- Cross-stage consistency (AOI → ICT → Depaneling)
- Role-based access control (RBAC)
- Production quality reporting dashboards

---

##  My QA Role

As QA Engineer, I was responsible for:

- Validating data integrity from AOI CSV exports
- Verifying KPI calculations against expected outputs
- Testing edge cases in S1∪S2 defect aggregation logic
- Ensuring consistency across multiple production stages
- Performing API testing (CRUD, RBAC, validation, error handling)
- Designing full traceability from Use Cases → Test Cases → Bugs

---

##  QA Impact

- Identified critical KPI calculation issues affecting production reporting accuracy
- Detected S1/S2 duplication logic defects impacting yield calculations
- Found RBAC security vulnerability allowing unauthorized data deletion
- Ensured consistency between multiple dashboard modules using shared calculation logic
- Validated end-to-end data flow integrity across AOI → KPI pipeline

---

##  Testing Approach

| Technique | Application |
|-----------|-------------|
| Equivalence Partitioning | Defect classification (S1, S2, False Call) |
| Boundary Value Analysis | KPI thresholds (0%, 100%, limits) |
| Negative Testing | API validation, missing fields, invalid roles |
| Data Integrity Testing | CSV ingestion from AOI exports |
| Cross-module Testing | AOI ↔ Yield ↔ Projects consistency |
| Exploratory Testing | UI filters, dashboard interactions |

---

##  System Workflow

```
AOI Machine CSV Export
        ↓
Defect Aggregation (S1 ∪ S2 logic)
        ↓
KPI Calculation
   ├── FPY (First Pass Yield)
   ├── PPY (Production Part Yield)
   └── Scrap Rate
        ↓
Pareto Analysis (Top defects)
        ↓
Dashboard + API Layer
```

---

##  Bug Summary

- 11 bugs identified
- 10 fixed, 1 documented as known limitation

### Examples:

- KPI calculation mismatch (wrong denominator)
- S1/S2 duplication logic error
- Infinite render loop in Yield module
- RBAC vulnerability (unauthorized DELETE access)
- CSV parsing failure due to backend unpack mismatch

Full details: `docs/BUG_REPORTS.md`

---

## 📁 Documentation

| File | Description |
|------|-------------|
| `TEST_PLAN.md` | QA strategy, scope, risks |
| `USE_CASES.md` | 15 system use cases |
| `TEST_SUITE.md` | 55 structured test cases |
| `BUG_REPORTS.md` | 11 bugs with RCA |
| `TRACEABILITY_MATRIX.md` | Full UC → TC → Bug mapping |

---

## 🔌 API Testing (Postman)

- 34 structured API requests
- CRUD operations for all modules
- RBAC validation (Admin / Editor / Viewer)
- Negative testing (401 / 403 / 400 / 500 cases)
- Data validation & schema checks

---

## ▶️ Run Locally

```bash
cd app
pip install flask
python app.py
```

Open:

```
http://localhost:5000
```

Import Postman collection:

```
postman/SMT_AOI_Collection.json
```

---

## 🛠 Tech Stack

Python · Flask · Postman · REST API · HTML/CSS/JS · SMT/AOI Domain Logic

---

## 💡 What This Project Demonstrates

- QA mindset focused on system correctness, not just UI testing
- Ability to design structured QA documentation (Test Plan,TC, RTM, Bug Reports)
- Understanding of industrial production data flows (SMT / AOI systems)
- Strong API testing and validation skills
- Data integrity and KPI validation experience

---

## 📌 Note

This project was built to simulate a real industrial QA environment where incorrect data or KPI calculations can directly impact production decisions and yield quality.

My focus was not development — but **breaking, validating, and ensuring correctness of the system under real-world conditions**.
