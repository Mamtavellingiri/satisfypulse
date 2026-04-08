from flask import Flask, request, jsonify, session, send_from_directory, redirect
from flask_cors import CORS
from datetime import timedelta
import psycopg2
import psycopg2.extras
import re
import os

from database import get_db_connection, init_database

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'satisfypulse_secret_key_2024')

is_secure_cookie = (
    os.environ.get('SESSION_COOKIE_SECURE', '').lower() in {'1', 'true', 'yes'}
    or bool(os.environ.get('RENDER_EXTERNAL_URL'))
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None' if is_secure_cookie else 'Lax',
    SESSION_COOKIE_SECURE=is_secure_cookie,
    PERMANENT_SESSION_LIFETIME=timedelta(days=30)
)

allowed_origins = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5000',
    'http://127.0.0.1:5000',
    'https://satisfypulse.vercel.app',
    'https://satisfypulse.onrender.com'
]

frontend_origin = os.environ.get('FRONTEND_ORIGIN')
if frontend_origin and frontend_origin not in allowed_origins:
    allowed_origins.append(frontend_origin)

CORS(app, supports_credentials=True, origins=allowed_origins)

try:
    init_database()
except Exception as e:
    print(f"Error initializing database: {e}")

def get_db():
    return get_db_connection()

def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def fetch_one(cursor, query, params=()):
    cursor.execute(query, params)
    return cursor.fetchone()

def fetch_all(cursor, query, params=()):
    cursor.execute(query, params)
    return cursor.fetchall()

def get_logged_in_student(cursor):
    return fetch_one(
        cursor,
        'SELECT student_id FROM students WHERE user_id = %s',
        (session['user_id'],)
    )

def analyze_sentiment(text):
    if not text or text.strip() == '':
        return 0.0, 'Neutral'
    
    # Simple keyword-based sentiment (no external ML deps needed)
    positive_words = {'good','great','excellent','amazing','wonderful','best','happy','satisfied',
                      'love','fantastic','helpful','clear','perfect','outstanding','brilliant'}
    negative_words = {'bad','poor','worst','terrible','horrible','awful','disappointing','useless',
                      'hate','difficult','confusing','unclear','boring','slow','rude','unhappy'}
    
    words = re.findall(r'\b\w+\b', text.lower())
    score = sum(1 for w in words if w in positive_words) - sum(1 for w in words if w in negative_words)
    
    if score > 0:
        return round(min(score * 0.2, 1.0), 2), 'Positive'
    elif score < 0:
        return round(max(score * 0.2, -1.0), 2), 'Negative'
    else:
        return 0.0, 'Neutral'

def calculate_prediction(ratings):
    if not ratings:
        return 0, 'Low Satisfaction'
    
    avg_rating = sum(ratings) / len(ratings)
    percentage = (avg_rating / 5) * 100
    
    if percentage >= 80:
        label = 'Highly Satisfied'
    elif percentage >= 60:
        label = 'Satisfied'
    elif percentage >= 40:
        label = 'Neutral'
    elif percentage >= 20:
        label = 'Dissatisfied'
    else:
        label = 'Highly Dissatisfied'
    
    return round(percentage, 2), label

