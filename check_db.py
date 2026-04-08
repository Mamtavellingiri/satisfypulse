import psycopg2

URL='postgresql://satisfypulse_db_user:cY46Rqtg44BuS3Kc0iRHhvHZMQcuZ1aV@dpg-d7acejogjchc73bah490-a.singapore-postgres.render.com/satisfypulse_db'

try:
    conn = psycopg2.connect(URL)
    cursor = conn.cursor()
    cursor.execute("SELECT email, password FROM users;")
    rows = cursor.fetchall()
    print("USERS IN DATABASE:")
    for row in rows:
        print(row)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
