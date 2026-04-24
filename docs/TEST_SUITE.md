 
# Test Cases — SMT AOI Quality Dashboard
> **Portfolio Project** | QA Manual Engineer | 2026 

**Project:** SMT AOI Quality Dashboard  
**Tester:** QA Manual Engineer  
**Version:** 1.0  
**Date:** April 2026

---

## TC-001 — User Authentication

### TC-001-01: Valid login
**Preconditions:** Application running, default users created  
**Steps:**
1. Navigate to `http://localhost:5000`
2. Enter username: `admin`, password: `admin123`
3. Click Login

**Expected:** Dashboard loads, header shows "Administrator — ADMIN", tabs visible  
**Status:** ✅ PASS

---

### TC-001-02: Invalid credentials
**Steps:**
1. Enter username: `admin`, password: `wrongpassword`
2. Click Login

**Expected:** Error message shown, user stays on login screen  
**Status:** ✅ PASS

---

### TC-001-03: Viewer cannot access Files tab
**Preconditions:** Logged in as `viewer / view123`  
**Steps:**
1. Observe navigation tabs

**Expected:** Files tab not visible, no upload controls accessible  
**Status:** ✅ PASS

---

### TC-001-04: Session persistence after refresh
**Steps:**
1. Login as admin
2. Refresh browser (F5)

**Expected:** User remains logged in, same tab active  
**Status:** ✅ PASS

---

## TC-002 — CSV Upload

### TC-002-01: Successful CSV upload
**Preconditions:** Board Master configured with correct board keys  
**Steps:**
1. Navigate to Files tab
2. Drag-and-drop valid `Report_xxxxxxxx.csv`
3. Click "Анализирай"

**Expected:** Dashboard populates with KPI data, session chip appears  
**Status:** ✅ PASS

---

### TC-002-02: CSV with missing board keys
**Steps:**
1. Upload CSV containing board keys not in Board Master

**Expected:** Warning shown listing missing keys, keys auto-added with `subboards=0`, upload blocked until subboards filled  
**Status:** ✅ PASS

---

### TC-002-03: CSV with missing required columns
**Steps:**
1. Upload CSV file missing `OperatorJudgement` column

**Expected:** Error message: "Липсват колони: OperatorJudgement"  
**Status:** ✅ PASS

---

### TC-002-04: Upload with non-UTF8 encoding
**Steps:**
1. Upload CSV with Latin-1 encoding (Cyrillic characters)

**Expected:** File parsed correctly, no encoding errors  
**Status:** ✅ PASS

---

## TC-003 — KPI Calculations

### TC-003-01: PPY calculation
**Preconditions:** Known dataset loaded (20 panels × 8 subboards = 160 total, 3 NG subboards)  
**Expected PPY:** `(160 - 3) / 160 × 100 = 98.125%`  
**Actual:** 98.13% ✅  
**Status:** ✅ PASS — verified against SAKI AOI machine output

---

### TC-003-02: FPY calculation
**Preconditions:** Same dataset, 3 NG + 5 FalseCall subboards  
**Expected FPY:** `(160 - 3 - 5) / 160 × 100 = 95.0%`  
**Status:** ✅ PASS

---

### TC-003-03: TOP 10 NG components — unique PCB counting
**Scenario:** Component Q2 has Bridge + Shift + ComponentNG on the same board  
**Expected:** Q2 counts as **1 NG board**, not 3  
**Verification:** Compared with SAKI AOI TOP 10 report — 100% match  
**Status:** ✅ PASS

---

### TC-003-04: TOP 10 percentage base
**Expected:** Percentage shows `NG boards for this reference / Total NG boards × 100`  
**Not:** Percentage of TOP 10 sum only  
**Status:** ✅ PASS (fixed from initial implementation)

---

### TC-003-05: S1∪S2 union logic for double-sided PCBs
**Scenario:** Lot with 155 panels in S1, 159 panels in S2  
**Expected total:** 159 panels (union, not sum of 314)  
**Expected scrap:** NG from either side / 159  
**Status:** ✅ PASS

---

## TC-004 — Board Master

### TC-004-01: Add new board key
**Steps:**
1. Navigate to Users → Board Master
2. Click "+ Добави"
3. Enter Board Key: `10012144846`, Project: `Audi_MAIN`, Subboards: `38`
4. Click Save

**Expected:** Record appears in table immediately  
**Status:** ✅ PASS

---

### TC-004-02: Duplicate board key rejected
**Steps:**
1. Attempt to add board key that already exists

**Expected:** Error: "BoardKey '...' вече съществува"  
**Status:** ✅ PASS

---

### TC-004-03: Pair configuration for double-sided boards
**Steps:**
1. Set `pair = 12144846` on both `10012144846` (S1) and `20012144846` (S2)
2. Navigate to Yield tab

**Expected:** Both boards show under single row with "S1∪S2" badge  
**Status:** ✅ PASS

---