# Serve frontend files
@app.route('/')
def serve_index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'student': return redirect('/student.html')
        if role == 'faculty': return redirect('/faculty.html')
        if role == 'admin': return redirect('/admin.html')
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role')
    department = data.get('department')

    if not email or not password or not full_name or not role:
        return jsonify({'error': 'Missing required registration fields'}), 400
    
    if role == 'student':
        # name.deptYY@bitsathy.ac.in
        pattern = r'^[a-z]+\.[a-z]+[0-9]{2}@bitsathy\.ac\.in$'
        if not re.match(pattern, email.lower()):
            return jsonify({'error': 'Invalid student email format. Use: name.deptYY@bitsathy.ac.in (e.g. mamta.se23@bitsathy.ac.in)'}), 400
    elif role == 'faculty':
        # name_faculty@bitsathy.ac.in
        pattern = r'^[a-z]+_faculty@bitsathy\.ac\.in$'
        if not re.match(pattern, email.lower()):
            return jsonify({'error': 'Invalid faculty email format. Use: name_faculty@bitsathy.ac.in'}), 400
    elif role == 'admin':
        if 'admin' not in email.lower():
            return jsonify({'error': 'Admin email must contain "admin"'}), 400
    
    conn = get_db()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute('''
        INSERT INTO users (email, password, full_name, role, department)
        VALUES (%s, %s, %s, %s, %s) RETURNING user_id
        ''', (email, password, full_name, role, department))
        
        user_id = cursor.fetchone()['user_id']
        
        if role == 'student':
            reg_no = f"BIT{full_name[:3].upper()}{user_id}"
            cursor.execute('''
            INSERT INTO students (user_id, reg_no, joining_year, current_year)
            VALUES (%s, %s, %s, %s)
            ''', (user_id, reg_no, 2024, 1))
        
        conn.commit()
        return jsonify({'message': 'Registration successful'}), 201
    
    except psycopg2.IntegrityError as exc:
        conn.rollback()
        if 'email' in str(exc).lower():
            return jsonify({'error': 'Email already exists'}), 400
        return jsonify({'error': 'Registration failed. Please verify the submitted data.'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db()
    cursor = get_cursor(conn)
    
    cursor.execute('''
    SELECT user_id, email, role, full_name, department FROM users 
    WHERE email = %s AND password = %s
    ''', (email, password))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session.permanent = True
        session['user_id'] = user['user_id']
        session['email'] = user['email']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        session['department'] = user['department']
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['user_id'],
                'email': user['email'],
                'role': user['role'],
                'full_name': user['full_name'],
                'department': user['department']
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'id': session['user_id'],
        'email': session['email'],
        'role': session['role'],
        'full_name': session['full_name'],
        'department': session.get('department')
    })

# Feedback Routes
@app.route('/api/feedback/faculty', methods=['POST'])
def submit_faculty_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json(silent=True) or {}
    sentiment_score, sentiment_label = analyze_sentiment(data.get('comments', ''))
    
    conn = get_db()
    cursor = get_cursor(conn)
    
    student = get_logged_in_student(cursor)
    
    if not student:
        conn.close()
        return jsonify({'error': 'Student record not found'}), 400
    
    cursor.execute('''
    INSERT INTO faculty_feedback 
    (student_id, instructor_name, subject, teaching_quality, punctuality, 
     doubt_clearing, overall_rating, comments, sentiment_score, sentiment_label)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (student['student_id'], data.get('instructor_name'), data.get('subject'),
          data.get('teaching_quality'), data.get('punctuality'), data.get('doubt_clearing'),
          data.get('overall_rating'), data.get('comments'), sentiment_score, sentiment_label))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Feedback submitted successfully', 'sentiment': sentiment_label})

@app.route('/api/feedback/hostel', methods=['POST'])
def submit_hostel_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json(silent=True) or {}
    sentiment_score, sentiment_label = analyze_sentiment(data.get('comments', ''))
    
    conn = get_db()
    cursor = get_cursor(conn)
    
    student = get_logged_in_student(cursor)

    if not student:
        conn.close()
        return jsonify({'error': 'Student record not found'}), 400
    
    cursor.execute('''
    INSERT INTO hostel_feedback 
    (student_id, block_name, room_type, cleanliness, water_supply, electricity,
     wifi_quality, warden_behavior, security, maintenance, comments, sentiment_score, sentiment_label)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (student['student_id'], data.get('block_name'), data.get('room_type'),
          data.get('cleanliness'), data.get('water_supply'), data.get('electricity'),
          data.get('wifi_quality'), data.get('warden_behavior'), data.get('security'),
          data.get('maintenance'), data.get('comments'), sentiment_score, sentiment_label))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Hostel feedback submitted successfully', 'sentiment': sentiment_label})

