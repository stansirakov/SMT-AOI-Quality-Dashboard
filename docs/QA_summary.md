> **Portfolio Project** | QA Manual Engineer | 2026 
# QA Summary — SMT AOI Quality Dashboard

## Purpose
This document explains how quality metrics and domain-specific logic are applied in the system.

The project simulates SMT (Surface Mount Technology) AOI production data validation, focusing on defect accuracy, KPI correctness, and cross-stage consistency.

---

## Key Quality Metrics

### PPY (Process Performance Yield)
PPY% = (Total subboards - NG subboards) / Total subboards × 100

---

### FPY (First Pass Yield)
FPY% = (Total subboards - NG - FalseCall) / Total subboards × 100

---

### Real Scrap Rate (Physical PCB Level)

Total panels = UNION(S1, S2) × subboards per panel

Real Scrap% = (AOI NG + ICT NG + Depaneling NG) / Total × 100

---

## S1 ∪ S2 Logic
Double-sided PCBs require UNION logic to avoid double counting.

---

## Data Integrity Rules
- Only OperatorJudgement = NG used for KPIs
- Machine-only results excluded
- Unique identifier: Barcode + SubBoardId
