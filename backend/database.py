import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('satisfypulse.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT UNIQUE,
        course_name TEXT NOT NULL,
        department TEXT NOT NULL,
        year INTEGER,
        semester INTEGER,
        period TEXT,
        faculty_name TEXT
    )
    ''')
    
    conn.commit()
    
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
        ('Dr Chelladurai V', 'AGRICULTURAL ENGINEERING', 'Head', 'chelladurai@bitsathy.ac.in'),
        ('Dr Uvaraja V C', 'AGRICULTURAL ENGINEERING', 'Professor', 'uvaraja@bitsathy.ac.in'),
        ('Dr Vasudevan M', 'AGRICULTURAL ENGINEERING', 'Associate Professor', 'vasudevan@bitsathy.ac.in'),
        ('Dr Vinoth Kumar J', 'AGRICULTURAL ENGINEERING', 'Assistant Professor Level III', 'vinothkumar@bitsathy.ac.in'),
        ('Dr Praveen Kumar D', 'AGRICULTURAL ENGINEERING', 'Assistant Professor Level II', 'praveenkumar@bitsathy.ac.in'),
        ('Prof. Ananthi D', 'AGRICULTURAL ENGINEERING', 'Assistant Professor', 'ananthi@bitsathy.ac.in'),
        ('Prof. Muthukumaravel K', 'AGRICULTURAL ENGINEERING', 'Assistant Professor', 'muthukumaravel@bitsathy.ac.in'),
        ('Prof. Raghul S', 'AGRICULTURAL ENGINEERING', 'Assistant Professor', 'raghul@bitsathy.ac.in'),
        ('Prof. Snekha A R', 'AGRICULTURAL ENGINEERING', 'Assistant Professor', 'snekha@bitsathy.ac.in'),
        
        # ARTIFICIAL INTELLIGENCE AND DATA SCIENCE
        ('Dr Gomathi R', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Professor & Head', 'gomathi@bitsathy.ac.in'),
        ('Dr Sundara Murthy S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Professor', 'sundaramurthy@bitsathy.ac.in'),
        ('Dr Eswaramoorthy V', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Professor', 'eswaramoorthy@bitsathy.ac.in'),
        ('Dr Arun Kumar R', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Associate Professor', 'arunkumar@bitsathy.ac.in'),
        ('Dr Nandhini S S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Associate Professor', 'nandhini@bitsathy.ac.in'),
        ('Dr Balasamy K', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Associate Professor', 'balasamy@bitsathy.ac.in'),
        ('Dr Subbulakshmi M', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Associate Professor', 'subbulakshmi@bitsathy.ac.in'),
        ('Prof. Ranjith G', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'ranjith@bitsathy.ac.in'),
        ('Prof. Prabanand S C', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'prabanand@bitsathy.ac.in'),
        ('Prof. Nithyapriya S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'nithyapriya@bitsathy.ac.in'),
        ('Prof. Esakki Madura E', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'esakkimadura@bitsathy.ac.in'),
        ('Prof. Chozharajan P', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'chozharajan@bitsathy.ac.in'),
        ('Prof. Navaneeth Kumar K', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level III', 'navaneethkumar@bitsathy.ac.in'),
        ('Prof. Nisha Devi K', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level II', 'nishadevi@bitsathy.ac.in'),
        ('Prof. Raj Kumar V S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level II', 'rajkumar@bitsathy.ac.in'),
        ('Prof. Divyabarathi P', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level II', 'divyabarathi@bitsathy.ac.in'),
        ('Prof. Vaanathi S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level II', 'vaanathi@bitsathy.ac.in'),
        ('Prof. Satheeshkumar S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor Level II', 'satheeshkumar@bitsathy.ac.in'),
        ('Prof. Satheesh N P', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'satheesh@bitsathy.ac.in'),
        ('Prof. Kiruthiga R', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'kiruthiga@bitsathy.ac.in'),
        ('Prof. Ashforn Hermina J M', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'ashfornhermina@bitsathy.ac.in'),
        ('Prof. Jeevitha S V', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'jeevitha@bitsathy.ac.in'),
        ('Prof. Premkumar C', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'premkumar@bitsathy.ac.in'),
        ('Prof. Benita Gracia Thangam J', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'benitagracia@bitsathy.ac.in'),
        ('Prof. Reshmi T S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'reshmi@bitsathy.ac.in'),
        ('Prof. Kalpana R', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'kalpana@bitsathy.ac.in'),
        ('Prof. Suriya V', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'suriya@bitsathy.ac.in'),
        ('Prof. Hema Priya D', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'hemapriya@bitsathy.ac.in'),
        ('Prof. Priyadharshni S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'priyadharshni@bitsathy.ac.in'),
        ('Prof. Manju M', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'manju@bitsathy.ac.in'),
        ('Prof. Sasson Taffwin Moses S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'sassontaffwin@bitsathy.ac.in'),
        ('Prof. Manochitra A S', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE', 'Assistant Professor', 'manochitra@bitsathy.ac.in'),
        
        # ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING
        ('Dr Bharathi A', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Professor & Head', 'bharathi@bitsathy.ac.in'),
        ('Dr Gopalakrishnan B', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Professor', 'gopalakrishnan@bitsathy.ac.in'),
        ('Dr Kodieswari A', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Associate Professor', 'kodieswari@bitsathy.ac.in'),
        ('Dr Rajasekar S S', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Associate Professor', 'rajasekar@bitsathy.ac.in'),
        ('Dr Padmashree A', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Associate Professor', 'padmashree@bitsathy.ac.in'),
        ('Dr Karthikeyan G', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level III', 'karthikeyan@bitsathy.ac.in'),
        ('Prof. Eugene Berna I', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level III', 'eugeneberna@bitsathy.ac.in'),
        ('Prof. Balamurugan E', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level II', 'balamurugan@bitsathy.ac.in'),
        ('Prof. Sudha R', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level II', 'sudha@bitsathy.ac.in'),
        ('Prof. Haripriya R', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level II', 'haripriya@bitsathy.ac.in'),
        ('Prof. Nithin P', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level II', 'nithin@bitsathy.ac.in'),
        ('Prof. Satheshkumar K', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor Level II', 'satheshkumar@bitsathy.ac.in'),
        ('Prof. Karthika S', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'karthika@bitsathy.ac.in'),
        ('Prof. Mohanapriya K', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'mohanapriya@bitsathy.ac.in'),
        ('Prof. Ezhil R', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'ezhil@bitsathy.ac.in'),
        ('Prof. Pavithra G', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'pavithra@bitsathy.ac.in'),
        ('Prof. Kanimozhi A', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'kanimozhi@bitsathy.ac.in'),
        ('Prof. Nishanthini S', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'nishanthini@bitsathy.ac.in'),
        ('Prof. Lokeswari P', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'lokeswari@bitsathy.ac.in'),
        ('Prof. Gayathridevi M', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'gayathridevi@bitsathy.ac.in'),
        ('Prof. Sasithra S', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'sasithra@bitsathy.ac.in'),
        ('Prof. Saranya M K', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'saranyamk@bitsathy.ac.in'),
        ('Prof. Sindhujaa N', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', 'Assistant Professor', 'sindhujaa@bitsathy.ac.in'),
        
        # BIOMEDICAL ENGINEERING
        ('Dr Deepa D', 'BIOMEDICAL ENGINEERING', 'Professor & Head', 'deepa@bitsathy.ac.in'),
        ('Prof. Prathap M R', 'BIOMEDICAL ENGINEERING', 'Assistant Professor Level II', 'prathap@bitsathy.ac.in'),
        ('Prof. Caroline Vinnetia S', 'BIOMEDICAL ENGINEERING', 'Assistant Professor Level II', 'carolinevinnetia@bitsathy.ac.in'),
        ('Prof. Saahina S', 'BIOMEDICAL ENGINEERING', 'Assistant Professor', 'saahina@bitsathy.ac.in'),
        ('Prof. Syed Althaf S', 'BIOMEDICAL ENGINEERING', 'Assistant Professor', 'syedalthaf@bitsathy.ac.in'),
        ('Prof. Sreeniveatha P', 'BIOMEDICAL ENGINEERING', 'Assistant Professor', 'sreeniveatha@bitsathy.ac.in'),
        ('Prof. Pratheebha G', 'BIOMEDICAL ENGINEERING', 'Assistant Professor', 'pratheebha@bitsathy.ac.in'),
        
        # BIOTECHNOLOGY
        ('Dr Balakrishnaraja R', 'BIOTECHNOLOGY', 'Professor & Head', 'balakrishnaraja@bitsathy.ac.in'),
        ('Dr Kannan K P', 'BIOTECHNOLOGY', 'Professor', 'kannan@bitsathy.ac.in'),
        ('Dr Tamilselvi S', 'BIOTECHNOLOGY', 'Professor', 'tamilselvi@bitsathy.ac.in'),
        ('Dr Kirupa Sankar M', 'BIOTECHNOLOGY', 'Associate Professor', 'kirupasankar@bitsathy.ac.in'),
        ('Dr Pavithra M K S', 'BIOTECHNOLOGY', 'Associate Professor', 'pavithra@bitsathy.ac.in'),
        ('Dr Ashwin Raj S', 'BIOTECHNOLOGY', 'Assistant Professor Level III', 'ashwinraj@bitsathy.ac.in'),
        ('Dr Sandhyarani R', 'BIOTECHNOLOGY', 'Assistant Professor Level III', 'sandhyarani@bitsathy.ac.in'),
        ('Prof. Rajaseetharama S', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'rajaseetharama@bitsathy.ac.in'),
        ('Prof. Jeyavel Karthick P', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'jeyavelkarthick@bitsathy.ac.in'),
        ('Dr Suresh Chaluvadi', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'sureshchaluvadi@bitsathy.ac.in'),
        ('Prof. Sakthishobana K', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'sakthishobana@bitsathy.ac.in'),
        ('Prof. Balaji S', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'balaji@bitsathy.ac.in'),
        ('Dr Saranya S', 'BIOTECHNOLOGY', 'Assistant Professor Level II', 'saranya@bitsathy.ac.in'),
        ('Prof. Swathi G', 'BIOTECHNOLOGY', 'Assistant Professor', 'swathi@bitsathy.ac.in'),
        ('Prof. Dhivya Dharshini U', 'BIOTECHNOLOGY', 'Assistant Professor', 'dhivyadharshini@bitsathy.ac.in'),
        ('Prof. Mahima P', 'BIOTECHNOLOGY', 'Assistant Professor', 'mahima@bitsathy.ac.in'),
        ('Prof. Nandhini N', 'BIOTECHNOLOGY', 'Assistant Professor', 'nandhini@bitsathy.ac.in'),
        ('Prof. Vinodhini R T', 'BIOTECHNOLOGY', 'Assistant Professor', 'vinodhini@bitsathy.ac.in'),
        ('Prof. Shankari V', 'BIOTECHNOLOGY', 'Assistant Professor', 'shankari@bitsathy.ac.in'),
        
        # CHEMISTRY
        ('Dr Praveena R', 'CHEMISTRY', 'Head', 'praveena@bitsathy.ac.in'),
        ('Dr Vijayanand P S', 'CHEMISTRY', 'Professor', 'vijayanand@bitsathy.ac.in'),
        ('Dr Subhapriya P', 'CHEMISTRY', 'Associate Professor', 'subhapriya@bitsathy.ac.in'),
        ('Dr Kavitha C', 'CHEMISTRY', 'Associate Professor', 'kavithac@bitsathy.ac.in'),
        ('Dr Malathi M', 'CHEMISTRY', 'Associate Professor', 'malathi@bitsathy.ac.in'),
        ('Dr Sathish V', 'CHEMISTRY', 'Assistant Professor Level III', 'sathishv@bitsathy.ac.in'),
        ('Dr Muthukumar P', 'CHEMISTRY', 'Assistant Professor Level III', 'muthukumar@bitsathy.ac.in'),
        ('Dr Viswanathan G', 'CHEMISTRY', 'Assistant Professor Level III', 'viswanathan@bitsathy.ac.in'),
        
        # CIVIL ENGINEERING
        ('Dr Mohanraj A', 'CIVIL ENGINEERING', 'Head', 'mohanraj@bitsathy.ac.in'),
        ('Dr Karthiga Shenbagam N', 'CIVIL ENGINEERING', 'Associate Professor', 'karthigashenbagam@bitsathy.ac.in'),
        ('Dr Geethamani R', 'CIVIL ENGINEERING', 'Assistant Professor Level III', 'geethamani@bitsathy.ac.in'),
        ('Prof. Rajendran M', 'CIVIL ENGINEERING', 'Assistant Professor Level III', 'rajendran@bitsathy.ac.in'),
        
        # COMPUTER SCIENCE AND BUSINESS SYSTEMS
        ('Prof. Chandru K S', 'COMPUTER SCIENCE AND BUSINESS SYSTEMS', 'Assistant Professor Level III', 'chandru@bitsathy.ac.in'),
        ('Prof. Yuvalatha S', 'COMPUTER SCIENCE AND BUSINESS SYSTEMS', 'Assistant Professor Level III', 'yuvalatha@bitsathy.ac.in'),
        
        # COMPUTER SCIENCE AND DESIGN
        ('Prof. Maheshkumar K', 'COMPUTER SCIENCE AND DESIGN', 'Assistant Professor Level II', 'maheshkumar@bitsathy.ac.in'),
        ('Prof. Preethimathi L', 'COMPUTER SCIENCE AND DESIGN', 'Assistant Professor', 'preethimathi@bitsathy.ac.in'),
        
        # COMPUTER SCIENCE AND ENGINEERING
        ('Dr Sasikala D', 'COMPUTER SCIENCE AND ENGINEERING', 'Professor & Head', 'sasikala@bitsathy.ac.in'),
        ('Dr Premalatha K', 'COMPUTER SCIENCE AND ENGINEERING', 'Professor', 'premalatha@bitsathy.ac.in'),
        ('Dr Sathishkumar P', 'COMPUTER SCIENCE AND ENGINEERING', 'Professor', 'sathishkumar@bitsathy.ac.in'),
        ('Dr Sangeethaa S N', 'COMPUTER SCIENCE AND ENGINEERING', 'Professor', 'sangeethaa@bitsathy.ac.in'),
        ('Dr Rajeshkumar G', 'COMPUTER SCIENCE AND ENGINEERING', 'Professor', 'rajeshkumar@bitsathy.ac.in'),
        ('Dr Karthiga M', 'COMPUTER SCIENCE AND ENGINEERING', 'Associate Professor', 'karthiga@bitsathy.ac.in'),
        ('Dr Saranya K', 'COMPUTER SCIENCE AND ENGINEERING', 'Associate Professor', 'saranya@bitsathy.ac.in'),
        ('Dr Deepa Priya B S', 'COMPUTER SCIENCE AND ENGINEERING', 'Associate Professor', 'deepapriya@bitsathy.ac.in'),
        ('Dr Ramya R', 'COMPUTER SCIENCE AND ENGINEERING', 'Associate Professor', 'ramya@bitsathy.ac.in'),
        
        # COMPUTER TECHNOLOGY
        ('Dr Thanga Parvathi B', 'COMPUTER TECHNOLOGY', 'Professor', 'thangaparvathi@bitsathy.ac.in'),
        ('Dr Murugesan P', 'COMPUTER TECHNOLOGY', 'Assistant Professor Level III', 'murugesan@bitsathy.ac.in'),
        
        # ELECTRICAL AND ELECTRONICS ENGINEERING
        ('Dr Maheswari K T', 'ELECTRICAL AND ELECTRONICS ENGINEERING', 'Head', 'maheswari@bitsathy.ac.in'),
        ('Dr Bharani Kumar R', 'ELECTRICAL AND ELECTRONICS ENGINEERING', 'Professor', 'bhananikumar@bitsathy.ac.in'),
        ('Dr Sivaraman P', 'ELECTRICAL AND ELECTRONICS ENGINEERING', 'Professor', 'sivaraman@bitsathy.ac.in'),
        
        # ELECTRONICS AND COMMUNICATION ENGINEERING
        ('Dr Prakash S P', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'Head', 'prakashsp@bitsathy.ac.in'),
        ('Dr Harikumar R', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'Professor', 'harikumar@bitsathy.ac.in'),
        ('Dr Poongodi C', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'Professor', 'poongodi@bitsathy.ac.in'),
        ('Dr Sampoornam K P', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'Professor', 'sampoornam@bitsathy.ac.in'),
        ('Dr Perarasi T', 'ELECTRONICS AND COMMUNICATION ENGINEERING', 'Professor', 'perarasi@bitsathy.ac.in'),
        
        # ELECTRONICS AND INSTRUMENTATION ENGINEERING
        ('Dr Vairavel K S', 'ELECTRONICS AND INSTRUMENTATION ENGINEERING', 'Head', 'vairavel@bitsathy.ac.in'),
        ('Dr Ganesh Babu C', 'ELECTRONICS AND INSTRUMENTATION ENGINEERING', 'Professor', 'ganeshbabu@bitsathy.ac.in'),
        
        # FASHION TECHNOLOGY
        ('Prof. Saranya D V', 'FASHION TECHNOLOGY', 'Head', 'saranyadv@bitsathy.ac.in'),
        ('Dr Mohan Bharathi C', 'FASHION TECHNOLOGY', 'Assistant Professor Level III', 'mohanbharathi@bitsathy.ac.in'),
        
        # FOOD TECHNOLOGY
        ('Prof. Gowrishankar L', 'FOOD TECHNOLOGY', 'Head', 'gowrishankar@bitsathy.ac.in'),
        ('Dr Tna Arunasree', 'FOOD TECHNOLOGY', 'Assistant Professor Level II', 'arunasree@bitsathy.ac.in'),
        
        # HUMANITIES
        ('Dr Ajai A', 'HUMANITIES', 'Head', 'ajai@bitsathy.ac.in'),
        ('Dr Nandhini A P', 'HUMANITIES', 'Assistant Professor', 'nandhiniap@bitsathy.ac.in'),
        ('Dr Gayathri G M', 'HUMANITIES', 'Assistant Professor', 'gayathrigm@bitsathy.ac.in'),
        
        # INFORMATION SCIENCE AND ENGINEERING
        ('Dr Anandakumar K', 'INFORMATION SCIENCE AND ENGINEERING', 'Assistant Professor Level III', 'anandakumar@bitsathy.ac.in'),
        ('Prof. Pandiyan M', 'INFORMATION SCIENCE AND ENGINEERING', 'Assistant Professor Level III', 'pandiyan@bitsathy.ac.in'),
        
        # INFORMATION TECHNOLOGY
        ('Dr Naveena S', 'INFORMATION TECHNOLOGY', 'Head', 'naveena@bitsathy.ac.in'),
        ('Dr Palanisamy C', 'INFORMATION TECHNOLOGY', 'Professor', 'palanisamy@bitsathy.ac.in'),
        ('Dr Sadhasivam N', 'INFORMATION TECHNOLOGY', 'Professor', 'sadhasivam@bitsathy.ac.in'),
        ('Dr Paarivallal Ra.', 'INFORMATION TECHNOLOGY', 'Associate Professor', 'paarivallal@bitsathy.ac.in'),
        ('Dr Sathis Kumar K', 'INFORMATION TECHNOLOGY', 'Associate Professor', 'sathiskumar@bitsathy.ac.in'),
        
        # MATHEMATICS
        ('Dr Parimala M', 'MATHEMATICS', 'Head', 'parimala@bitsathy.ac.in'),
        ('Dr Thulasimani T', 'MATHEMATICS', 'Associate Professor', 'thulasimani@bitsathy.ac.in'),
        ('Dr Indirani C', 'MATHEMATICS', 'Assistant Professor Level III', 'indirani@bitsathy.ac.in'),
        ('Dr Vinothini V R', 'MATHEMATICS', 'Assistant Professor Level III', 'vinothini@bitsathy.ac.in'),
        
        # MECHANICAL ENGINEERING
        ('Dr Ravi Kumar M', 'MECHANICAL ENGINEERING', 'Professor & Head', 'ravikumar@bitsathy.ac.in'),
        ('Dr Sivakumar K', 'MECHANICAL ENGINEERING', 'Senior Professor', 'sivakumar@bitsathy.ac.in'),
        ('Dr Muthukumar K', 'MECHANICAL ENGINEERING', 'Adjunct Faculty', 'muthukumar@bitsathy.ac.in'),
        ('Dr Senthilkumar G', 'MECHANICAL ENGINEERING', 'Professor', 'senthilkumar@bitsathy.ac.in'),
        
        # MECHATRONICS ENGINEERING
        ('Dr Senthil Kumar K L', 'MECHATRONICS ENGINEERING', 'Professor & Head', 'senthilkumarkl@bitsathy.ac.in'),
        ('Dr Jegadheeswaran S', 'MECHATRONICS ENGINEERING', 'Professor', 'jegadheeswaran@bitsathy.ac.in'),
        
        # PHYSICS
        ('Dr Sadasivam K', 'PHYSICS', 'Professor & Head', 'sadasivam@bitsathy.ac.in'),
        ('Dr Vijayakumar V N', 'PHYSICS', 'Professor', 'vijayakumar@bitsathy.ac.in'),
        ('Dr Pongali Sathya Prabu N', 'PHYSICS', 'Associate Professor', 'pongali@bitsathy.ac.in'),
        ('Dr Ashokan S', 'PHYSICS', 'Assistant Professor Level III', 'ashokan@bitsathy.ac.in'),
        
        # SCHOOL OF MANAGEMENT STUDIES
        ('Dr Murugappan S', 'SCHOOL OF MANAGEMENT STUDIES', 'Professor & Director', 'murugappan@bitsathy.ac.in'),
        ('Dr Adhinarayanan B', 'SCHOOL OF MANAGEMENT STUDIES', 'Associate Professor', 'adhinarayanan@bitsathy.ac.in'),
        
        # TEXTILE TECHNOLOGY
        ('Dr Janarthanan M', 'TEXTILE TECHNOLOGY', 'Head', 'janarthanan@bitsathy.ac.in'),
        ('Prof. Mounika S', 'TEXTILE TECHNOLOGY', 'Assistant Professor', 'mounika@bitsathy.ac.in'),
    ]
    
    for faculty in faculty_list:
        cursor.execute('''
        INSERT OR IGNORE INTO instructors (name, department, designation, email)
        VALUES (?, ?, ?, ?)
        ''', (faculty[0], faculty[1], faculty[2], faculty[3]))

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
        INSERT OR IGNORE INTO courses (course_code, course_name, department, year, semester, period, faculty_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', course)

def insert_sample_users(cursor):
    users = [
        ('admin@bitsathy.ac.in', 'admin123', 'admin', 'System Administrator', None),
        ('rahul.cs23@bitsathy.ac.in', 'password123', 'student', 'Rahul Kumar', 'COMPUTER SCIENCE AND ENGINEERING'),
        ('priya.it23@bitsathy.ac.in', 'password123', 'student', 'Priya Srinivasan', 'INFORMATION TECHNOLOGY'),
        ('ankit.aids23@bitsathy.ac.in', 'password123', 'student', 'Ankit Sharma', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE'),
        ('divya.ece23@bitsathy.ac.in', 'password123', 'student', 'Divya Lakshmi', 'ELECTRONICS AND COMMUNICATION ENGINEERING'),
        ('karthik.mech23@bitsathy.ac.in', 'password123', 'student', 'Karthik Raj', 'MECHANICAL ENGINEERING'),
        ('sneha.civil23@bitsathy.ac.in', 'password123', 'student', 'Sneha Priya', 'CIVIL ENGINEERING'),
        ('dr.sasikala@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Sasikala D', 'COMPUTER SCIENCE AND ENGINEERING'),
        ('dr.premalatha@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Premalatha K', 'COMPUTER SCIENCE AND ENGINEERING'),
        ('dr.naveena@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Naveena S', 'INFORMATION TECHNOLOGY'),
        ('dr.gomathi@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Gomathi R', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE'),
        ('dr.ravikumar@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Ravi Kumar M', 'MECHANICAL ENGINEERING'),
        ('dr.prakash@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Prakash S P', 'ELECTRONICS AND COMMUNICATION ENGINEERING'),
        ('dr.parimala@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Parimala M', 'MATHEMATICS'),
        ('dr.sadasivam@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Sadasivam K', 'PHYSICS'),
        ('dr.praveena@bitsathy.ac.in', 'faculty123', 'faculty', 'Dr Praveena R', 'CHEMISTRY'),
    ]
    
    for user in users:
        # Check if user already exists
        cursor.execute('SELECT user_id FROM users WHERE email = ?', (user[0],))
        existing = cursor.fetchone()
        
        if not existing:
            cursor.execute('''
            INSERT INTO users (email, password, role, full_name, department)
            VALUES (?, ?, ?, ?, ?)
            ''', (user[0], user[1], user[2], user[3], user[4]))
            
            user_id = cursor.lastrowid
            
            if user[2] == 'student':
                reg_no = f"BIT{user[0].split('.')[0][:3].upper()}{user_id}"
                cursor.execute('''
                INSERT INTO students (user_id, reg_no, joining_year, current_year, is_hosteler)
                VALUES (?, ?, ?, ?, ?)
                ''', (user_id, reg_no, 2023, 2, 1))
            elif user[2] == 'faculty':
                cursor.execute('''
                INSERT INTO faculty (user_id, faculty_code, designation, join_date)
                VALUES (?, ?, ?, ?)
                ''', (user_id, f'FAC{user_id}', 'Professor', '2020-06-01'))

if __name__ == '__main__':
    init_database()
    print("Database initialized successfully with all BIT faculty members!")