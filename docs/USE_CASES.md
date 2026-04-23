# Use Cases — SMT AOI Quality Dashboard

| Field | Value |
|-------|-------|
| **Document ID** | UC-001 |
| **Version** | 1.0 |
| **Date** | April 2026 |

---

## Actors

| Actor | Description |
|-------|-------------|
| **Admin** | Full access — users, Board Master, uploads, deletes |
| **Editor** | Upload CSV, ICT/Depaneling input, actions |
| **Viewer** | Read-only all dashboards |
| **System** | Flask backend, SQLite, SAKI CSV |

---

## UC-01 — User Login
**Actor:** All | **Goal:** Access dashboard

**Main Flow:** User enters credentials → System validates → Session created → Dashboard opens

**Alternatives:**
- Wrong password → 401 "Грешно потребителско име или парола"
- Empty fields → 400 "Въведи потребителско име и парола"

---

## UC-02 — Upload AOI CSV
**Actor:** Admin, Editor | **Goal:** Load production data

**Main Flow:** Select CSV → Validate columns → Check Board Master → Parse records → Calculate KPIs → Save to DB

**Alternatives:**
- Unknown board keys → Auto-added with `subboards=0` → Warning shown → Re-upload required
- Missing column → Error: "Липсват колони: [column]"

---

## UC-03 — Configure Board Master
**Actor:** Admin | **Goal:** Define PCB configuration

**Key fields:** Board Key, Project, Subboards/panel, Pair (S1∪S2), ICT flag, Depaneling flag

**Business Rule:** Board Key = leading digits from BoardName (e.g. `10012144846-05_Mother` → `10012144846`)

---

## UC-04 — View AOI Report KPIs
**Actor:** All | **Goal:** Monitor PPY% and FPY%

**Display:** Semi-circle gradient gauges (red→yellow→green), needle at current value, blue target marker

**Thresholds:** PPY ≥ 99.5% = green | FPY ≥ 95% = green

---

## UC-05 — Analyze TOP 10 NG Components
**Actor:** All | **Goal:** Identify most problematic components

**Metric:** Unique NG boards per Reference / Total NG boards × 100

**Action:** Click "+ Екшън" → pre-fills Action Plan modal

---

## UC-06 — View Real Yield (Physical PCB)
**Actor:** All | **Goal:** See actual scrap per physical board

**Formula:**
```
Total = UNION(S1 panels, S2 panels) × subboards/panel
Scrap% = (AOI NG + ICT NG + Dep NG) / Total × 100
```

**Features:** Filters (Project/Variant/Lot/Date), sortable columns, Pie chart

---

## UC-07 — Enter ICT / Depaneling NG
**Actor:** Admin, Editor | **Goal:** Complete real scrap calculation

**Flow:** Click ✏️ → Enter values → Click 💾 → Row recalculates immediately

---

## UC-08 — Check S1/S2 Pairing
**Actor:** All | **Goal:** Verify all panels inspected on both sides

**Results:**
- ✅ All panels matched
- ⚠️ X panels only in S1 — waiting for S2
- ⚠️ X panels only in S2 — data anomaly

---

## UC-09 — Delete a Lot
**Actor:** Admin only | **Goal:** Remove incorrect/test data

**Flow:** Click 🗑️ → Confirm → Deletes from `aoi_raw`, `aoi_lots`, `ict_data` → Auto-clean orphaned sessions

---

## UC-10 — Analyze Recurring Defects
**Actor:** All | **Goal:** Identify systematic defects

**Grouping:** `Reference + NgType + Variant` (per product line)
**Sort:** By total NG count descending
**Limit:** TOP 20

---

## UC-11 — Create Action Plan
**Actor:** Admin, Editor | **Goal:** Document corrective action

**Status lifecycle:** R (Open) → Y (In Progress) → G (Closed)

**Pre-fill sources:** TOP 10, Yield tab, Recurring tab

---

## UC-12 — Manage Users
**Actor:** Admin | **Goal:** Create/edit team accounts

**Roles:** Admin | Editor | Viewer

---

## UC-13 — Filter by Project
**Actor:** All | **Goal:** Compare quality across product lines

**Note:** Projects tab uses same `calcYieldRows()` as Yield — consistent numbers

---

## UC-14 — View Trend Analysis
**Actor:** All | **Goal:** Monitor scrap over time

**Modes:** По лот / Дни / Седмици / Месеци

**Prerequisite:** CSV uploaded after `date_str` migration

---

## UC-15 — Change Password
**Actor:** All | **Goal:** Update own password

**Validation:** Old password required, minimum 4 characters
