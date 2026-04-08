import psycopg2
import json
URL='postgresql://satisfypulse_db_user:cY46Rqtg44BuS3Kc0iRHhvHZMQcuZ1aV@dpg-d7acejogjchc73bah490-a.singapore-postgres.render.com/satisfypulse_db'
conn = psycopg2.connect(URL)
cursor = conn.cursor()
cursor.execute("SELECT email, password, full_name, department FROM users WHERE email='mamta.se23@bitsathy.ac.in';")
user = cursor.fetchone()
print("Found User:", bool(user))
if user:
    print("User Details:", user)
conn.close()
