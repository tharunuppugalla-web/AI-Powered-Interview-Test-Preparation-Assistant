import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "ai_prep_final_v2_2026"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview_assistant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Resume Storage Configuration
UPLOAD_FOLDER = 'uploads/resumes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

with app.app_context():
    db.create_all()

# --- AUTHENTICATION ROUTES ---

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    user_exists = User.query.filter_by(email=email).first()
    if user_exists:
        return redirect(url_for('login_page'))

    hashed_pw = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
    new_user = User(full_name=request.form.get('full_name'), mobile=request.form.get('mobile'),
                    email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    session['user_name'] = new_user.full_name
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(email=request.form.get('email')).first()
    if user and bcrypt.check_password_hash(user.password, request.form.get('password')):
        session['user_name'] = user.full_name
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- CORE APPLICATION FLOW ---

@app.route('/dashboard')
def dashboard():
    if 'user_name' not in session: return redirect(url_for('login_page'))
    return render_template('dashboard.html', name=session['user_name'])

@app.route('/setup/<domain>')
def setup_page(domain):
    if 'user_name' not in session: return redirect(url_for('login_page'))
    return render_template('setup.html', domain=domain)

@app.route('/analyze_resume', methods=['POST'])
def analyze_resume():
    if 'user_name' not in session: return redirect(url_for('login_page'))
    file = request.files.get('resume')
    if file:
        filename = secure_filename(f"{session['user_name']}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    session['domain'] = request.form.get('domain')
    session['selected_role'] = request.form.get('job_role')
    session['difficulty'] = request.form.get('level')

    return render_template('ats_checker.html', score=82, domain=session.get('domain'), suggestions=[
        {"type": "Action", "text": "Use more power verbs like 'Executed' or 'Optimized'."},
        {"type": "Keywords", "text": f"Add skills specific to {session['selected_role']}"}
    ])

# --- MOCK TEST LOGIC ---

@app.route('/mock_test')
def mock_test():
    if 'user_name' not in session: 
        return redirect(url_for('login_page'))
    return render_template('mock_test.html', domain=session.get('domain', 'IT'))

@app.route('/get_test_questions')
def get_test_questions():
    test_data = {
        "aptitude": [
            {"question": "A train 150m long passes a pole in 15 seconds. Speed in km/hr?", "options": ["30", "36", "45", "50"], "answer": "36"},
            {"question": "The average of first 50 natural numbers is?", "options": ["25.25", "25.5", "25", "26"], "answer": "25.5"},
            {"question": "If 20% of a = b, then b% of 20 is the same as:", "options": ["4% of a", "5% of a", "20% of a", "None"], "answer": "4% of a"},
            {"question": "Square root of 0.0009 is?", "options": ["0.03", "0.003", "0.3", "0.0003"], "answer": "0.03"},
            {"question": "Find the odd one out: 3, 5, 11, 14, 17, 21", "options": ["14", "17", "21", "3"], "answer": "14"},
            {"question": "100 + 50 * 2 = ?", "options": ["300", "200", "250", "150"], "answer": "200"},
            {"question": "HCF of 12, 18, 24 is?", "options": ["3", "4", "6", "12"], "answer": "6"},
            {"question": "Next number: 1, 4, 9, 16, 25, ?", "options": ["30", "35", "36", "49"], "answer": "36"},
            {"question": "Area of circle with radius 7 (π=22/7)?", "options": ["154", "44", "49", "144"], "answer": "154"},
            {"question": "Convert 0.75 to percentage.", "options": ["7.5%", "75%", "0.75%", "750%"], "answer": "75%"}
        ],
        "verbal": [
            {"question": "Synonym of 'Fragile'?", "options": ["Strong", "Weak", "Delicate", "Flexible"], "answer": "Delicate"},
            {"question": "Antonym of 'Gigantic'?", "options": ["Huge", "Small", "Tiny", "Short"], "answer": "Tiny"},
            {"question": "Correct spelling?", "options": ["Occurrence", "Occurence", "Ocurrence", "Occurance"], "answer": "Occurrence"},
            {"question": "Fill: She __ to the gym every day.", "options": ["go", "going", "goes", "gone"], "answer": "goes"},
            {"question": "A person who writes books is an:", "options": ["Actor", "Author", "Artist", "Architect"], "answer": "Author"},
            {"question": "Opposite of 'Arrival'?", "options": ["Departure", "Exit", "Coming", "Stay"], "answer": "Departure"},
            {"question": "Idiom: 'Piece of cake' means?", "options": ["Delicious", "Very easy", "Hard work", "Something sweet"], "answer": "Very easy"},
            {"question": "Select the verb: 'He runs fast.'", "options": ["He", "runs", "fast", "None"], "answer": "runs"},
            {"question": "Synonym of 'Benevolent'?", "options": ["Cruel", "Kind", "Rich", "Smart"], "answer": "Kind"},
            {"question": "Plural of 'Mouse'?", "options": ["Mouses", "Mice", "Micey", "Mice-s"], "answer": "Mice"}
        ],
        "it_domain": [
            {"question": "Main memory of computer?", "options": ["HDD", "RAM", "ROM", "SSD"], "answer": "RAM"},
            {"question": "HTTP stands for?", "options": ["Hyper Transfer Text Protocol", "HyperText Transfer Protocol", "High Text Transfer Protocol", "None"], "answer": "HyperText Transfer Protocol"},
            {"question": "Father of C Language?", "options": ["Dennis Ritchie", "James Gosling", "Guido van Rossum", "Bjarne Stroustrup"], "answer": "Dennis Ritchie"},
            {"question": "Which is not a programming language?", "options": ["Python", "HTML", "Java", "C++"], "answer": "HTML"},
            {"question": "1 Byte equals?", "options": ["4 bits", "8 bits", "16 bits", "32 bits"], "answer": "8 bits"},
            {"question": "Standard port for HTTP?", "options": ["21", "25", "80", "443"], "answer": "80"},
            {"question": "SQL stands for?", "options": ["Simple Query Language", "Structured Query Language", "Sequential Query Language", "None"], "answer": "Structured Query Language"},
            {"question": "Extension of Python file?", "options": [".py", ".pt", ".ph", ".python"], "answer": ".py"},
            {"question": "Which is an Operating System?", "options": ["Chrome", "Linux", "Word", "Oracle"], "answer": "Linux"},
            {"question": "Data structure following LIFO?", "options": ["Queue", "Stack", "Tree", "Array"], "answer": "Stack"}
        ],
        "non_it_domain": [
            {"question": "Who is often called the Father of Management?", "options": ["Peter Drucker", "Henry Fayol", "F.W. Taylor", "Elon Musk"], "answer": "F.W. Taylor"},
            {"question": "4 P's of Marketing include Product, Price, Place and?", "options": ["Promotion", "People", "Process", "Profit"], "answer": "Promotion"},
            {"question": "SWOT analysis: 'S' stands for?", "options": ["Safety", "Strength", "Smart", "Salary"], "answer": "Strength"},
            {"question": "Full form of HR?", "options": ["Human Resources", "High Relations", "Home Room", "Heavy Recruitment"], "answer": "Human Resources"},
            {"question": "Which is a liability?", "options": ["Cash", "Machinery", "Bank Loan", "Inventory"], "answer": "Bank Loan"},
            {"question": "Process of hiring people is?", "options": ["Selection", "Recruitment", "Orientation", "Training"], "answer": "Recruitment"},
            {"question": "CEO stands for?", "options": ["Chief Executive Officer", "Chief Energy Officer", "Core Executive Officer", "None"], "answer": "Chief Executive Officer"},
            {"question": "A planned spending sheet is a:", "options": ["Ledger", "Balance Sheet", "Budget", "Invoice"], "answer": "Budget"},
            {"question": "Which is a leadership style?", "options": ["Autocratic", "Systematic", "Mathematical", "Logical"], "answer": "Autocratic"},
            {"question": "Exchange of goods for money is?", "options": ["Barter", "Sales", "Purchase", "Audit"], "answer": "Sales"}
        ]
    }
    return jsonify(test_data)

@app.route('/submit_test', methods=['POST'])
def submit_test():
    session['test_results'] = request.json # {aptitude: X, verbal: Y, domain: Z}
    return jsonify({"status": "success", "redirect": url_for('final_results', type='test')})

# --- VOICE INTERVIEW LOGIC ---

@app.route('/interview')
def interview_room():
    if 'user_name' not in session: return redirect(url_for('login_page'))
    # Ensure this list is not empty!
    questions = ["Tell me about yourself.", "What are your strengths?"] 
    return render_template('interview.html', questions=questions)

@app.route('/submit_interview', methods=['POST'])
def submit_interview():
    session['interview_results'] = request.json.get('responses')
    return jsonify({"status": "success", "redirect": url_for('final_results', type='interview')})

# --- UNIFIED RESULTS PAGE ---

@app.route('/results')
def final_results():
    if 'user_name' not in session: 
        return redirect(url_for('login_page'))
    
    res_type = request.args.get('type', 'interview')
    
    if res_type == 'test':
        details = session.get('test_results', {})
        percentage = int(sum(details.values()) / 3) if details else 0
    else:
        # Get data with a fallback to an empty list
        raw_data = session.get('interview_results', [])
        
        processed = []
        # Keywords to look for in answers to award points
        keywords = ["experience", "skill", "team", "project", "learned", "challenge", "goal"]
        
        total_score = 0
        for item in raw_data:
            ans = item.get('answer', "").lower()
            # Scoring: 5 points for length, up to 5 points for keywords
            score = 5 if len(ans.split()) > 10 else 2
            score += min(sum(1 for k in keywords if k in ans), 5)
            
            total_score += score
            processed.append({
                "question": item.get('question', "N/A"),
                "answer": item.get('answer', "No response captured."),
                "score": score
            })
        
        # Calculate percentage based on 10 questions (max 100 points)
        percentage = min(total_score, 100)
        details = processed

    return render_template('results.html', 
                           name=session['user_name'], 
                           type=res_type, 
                           percentage=int(percentage), 
                           details=details)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    app.run(debug=True)