@app.route('/api/feedback/mess', methods=['POST'])
def submit_mess_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json(silent=True) or {}
    sentiment_score, sentiment_label = analyze_sentiment(data.get('suggestions', ''))
    
    conn = get_db()
    cursor = get_cursor(conn)
    
    student = get_logged_in_student(cursor)

    if not student:
        conn.close()
        return jsonify({'error': 'Student record not found'}), 400
    
    cursor.execute('''
    INSERT INTO mess_feedback 
    (student_id, mess_type, food_quality, taste, hygiene, variety, quantity, serving_staff, suggestions, sentiment_score, sentiment_label)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (student['student_id'], data.get('mess_type'), data.get('food_quality'),
          data.get('taste'), data.get('hygiene'), data.get('variety'), data.get('quantity'),
          data.get('serving_staff'), data.get('suggestions'), sentiment_score, sentiment_label))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Mess feedback submitted successfully', 'sentiment': sentiment_label})

@app.route('/api/feedback/infrastructure', methods=['POST'])
def submit_infrastructure_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json(silent=True) or {}
    sentiment_score, sentiment_label = analyze_sentiment(data.get('comments', ''))
    
    conn = get_db()
    cursor = get_cursor(conn)
    
    student = get_logged_in_student(cursor)

    if not student:
        conn.close()
        return jsonify({'error': 'Student record not found'}), 400
    
    cursor.execute('''
    INSERT INTO infrastructure_feedback 
    (student_id, location, cleanliness, seating, lighting, ventilation, equipment, maintenance, comments, sentiment_score, sentiment_label)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (student['student_id'], data.get('location'), data.get('cleanliness'),
          data.get('seating'), data.get('lighting'), data.get('ventilation'),
          data.get('equipment'), data.get('maintenance'), data.get('comments'),
          sentiment_score, sentiment_label))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Infrastructure feedback submitted successfully', 'sentiment': sentiment_label})