### TC-004-04: DB migration — no data loss on schema update
**Scenario:** Existing database without `pair` and `has_ict` columns  
**Steps:** Replace `app.py` with new version, restart Flask

**Expected:** New columns added automatically via migration, existing data preserved  
**Status:** ✅ PASS

---

## TC-005 — Yield Tab

### TC-005-01: ICT NG entry saved to DB
**Preconditions:** Board has `has_ict = true`  
**Steps:**
1. Click ✏️ on a Yield row
2. Enter ICT NG value: `5`
3. Click 💾

**Expected:** Value saved, Total NG and Scrap% recalculate immediately without page refresh  
**Status:** ✅ PASS

---

### TC-005-02: Viewer cannot edit ICT NG
**Preconditions:** Logged in as Viewer  
**Steps:**
1. Navigate to Yield tab

**Expected:** No ✏️ edit buttons visible, ICT fields are read-only display  
**Status:** ✅ PASS

---

### TC-005-03: Delete lot (Admin only)
**Steps:**
1. Login as Admin
2. Click 🗑️ on a Yield row
3. Confirm deletion

**Expected:** Row removed, data deleted from `aoi_raw`, `aoi_lots` and `ict_data`  
**Status:** ✅ PASS

---

### TC-005-04: Date filter
**Steps:**
1. Set "От" date to filter range
2. Observe table

**Expected:** Only rows with `date_str` within range shown, Pie chart updates  
**Status:** ✅ PASS

---

### TC-005-05: Sortable columns
**Steps:**
1. Click "Scrap %" column header

**Expected:** Rows sorted descending (▼), click again → ascending (▲)  
**Status:** ✅ PASS

---

## TC-006 — Pairing Check

### TC-006-01: Perfect pairing
**Scenario:** S1 and S2 have identical barcodes  
**Steps:**
1. Click 🔗 Провери on a paired row

**Expected:** Alert shows "✅ Паринг OK — всички панели съвпадат!"  
**Status:** ✅ PASS

---

### TC-006-02: Missing panels in S2
**Scenario:** 4 barcodes exist in S1 but not in S2  
**Expected:** Alert lists missing barcodes: "⚠️ Само в S1 (4 бр): 00001, 00002..."  
**Status:** ✅ PASS

---

## TC-007 — Recurring Defects

### TC-007-01: Grouping by variant
**Scenario:** R1/Bridge appears in Audi_MAIN and Stabilus  
**Expected:** Two separate Recurring entries — one per variant  
**Not:** One combined entry  
**Status:** ✅ PASS (fixed from initial implementation)

---

### TC-007-02: Sorted by total NG
**Expected:** Entry with 500 total NG ranks above entry with 5 NG (even if second has more lots)  
**Status:** ✅ PASS

---

## TC-008 — Action Plan

### TC-008-01: Editor can create actions
**Preconditions:** Logged in as Editor  
**Steps:**
1. Navigate to Екшън план
2. Click "+ Нов Екшън"
3. Fill required fields, save

**Expected:** Action created and visible  
**Status:** ✅ PASS

---

### TC-008-02: Viewer cannot create/edit actions
**Expected:** No "+ Нов Екшън" button visible, no edit/delete controls  
**Status:** ✅ PASS

---

### TC-008-03: Action created from TOP 10 pre-fills fields
**Steps:**
1. In AOI Report, click "+ Екшън" on TOP 10 row
2. Observe modal

**Expected:** Reference, DefectType, Variant and Lots pre-filled from the row data  
**Status:** ✅ PASS

---

## TC-009 — Charts and Visualizations

### TC-009-01: Pareto drilldown
**Steps:**
1. Click on a bar in the Pareto chart in AOI Report

**Expected:** Drill-down panel shows TOP 10 for selected lot/variant  
**Status:** ✅ PASS

---

### TC-009-02: Trend chart — mode switching
**Steps:**
1. In Projects tab, click "Дни", "Седмици", "Месеци" buttons

**Expected:** Chart X-axis aggregates accordingly  
**Precondition:** date_str populated (requires re-upload after schema update)  
**Status:** ✅ PASS (requires date data)

---

### TC-009-03: PPY/FPY gauge visual management
**Scenario A:** PPY = 98.91% (below 99.5% target)  
**Expected:** Gauge shows red, "⚠ Под норма"

**Scenario B:** PPY = 99.7% (above target)  
**Expected:** Gauge shows green, "✓ В норма"  
**Status:** ✅ PASS

---

## Known Limitations

| # | Description | Workaround |
|---|-------------|------------|
| L-001 | Trend by day/week/month requires re-uploading CSV after initial setup (date_str migration) | Re-upload CSV files |
| L-002 | Pairing check uses in-memory data — only works for currently loaded sessions | Ensure relevant CSV is loaded |
| L-003 | No export functionality (deferred) | Use browser print or screenshot |
| L-004 | TEST_BARCODE type data must be filtered before CSV export from SAKI | Filter in SAKI before export |
