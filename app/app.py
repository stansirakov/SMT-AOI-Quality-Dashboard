"""
SMT AOI Quality Dashboard — Flask + SQLite + RBAC
CSV upload + Board Master table
"""
from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3, os, datetime, secrets, io, csv, re

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SMT_SECRET', secrets.token_hex(32))
app.permanent_session_lifetime = datetime.timedelta(days=7)
DB = os.path.join(os.path.dirname(__file__), 'smt_aoi.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role          TEXT NOT NULL DEFAULT 'viewer',
            full_name     TEXT DEFAULT '',
            active        INTEGER DEFAULT 1,
            created_at    TEXT DEFAULT (datetime('now')),
            last_login    TEXT
        );
        CREATE TABLE IF NOT EXISTS action_plan (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            status         TEXT DEFAULT 'R',
            problem        TEXT NOT NULL,
            action         TEXT, variant TEXT, reference TEXT,
            defect_type    TEXT, lots TEXT, owner TEXT, target_date TEXT,
            progress       INTEGER DEFAULT 0, completed_date TEXT,
            occurrences    INTEGER DEFAULT 1, notes TEXT,
            created_by     TEXT, updated_by TEXT,
            created_at     TEXT DEFAULT (datetime('now')),
            updated_at     TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS aoi_sessions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT, lot TEXT, date_range TEXT, record_count INTEGER,
            uploaded_by  TEXT,
            created_at   TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS aoi_raw (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES aoi_sessions(id) ON DELETE CASCADE,
            _key TEXT UNIQUE,
            aoi_datetime TEXT, lot_clean TEXT, barcode TEXT,
            sub_board_id INTEGER, reference TEXT, ng_type TEXT,
            operator_judgement TEXT, board_name TEXT, board_key TEXT,
            group_name TEXT, lot_raw TEXT, link_id TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS aoi_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES aoi_sessions(id) ON DELETE CASCADE,
            lot TEXT, board_name TEXT, board_key TEXT, group_name TEXT,
            date_str TEXT DEFAULT '',
            unique_panels INTEGER DEFAULT 0,
            subboards_per_panel INTEGER DEFAULT 0,
            subboards_total INTEGER DEFAULT 0,
            ng_ppy INTEGER DEFAULT 0,
            ng_fpy INTEGER DEFAULT 0,
            ppy_pct REAL DEFAULT 0,
            fpy_pct REAL DEFAULT 0,
            scrap_pct REAL DEFAULT 0,
            UNIQUE(lot, board_key)
        );
        CREATE TABLE IF NOT EXISTS board_master (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            board_key   TEXT NOT NULL UNIQUE,
            project     TEXT NOT NULL,
            subboards   INTEGER NOT NULL,
            pair        TEXT DEFAULT '',
            has_ict     INTEGER DEFAULT 0,
            has_depaneling INTEGER DEFAULT 0,
            notes       TEXT DEFAULT '',
            created_by  TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        );
        -- Добавяме колоните ако липсват (migration)
        CREATE TABLE IF NOT EXISTS ict_data (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lot         TEXT NOT NULL,
            board_key   TEXT NOT NULL,
            ict_ng      INTEGER DEFAULT 0,
            depaneling_ng INTEGER DEFAULT 0,
            notes       TEXT DEFAULT '',
            updated_by  TEXT,
            updated_at  TEXT DEFAULT (datetime('now')),
            UNIQUE(lot, board_key)
        );
        CREATE INDEX IF NOT EXISTS idx_raw_lot    ON aoi_raw(lot_clean);
        CREATE INDEX IF NOT EXISTS idx_raw_ref    ON aoi_raw(reference);
        CREATE INDEX IF NOT EXISTS idx_raw_judge  ON aoi_raw(operator_judgement);
        CREATE INDEX IF NOT EXISTS idx_raw_bkey   ON aoi_raw(board_key);
        """)
        # ── Migration — добавяме нови колони без да трием DB ──────
        migrations = [
            "ALTER TABLE aoi_lots ADD COLUMN date_str TEXT DEFAULT ''",
            "ALTER TABLE aoi_raw ADD COLUMN link_id TEXT DEFAULT ''",
            "ALTER TABLE board_master ADD COLUMN pair TEXT DEFAULT ''",
            "ALTER TABLE board_master ADD COLUMN has_ict INTEGER DEFAULT 0",
            "ALTER TABLE board_master ADD COLUMN has_depaneling INTEGER DEFAULT 0",
            "ALTER TABLE ict_data ADD COLUMN depaneling_ng INTEGER DEFAULT 0",
        ]
        for sql in migrations:
            try:
                db.execute(sql)
                db.commit()
            except Exception:
                pass  # Колоната вече съществува — пропускаме

        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            for u, p, r, fn in [
                ('admin',   'admin123', 'admin',  'Administrator'),
                ('smt_eng', 'smt123',   'editor', 'SMT Engineer'),
                ('viewer',  'view123',  'viewer', 'Read Only'),
            ]:
                db.execute("INSERT INTO users (username,password_hash,role,full_name) VALUES (?,?,?,?)",
                           (u, generate_password_hash(p), r, fn))
            db.commit()
            print("  admin/admin123  smt_eng/smt123  viewer/view123")

# ── Helpers ──────────────────────────────────────────────────
def board_key_from_name(board_name):
    """10012144846-05_Mother → 10012144846"""
    m = re.match(r'(\d+)', str(board_name).strip())
    return m.group(1) if m else str(board_name).strip()

def normalize_judgement(v):
    v = str(v or '').strip()
    if re.match(r'^(ng|componentng|component_ng)$', v, re.I): return 'Ng'
    if re.match(r'^falsecall$', v, re.I): return 'FalseCall'
    if not v or re.match(r'^(nan|none|null)$', v, re.I): return 'Ok'
    return v

def parse_lot(lot_raw):
    """'20260323 A04419' → ('A04419', '20260323')"""
    parts = str(lot_raw or '').strip().split()
    if len(parts) >= 2:
        return parts[1], parts[0]
    return str(lot_raw).strip(), ''

# ── Decorators ───────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if 'user_id' not in session:
            return jsonify({'error': 'not_authenticated'}), 401
        return f(*a, **kw)
    return dec

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def dec(*a, **kw):
            if 'user_id' not in session:
                return jsonify({'error': 'not_authenticated'}), 401
            if session.get('role') not in roles:
                return jsonify({'error': 'forbidden'}), 403
            return f(*a, **kw)
        return dec
    return decorator

# ── AUTH ─────────────────────────────────────────────────────
@app.route('/api/auth/login', methods=['POST'])
def login():
    d = request.json or {}
    username = d.get('username', '').strip()
    password = d.get('password', '')
    if not username or not password:
        return jsonify({'error': 'Въведи потребителско име и парола'}), 400
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE username=? AND active=1", (username,)).fetchone()
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Грешно потребителско име или парола'}), 401
    session.permanent = True
    session['user_id']   = user['id']
    session['username']  = user['username']
    session['role']      = user['role']
    session['full_name'] = user['full_name'] or user['username']
    with get_db() as db:
        db.execute("UPDATE users SET last_login=? WHERE id=?",
                   (datetime.datetime.utcnow().isoformat(), user['id']))
        db.commit()
    return jsonify({'username': user['username'], 'role': user['role'], 'full_name': user['full_name']})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/auth/me')
def me():
    if 'user_id' not in session:
        return jsonify({'authenticated': False})
    return jsonify({'authenticated': True, 'username': session['username'],
                    'role': session['role'], 'full_name': session['full_name']})

@app.route('/api/auth/change-password', methods=['POST'])
@login_required
def change_password():
    d = request.json or {}
    if not d.get('old_password') or not d.get('new_password'):
        return jsonify({'error': 'Попълни старата и новата парола'}), 400
    if len(d['new_password']) < 4:
        return jsonify({'error': 'Минимум 4 символа'}), 400
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
        if not check_password_hash(user['password_hash'], d['old_password']):
            return jsonify({'error': 'Грешна стара парола'}), 401
        db.execute("UPDATE users SET password_hash=? WHERE id=?",
                   (generate_password_hash(d['new_password']), session['user_id']))
        db.commit()
    return jsonify({'ok': True})

# ── BOARD MASTER ─────────────────────────────────────────────
@app.route('/api/board-master')
@login_required
def get_board_master():
    with get_db() as db:
        rows = db.execute("SELECT * FROM board_master ORDER BY project, board_key").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/board-master', methods=['POST'])
@role_required('admin')
def create_board_master():
    d = request.json or {}
    if not d.get('board_key') or not d.get('project') or not d.get('subboards'):
        return jsonify({'error': 'Нужни са board_key, project и subboards'}), 400
    try:
        with get_db() as db:
            db.execute("""INSERT INTO board_master (board_key, project, subboards, pair, has_ict, has_depaneling, notes, created_by)
                          VALUES (?,?,?,?,?,?,?,?)""",
                       (d['board_key'].strip(), d['project'].strip(),
                        int(d['subboards']), d.get('pair','').strip(),
                        1 if d.get('has_ict') else 0,
                        1 if d.get('has_depaneling') else 0,
                        d.get('notes', ''), session['username']))
            db.commit()
            row = db.execute("SELECT * FROM board_master WHERE board_key=?", (d['board_key'].strip(),)).fetchone()
        return jsonify(dict(row)), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': f"BoardKey '{d['board_key']}' вече съществува"}), 409

@app.route('/api/board-master/<int:mid>', methods=['PUT'])
@role_required('admin')
def update_board_master(mid):
    d = request.json or {}
    now = datetime.datetime.utcnow().isoformat()
    with get_db() as db:
        sets, vals = [], []
        for col in ['project', 'subboards', 'notes', 'pair']:
            if col in d:
                sets.append(f'{col}=?')
                vals.append(int(d[col]) if col == 'subboards' else d[col])
        if 'has_ict' in d:
            sets.append('has_ict=?')
            vals.append(1 if d['has_ict'] else 0)
        if 'has_depaneling' in d:
            sets.append('has_depaneling=?')
            vals.append(1 if d['has_depaneling'] else 0)
        if not sets:
            return jsonify({'error': 'Няма какво да се обнови'}), 400
        sets.append('updated_at=?'); vals.append(now); vals.append(mid)
        db.execute(f"UPDATE board_master SET {','.join(sets)} WHERE id=?", vals)
        db.commit()
        row = db.execute("SELECT * FROM board_master WHERE id=?", (mid,)).fetchone()
    return jsonify(dict(row))

@app.route('/api/board-master/<int:mid>', methods=['DELETE'])
@role_required('admin')
def delete_board_master(mid):
    with get_db() as db:
        db.execute("DELETE FROM board_master WHERE id=?", (mid,))
        db.commit()
    return jsonify({'ok': True})

# ── CSV UPLOAD ────────────────────────────────────────────────
REQUIRED_COLS = {'GroupName','BoardName','Lot','Barcode','Reference',
                 'AoiJudgement','NgType','AoiDateTime','OperatorJudgement','SubBoardId'}

@app.route('/api/upload', methods=['POST'])
@role_required('admin', 'editor')
def upload_csv():
    if 'report' not in request.files:
        return jsonify({'error': 'Липсва CSV файл (report)'}), 400

    file = request.files['report']
    try:
        text = file.read().decode('utf-8-sig')  # utf-8-sig handles BOM
    except UnicodeDecodeError:
        text = file.read().decode('latin-1')

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return jsonify({'error': 'Празен файл'}), 400

    # Проверка за нужните колони
    cols = set(rows[0].keys())
    missing = REQUIRED_COLS - cols
    if missing:
        return jsonify({'error': f'Липсват колони: {", ".join(missing)}'}), 400

    # Четем board_master от DB
    with get_db() as db:
        master_rows = db.execute("SELECT board_key, project, subboards FROM board_master").fetchall()
    master = {r['board_key']: {'project': r['project'], 'subboards': r['subboards']} for r in master_rows}

    now = datetime.datetime.utcnow().isoformat()
    raw_records = []
    unknown_keys = set()

    for i, r in enumerate(rows):
        board_name = str(r.get('BoardName', '')).strip()
        bkey       = board_key_from_name(board_name)
        lot_raw    = str(r.get('Lot', '')).strip()
        lot_clean, date_str = parse_lot(lot_raw)
        barcode    = str(r.get('Barcode', '')).strip()
        sub_id     = int(float(r.get('SubBoardId', 0) or 0))
        reference  = str(r.get('Reference', '')).strip()
        ng_type    = str(r.get('NgType', '')).strip()
        link_id    = str(r.get('LinkID', '')).strip()
        aoi_dt     = str(r.get('AoiDateTime', '')).strip().replace('/', '-').replace(' ', 'T')
        op_judge   = normalize_judgement(r.get('OperatorJudgement', ''))
        group_name = str(r.get('GroupName', '')).strip()

        if bkey not in master:
            unknown_keys.add(bkey)

        key = f"{barcode}_{sub_id}_{reference}_{ng_type}_{i}"
        raw_records.append((key, aoi_dt, lot_clean, barcode, sub_id,
                            reference, ng_type, op_judge, board_name,
                            bkey, group_name, lot_raw, link_id))

    # Ако има непознати board_keys - добавяме ги автоматично с subboards=0
    if unknown_keys:
        # Намираме проекта за всеки непознат ключ от CSV данните
        key_to_project = {}
        for r in rows:
            bkey = board_key_from_name(str(r.get('BoardName','')))
            if bkey in unknown_keys:
                key_to_project[bkey] = str(r.get('GroupName','')).strip()

        with get_db() as db:
            for bkey in unknown_keys:
                proj = key_to_project.get(bkey, '')
                try:
                    db.execute("""INSERT OR IGNORE INTO board_master
                        (board_key, project, subboards, notes, created_by)
                        VALUES (?,?,0,?,?)""",
                        (bkey, proj, 'Автоматично добавен - попълни субборди!', session['username']))
                except Exception:
                    pass
            db.commit()

        return jsonify({
            'error': 'missing_subboards',
            'unknown_keys': sorted(unknown_keys),
            'message': f'Добавени са {len(unknown_keys)} нови Board Keys. Попълни броя субборди в Admin → Board Master и качи отново.'
        }), 422

    # Изчисляваме KPI по lot+board_key
    # Групираме записите
    from collections import defaultdict
    lot_board = defaultdict(lambda: {
        'barcodes': set(), 'ng_subs': set(), 'fc_subs': set(),
        'board_name': '', 'group_name': '', 'bkey': '', 'date_str': ''
    })

    for rec in raw_records:
        key, aoi_dt, lot_clean, barcode, sub_id, reference, ng_type, op_judge, board_name, bkey, group_name, lot_raw, link_id = rec
        k = (lot_clean, bkey)
        lot_board[k]['barcodes'].add(barcode)
        lot_board[k]['board_name'] = board_name
        lot_board[k]['group_name'] = group_name
        lot_board[k]['bkey'] = bkey
        # Взимаме най-ранната дата за лота
        if aoi_dt and (not lot_board[k]['date_str'] or aoi_dt < lot_board[k]['date_str']):
            # Нормализираме до YYYYMMDD
            try:
                ds = aoi_dt.replace('-','').replace('T',' ').replace('/','')[:8]
                lot_board[k]['date_str'] = ds
            except:
                pass
        if op_judge == 'Ng':
            lot_board[k]['ng_subs'].add(f"{barcode}_{sub_id}")
        elif op_judge == 'FalseCall':
            lot_board[k]['fc_subs'].add(f"{barcode}_{sub_id}")

    # Записваме в DB
    lots_list = list({rec[2] for rec in raw_records})  # уникални лотове
    label = file.filename

    with get_db() as db:
        # Намираме date range от данните
        dates = sorted([r[1] for r in raw_records if r[1]])
        date_range = ''
        if dates:
            d_from = dates[0][:10]
            d_to   = dates[-1][:10]
            date_range = f"{d_from} → {d_to}" if d_from != d_to else d_from

        cur = db.execute(
            "INSERT INTO aoi_sessions (label,lot,date_range,record_count,uploaded_by,created_at) VALUES (?,?,?,?,?,?)",
            (label, ','.join(lots_list), date_range, len(raw_records), session['username'], now))
        sid = cur.lastrowid

        # Raw записи
        db.executemany("""INSERT OR REPLACE INTO aoi_raw
            (session_id,_key,aoi_datetime,lot_clean,barcode,sub_board_id,
             reference,ng_type,operator_judgement,board_name,board_key,group_name,lot_raw,link_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [(sid,)+r for r in raw_records])

        # Lots с KPI
        lots_records = []
        kpis_out = []
        for (lot_clean, bkey), d in lot_board.items():
            m = master[bkey]
            unique_panels   = len(d['barcodes'])
            subs_per_panel  = m['subboards']
            total           = unique_panels * subs_per_panel
            ng_count        = len(d['ng_subs'])
            fc_count        = len(d['fc_subs'])
            ppy = round((total - ng_count) / total * 100, 2) if total else 0
            fpy = round((total - ng_count - fc_count) / total * 100, 2) if total else 0
            scrap = round(ng_count / total * 100, 3) if total else 0

            lots_records.append((sid, lot_clean, d['board_name'], bkey, d['group_name'],
                                  d.get('date_str',''),
                                  unique_panels, subs_per_panel, total,
                                  ng_count, ng_count + fc_count, ppy, fpy, scrap))
            kpis_out.append({
                'lot_id':    lot_clean,
                'board_key': bkey,
                'project':   m['project'],
                'total':     total,
                'ng':        ng_count,
                'fc':        fc_count,
                'ppy_pct':   ppy,
                'fpy_pct':   fpy,
                'scrap_pct': scrap,
            })

        db.executemany("""INSERT OR REPLACE INTO aoi_lots
            (session_id,lot,board_name,board_key,group_name,date_str,
             unique_panels,subboards_per_panel,subboards_total,
             ng_ppy,ng_fpy,ppy_pct,fpy_pct,scrap_pct)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", lots_records)

        db.commit()

    return jsonify({'ok': True, 'kpis': kpis_out, 'records': len(raw_records)}), 201

# ── DATA ──────────────────────────────────────────────────────
@app.route('/api/data')
@login_required
def get_all_data():
    with get_db() as db:
        raw  = db.execute("SELECT * FROM aoi_raw ORDER BY aoi_datetime").fetchall()
        lots = db.execute("SELECT * FROM aoi_lots ORDER BY lot,board_key").fetchall()
        sess = db.execute("SELECT * FROM aoi_sessions ORDER BY created_at").fetchall()

    def to_raw(r):
        return {
            '_key': r['_key'], 'AoiDateTime': r['aoi_datetime'],
            'Lot_Clean': r['lot_clean'], 'Barcode': r['barcode'],
            'SubBoardId': r['sub_board_id'], 'Reference': r['reference'],
            'NgType': r['ng_type'], 'OperatorJudgement': r['operator_judgement'],
            'BoardName': r['board_name'], 'BoardKey': r['board_key'], 'LinkID': r['link_id'] if 'link_id' in r.keys() else '',
            'GroupName': r['group_name'], 'Variant': r['board_key'],
        }

    def to_lot(l):
        return {
            'lot': l['lot'], 'board_name': l['board_name'],
            'board_key': l['board_key'], 'group_name': l['group_name'],
            'variant': l['board_key'],
            'unique_panels': l['unique_panels'],
            'subboards_per_panel': l['subboards_per_panel'],
            'subboards_total': l['subboards_total'],
            'ng_ppy': l['ng_ppy'], 'ng_fpy': l['ng_fpy'],
            'ppy_pct': l['ppy_pct'], 'fpy_pct': l['fpy_pct'],
            'scrap_pct': l['scrap_pct'],
            # Compatibility с текущия frontend
            'subboards_ng_op': l['ng_ppy'],
            'subboards_ng_aoi': l['ng_fpy'],
            'ppy_sub': f"{l['ppy_pct']} PPY [%]",
            'fpy_sub': f"{l['fpy_pct']} FPY [%]",
            'ppy_pct': l['ppy_pct'], 'fpy_pct': l['fpy_pct'],
            'dateStr': l['date_str'] or '',
        }

    return jsonify({
        'raw':      [to_raw(r) for r in raw],
        'lots':     [to_lot(l) for l in lots],
        'sessions': [dict(s) for s in sess],
    })

@app.route('/api/kpi')
@login_required
def get_kpi():
    with get_db() as db:
        lots = db.execute("""
            SELECT l.*, m.project
            FROM aoi_lots l
            LEFT JOIN board_master m ON l.board_key = m.board_key
            ORDER BY l.lot, l.board_key
        """).fetchall()

    if not lots:
        return jsonify({'kpis': [], 'defects': [], 'pareto_type': [], 'pareto_ref': [], 'pareto_project': []})

    # Групираме по project+lot
    from collections import defaultdict as dd
    proj_map = dd(lambda: {'ng': 0, 'total': 0, 'lots': set()})
    kpis = []
    for l in lots:
        proj = l['project'] or '—'
        proj_map[proj]['ng']    += l['ng_ppy']
        proj_map[proj]['total'] += l['subboards_total']
        proj_map[proj]['lots'].add(l['lot'])
        kpis.append({
            'project':   proj,
            'product':   l['board_key'],
            'lot_id':    l['lot'],
            'sub_total': l['subboards_total'],
            'ng_union':  l['ng_ppy'],
            'scrap_pct': l['scrap_pct'],
            'ppy_pct':   l['ppy_pct'],
            'fpy_pct':   l['fpy_pct'],
        })

    # Pareto по проект
    pareto_project = sorted([
        {'project': p, 'ng': v['ng'], 'total': v['total'],
         'scrap_pct': round(v['ng']/v['total']*100, 3) if v['total'] else 0,
         'lots': len(v['lots'])}
        for p, v in proj_map.items()
    ], key=lambda x: -x['scrap_pct'])

    # Дефекти от raw
    with get_db() as db:
        def_rows = db.execute("""
            SELECT reference, ng_type, group_name as project, board_key as product, lot_clean as lot_id,
                   COUNT(DISTINCT barcode||'_'||sub_board_id) as affected_subboards
            FROM aoi_raw
            WHERE operator_judgement='Ng'
            GROUP BY reference, ng_type, board_key, lot_clean
            ORDER BY affected_subboards DESC
        """).fetchall()

    pt = dd(int); pr = dd(int)
    for d in def_rows:
        pt[d['ng_type']]   += d['affected_subboards']
        pr[d['reference']] += d['affected_subboards']

    total_t = sum(pt.values()) or 1
    cum = 0; pareto_type = []
    for tp, cnt in sorted(pt.items(), key=lambda x: -x[1]):
        cum += cnt
        pareto_type.append({'ng_type': tp, 'count': cnt,
            'pct': round(cnt/total_t*100, 1), 'cum_pct': round(cum/total_t*100, 1)})

    total_r = sum(pr.values()) or 1
    cum2 = 0; pareto_ref = []
    for ref, cnt in sorted(pr.items(), key=lambda x: -x[1])[:15]:
        cum2 += cnt
        pareto_ref.append({'reference': ref, 'count': cnt,
            'pct': round(cnt/total_r*100, 1), 'cum_pct': round(cum2/total_r*100, 1)})

    return jsonify({'kpis': kpis, 'defects': [dict(r) for r in def_rows[:50]],
                    'pareto_type': pareto_type, 'pareto_ref': pareto_ref,
                    'pareto_project': pareto_project})

# ── SESSIONS ──────────────────────────────────────────────────
@app.route('/api/sessions')
@login_required
def get_sessions():
    with get_db() as db:
        rows = db.execute("SELECT * FROM aoi_sessions ORDER BY created_at DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/sessions/<int:sid>', methods=['DELETE'])
@role_required('admin')
def delete_session(sid):
    with get_db() as db:
        db.execute("DELETE FROM aoi_raw  WHERE session_id=?", (sid,))
        db.execute("DELETE FROM aoi_lots WHERE session_id=?", (sid,))
        db.execute("DELETE FROM aoi_sessions WHERE id=?", (sid,))
        db.commit()
    return jsonify({'ok': True})

# ── ACTIONS ───────────────────────────────────────────────────
@app.route('/api/actions')
@login_required
def get_actions():
    with get_db() as db:
        rows = db.execute("""SELECT * FROM action_plan
            ORDER BY CASE status WHEN 'R' THEN 0 WHEN 'Y' THEN 1 ELSE 2 END, updated_at DESC""").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/actions', methods=['POST'])
@role_required('admin', 'editor')
def create_action():
    d = request.json; now = datetime.datetime.utcnow().isoformat()
    with get_db() as db:
        cur = db.execute("""INSERT INTO action_plan
            (status,problem,action,variant,reference,defect_type,lots,owner,
             target_date,progress,completed_date,occurrences,notes,created_by,updated_by,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (d.get('status','R'), d['problem'], d.get('action',''), d.get('variant',''),
             d.get('reference',''), d.get('defect_type',''), d.get('lots',''), d.get('owner',''),
             d.get('target_date',''), d.get('progress',0), d.get('completed_date',''),
             d.get('occurrences',1), d.get('notes',''),
             session['username'], session['username'], now, now))
        db.commit()
        row = db.execute("SELECT * FROM action_plan WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route('/api/actions/<int:aid>', methods=['PUT'])
@role_required('admin', 'editor')
def update_action(aid):
    d = request.json; now = datetime.datetime.utcnow().isoformat()
    with get_db() as db:
        db.execute("""UPDATE action_plan SET
            status=?,problem=?,action=?,variant=?,reference=?,defect_type=?,
            lots=?,owner=?,target_date=?,progress=?,completed_date=?,
            occurrences=?,notes=?,updated_by=?,updated_at=? WHERE id=?""",
            (d.get('status','R'), d['problem'], d.get('action',''), d.get('variant',''),
             d.get('reference',''), d.get('defect_type',''), d.get('lots',''), d.get('owner',''),
             d.get('target_date',''), d.get('progress',0), d.get('completed_date',''),
             d.get('occurrences',1), d.get('notes',''), session['username'], now, aid))
        db.commit()
        row = db.execute("SELECT * FROM action_plan WHERE id=?", (aid,)).fetchone()
    return jsonify(dict(row))

@app.route('/api/actions/<int:aid>', methods=['DELETE'])
@role_required('admin')
def delete_action(aid):
    with get_db() as db:
        db.execute("DELETE FROM action_plan WHERE id=?", (aid,))
        db.commit()
    return jsonify({'ok': True})

# ── USERS ─────────────────────────────────────────────────────
@app.route('/api/users')
@role_required('admin')
def get_users():
    with get_db() as db:
        rows = db.execute("SELECT id,username,role,full_name,active,created_at,last_login FROM users ORDER BY role,username").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/users', methods=['POST'])
@role_required('admin')
def create_user():
    d = request.json or {}
    if not d.get('username') or not d.get('password'):
        return jsonify({'error': 'Нужни са потребителско име и парола'}), 400
    try:
        with get_db() as db:
            db.execute("INSERT INTO users (username,password_hash,role,full_name) VALUES (?,?,?,?)",
                       (d['username'], generate_password_hash(d['password']),
                        d.get('role', 'viewer'), d.get('full_name', '')))
            db.commit()
            row = db.execute("SELECT id,username,role,full_name,active,created_at FROM users WHERE username=?",
                             (d['username'],)).fetchone()
        return jsonify(dict(row)), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': f"Потребителят '{d['username']}' вече съществува"}), 409

@app.route('/api/users/<int:uid>', methods=['PUT'])
@role_required('admin')
def update_user(uid):
    d = request.json or {}
    with get_db() as db:
        sets, vals = [], []
        for col, key in [('role','role'),('full_name','full_name'),('active','active')]:
            if key in d: sets.append(f'{col}=?'); vals.append(d[key])
        if d.get('password'):
            sets.append('password_hash=?'); vals.append(generate_password_hash(d['password']))
        if sets:
            vals.append(uid)
            db.execute(f"UPDATE users SET {','.join(sets)} WHERE id=?", vals)
            db.commit()
        row = db.execute("SELECT id,username,role,full_name,active,created_at,last_login FROM users WHERE id=?", (uid,)).fetchone()
    return jsonify(dict(row))

@app.route('/api/users/<int:uid>', methods=['DELETE'])
@role_required('admin')
def delete_user(uid):
    if uid == session.get('user_id'):
        return jsonify({'error': 'Не може да изтриеш собствения си акаунт'}), 400
    with get_db() as db:
        db.execute("DELETE FROM users WHERE id=?", (uid,))
        db.commit()
    return jsonify({'ok': True})

# ── ICT DATA ─────────────────────────────────────────────────
@app.route('/api/ict')
@login_required
def get_ict():
    with get_db() as db:
        rows = db.execute("SELECT * FROM ict_data ORDER BY lot, board_key").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/ict', methods=['POST'])
@role_required('admin', 'editor')
def save_ict():
    d = request.json or {}
    if not d.get('lot') or not d.get('board_key'):
        return jsonify({'error': 'Нужни са lot и board_key'}), 400
    now = datetime.datetime.utcnow().isoformat()
    with get_db() as db:
        db.execute("""INSERT INTO ict_data (lot, board_key, ict_ng, depaneling_ng, notes, updated_by, updated_at)
                      VALUES (?,?,?,?,?,?,?)
                      ON CONFLICT(lot, board_key) DO UPDATE SET
                      ict_ng=excluded.ict_ng, depaneling_ng=excluded.depaneling_ng,
                      notes=excluded.notes,
                      updated_by=excluded.updated_by, updated_at=excluded.updated_at""",
                   (d['lot'], d['board_key'], int(d.get('ict_ng', 0)),
                    int(d.get('depaneling_ng', 0)),
                    d.get('notes', ''), session['username'], now))
        db.commit()
    return jsonify({'ok': True})

# ── PAIRING CHECK ─────────────────────────────────────────────
@app.route('/api/pairing-check', methods=['POST'])
@login_required
def pairing_check():
    """Проверява паринг S1/S2 от CSV данни без да записва"""
    if 'report' not in request.files:
        return jsonify({'error': 'Липсва CSV'}), 400
    try:
        text = request.files['report'].read().decode('utf-8-sig')
    except UnicodeDecodeError:
        text = request.files['report'].read().decode('latin-1')

    import csv as csv_mod
    reader = csv_mod.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return jsonify({'error': 'Празен файл'}), 400

    # Вземаме pair дефинициите от board_master
    with get_db() as db:
        master = db.execute("SELECT board_key, pair, project FROM board_master WHERE pair != '' AND pair IS NOT NULL").fetchall()
    
    # Групираме по pair
    pairs = {}
    for m in master:
        if m['pair']:
            if m['pair'] not in pairs:
                pairs[m['pair']] = []
            pairs[m['pair']].append(m['board_key'])

    # За всеки ред намираме board_key и barcode
    lot_board_barcodes = {}
    for r in rows:
        bkey = board_key_from_name(str(r.get('BoardName', '')))
        lot_clean, _ = parse_lot(str(r.get('Lot', '')))
        barcode = str(r.get('Barcode', '')).strip()
        k = (lot_clean, bkey)
        if k not in lot_board_barcodes:
            lot_board_barcodes[k] = set()
        lot_board_barcodes[k].add(barcode)

    # Проверяваме паринга
    results = []
    checked_pairs = set()
    for pair_key, pair_boards in pairs.items():
        if len(pair_boards) < 2:
            continue
        # Намираме лотовете в CSV за тези бордове
        lots = set()
        for (lot, bkey) in lot_board_barcodes:
            if bkey in pair_boards:
                lots.add(lot)
        
        for lot in lots:
            pk = (lot, pair_key)
            if pk in checked_pairs:
                continue
            checked_pairs.add(pk)
            
            board_sets = {}
            for bkey in pair_boards:
                barcodes = lot_board_barcodes.get((lot, bkey), set())
                if barcodes:
                    board_sets[bkey] = barcodes

            if len(board_sets) < 2:
                continue

            keys = list(board_sets.keys())
            s1_set = board_sets[keys[0]]
            s2_set = board_sets[keys[1]]
            only_s1 = s1_set - s2_set
            only_s2 = s2_set - s1_set
            common = s1_set & s2_set

            results.append({
                'lot': lot,
                'pair': pair_key,
                's1_key': keys[0],
                's2_key': keys[1],
                's1_count': len(s1_set),
                's2_count': len(s2_set),
                'common': len(common),
                'only_s1': sorted(list(only_s1))[:20],
                'only_s1_count': len(only_s1),
                'only_s2': sorted(list(only_s2))[:20],
                'only_s2_count': len(only_s2),
                'ok': len(only_s1) == 0 and len(only_s2) == 0
            })

    return jsonify({'results': results, 'has_pairs': len(pairs) > 0})

# ── DELETE LOT ───────────────────────────────────────────────
@app.route('/api/delete-lot', methods=['POST'])
@role_required('admin')
def delete_lot():
    d = request.json or {}
    lot = d.get('lot','').strip()
    board_key = d.get('board_key','').strip()
    if not lot or not board_key:
        return jsonify({'error': 'Нужни са lot и board_key'}), 400
    with get_db() as db:
        db.execute("DELETE FROM aoi_raw WHERE lot_clean=? AND board_key=?", (lot, board_key))
        db.execute("DELETE FROM aoi_lots WHERE lot=? AND board_key=?", (lot, board_key))
        db.execute("DELETE FROM ict_data WHERE lot=? AND board_key=?", (lot, board_key))
        # Почистваме сесии без записи
        db.execute("""DELETE FROM aoi_sessions WHERE id NOT IN
            (SELECT DISTINCT session_id FROM aoi_raw WHERE session_id IS NOT NULL)""")
        db.commit()
    return jsonify({'ok': True})

# ── SERVE ─────────────────────────────────────────────────────
@app.route('/')
def index(): return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    init_db()
    print("\n" + "="*52)
    print("  SMT AOI Dashboard  |  http://localhost:5000")
    print("="*52 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