@app.route('/api/academic/feedback', methods=['POST'])
def submit_academic_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json(silent=True) or {}
    ratings = [data.get('clarity'), data.get('materials'), data.get('time_management'),
               data.get('syllabus_coverage'), data.get('overall_satisfaction')]
    
    prediction_score, prediction_label = calculate_prediction(ratings)
    
    conn = get_db()
    cursor = get_cursor(conn)
    
    student = get_logged_in_student(cursor)

    if not student:
        conn.close()
        return jsonify({'error': 'Student record not found'}), 400
    
    cursor.execute('''
    INSERT INTO academic_feedback 
    (student_id, student_name, course_code, course_name, faculty_name, clarity, materials,
     time_management, syllabus_coverage, overall_satisfaction, comments, prediction_score, prediction_label)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (student['student_id'], session['full_name'], data.get('course_code'),
          data.get('course_name'), data.get('faculty_name'), data.get('clarity'),
          data.get('materials'), data.get('time_management'), data.get('syllabus_coverage'),
          data.get('overall_satisfaction'), data.get('comments'), prediction_score, prediction_label))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': 'Academic feedback submitted successfully',
        'prediction_score': prediction_score,
        'prediction_label': prediction_label
    })

# Data Retrieval Routes
@app.route('/api/student/my-feedback', methods=['GET'])
def get_student_feedback():
    if 'user_id' not in session or session['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('SELECT student_id FROM students WHERE user_id = %s', (session['user_id'],))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({'error': 'Student record not found'}), 400
    student_id = student['student_id']
    
    cursor.execute('''
    SELECT 'faculty' as type, instructor_name, overall_rating, comments, sentiment_label, submission_date
    FROM faculty_feedback WHERE student_id = %s ORDER BY submission_date DESC LIMIT 10
    ''', (student_id,))
    faculty_fb = cursor.fetchall()
    
    cursor.execute('''
    SELECT 'hostel' as type, block_name, cleanliness, comments, sentiment_label, submission_date
    FROM hostel_feedback WHERE student_id = %s ORDER BY submission_date DESC LIMIT 10
    ''', (student_id,))
    hostel_fb = cursor.fetchall()
    
    cursor.execute('''
    SELECT 'mess' as type, mess_type, food_quality, suggestions, sentiment_label, submission_date
    FROM mess_feedback WHERE student_id = %s ORDER BY submission_date DESC LIMIT 10
    ''', (student_id,))
    mess_fb = cursor.fetchall()
    
    cursor.execute('''
    SELECT 'infrastructure' as type, location, cleanliness, comments, sentiment_label, submission_date
    FROM infrastructure_feedback WHERE student_id = %s ORDER BY submission_date DESC LIMIT 10
    ''', (student_id,))
    infra_fb = cursor.fetchall()
    
    cursor.execute('''
    SELECT 'academic' as type, course_name, overall_satisfaction, prediction_label, submission_date
    FROM academic_feedback WHERE student_id = %s ORDER BY submission_date DESC LIMIT 10
    ''', (student_id,))
    academic_fb = cursor.fetchall()
    
    conn.close()
    
    all_feedback = []
    for fb in faculty_fb: all_feedback.append(dict(fb))
    for fb in hostel_fb: all_feedback.append(dict(fb))
    for fb in mess_fb: all_feedback.append(dict(fb))
    for fb in infra_fb: all_feedback.append(dict(fb))
    for fb in academic_fb: all_feedback.append(dict(fb))
    
    return jsonify(all_feedback)

@app.route('/api/student/stats', methods=['GET'])
def get_student_stats():
    if 'user_id' not in session or session['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('SELECT student_id FROM students WHERE user_id = %s', (session['user_id'],))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({'error': 'Student record not found'}), 400
    student_id = student['student_id']
    
    cursor.execute('''
    SELECT COUNT(*) as count FROM (
        SELECT id FROM faculty_feedback WHERE student_id = %s
        UNION ALL SELECT id FROM hostel_feedback WHERE student_id = %s
        UNION ALL SELECT id FROM mess_feedback WHERE student_id = %s
        UNION ALL SELECT id FROM infrastructure_feedback WHERE student_id = %s
        UNION ALL SELECT id FROM academic_feedback WHERE student_id = %s
    ) AS t
    ''', (student_id, student_id, student_id, student_id, student_id))
    total_fb = cursor.fetchone()['count']
    
    cursor.execute('''
    SELECT AVG(overall_satisfaction) as avg FROM academic_feedback WHERE student_id = %s
    ''', (student_id,))
    avg_rating = cursor.fetchone()['avg'] or 0
    
    conn.close()
    
    return jsonify({
        'total_feedback': total_fb,
        'average_rating': round(float(avg_rating), 1)
    })

@app.route('/api/faculty/my-feedback', methods=['GET'])
def get_faculty_feedback():
    if 'user_id' not in session or session['role'] != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    faculty_name = session['full_name']
    
    # Now fetching from academic_feedback for course-specific evaluation
    # Smart matching: ignores titles like 'Dr.' or 'Prof.' and case-insensitivity
    cursor.execute('''
    SELECT * FROM academic_feedback 
    WHERE REPLACE(REPLACE(LOWER(faculty_name), 'dr. ', ''), 'prof. ', '') = REPLACE(REPLACE(LOWER(%s), 'dr. ', ''), 'prof. ', '')
       OR LOWER(faculty_name) LIKE LOWER('%%' || %s || '%%')
    ORDER BY submission_date DESC
    ''', (faculty_name, faculty_name))
    feedback = cursor.fetchall()
    
    conn.close()
    return jsonify([dict(fb) for fb in feedback])

@app.route('/api/faculty/my-alerts', methods=['GET'])
def get_faculty_alerts():
    if 'user_id' not in session or session['role'] != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    faculty_name = session['full_name']
    
    # Smart matching for alerts as well
    cursor.execute('''
    SELECT * FROM faculty_alerts 
    WHERE REPLACE(REPLACE(LOWER(faculty_name), 'dr. ', ''), 'prof. ', '') = REPLACE(REPLACE(LOWER(%s), 'dr. ', ''), 'prof. ', '')
       OR LOWER(faculty_name) LIKE LOWER('%%' || %s || '%%')
    ORDER BY created_at DESC
    ''', (faculty_name, faculty_name))
    alerts = cursor.fetchall()
    
    conn.close()
    return jsonify([dict(a) for a in alerts])

@app.route('/api/admin/all-feedback', methods=['GET'])
def get_all_feedback():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Transitioned: Faculty evaluation now handled by academic_feedback
    faculty_fb = []
    
    cursor.execute('''
    SELECT 'hostel' as category, u.full_name as student_name, h.block_name,
           h.cleanliness, h.comments, h.sentiment_label, h.submission_date
    FROM hostel_feedback h
    JOIN students s ON h.student_id = s.student_id
    JOIN users u ON s.user_id = u.user_id
    ORDER BY h.submission_date DESC LIMIT 50
    ''')
    hostel_fb = cursor.fetchall()
    
    cursor.execute('''
    SELECT 'academic' as category, a.student_name, a.course_name,
           a.overall_satisfaction, a.prediction_label, a.submission_date
    FROM academic_feedback a
    ORDER BY a.submission_date DESC LIMIT 50
    ''')
    academic_fb = cursor.fetchall()
    
    cursor.execute('''
    SELECT 'mess' as category, u.full_name as student_name, m.mess_type as instructor_name,
           m.food_quality as overall_rating, m.suggestions as comments, m.sentiment_label, m.submission_date
    FROM mess_feedback m
    JOIN students s ON m.student_id = s.student_id
    JOIN users u ON s.user_id = u.user_id
    ORDER BY m.submission_date DESC LIMIT 50
    ''')
    mess_fb = cursor.fetchall()
    
    cursor.execute('''
    SELECT 'infrastructure' as category, u.full_name as student_name, i.location as instructor_name,
           i.cleanliness as overall_rating, i.comments, i.sentiment_label, i.submission_date
    FROM infrastructure_feedback i
    JOIN students s ON i.student_id = s.student_id
    JOIN users u ON s.user_id = u.user_id
    ORDER BY i.submission_date DESC LIMIT 50
    ''')
    infra_fb = cursor.fetchall()
    conn.close()
    
    all_feedback = []
    for fb in faculty_fb: all_feedback.append(dict(fb))
    for fb in hostel_fb: all_feedback.append(dict(fb))
    for fb in academic_fb: all_feedback.append(dict(fb))
    for fb in mess_fb: all_feedback.append(dict(fb))
    for fb in infra_fb: all_feedback.append(dict(fb))
    
    return jsonify(all_feedback)

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('''
    SELECT SUM(count) as total FROM (
        SELECT COUNT(*) as count FROM hostel_feedback
        UNION ALL SELECT COUNT(*) FROM mess_feedback
        UNION ALL SELECT COUNT(*) FROM infrastructure_feedback
        UNION ALL SELECT COUNT(*) FROM academic_feedback
    ) AS t
    ''')
    total_feedback = cursor.fetchone()['total'] or 0
    
    cursor.execute('SELECT AVG(overall_satisfaction) as avg FROM academic_feedback')
    avg_rating = cursor.fetchone()['avg'] or 0
    
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
    student_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM instructors')
    instructor_count = cursor.fetchone()['count']
    
    fac_count = 0 # General faculty feedback removed
    cursor.execute('SELECT COUNT(*) as cnt FROM hostel_feedback')
    hos_count = cursor.fetchone()['cnt']
    cursor.execute('SELECT COUNT(*) as cnt FROM mess_feedback')
    mess_count = cursor.fetchone()['cnt']
    cursor.execute('SELECT COUNT(*) as cnt FROM infrastructure_feedback')
    infra_count = cursor.fetchone()['cnt']
    cursor.execute('SELECT COUNT(*) as cnt FROM academic_feedback')
    acad_count = cursor.fetchone()['cnt']

    distribution = {
        'faculty': fac_count,
        'hostel': hos_count,
        'mess': mess_count,
        'infrastructure': infra_count,
        'academic': acad_count
    }
    
    conn.close()
    
    return jsonify({
        'total_feedback': int(total_feedback),
        'average_rating': round(float(avg_rating), 1),
        'student_count': int(student_count),
        'instructor_count': int(instructor_count),
        'distribution': {k: int(v) for k, v in distribution.items()}
    })

@app.route('/api/instructors', methods=['GET'])
def get_instructors():
    department = request.args.get('department')
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    if department:
        cursor.execute('SELECT * FROM instructors WHERE department = %s', (department,))
    else:
        cursor.execute('SELECT * FROM instructors')
    instructors = cursor.fetchall()
    
    conn.close()
    return jsonify([dict(i) for i in instructors])

@app.route('/api/instructors', methods=['POST'])
def add_instructor():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('''
    INSERT INTO instructors (name, department, subject, email, added_by)
    VALUES (%s, %s, %s, %s, %s)
    ''', (data['name'], data['department'], data.get('subject'), data.get('email'), session['user_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Instructor added successfully'})

@app.route('/api/instructors/<int:instructor_id>', methods=['DELETE'])
def delete_instructor(instructor_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('DELETE FROM instructors WHERE instructor_id = %s', (instructor_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Instructor deleted successfully'})

@app.route('/api/admin/faculty-performance', methods=['GET'])
def get_faculty_performance():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('SELECT AVG(overall_satisfaction) as avg FROM academic_feedback')
    global_avg_row = cursor.fetchone()
    global_avg = float(global_avg_row['avg']) if global_avg_row['avg'] else 0
    
    cursor.execute('''
    SELECT i.name, i.email, i.department, COALESCE(AVG(a.overall_satisfaction), 0) as avg_rating, COUNT(a.id) as feedback_count
    FROM instructors i
    LEFT JOIN academic_feedback a ON i.name = a.faculty_name
    GROUP BY i.name, i.email, i.department
    ORDER BY avg_rating DESC
    ''')
    faculty_perf = cursor.fetchall()
    
    conn.close()
    
    # Cast Decimal objects to float for JSON serialization
    processed_performances = []
    for fp in faculty_perf:
        d = dict(fp)
        d['avg_rating'] = float(d['avg_rating'])
        d['feedback_count'] = int(d['feedback_count'])
        processed_performances.append(d)
        
    return jsonify({
        'global_average': round(float(global_avg), 2),
        'performances': processed_performances
    })

@app.route('/api/admin/send-alert', methods=['POST'])
def send_alert():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    faculty_name = data.get('faculty_name')
    message = data.get('message', 'Your feedback performance is below the institute average. Please review your teaching methods.')
    
    if not faculty_name:
        return jsonify({'error': 'Faculty name required'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO faculty_alerts (faculty_name, message)
    VALUES (%s, %s)
    ''', (faculty_name, message))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Alert sent to faculty member.'})

