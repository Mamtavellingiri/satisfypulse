import psycopg2
import os

DEFAULT_DATABASE_URL = 'postgresql://satisfypulse_db_user:cY46Rqtg44BuS3Kc0iRHhvHZMQcuZ1aV@dpg-d7acejogjchc73bah490-a.singapore-postgres.render.com/satisfypulse_db'
DATABASE_URL = os.environ.get('DATABASE_URL', DEFAULT_DATABASE_URL)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def drop_legacy_constraints(cursor):
    cursor.execute('ALTER TABLE users DROP CONSTRAINT IF EXISTS users_full_name_key')
    cursor.execute('ALTER TABLE faculty_feedback DROP CONSTRAINT IF EXISTS faculty_feedback_instructor_name_key')
    cursor.execute('ALTER TABLE courses DROP CONSTRAINT IF EXISTS courses_course_name_key')

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        full_name TEXT NOT NULL,
        department TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Students table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        student_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        reg_no TEXT UNIQUE,
        joining_year INTEGER,
        current_year INTEGER,
        is_hosteler INTEGER DEFAULT 0,
        is_final_year INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # Faculty table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS faculty (
        faculty_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        faculty_code TEXT UNIQUE,
        designation TEXT,
        subjects TEXT,
        join_date DATE,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # Instructors table (ALL faculty members)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instructors (
        instructor_id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        designation TEXT,
        subject TEXT,
        email TEXT,
        added_by INTEGER,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Faculty Feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS faculty_feedback (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL,
        instructor_id INTEGER,
        instructor_name TEXT NOT NULL,
        subject TEXT,
        teaching_quality INTEGER,
        punctuality INTEGER,
        doubt_clearing INTEGER,
        overall_rating INTEGER,
        comments TEXT,
        sentiment_score REAL,
        sentiment_label TEXT,
        submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
    ''')
    
    # Hostel Feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hostel_feedback (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL,
        block_name TEXT,
        room_type TEXT,
        cleanliness INTEGER,
        water_supply INTEGER,
        electricity INTEGER,
        wifi_quality INTEGER,
        warden_behavior INTEGER,
        security INTEGER,
        maintenance INTEGER,
        comments TEXT,
        sentiment_score REAL,
        sentiment_label TEXT,
        submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
    ''')
    
    # Mess Feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mess_feedback (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL,
        mess_type TEXT,
        food_quality INTEGER,
        taste INTEGER,
        hygiene INTEGER,
        variety INTEGER,
        quantity INTEGER,
        serving_staff INTEGER,
        suggestions TEXT,
        sentiment_score REAL,
        sentiment_label TEXT,
        submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
    ''')
    
    # Infrastructure Feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS infrastructure_feedback (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL,
        location TEXT,
        cleanliness INTEGER,
        seating INTEGER,
        lighting INTEGER,
        ventilation INTEGER,
        equipment INTEGER,
        maintenance INTEGER,
        comments TEXT,
        sentiment_score REAL,
        sentiment_label TEXT,
        submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
    ''')
    
    # Academic Feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS academic_feedback (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL,
        student_name TEXT,
        course_code TEXT,
        course_name TEXT,
        faculty_name TEXT,
        clarity INTEGER,
        materials INTEGER,
        time_management INTEGER,
        syllabus_coverage INTEGER,
        overall_satisfaction INTEGER,
        comments TEXT,
        prediction_score REAL,
        prediction_label TEXT,
        submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
    ''')
    
    # Courses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        course_id SERIAL PRIMARY KEY,
        course_code TEXT UNIQUE,
        course_name TEXT NOT NULL,
        department TEXT NOT NULL,
        year INTEGER,
        semester INTEGER,
        period TEXT,
        faculty_name TEXT
    )
    ''')

    # Faculty Alerts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS faculty_alerts (
        id SERIAL PRIMARY KEY,
        faculty_name TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    drop_legacy_constraints(cursor)
    
    conn.commit()
    
    # ---------------------------------------------------------
    # MIGRATION: Force update existing emails to new standards
    # ---------------------------------------------------------
    # 1. Update Instructors
    cursor.execute("""
        UPDATE instructors 
        SET email = REPLACE(email, '@bitsathy.ac.in', '_faculty@bitsathy.ac.in')
        WHERE email LIKE '%@bitsathy.ac.in' 
        AND email NOT LIKE '%_faculty@bitsathy.ac.in'
    """)
    # 2. Update Users (Faculty only)
    cursor.execute("""
        UPDATE users 
        SET email = REPLACE(email, '@bitsathy.ac.in', '_faculty@bitsathy.ac.in')
        WHERE role = 'faculty' 
        AND email LIKE '%@bitsathy.ac.in' 
        AND email NOT LIKE '%_faculty@bitsathy.ac.in'
    """)
    # 3. Cleanup any double extensions (safety)
    cursor.execute("UPDATE instructors SET email = REPLACE(email, '_faculty_faculty', '_faculty')")
    cursor.execute("UPDATE users SET email = REPLACE(email, '_faculty_faculty', '_faculty')")
    # ---------------------------------------------------------
    
    # Insert all faculty members
    insert_all_faculty(cursor)
    insert_sample_courses(cursor)
    insert_sample_users(cursor)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def insert_all_faculty(cursor):
    faculty_list = [
        # AGRICULTURAL ENGINEERING
        ('Dr Chelladurai V', 'AGRICULTURAL ENGINEERING', 'Head', 'chelladurai_faculty@bitsathy.ac.in'),
        ('Dr Uvaraja V C', 'AGRICULTURAL ENGINEERING', 'Professor', 'uvaraja_faculty@bitsathy.ac.in'),
        ('Dr Vasudevan M', 'AGRICULTURAL ENGINEERING', 'Associate Professor', 'vasudevan_faculty@bitsathy.ac.in'),
        ('Dr Vinoth Kumar J', 'AGRICULTURAL ENGINEERING', 'Assistant Professor Level III', 'vinothkumar_faculty@bitsathy.ac.in'),
        ('Dr Praveen Kumar D', 'AGRICULTURAL ENGINEERING', 'Assistant Professor Level II', 'praveenkumar_faculty@bitsathy.ac.in'),
        ('Prof. Ananthi D', 'AGRICULTURAL ENGINEERING', 'Assistant Professor', 'ananthi_faculty@bitsathy.ac.in'),
        ('Prof. Muthukumaravel K', 'AGRICULTURAL ENGINEERING', 'Assistant Professor', 'muthukumaravel_faculty@bitsathy.ac.in'),
        ('Prof. Raghul S', 'AGRICULTURAL ENGINEERING', 'Assistant Professor', 'raghul_faculty@bitsathy.ac.in'),
        ('Prof. Snekha A R', 'AGRICULTURAL ENGINEERING', 'Assistant Professor', 'snekha_faculty@bitsathy.ac.in'),
        
        # ARTIFICIAL INTELLIGENCE AND DATA SCIENCE
        ('Dr Gomathi R', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Professor & Head', 'gomathi_faculty@bitsathy.ac.in'),
        ('Dr Sundara Murthy S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Professor', 'sundaramurthy_faculty@bitsathy.ac.in'),
        ('Dr Eswaramoorthy V', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Professor', 'eswaramoorthy_faculty@bitsathy.ac.in'),
        ('Dr Arun Kumar R', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Associate Professor', 'arunkumar_faculty@bitsathy.ac.in'),
        ('Dr Nandhini S S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Associate Professor', 'nandhini_faculty@bitsathy.ac.in'),
        ('Dr Balasamy K', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Associate Professor', 'balasamy_faculty@bitsathy.ac.in'),
        ('Dr Subbulakshmi M', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Associate Professor', 'subbulakshmi_faculty@bitsathy.ac.in'),
        ('Prof. Ranjith G', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'ranjith_faculty@bitsathy.ac.in'),
        ('Prof. Prabanand S C', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'prabanand_faculty@bitsathy.ac.in'),
        ('Prof. Nithyapriya S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'nithyapriya_faculty@bitsathy.ac.in'),
        ('Prof. Esakki Madura E', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'esakkimadura_faculty@bitsathy.ac.in'),
        ('Prof. Chozharajan P', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'chozharajan_faculty@bitsathy.ac.in'),
        ('Prof. Navaneeth Kumar K', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'navaneethkumar_faculty@bitsathy.ac.in'),
        ('Prof. Nisha Devi K', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level II', 'nishadevi_faculty@bitsathy.ac.in'),
        ('Prof. Raj Kumar V S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level II', 'rajkumar_faculty@bitsathy.ac.in'),
        ('Prof. Divyabarathi P', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level II', 'divyabarathi_faculty@bitsathy.ac.in'),
        ('Prof. Vaanathi S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level II', 'vaanathi_faculty@bitsathy.ac.in'),
        ('Prof. Satheeshkumar S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level II', 'satheeshkumar_faculty@bitsathy.ac.in'),
        ('Prof. Satheesh N P', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'satheesh_faculty@bitsathy.ac.in'),
        ('Prof. Kiruthiga R', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'kiruthiga_faculty@bitsathy.ac.in'),
        ('Prof. Ashforn Hermina J M', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'ashfornhermina_faculty@bitsathy.ac.in'),
        ('Prof. Jeevitha S V', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'jeevitha_faculty@bitsathy.ac.in'),
        ('Prof. Premkumar C', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'premkumar_faculty@bitsathy.ac.in'),
        ('Prof. Benita Gracia Thangam J', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'benitagracia_faculty@bitsathy.ac.in'),
        ('Prof. Reshmi T S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'reshmi_faculty@bitsathy.ac.in'),
        ('Prof. Kalpana R', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'kalpana_faculty@bitsathy.ac.in'),
        ('Prof. Suriya V', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'suriya_faculty@bitsathy.ac.in'),
        ('Prof. Hema Priya D', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'hemapriya_faculty@bitsathy.ac.in'),
        ('Prof. Priyadharshni S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'priyadharshni_faculty@bitsathy.ac.in'),
        ('Prof. Manju M', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'manju_faculty@bitsathy.ac.in'),
        ('Prof. Sasson Taffwin Moses S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'sassontaffwin_faculty@bitsathy.ac.in'),
        ('Prof. Manochitra A S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'manochitra_faculty@bitsathy.ac.in'),
        
        # ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING
        ('Dr Bharathi A', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Professor & Head', 'bharathi_faculty@bitsathy.ac.in'),
        ('Dr Gopalakrishnan B', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Professor', 'gopalakrishnan_faculty@bitsathy.ac.in'),
        ('Dr Kodieswari A', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Associate Professor', 'kodieswari_faculty@bitsathy.ac.in'),
        ('Dr Rajasekar S S', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Associate Professor', 'rajasekar_faculty@bitsathy.ac.in'),
        ('Dr Padmashree A', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Associate Professor', 'padmashree_faculty@bitsathy.ac.in'),
        ('Dr Karthikeyan G', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level III', 'karthikeyan_faculty@bitsathy.ac.in'),
        ('Prof. Eugene Berna I', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level III', 'eugeneberna_faculty@bitsathy.ac.in'),
        ('Prof. Balamurugan E', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level II', 'balamurugan_faculty@bitsathy.ac.in'),
        ('Prof. Sudha R', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level II', 'sudha_faculty@bitsathy.ac.in'),
        ('Prof. Haripriya R', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level II', 'haripriya_faculty@bitsathy.ac.in'),
        ('Prof. Nithin P', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level II', 'nithin_faculty@bitsathy.ac.in'),
        ('Prof. Satheshkumar K', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level II', 'satheshkumar_faculty@bitsathy.ac.in'),
        ('Prof. Karthika S', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'karthika_faculty@bitsathy.ac.in'),
        ('Prof. Mohanapriya K', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'mohanapriya_faculty@bitsathy.ac.in'),
        ('Prof. Ezhil R', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'ezhil_faculty@bitsathy.ac.in'),
        ('Prof. Pavithra G', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'pavithra_faculty@bitsathy.ac.in'),
        ('Prof. Kanimozhi A', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'kanimozhi_faculty@bitsathy.ac.in'),
        ('Prof. Nishanthini S', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'nishanthini_faculty@bitsathy.ac.in'),
        ('Prof. Lokeswari P', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'lokeswari_faculty@bitsathy.ac.in'),
        ('Prof. Gayathridevi M', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'gayathridevi_faculty@bitsathy.ac.in'),
        ('Prof. Sasithra S', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'sasithra_faculty@bitsathy.ac.in'),
        ('Prof. Saranya M K', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'saranyamk_faculty@bitsathy.ac.in'),
        ('Prof. Sindhujaa N', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'sindhujaa_faculty@bitsathy.ac.in'),
        
        # BIOMEDICAL ENGINEERING
        ('Dr Deepa D', 'BIOMEDICAL ENGINEERING', 'Professor & Head', 'deepa_faculty@bitsathy.ac.in'),
        ('Prof. Prathap M R', 'BIOMEDICAL ENGINEERING', 'Assistant Professor Level II', 'prathap_faculty@bitsathy.ac.in'),
        ('Prof. Caroline Vinnetia S', 'BIOMEDICAL ENGINEERING', 'Assistant Professor Level II', 'carolinevinnetia_faculty@bitsathy.ac.in'),
        ('Prof. Saahina S', 'BIOMEDICAL ENGINEERING', 'Assistant Professor', 'saahina_faculty@bitsathy.ac.in'),
        ('Prof. Syed Althaf S', 'BIOMEDICAL ENGINEERING', 'Assistant Professor', 'syedalthaf_faculty@bitsathy.ac.in'),
        ('Prof. Sreeniveatha P', 'BIOMEDICAL ENGINEERING', 'Assistant Professor', 'sreeniveatha_faculty@bitsathy.ac.in'),
        ('Prof. Pratheebha G', 'BIOMEDICAL ENGINEERING', 'Assistant Professor', 'pratheebha_faculty@bitsathy.ac.in'),
        
        # BIOTECHNOLOGY
        ('Dr Balakrishnaraja R', 'BIOTECHNOLOGY', 'Professor & Head', 'balakrishnaraja_faculty@bitsathy.ac.in'),
        ('Dr Kannan K P', 'BIOTECHNOLOGY', 'Professor', 'kannan_faculty@bitsathy.ac.in'),
        ('Dr Tamilselvi S', 'BIOTECHNOLOGY', 'Professor', 'tamilselvi_faculty@bitsathy.ac.in'),
        ('Dr Kirupa Sankar M', 'BIOTECHNOLOGY', 'Associate Professor', 'kirupasankar_faculty@bitsathy.ac.in'),
        ('Dr Pavithra M K S', 'BIOTECHNOLOGY', 'Associate Professor', 'pavithra_faculty@bitsathy.ac.in'),
        ('Dr Ashwin Raj S', 'BIOTECHNOLOGY', 'Assistant Professor Level III', 'ashwinraj_faculty@bitsathy.ac.in'),
        ('Dr Sandhyarani R', 'BIOTECHNOLOGY', 'Assistant Professor Level III', 'sandhyarani_faculty@bitsathy.ac.in'),
        ('Prof. Rajaseetharama S', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'rajaseetharama_faculty@bitsathy.ac.in'),
        ('Prof. Jeyavel Karthick P', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'jeyavelkarthick_faculty@bitsathy.ac.in'),
        ('Dr Suresh Chaluvadi', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'sureshchaluvadi_faculty@bitsathy.ac.in'),
        ('Prof. Sakthishobana K', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'sakthishobana_faculty@bitsathy.ac.in'),
        ('Prof. Balaji S', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'balaji_faculty@bitsathy.ac.in'),
        ('Dr Saranya S', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'saranya_faculty@bitsathy.ac.in'),
        ('Prof. Swathi G', 'BIOTECHNOLOGY', 'Assistant Professor', 'swathi_faculty@bitsathy.ac.in'),
        ('Prof. Dhivya Dharshini U', 'BIOTECHNOLOGY', 'Assistant Professor', 'dhivyadharshini_faculty@bitsathy.ac.in'),
        ('Prof. Mahima P', 'BIOTECHNOLOGY', 'Assistant Professor', 'mahima_faculty@bitsathy.ac.in'),
        ('Prof. Nandhini N', 'BIOTECHNOLOGY', 'Assistant Professor', 'nandhini_faculty@bitsathy.ac.in'),
        ('Prof. Vinodhini R T', 'BIOTECHNOLOGY', 'Assistant Professor', 'vinodhini_faculty@bitsathy.ac.in'),
        ('Prof. Shankari V', 'BIOTECHNOLOGY', 'Assistant Professor', 'shankari_faculty@bitsathy.ac.in'),
        
        # CHEMISTRY
        ('Dr Praveena R', 'CHEMISTRY', 'Head', 'praveena_faculty@bitsathy.ac.in'),
        ('Dr Vijayanand P S', 'CHEMISTRY', 'Professor', 'vijayanand_faculty@bitsathy.ac.in'),
        ('Dr Subhapriya P', 'CHEMISTRY', 'Associate Professor', 'subhapriya_faculty@bitsathy.ac.in'),
        ('Dr Kavitha C', 'CHEMISTRY', 'Associate Professor', 'kavithac_faculty@bitsathy.ac.in'),
        ('Dr Malathi M', 'CHEMISTRY', 'Associate Professor', 'malathi_faculty@bitsathy.ac.in'),
        ('Dr Sathish V', 'CHEMISTRY', 'Assistant Professor Level III', 'sathishv_faculty@bitsathy.ac.in'),
        ('Dr Muthukumar P', 'CHEMISTRY', 'Assistant Professor Level III', 'muthukumar_faculty@bitsathy.ac.in'),
        ('Dr Viswanathan G', 'CHEMISTRY', 'Assistant Professor Level III', 'viswanathan_faculty@bitsathy.ac.in'),
        
        # CIVIL ENGINEERING
        ('Dr Mohanraj A', 'CIVIL ENGINEERING', 'Head', 'mohanraj_faculty@bitsathy.ac.in'),
        ('Dr Karthiga Shenbagam N', 'CIVIL ENGINEERING', 'Associate Professor', 'karthigashenbagam_faculty@bitsathy.ac.in'),
        ('Dr Geethamani R', 'CIVIL ENGINEERING', 'Assistant Professor Level III', 'geethamani_faculty@bitsathy.ac.in'),
        ('Prof. Rajendran M', 'CIVIL ENGINEERING', 'Assistant Professor Level III', 'rajendran_faculty@bitsathy.ac.in'),
        
        # COMPUTER SCIENCE AND BUSINESS SYSTEMS
        ('Prof. Chandru K S', 'COMPUTER SCIENCE AND BUSINESS SYSTEMS', 'Assistant Professor Level III', 'chandru_faculty@bitsathy.ac.in'),
        ('Prof. Yuvalatha S', 'COMPUTER SCIENCE AND BUSINESS SYSTEMS', 'Assistant Professor Level III', 'yuvalatha_faculty@bitsathy.ac.in'),
        
        # COMPUTER SCIENCE AND DESIGN
        ('Prof. Maheshkumar K', 'COMPUTER SCIENCE AND DESIGN', 'Assistant Professor Level II', 'maheshkumar_faculty@bitsathy.ac.in'),
        ('Prof. Preethimathi L', 'COMPUTER SCIENCE AND DESIGN', 'Assistant Professor', 'preethimathi_faculty@bitsathy.ac.in'),
        
        # COMPUTER SCIENCE AND ENGINEERING
        ('Dr Sasikala D', 'COMPUTER SCIENCE AND ENGINEERING', 'Professor & Head', 'sasikala_faculty@bitsathy.ac.in'),
        ('Dr Premalatha K', 'COMPUTER SCIENCE AND ENGINEERING', 'Professor', 'premalatha_faculty@bitsathy.ac.in'),
        ('Dr Sathishkumar P', 'COMPUTER SCIENCE AND ENGINEERING', 'Professor', 'sathishkumar_faculty@bitsathy.ac.in'),
        ('Dr Sangeethaa S N', 'COMPUTER SCIENCE AND ENGINEERING', 'Professor', 'sangeethaa_faculty@bitsathy.ac.in'),
        ('Dr Rajeshkumar G', 'COMPUTER SCIENCE AND ENGINEERING', 'Professor', 'rajeshkumar_faculty@bitsathy.ac.in'),
        ('Dr Karthiga M', 'COMPUTER SCIENCE AND ENGINEERING', 'Associate Professor', 'karthiga_faculty@bitsathy.ac.in'),
        ('Dr Saranya K', 'COMPUTER SCIENCE AND ENGINEERING', 'Associate Professor', 'saranya_faculty@bitsathy.ac.in'),
        ('Dr Deepa Priya B S', 'COMPUTER SCIENCE AND ENGINEERING', 'Associate Professor', 'deepapriya_faculty@bitsathy.ac.in'),
        ('Dr Ramya R', 'COMPUTER SCIENCE AND ENGINEERING', 'Associate Professor', 'ramya_faculty@bitsathy.ac.in'),
        
        # COMPUTER TECHNOLOGY
        ('Dr Thanga Parvathi B', 'COMPUTER TECHNOLOGY', 'Professor', 'thangaparvathi_faculty@bitsathy.ac.in'),
        ('Dr Murugesan P', 'COMPUTER TECHNOLOGY', 'Assistant Professor Level III', 'murugesan_faculty@bitsathy.ac.in'),
        
        # ELECTRICAL AND ELECTRONICS ENGINEERING
        ('Dr Maheswari K T', 'ELECTRICAL AND ELECTRONICS ENGINEERING', 'Head', 'maheswari_faculty@bitsathy.ac.in'),
        ('Dr Bharani Kumar R', 'ELECTRICAL AND ELECTRONICS ENGINEERING', 'Professor', 'bhananikumar_faculty@bitsathy.ac.in'),
        ('Dr Sivaraman P', 'ELECTRICAL AND ELECTRONICS ENGINEERING', 'Professor', 'sivaraman_faculty@bitsathy.ac.in'),
        
        # ELECTRONICS AND COMMUNICATION ENGINEERING
        ('Dr Prakash S P', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'Head', 'prakashsp_faculty@bitsathy.ac.in'),
        ('Dr Harikumar R', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'Professor', 'harikumar_faculty@bitsathy.ac.in'),
        ('Dr Poongodi C', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'Professor', 'poongodi_faculty@bitsathy.ac.in'),
        ('Dr Sampoornam K P', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'Professor', 'sampoornam_faculty@bitsathy.ac.in'),
        ('Dr Perarasi T', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'Professor', 'perarasi_faculty@bitsathy.ac.in'),
        
        # ELECTRONICS AND INSTRUMENTATION ENGINEERING
        ('Dr Vairavel K S', 'ELECTRONICS AND INSTRUMENTATION ENGINEERING', 'Head', 'vairavel_faculty@bitsathy.ac.in'),
        ('Dr Ganesh Babu C', 'ELECTRONICS AND INSTRUMENTATION ENGINEERING', 'Professor', 'ganeshbabu_faculty@bitsathy.ac.in'),
        
        # FASHION TECHNOLOGY
        ('Prof. Saranya D V', 'FASHION TECHNOLOGY', 'Head', 'saranyadv_faculty@bitsathy.ac.in'),
        ('Dr Mohan Bharathi C', 'FASHION TECHNOLOGY', 'Assistant Professor Level III', 'mohanbharathi_faculty@bitsathy.ac.in'),
        
        # FOOD TECHNOLOGY
        ('Prof. Gowrishankar L', 'FOOD TECHNOLOGY', 'Head', 'gowrishankar_faculty@bitsathy.ac.in'),
        ('Dr Tna Arunasree', 'FOOD TECHNOLOGY', 'Assistant Professor Level II', 'arunasree_faculty@bitsathy.ac.in'),
        
        # HUMANITIES
        ('Dr Ajai A', 'HUMANITIES', 'Head', 'ajai_faculty@bitsathy.ac.in'),
        ('Dr Nandhini A P', 'HUMANITIES', 'Assistant Professor', 'nandhiniap_faculty@bitsathy.ac.in'),
        ('Dr Gayathri G M', 'HUMANITIES', 'Assistant Professor', 'gayathrigm_faculty@bitsathy.ac.in'),
        
        # INFORMATION SCIENCE AND ENGINEERING
        ('Dr Anandakumar K', 'INFORMATION SCIENCE AND ENGINEERING', 'Assistant Professor Level III', 'anandakumar_faculty@bitsathy.ac.in'),
        ('Prof. Pandiyan M', 'INFORMATION SCIENCE AND ENGINEERING', 'Assistant Professor Level III', 'pandiyan_faculty@bitsathy.ac.in'),
        
        # INFORMATION TECHNOLOGY
        ('Dr Naveena S', 'INFORMATION TECHNOLOGY', 'Head', 'naveena_faculty@bitsathy.ac.in'),
        ('Dr Palanisamy C', 'INFORMATION TECHNOLOGY', 'Professor', 'palanisamy_faculty@bitsathy.ac.in'),
        ('Dr Sadhasivam N', 'INFORMATION TECHNOLOGY', 'Professor', 'sadhasivam_faculty@bitsathy.ac.in'),
        ('Dr Paarivallal Ra.', 'INFORMATION TECHNOLOGY', 'Associate Professor', 'paarivallal_faculty@bitsathy.ac.in'),
        ('Dr Sathis Kumar K', 'INFORMATION TECHNOLOGY', 'Associate Professor', 'sathiskumar_faculty@bitsathy.ac.in'),
        
        # MATHEMATICS
        ('Dr Parimala M', 'MATHEMATICS', 'Head', 'parimala_faculty@bitsathy.ac.in'),
        ('Dr Thulasimani T', 'MATHEMATICS', 'Associate Professor', 'thulasimani_faculty@bitsathy.ac.in'),
        ('Dr Indirani C', 'MATHEMATICS', 'Assistant Professor Level III', 'indirani_faculty@bitsathy.ac.in'),
        ('Dr Vinothini V R', 'MATHEMATICS', 'Assistant Professor Level III', 'vinothini_faculty@bitsathy.ac.in'),
        
        # MECHANICAL ENGINEERING
        ('Dr Ravi Kumar M', 'MECHANICAL ENGINEERING', 'Professor & Head', 'ravikumar_faculty@bitsathy.ac.in'),
        ('Dr Sivakumar K', 'MECHANICAL ENGINEERING', 'Senior Professor', 'sivakumar_faculty@bitsathy.ac.in'),
        ('Dr Muthukumar K', 'MECHANICAL ENGINEERING', 'Adjunct Faculty', 'muthukumar_faculty@bitsathy.ac.in'),
        ('Dr Senthilkumar G', 'MECHANICAL ENGINEERING', 'Professor', 'senthilkumar_faculty@bitsathy.ac.in'),
        
        # MECHATRONICS ENGINEERING
        ('Dr Senthil Kumar K L', 'MECHATRONICS ENGINEERING', 'Professor & Head', 'senthilkumarkl_faculty@bitsathy.ac.in'),
        ('Dr Jegadheeswaran S', 'MECHATRONICS ENGINEERING', 'Professor', 'jegadheeswaran_faculty@bitsathy.ac.in'),
        
        # PHYSICS
        ('Dr Sadasivam K', 'PHYSICS', 'Professor & Head', 'sadasivam_faculty@bitsathy.ac.in'),
        ('Dr Vijayakumar V N', 'PHYSICS', 'Professor', 'vijayakumar_faculty@bitsathy.ac.in'),
        ('Dr Pongali Sathya Prabu N', 'PHYSICS', 'Associate Professor', 'pongali_faculty@bitsathy.ac.in'),
        ('Dr Ashokan S', 'PHYSICS', 'Assistant Professor Level III', 'ashokan_faculty@bitsathy.ac.in'),
        
        # SCHOOL OF MANAGEMENT STUDIES
        ('Dr Murugappan S', 'SCHOOL OF MANAGEMENT STUDIES', 'Professor & Director', 'murugappan_faculty@bitsathy.ac.in'),
        ('Dr Adhinarayanan B', 'SCHOOL OF MANAGEMENT STUDIES', 'Associate Professor', 'adhinarayanan_faculty@bitsathy.ac.in'),
        
        # TEXTILE TECHNOLOGY
        ('Dr Janarthanan M', 'TEXTILE TECHNOLOGY', 'Head', 'janarthanan_faculty@bitsathy.ac.in'),
        ('Prof. Mounika S', 'TEXTILE TECHNOLOGY', 'Assistant Professor', 'mounika_faculty@bitsathy.ac.in'),
    ]
    
    for faculty in faculty_list:
        cursor.execute('''
        INSERT INTO instructors (name, department, designation, email)
        SELECT %s, %s, %s, %s
        WHERE NOT EXISTS (
            SELECT 1 FROM instructors WHERE name = %s
        )
        ''', (faculty[0], faculty[1], faculty[2], faculty[3], faculty[0]))

def insert_sample_courses(cursor):
    courses = [
        ('CS101', 'Python Programming', 'COMPUTER SCIENCE AND ENGINEERING', 1, 1, 'PT1', 'Dr Sasikala D'),
        ('CS102', 'Data Structures', 'COMPUTER SCIENCE AND ENGINEERING', 1, 1, 'PT2', 'Dr Premalatha K'),
        ('CS103', 'Database Management', 'COMPUTER SCIENCE AND ENGINEERING', 2, 3, 'FINAL', 'Dr Sathishkumar P'),
        ('IT101', 'Web Technologies', 'INFORMATION TECHNOLOGY', 1, 1, 'PT1', 'Dr Naveena S'),
        ('IT102', 'Cloud Computing', 'INFORMATION TECHNOLOGY', 2, 3, 'FINAL', 'Dr Palanisamy C'),
        ('AIDS101', 'Machine Learning', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 2, 3, 'PT1', 'Dr Gomathi R'),
        ('ECE101', 'Digital Electronics', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 1, 1, 'PT1', 'Dr Prakash S P'),
        ('MECH101', 'Engineering Mechanics', 'MECHANICAL ENGINEERING', 1, 1, 'PT2', 'Dr Ravi Kumar M'),
        ('MAT101', 'Engineering Mathematics', 'MATHEMATICS', 1, 1, 'PT1', 'Dr Parimala M'),
        ('PHY101', 'Engineering Physics', 'PHYSICS', 1, 1, 'PT1', 'Dr Sadasivam K'),
        ('CHEM101', 'Engineering Chemistry', 'CHEMISTRY', 1, 1, 'PT1', 'Dr Praveena R'),
    ]
    
    for course in courses:
        cursor.execute('''
        INSERT INTO courses (course_code, course_name, department, year, semester, period, faculty_name)
        SELECT %s, %s, %s, %s, %s, %s, %s
        WHERE NOT EXISTS (
            SELECT 1 FROM courses WHERE course_code = %s
        )
        ''', course + (course[0],))

def insert_sample_users(cursor):
    users = [
        ('admin@bitsathy.ac.in', 'admin123', 'admin', 'System Administrator', None),
        ('rahul.cs23@bitsathy.ac.in', 'password123', 'student', 'Rahul Kumar', 'COMPUTER SCIENCE AND ENGINEERING'),
        ('priya.it23@bitsathy.ac.in', 'password123', 'student', 'Priya Srinivasan', 'INFORMATION TECHNOLOGY'),
        ('ankit.aids23@bitsathy.ac.in', 'password123', 'student', 'Ankit Sharma', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE'),
        ('divya.ece23@bitsathy.ac.in', 'password123', 'student', 'Divya Lakshmi', 'ELECTRONICS AND COMMUNICATION ENGINEERING'),
        ('karthik.mech23@bitsathy.ac.in', 'password123', 'student', 'Karthik Raj', 'MECHANICAL ENGINEERING'),
        ('sneha.civil23@bitsathy.ac.in', 'password123', 'student', 'Sneha Priya', 'CIVIL ENGINEERING'),
        ('sasikala_faculty@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Sasikala D', 'COMPUTER SCIENCE AND ENGINEERING'),
        ('premalatha_faculty@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Premalatha K', 'COMPUTER SCIENCE AND ENGINEERING'),
        ('naveena_faculty@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Naveena S', 'INFORMATION TECHNOLOGY'),
        ('gomathi_faculty@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Gomathi R', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE'),
        ('ravikumar_faculty@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Ravi Kumar M', 'MECHANICAL ENGINEERING'),
        ('prakash_faculty@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Prakash S P', 'ELECTRONICS AND COMMUNICATION ENGINEERING'),
        ('parimala_faculty@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Parimala M', 'MATHEMATICS'),
        ('sadasivam_faculty@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Sadasivam K', 'PHYSICS'),
        ('praveena_faculty@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Praveena R', 'CHEMISTRY'),
    ]
    
    for user in users:
        # Check if user already exists
        cursor.execute('SELECT user_id FROM users WHERE email = %s', (user[0],))
        existing = cursor.fetchone()
        
        if not existing:
            cursor.execute('''
            INSERT INTO users (email, password, role, full_name, department)
            VALUES (%s, %s, %s, %s, %s) RETURNING user_id
            ''', (user[0], user[1], user[2], user[3], user[4]))
            
            user_id = cursor.fetchone()[0]
            
            if user[2] == 'student':
                reg_no = f"BIT{user[0].split('.')[0][:3].upper()}{user_id}"
                cursor.execute('''
                INSERT INTO students (user_id, reg_no, joining_year, current_year, is_hosteler)
                VALUES (%s, %s, %s, %s, %s)
                ''', (user_id, reg_no, 2023, 2, 1))
            elif user[2] == 'faculty':
                cursor.execute('''
                INSERT INTO faculty (user_id, faculty_code, designation, join_date)
                VALUES (%s, %s, %s, %s)
                ''', (user_id, f'FAC{user_id}', 'Professor', '2020-06-01'))

if __name__ == '__main__':
    init_database()
    print("Database initialized successfully with all BIT faculty members!")
