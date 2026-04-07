from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from textblob import TextBlob
import sqlite3
import re
import os
from datetime import datetime

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = 'satisfypulse_secret_key_2024'

# Initialize database so it is created on Render
from database import init_database
try:
    init_database()
except Exception as e:
    print(f"Error initializing database: {e}")

CORS(app, supports_credentials=True, origins=[
    'http://localhost:5000',
    'http://127.0.0.1:5000',
    'https://satisfypulse.vercel.app',
    'https://satisfypulse.onrender.com'
])

def get_db():
    conn = sqlite3.connect('satisfypulse.db')
    conn.row_factory = sqlite3.Row
    return conn

def analyze_sentiment(text):
    if not text or text.strip() == '':
        return 0.0, 'Neutral'
    
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity
    
    if sentiment_score > 0.2:
        label = 'Positive'
    elif sentiment_score < -0.2:
        label = 'Negative'
    else:
        label = 'Neutral'
    
    return round(sentiment_score, 2), label

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
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role')
    department = data.get('department')
    
    if role == 'student':
        pattern = r'^[a-zA-Z]+\.[a-zA-Z]+(?:[0-9]{2})?@bitsathy\.ac\.in$'
        if not re.match(pattern, email):
            return jsonify({'error': 'Invalid student email format. Use: name.departmentYY@bitsathy.ac.in'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO users (email, password, full_name, role, department)
        VALUES (?, ?, ?, ?, ?)
        ''', (email, password, full_name, role, department))
        
        user_id = cursor.lastrowid
        
        if role == 'student':
            reg_no = f"BIT{full_name[:3].upper()}{user_id}"
            cursor.execute('''
            INSERT INTO students (user_id, reg_no, joining_year, current_year)
            VALUES (?, ?, ?, ?)
            ''', (user_id, reg_no, 2024, 1))
        
        conn.commit()
        return jsonify({'message': 'Registration successful'}), 201
    
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT user_id, email, role, full_name, department FROM users 
    WHERE email = ? AND password = ?
    ''', (email, password))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
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
    
    data = request.json
    sentiment_score, sentiment_label = analyze_sentiment(data.get('comments', ''))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (session['user_id'],))
    student = cursor.fetchone()
    
    if not student:
        return jsonify({'error': 'Student record not found'}), 400
    
    cursor.execute('''
    INSERT INTO faculty_feedback 
    (student_id, instructor_name, subject, teaching_quality, punctuality, 
     doubt_clearing, overall_rating, comments, sentiment_score, sentiment_label)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    
    data = request.json
    sentiment_score, sentiment_label = analyze_sentiment(data.get('comments', ''))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (session['user_id'],))
    student = cursor.fetchone()
    
    cursor.execute('''
    INSERT INTO hostel_feedback 
    (student_id, block_name, room_type, cleanliness, water_supply, electricity,
     wifi_quality, warden_behavior, security, maintenance, comments, sentiment_score, sentiment_label)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    
    data = request.json
    sentiment_score, sentiment_label = analyze_sentiment(data.get('suggestions', ''))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (session['user_id'],))
    student = cursor.fetchone()
    
    cursor.execute('''
    INSERT INTO mess_feedback 
    (student_id, mess_type, food_quality, taste, hygiene, variety, quantity, serving_staff, suggestions, sentiment_score, sentiment_label)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    
    data = request.json
    sentiment_score, sentiment_label = analyze_sentiment(data.get('comments', ''))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (session['user_id'],))
    student = cursor.fetchone()
    
    cursor.execute('''
    INSERT INTO infrastructure_feedback 
    (student_id, location, cleanliness, seating, lighting, ventilation, equipment, maintenance, comments, sentiment_score, sentiment_label)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    
    data = request.json
    ratings = [data.get('clarity'), data.get('materials'), data.get('time_management'),
               data.get('syllabus_coverage'), data.get('overall_satisfaction')]
    
    prediction_score, prediction_label = calculate_prediction(ratings)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (session['user_id'],))
    student = cursor.fetchone()
    
    cursor.execute('''
    INSERT INTO academic_feedback 
    (student_id, student_name, course_code, course_name, faculty_name, clarity, materials,
     time_management, syllabus_coverage, overall_satisfaction, comments, prediction_score, prediction_label)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    cursor = conn.cursor()
    
    cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (session['user_id'],))
    student = cursor.fetchone()
    student_id = student['student_id']
    
    faculty_fb = cursor.execute('''
    SELECT 'faculty' as type, instructor_name, overall_rating, comments, sentiment_label, submission_date
    FROM faculty_feedback WHERE student_id = ? ORDER BY submission_date DESC LIMIT 10
    ''', (student_id,)).fetchall()
    
    hostel_fb = cursor.execute('''
    SELECT 'hostel' as type, block_name, cleanliness, comments, sentiment_label, submission_date
    FROM hostel_feedback WHERE student_id = ? ORDER BY submission_date DESC LIMIT 10
    ''', (student_id,)).fetchall()
    
    mess_fb = cursor.execute('''
    SELECT 'mess' as type, mess_type, food_quality, suggestions, sentiment_label, submission_date
    FROM mess_feedback WHERE student_id = ? ORDER BY submission_date DESC LIMIT 10
    ''', (student_id,)).fetchall()
    
    infra_fb = cursor.execute('''
    SELECT 'infrastructure' as type, location, cleanliness, comments, sentiment_label, submission_date
    FROM infrastructure_feedback WHERE student_id = ? ORDER BY submission_date DESC LIMIT 10
    ''', (student_id,)).fetchall()
    
    academic_fb = cursor.execute('''
    SELECT 'academic' as type, course_name, overall_satisfaction, prediction_label, submission_date
    FROM academic_feedback WHERE student_id = ? ORDER BY submission_date DESC LIMIT 10
    ''', (student_id,)).fetchall()
    
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
    cursor = conn.cursor()
    
    cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (session['user_id'],))
    student = cursor.fetchone()
    student_id = student['student_id']
    
    total_fb = cursor.execute('''
    SELECT COUNT(*) as count FROM (
        SELECT id FROM faculty_feedback WHERE student_id = ?
        UNION ALL SELECT id FROM hostel_feedback WHERE student_id = ?
        UNION ALL SELECT id FROM mess_feedback WHERE student_id = ?
        UNION ALL SELECT id FROM infrastructure_feedback WHERE student_id = ?
        UNION ALL SELECT id FROM academic_feedback WHERE student_id = ?
    )
    ''', (student_id, student_id, student_id, student_id, student_id)).fetchone()['count']
    
    avg_rating = cursor.execute('''
    SELECT AVG(overall_satisfaction) as avg FROM academic_feedback WHERE student_id = ?
    ''', (student_id,)).fetchone()['avg'] or 0
    
    conn.close()
    
    return jsonify({
        'total_feedback': total_fb,
        'average_rating': round(avg_rating, 1)
    })

@app.route('/api/faculty/my-feedback', methods=['GET'])
def get_faculty_feedback():
    if 'user_id' not in session or session['role'] != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    faculty_name = session['full_name']
    
    feedback = cursor.execute('''
    SELECT f.*, u.full_name as student_name
    FROM faculty_feedback f
    JOIN students s ON f.student_id = s.student_id
    JOIN users u ON s.user_id = u.user_id
    WHERE f.instructor_name = ?
    ORDER BY f.submission_date DESC
    ''', (faculty_name,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(fb) for fb in feedback])

@app.route('/api/admin/all-feedback', methods=['GET'])
def get_all_feedback():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    faculty_fb = cursor.execute('''
    SELECT 'faculty' as category, u.full_name as student_name, f.instructor_name, 
           f.overall_rating, f.comments, f.sentiment_label, f.submission_date
    FROM faculty_feedback f
    JOIN students s ON f.student_id = s.student_id
    JOIN users u ON s.user_id = u.user_id
    ORDER BY f.submission_date DESC LIMIT 50
    ''').fetchall()
    
    hostel_fb = cursor.execute('''
    SELECT 'hostel' as category, u.full_name as student_name, h.block_name,
           h.cleanliness, h.comments, h.sentiment_label, h.submission_date
    FROM hostel_feedback h
    JOIN students s ON h.student_id = s.student_id
    JOIN users u ON s.user_id = u.user_id
    ORDER BY h.submission_date DESC LIMIT 50
    ''').fetchall()
    
    academic_fb = cursor.execute('''
    SELECT 'academic' as category, a.student_name, a.course_name,
           a.overall_satisfaction, a.prediction_label, a.submission_date
    FROM academic_feedback a
    ORDER BY a.submission_date DESC LIMIT 50
    ''').fetchall()
    
    conn.close()
    
    all_feedback = []
    for fb in faculty_fb: all_feedback.append(dict(fb))
    for fb in hostel_fb: all_feedback.append(dict(fb))
    for fb in academic_fb: all_feedback.append(dict(fb))
    
    return jsonify(all_feedback)

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    total_feedback = cursor.execute('''
    SELECT SUM(count) as total FROM (
        SELECT COUNT(*) as count FROM faculty_feedback
        UNION ALL SELECT COUNT(*) FROM hostel_feedback
        UNION ALL SELECT COUNT(*) FROM mess_feedback
        UNION ALL SELECT COUNT(*) FROM infrastructure_feedback
        UNION ALL SELECT COUNT(*) FROM academic_feedback
    )
    ''').fetchone()['total'] or 0
    
    avg_rating = cursor.execute('SELECT AVG(overall_satisfaction) as avg FROM academic_feedback').fetchone()['avg'] or 0
    
    student_count = cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "student"').fetchone()['count']
    instructor_count = cursor.execute('SELECT COUNT(*) as count FROM instructors').fetchone()['count']
    
    distribution = {
        'faculty': cursor.execute('SELECT COUNT(*) FROM faculty_feedback').fetchone()[0],
        'hostel': cursor.execute('SELECT COUNT(*) FROM hostel_feedback').fetchone()[0],
        'mess': cursor.execute('SELECT COUNT(*) FROM mess_feedback').fetchone()[0],
        'infrastructure': cursor.execute('SELECT COUNT(*) FROM infrastructure_feedback').fetchone()[0],
        'academic': cursor.execute('SELECT COUNT(*) FROM academic_feedback').fetchone()[0]
    }
    
    conn.close()
    
    return jsonify({
        'total_feedback': total_feedback,
        'average_rating': round(avg_rating, 1),
        'student_count': student_count,
        'instructor_count': instructor_count,
        'distribution': distribution
    })

@app.route('/api/instructors', methods=['GET'])
def get_instructors():
    department = request.args.get('department')
    conn = get_db()
    cursor = conn.cursor()
    
    if department:
        instructors = cursor.execute('SELECT * FROM instructors WHERE department = ?', (department,)).fetchall()
    else:
        instructors = cursor.execute('SELECT * FROM instructors').fetchall()
    
    conn.close()
    return jsonify([dict(i) for i in instructors])

@app.route('/api/instructors', methods=['POST'])
def add_instructor():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO instructors (name, department, subject, email, added_by)
    VALUES (?, ?, ?, ?, ?)
    ''', (data['name'], data['department'], data.get('subject'), data.get('email'), session['user_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Instructor added successfully'})

@app.route('/api/instructors/<int:instructor_id>', methods=['DELETE'])
def delete_instructor():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM instructors WHERE instructor_id = ?', (instructor_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Instructor deleted successfully'})

@app.route('/api/academic/departments', methods=['GET'])
def get_departments():
    return jsonify(['COMPUTER SCIENCE AND ENGINEERING', 'INFORMATION TECHNOLOGY', 
                    'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING',
                    'ELECTRONICS AND COMMUNICATION ENGINEERING', 'MECHANICAL ENGINEERING'])

@app.route('/api/academic/courses', methods=['GET'])
def get_courses():
    department = request.args.get('department')
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM courses WHERE 1=1"
    params = []
    
    if department:
        query += " AND department = ?"
        params.append(department)
    
    courses = cursor.execute(query, params).fetchall()
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
    print("Faculty: dr.sasikala@bitsathy.ac.in / faculty123")
    print("="*50 + "\n")
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))