@app.route('/api/academic/departments', methods=['GET'])
def get_departments():
    return jsonify(['COMPUTER SCIENCE AND ENGINEERING', 'INFORMATION TECHNOLOGY', 
                    'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING',
                    'ELECTRONICS AND COMMUNICATION ENGINEERING', 'MECHANICAL ENGINEERING'])

@app.route('/api/academic/courses', methods=['GET'])
def get_courses():
    department = request.args.get('department')
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    query = "SELECT * FROM courses WHERE 1=1"
    params = []
    
    if department:
        query += " AND department = %s"
        params.append(department)
    
    cursor.execute(query, params)
    courses = cursor.fetchall()
    conn.close()
    
    return jsonify([dict(c) for c in courses])

@app.route('/api/ml/sentiment', methods=['POST'])
def analyze_text_sentiment():
    data = request.json
    text = data.get('text', '')
    score, label = analyze_sentiment(text)
    return jsonify({'score': score, 'label': label})

@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({'message': 'API is working!', 'status': 'active'})

# ============ FIXED: Only ONE main block ============
if __name__ == '__main__':
    from database import init_database
    init_database()
    print("\n" + "="*50)
    print("SatisfyPulse Server Started!")
    print("="*50)
    print("Access the application at: http://localhost:5000")
    print("\nDemo Credentials:")
    print("Admin: admin@bitsathy.ac.in / admin123")
    print("Student: rahul.cs23@bitsathy.ac.in / password123")
    print("Faculty: sasikala_faculty@bitsathy.ac.in / faculty123")
    print("="*50 + "\n")
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
