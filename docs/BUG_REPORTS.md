> **Portfolio Project** | QA Manual Engineer | 2026  
# Bug Reports — SMT AOI Quality Dashboard

**Project:** SMT AOI Quality Dashboard  
**Reporter:** QA Manual Engineer  
**Period:** April 2026

---

## BUG-001 — TOP 10 NG: Incorrect percentage base

**Severity:** High  
**Component:** AOI Report → TOP 10 NG Components  
**Status:** ✅ Fixed

**Description:**  
TOP 10 component percentages were calculated as a share of the TOP 10 sum, not of total NG boards. A component could show 100% if it was the only entry in TOP 10, even with just 1 NG.

**Steps to Reproduce:**
1. Load CSV with multiple NG components
2. Observe % next to #1 entry in TOP 10

**Expected:** `25 NG boards / 58 total NG boards = 43%`  
**Actual:** `25 / (sum of TOP 10 only) = inflated %`

**Root Cause:** `totalEvents` was computed from TOP 10 slice, not from full NG set  
**Fix:** Changed denominator to `totalNgPCBs` = all unique NG Barcode+SubBoardId

---

## BUG-002 — TOP 10 NG: Sorting by events instead of unique PCBs

**Severity:** Medium  
**Component:** AOI Report → TOP 10 NG Components  
**Status:** ✅ Fixed

**Description:**  
One component with 3 NgTypes on 1 board ranked higher than a component with 1 NgType on 5 boards, because sorting used event count (rows) not unique board count.

**Expected:** Sort by unique `Barcode+SubBoardId` with OperatorJudgement=Ng  
**Actual:** Sort by total row count  

**Fix:** Added `pcbs: new Set()` per reference, sorted by `pcbs.size`

---

## BUG-003 — Recurring defects: Cross-variant grouping

**Severity:** High  
**Component:** Recurring Tab  
**Status:** ✅ Fixed

**Description:**  
`R1/Bridge` appearing in Audi_MAIN and Stabilus was treated as one recurring defect spanning both projects, showing an inflated lot count. This produced 510 "recurring" entries — most meaningless.

**Steps to Reproduce:**
1. Load CSV data with multiple projects
2. Navigate to Recurring tab
3. Observe entries combining different variants

**Expected:** Recurring grouped per `Reference + NgType + Variant`  
**Actual:** Grouped by `Reference + NgType` only

**Fix:** Changed grouping key from `${ref}||${type}` to `${ref}||${type}||${variant}`  
**Impact:** Reduced from ~510 to meaningful TOP 20 per-variant entries

---

## BUG-004 — Yield tab: Infinite render loop

**Severity:** Critical  
**Component:** Yield Tab  
**Status:** ✅ Fixed

**Description:**  
Opening the Yield tab caused the browser to freeze. Console showed `renderYield` being called hundreds of times per second.

**Root Cause (chain):**
1. `renderYield()` calls `buildYieldLotFilter(rows)`
2. `buildYieldLotFilter` recreates DOM checkbox elements
3. DOM change triggers `applyLang()` (MutationObserver)
4. `applyLang()` detects active tab = Yield → calls `renderYield()`
5. Loop repeats indefinitely

**Fix:** Added early-return in `buildYieldLotFilter` if lot options haven't changed:
```js
const existing = [...drop.querySelectorAll('input:not(#yLotAll)')].map(i=>i.value);
if(JSON.stringify(existing.sort()) === JSON.stringify([...lots].sort())) return;
```

---

## BUG-005 — Yield KPI strip: null innerHTML crash

**Severity:** High  
**Component:** Yield Tab  
**Status:** ✅ Fixed

**Description:**  
Opening Yield tab threw `TypeError: Cannot set properties of null (setting 'innerHTML')` and the tab failed to render.

**Root Cause:** `yieldKpiStrip` element was removed from HTML but `renderYield()` still tried to write to it.

**Fix:** Removed the stale `document.getElementById('yieldKpiStrip').innerHTML = ...` call

---

## BUG-006 — barcodes_set serialized as empty object

**Severity:** High  
**Component:** Yield Tab — S1∪S2 calculation  
**Status:** ✅ Fixed

**Description:**  
S1 and S2 panel counts showed 0 in Yield table. Console showed `barcodes_set: {}` in lot data objects.

**Root Cause:** JavaScript `Set` objects are serialized as `{}` in JSON. The code was attaching `barcodes_set` to `ALL_LOTS_DATA` entries, then those entries were reused on re-render — but the Sets were empty objects after serialization/deserialization.

