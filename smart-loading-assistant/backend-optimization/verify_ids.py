import sqlite3

conn = sqlite3.connect('smart_loading.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute('SELECT id, human_readable_id, status, left_weight_kg, right_weight_kg FROM loading_plans')
plans = [dict(r) for r in c.fetchall()]
for p in plans:
    total = (p['left_weight_kg'] or 0) + (p['right_weight_kg'] or 0)
    print(p['human_readable_id'], '|', p['status'], '|', round(total), 'kg')
conn.close()
