import psycopg2
import psycopg2.extras

DATABASE_URL = 'postgresql://satisfypulse_db_user:cY46Rqtg44BuS3Kc0iRHhvHZMQcuZ1aV@dpg-d7acejogjchc73bah490-a.singapore-postgres.render.com/satisfypulse_db'

def diagnose():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check Instructors
        cursor.execute("SELECT COUNT(*) as count FROM instructors")
        inst_count = cursor.fetchone()['count']
        print(f"Total Instructors: {inst_count}")
        
        # Check Faculty Feedback
        cursor.execute("SELECT COUNT(*) as count FROM faculty_feedback")
        fb_count = cursor.fetchone()['count']
        print(f"Total Faculty Feedback: {fb_count}")
        
        # Sample Instructors
        cursor.execute("SELECT * FROM instructors LIMIT 5")
        insts = cursor.fetchall()
        print("\nSample Instructors:")
        for i in insts:
            print(f"- {i['name']} ({i['department']})")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    diagnose()
