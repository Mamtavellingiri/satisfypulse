import psycopg2
conn = psycopg2.connect('postgresql://satisfypulse_db_user:cY46Rqtg44BuS3Kc0iRHhvHZMQcuZ1aV@dpg-d7acejogjchc73bah490-a.singapore-postgres.render.com/satisfypulse_db')
cur = conn.cursor()
cur.execute("SELECT * FROM academic_feedback")
rows=cur.fetchall()
print(f'Found {len(rows)} academic feedbacks. First row: {rows[0] if rows else ""}')
