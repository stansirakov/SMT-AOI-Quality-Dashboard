> **Portfolio Project** | QA Manual Engineer | 2026 
# System Architecture — SMT AOI Quality Dashboard

## Overview
QA Project for SMT AOI production data validation.

---

## Flow
CSV → Parsing → Validation → Aggregation (S1∪S2) → KPI Calculation → SQLite → API → UI

---

## Design Principles
- Data integrity first
- Deterministic KPI calculation
- Minimal stack (Flask + Vanilla JS)

---

## Core Engine
S1 ∪ S2 aggregation ensures no double counting of double-sided PCBs.

---

## Role
This is a QA validation system, not just a dashboard.
