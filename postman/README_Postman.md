
# Postman API Tests — SMT AOI Dashboard
> **Portfolio Project** | QA Manual Engineer | 2026  

## Setup

1. Open Postman
2. Import `SMT_AOI_Collection.json` — File → Import
3. Import `SMT_AOI_Environment.json` — File → Import → Environment
4. Select **"SMT AOI Dashboard - Local"** environment (top right dropdown)
5. Start Flask app: `python app.py`

## Test Execution Order

Run requests in this order — some tests depend on previous responses:

```
1. Login - Admin (Valid)          ← sets session cookie
2. Create Board Master Entry      ← sets {{test_board_id}}
3. Update Board Master Entry      ← uses {{test_board_id}}
4. Delete Board Master Entry      ← uses {{test_board_id}}
5. Create Action                  ← sets {{test_action_id}}
6. Update Action Status           ← uses {{test_action_id}}
7. Delete Action                  ← uses {{test_action_id}}
8. Create New User                ← sets {{test_user_id}}
9. Update User Role               ← uses {{test_user_id}}
10. Delete Test User              ← uses {{test_user_id}}
```

## RBAC Negative Tests

For tests marked **"Login as viewer/editor first"**:

1. Run `Login - Viewer (Valid)` or `Login - Editor (Valid)`
2. Then run the negative test
3. Re-run `Login - Admin (Valid)` to restore admin session

## Collection Summary

| Folder | Requests | Positive | Negative |
|--------|----------|----------|----------|
| 01 - Authentication | 8 | 5 | 3 |
| 02 - Board Master | 6 | 4 | 2 |
| 03 - Sessions | 2 | 1 | 1 |
| 04 - Data & KPI | 3 | 2 | 1 |
| 05 - ICT Data | 3 | 2 | 1 |
| 06 - Action Plan | 6 | 4 | 2 |
| 07 - Users | 6 | 4 | 2 |
| **Total** | **34** | **22** | **12** |

## What Each Test Checks

**Authentication:**
- Valid login returns correct role and username
- Invalid credentials return 401
- Empty fields return 400
- Unauthenticated requests return 401

**Board Master:**
- CRUD operations return correct status codes
- Duplicate board key returns 409
- Missing required fields return 400
- Unauthorized roles return 403

**KPI Data:**
- PPY, FPY, Scrap all between 0-100
- Response structure matches expected schema
- Response time under 2000ms

**Users:**
- Password hash never exposed in responses
- Duplicate username returns 409
- Viewer cannot access user management (403)