**Fix:** Removed `barcodes_set` from `ALL_LOTS_DATA`. Now computed locally in `calcYieldRows()` as `barcodesByBoard[bkey] = new Set(...)` each render.

---

## BUG-007 — CSV upload 500 error: too many values to unpack

**Severity:** Critical  
**Component:** Backend — CSV Upload  
**Status:** ✅ Fixed

**Description:**  
Uploading any CSV after adding LinkID support caused a 500 Internal Server Error. Browser console showed `SyntaxError: Unexpected token '<'` (Flask error page returned instead of JSON).

**Terminal Error:**
```
ValueError: too many values to unpack (expected 12)
```

**Root Cause:** `link_id` was added to `raw_records` tuple (now 13 values) but the unpacking line still expected 12:
```python
key, aoi_dt, ..., lot_raw = rec  # expected 12, got 13
```

**Fix:** Updated unpack to include `link_id`:
```python
key, aoi_dt, lot_clean, barcode, sub_id, reference, ng_type, op_judge, board_name, bkey, group_name, lot_raw, link_id = rec
```

---

## BUG-008 — Scrap Rate shown incorrectly (avg vs real)

**Severity:** High  
**Component:** Projects Tab, Yield Pie Chart  
**Status:** ✅ Fixed (with clarification)

**Description:**  
After changing to "average arithmetic" scrap rate, Projects tab showed Stabilus at `1.08%` but subtitle showed `690 NG / 638,040` which equals `0.11%`. The two numbers were contradictory and confusing.

**Root Cause:** `scrap` field used arithmetic average of per-lot rates, but `ng` and `total` were summed across all lots — different formulas for the same metric.

**Decision:** Reverted to real scrap = `total_ng / total_boards × 100` for consistency everywhere.

**Note:** This was a design decision bug, not a coding error.

---

## BUG-009 — Projects trend: data from wrong source

**Severity:** Medium  
**Component:** Projects Tab — Trend Chart  
**Status:** ✅ Fixed

**Description:**  
Projects tab showed different scrap values in the KPI cards versus the trend chart for the same project and lot.

**Root Cause:** KPI cards used `calcYieldRows()` (S1∪S2 union), but trend chart used `LAST_KPI.kpis` (per-side data from API). Two different calculation paths for the same metric.

**Fix:** Updated `projLotMap` in Projects trend to also use `calcYieldRows()`, ensuring both views use identical data.

---

## BUG-010 — date_str empty for existing records after migration

**Severity:** Low  
**Component:** Yield Tab, Trend Charts  
**Status:** ⚠️ By Design

**Description:**  
After adding `date_str` column via migration, existing lot records show `—` for date. Trend by day/week/month cannot work for these records.

**Root Cause:** SQLite `ALTER TABLE ADD COLUMN` sets default value for new column, but existing rows have no date data — it was never stored previously.

**Workaround:** Re-upload CSV files. New uploads correctly populate `date_str` from `AoiDateTime`.  
**Lesson Learned:** Schema changes affecting existing data require data migration scripts, not just column additions.

---

## BUG-011 — Gauge: value arc color does not reflect target status

**Severity:** Low (UX)  
**Component:** AOI Report — PPY/FPY Gauges  
**Status:** ✅ Fixed

**Description:**  
Initial gauge implementation used a single color (red or green) for the entire arc. This did not give clear visual context of where the value sits relative to 0-100 range.

**Fix:** Redesigned gauge with 36 gradient segments (red→yellow→green), inactive segments at 15% opacity. Needle added to point to exact position. Target shown as a blue tick mark.

---

## Summary

| ID | Severity | Component | Status |
|----|----------|-----------|--------|
| BUG-001 | High | TOP 10 percentage | ✅ Fixed |
| BUG-002 | Medium | TOP 10 sorting | ✅ Fixed |
| BUG-003 | High | Recurring grouping | ✅ Fixed |
| BUG-004 | Critical | Yield infinite loop | ✅ Fixed |
| BUG-005 | High | Yield null crash | ✅ Fixed |
| BUG-006 | High | S1∪S2 barcodes_set | ✅ Fixed |
| BUG-007 | Critical | CSV upload 500 error | ✅ Fixed |
| BUG-008 | High | Scrap rate formula | ✅ Fixed |
| BUG-009 | Medium | Projects trend source | ✅ Fixed |
| BUG-010 | Low | date_str migration | ⚠️ By Design |
| BUG-011 | Low | Gauge UX | ✅ Fixed |

**Total: 11 bugs found and documented | 10 fixed | 1 by design**
