import os
import json
import uuid
import random
import time
import PyPDF2
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_caching import Cache
from flask_session import Session
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
import io
import sys
import PIL.Image

# 1. Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

# 2. Load environment variables
load_dotenv()

# --- MODEL PRIORITY LIST ---
# The system will try these models in this specific order.
MODELS_TO_TRY = [
    "models/gemini-1.5-flash",       # <--- Priority 1: Best balance of speed & quota
    "models/gemini-flash-latest",    # <--- Priority 2: Backup alias
    "models/gemini-1.5-flash-8b",    # <--- Priority 3: High speed / Low cost
    "models/gemini-2.0-flash-exp"    # <--- Priority 4: Experimental (Use last due to limit:0 issues)
]

# --- 🚀 SMART API KEY MANAGEMENT ---
def get_all_api_keys():
    """Collects all available API keys from environment variables."""
    api_keys = []
    # 1. Check standard key
    if os.getenv("GOOGLE_API_KEY"):
        api_keys.append(os.getenv("GOOGLE_API_KEY"))
    
    # 2. Check numbered keys (GOOGLE_API_KEY_1, _2, etc.)
    i = 1
    while True:
        key = os.getenv(f"GOOGLE_API_KEY_{i}")
        if not key:
            break
        api_keys.append(key)
        i += 1
        
    return api_keys

def initialize_any_key():
    """Initializes Gemini with the first available key so the app starts."""
    keys = get_all_api_keys()
    if keys:
        genai.configure(api_key=keys[0])
        return True
    return False

# --- 🛡️ ULTIMATE AI CALLER: SEQUENTIAL TRY ---
def generate_with_retry(model, prompt_parts):
    """
    1. Iterates through MODELS in priority order.
    2. For each model, iterates through ALL AVAILABLE KEYS.
    3. Only moves to the next model if ALL keys fail for the current one.
    """
    all_keys = get_all_api_keys()
    
    if not all_keys:
        raise Exception("❌ NO API KEYS FOUND. Please add GOOGLE_API_KEY to Render.")

    # LOOP 1: Go through Models in your priority order
    for model_name in MODELS_TO_TRY:
        print(f"\n🔄 PRIORITY CHECK: Attempting Model '{model_name}'...")
        
        # LOOP 2: Go through EVERY single key for this model
        for key_index, key in enumerate(all_keys):
            try:
                # Configure with the specific key for this attempt
                genai.configure(api_key=key)
                
                # Set up the model
                active_model = genai.GenerativeModel(model_name)
                
                # Attempt generation
                # print(f"   Key #{key_index+1}: Connecting...")
                response = active_model.generate_content(prompt_parts)
                
                # If we get here, it WORKED! Return immediately.
                print(f"   ✅ SUCCESS! Connected to {model_name} using Key #{key_index+1}")
                return response
                
            except Exception as e:
                error_msg = str(e)
                # print(f"   ⚠️ Key #{key_index+1} failed: {error_msg}")
                
                # If it's a 404 (Model Not Found), this model won't work with ANY key.
                if "404" in error_msg or "not found" in error_msg.lower():
                    print(f"   🚫 {model_name} is not available. Skipping to next model.")
                    break # Break inner loop -> Go to next model
                
                # If it's a Quota error (429), we just continue to the next key in the loop.
                continue

        # If we finish the key loop, it means this model failed on ALL keys.
        print(f"❌ Model '{model_name}' exhausted all keys. Switching to next model...\n")

    # If we exit both loops, we truly have no options left.
    raise Exception("❌ SYSTEM FAILURE: All models and all keys were exhausted.")

# Initialize startup
initialize_any_key()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "skillbridge-hackathon-secret-2024")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True

CORS(app)
Session(app)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# ==========================================
# 🌍 UNIVERSAL JOB ROLES DATABASE (FULL)
# ==========================================
JOB_ROLES = {
    # === SOFTWARE & IT ===
    "Frontend Developer": { "category": "IT & Software", "skills": ["React", "Vue.js", "Angular", "JavaScript", "TypeScript", "HTML5", "CSS3", "Tailwind", "Redux", "Webpack"], "salary_range": "$70k - $140k", "experience": "1-5 Years" },
    "Backend Developer": { "category": "IT & Software", "skills": ["Python", "Java", "Node.js", "Go", "Django", "Spring Boot", "PostgreSQL", "MongoDB", "Redis", "Docker"], "salary_range": "$80k - $150k", "experience": "2-6 Years" },
    "Full Stack Developer": { "category": "IT & Software", "skills": ["MERN Stack", "Next.js", "Python", "SQL", "NoSQL", "AWS", "REST APIs", "GraphQL", "Git", "CI/CD"], "salary_range": "$90k - $160k", "experience": "3-7 Years" },
    "DevOps Engineer": { "category": "IT & Software", "skills": ["AWS", "Azure", "Kubernetes", "Docker", "Jenkins", "Terraform", "Ansible", "Linux", "Bash Scripting"], "salary_range": "$100k - $170k", "experience": "3-8 Years" },
    "Mobile App Developer": { "category": "IT & Software", "skills": ["Flutter", "React Native", "Swift", "Kotlin", "iOS", "Android", "Firebase", "Dart"], "salary_range": "$80k - $145k", "experience": "2-5 Years" },
    "Cybersecurity Analyst": { "category": "IT & Software", "skills": ["Network Security", "Penetration Testing", "SIEM", "Firewalls", "Python", "Linux", "Risk Assessment"], "salary_range": "$90k - $160k", "experience": "2-6 Years" },
    "Data Scientist": { "category": "Data & AI", "skills": ["Python", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "SQL", "Statistics"], "salary_range": "$100k - $180k", "experience": "2-5 Years" },
    "Machine Learning Engineer": { "category": "Data & AI", "skills": ["Python", "TensorFlow", "Keras", "NLP", "Computer Vision", "MLOps", "AWS SageMaker"], "salary_range": "$110k - $200k", "experience": "3-7 Years" },

    # === CORE ENGINEERING ===
    "Civil Engineer": { "category": "Core Engineering", "skills": ["AutoCAD", "Civil 3D", "STAAD Pro", "Structural Analysis", "Project Management", "Surveying", "Revit"], "salary_range": "$65k - $120k", "experience": "2-6 Years" },
    "Mechanical Engineer": { "category": "Core Engineering", "skills": ["SolidWorks", "AutoCAD", "ANSYS", "Thermodynamics", "Fluid Mechanics", "GD&T", "Manufacturing"], "salary_range": "$70k - $130k", "experience": "2-6 Years" },
    "Electrical Engineer": { "category": "Core Engineering", "skills": ["Circuit Design", "PCB Design", "MATLAB", "Simulink", "PLC Programming", "AutoCAD Electrical", "Power Systems"], "salary_range": "$75k - $135k", "experience": "2-6 Years" },
    "Chemical Engineer": { "category": "Core Engineering", "skills": ["Process Simulation", "Aspen Plus", "Thermodynamics", "Reaction Engineering", "Safety Standards", "MATLAB"], "salary_range": "$75k - $140k", "experience": "2-6 Years" },

    # === BUSINESS & MANAGEMENT ===
    "Product Manager": { "category": "Business", "skills": ["Product Strategy", "Agile/Scrum", "User Research", "Roadmapping", "JIRA", "Data Analysis", "Stakeholder Mgmt"], "salary_range": "$110k - $190k", "experience": "4-8 Years" },
    "Project Manager": { "category": "Business", "skills": ["PMP", "Agile", "Scrum", "Risk Management", "Budgeting", "MS Project", "Communication"], "salary_range": "$90k - $160k", "experience": "3-7 Years" },
    "Business Analyst": { "category": "Business", "skills": ["SQL", "Excel", "Requirements Gathering", "Process Modeling", "UML", "Tableau", "Stakeholder Analysis"], "salary_range": "$75k - $125k", "experience": "2-5 Years" },
    "Marketing Manager": { "category": "Business", "skills": ["Digital Marketing", "SEO", "Content Strategy", "Google Analytics", "Social Media", "Email Marketing"], "salary_range": "$70k - $140k", "experience": "3-7 Years" },
    "HR Manager": { "category": "Business", "skills": ["Recruitment", "Employee Relations", "HRIS", "Labor Laws", "Performance Mgmt", "Onboarding"], "salary_range": "$70k - $130k", "experience": "4-8 Years" },
    "Sales Representative": { "category": "Business", "skills": ["CRM", "Negotiation", "Lead Generation", "Communication", "Cold Calling", "Salesforce"], "salary_range": "$50k - $100k", "experience": "1-4 Years" },

    # === FINANCE ===
    "Financial Analyst": { "category": "Finance", "skills": ["Financial Modeling", "Excel (Advanced)", "Forecasting", "Valuation", "SAP", "Accounting"], "salary_range": "$70k - $120k", "experience": "2-5 Years" },
    "Investment Banker": { "category": "Finance", "skills": ["M&A", "LBO Modeling", "Valuation", "Due Diligence", "Capital Markets", "Pitchbooks"], "salary_range": "$120k - $250k+", "experience": "2-5 Years" },
    "Chartered Accountant": { "category": "Finance", "skills": ["Auditing", "Taxation", "IFRS/GAAP", "Financial Reporting", "Internal Controls", "Compliance"], "salary_range": "$75k - $150k", "experience": "3-6 Years" },

    # === HEALTHCARE & SCIENCE ===
    "General Practitioner": { "category": "Healthcare", "skills": ["Diagnosis", "Patient Care", "Medical Records (EMR)", "Pharmacology", "Clinical Procedures"], "salary_range": "$150k - $250k", "experience": "Residency+" },
    "Registered Nurse": { "category": "Healthcare", "skills": ["Patient Assessment", "Critical Care", "IV Therapy", "Medication Admin", "BLS/ACLS", "Compassion"], "salary_range": "$60k - $110k", "experience": "Licensure" },
    "Pharmacist": { "category": "Healthcare", "skills": ["Pharmacology", "Dispensing", "Patient Counseling", "Drug Interactions", "Inventory Mgmt"], "salary_range": "$110k - $140k", "experience": "PharmD" },
    "Biologist": { "category": "Science", "skills": ["Lab Techniques", "Data Analysis", "Microscopy", "Genetics", "Research", "PCR"], "salary_range": "$55k - $95k", "experience": "2-5 Years" },
    "Chemist": { "category": "Science", "skills": ["HPLC", "Organic Chemistry", "Lab Safety", "Spectroscopy", "Analytical Chemistry"], "salary_range": "$60k - $100k", "experience": "2-5 Years" },

    # === LEGAL ===
    "Corporate Lawyer": { "category": "Legal", "skills": ["Contract Law", "Mergers & Acquisitions", "Corporate Governance", "Negotiation", "Legal Drafting"], "salary_range": "$120k - $220k", "experience": "3-7 Years" },
    "Litigation Attorney": { "category": "Legal", "skills": ["Trial Advocacy", "Legal Research", "Depositions", "Civil Procedure", "Case Management", "Evidence"], "salary_range": "$100k - $190k", "experience": "3-7 Years" },

    # === CREATIVE, ARTS & EDUCATION ===
    "Graphic Designer": { "category": "Creative", "skills": ["Adobe Photoshop", "Illustrator", "InDesign", "Typography", "Branding", "Layout Design"], "salary_range": "$50k - $90k", "experience": "2-5 Years" },
    "UI/UX Designer": { "category": "Creative", "skills": ["Figma", "Sketch", "Wireframing", "Prototyping", "User Research", "Interaction Design"], "salary_range": "$80k - $140k", "experience": "2-6 Years" },
    "Content Writer": { "category": "Creative", "skills": ["SEO", "Copywriting", "Editing", "Research", "Blogging", "CMS"], "salary_range": "$45k - $80k", "experience": "1-4 Years" },
    "Teacher (K-12)": { "category": "Education", "skills": ["Curriculum Design", "Classroom Mgmt", "Lesson Planning", "Student Assessment", "Communication"], "salary_range": "$45k - $85k", "experience": "Certification" },
    "University Professor": { "category": "Education", "skills": ["Research", "Lecturing", "Grant Writing", "Mentoring", "Academic Publishing"], "salary_range": "$80k - $160k", "experience": "PhD" },
    "Architect": { "category": "Creative", "skills": ["AutoCAD", "Revit", "SketchUp", "Building Codes", "Sustainable Design", "3D Rendering"], "salary_range": "$65k - $115k", "experience": "3-7 Years" }
}

def get_categories():
    categories = set()
    for role_data in JOB_ROLES.values():
        categories.add(role_data.get('category', 'Other'))
    return sorted(list(categories))

def extract_text_from_file(file):
    filename = file.filename.lower()
    if filename.endswith('.pdf'):
        try:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")
    elif filename.endswith(('.docx', '.doc')):
        try:
            import docx
            doc = docx.Document(file)
            return '\n'.join([para.text for para in doc.paragraphs])
        except ImportError:
            return "Error: python-docx library not installed."
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"
    elif filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
        try:
            image = PIL.Image.open(file)
            prompt = "Analyze this image of a resume and extract all the text content from it verbatim. Organize it clearly."
            print("📷 Image detected. Asking Gemini to read it...")
            
            # Using our Robust Retry Logic for OCR as well!
            response = generate_with_retry(None, [prompt, image])
            return response.text
        except Exception as e:
            print(f"❌ Image OCR Error: {e}")
            raise ValueError(f"Error reading Image: {str(e)}")
    else:
        raise ValueError("Unsupported file format. Please upload PDF, DOCX, or Image (JPG/PNG).")

def detect_resume_category(resume_text):
    resume_lower = resume_text.lower()
    counts = {cat: 0 for cat in get_categories()}
    for role, data in JOB_ROLES.items():
        cat = data['category']
        if role.lower() in resume_lower: counts[cat] += 3
        for skill in data['skills']:
            if skill.lower() in resume_lower: counts[cat] += 1
    if max(counts.values()) > 0: return max(counts, key=counts.get)
    return "General"

def clean_json_text(text):
    text = text.strip()
    if "```json" in text: text = text.split("```json")[1]
    elif "```" in text: text = text.split("```")[1]
    if "```" in text: text = text.split("```")[0]
    return text.strip()

def get_ai_feedback(resume_text, role, jd_text=None):
    role_info = JOB_ROLES.get(role, {})
    role_category = role_info.get('category', 'General')
    resume_category = detect_resume_category(resume_text)
    
    mismatch_warning = ""
    if resume_category != role_category and resume_category != "General":
        mismatch_warning = f"Resume seems to be {resume_category}-focused, but you applied for a {role_category} role ({role})."
    
    prompt = f"""You are an expert Career Coach. Analyze this resume for a {role} position ({role_category}).
    RESUME: {resume_text[:6000]}
    CONTEXT: {mismatch_warning}
    
    Return a VALID JSON OBJECT.
    JSON Schema:
    {{
        "compatibility_score": (integer 0-100),
        "score_explanation": (string),
        "skill_analysis": {{
            "present": [(list string)],
            "missing": [(list string)],
            "match_percentage": (integer 0-100)
        }},
        "critical_gaps": [
            {{"gap": (string), "priority": "High/Medium", "impact": (string)}}
        ],
        "professional_development": [
            {{"title": (string), "provider": (string), "type": "Course/Project", "duration": (string), "link": (string)}}
        ],
        "youtube_recommendations": [
            {{"title": (string), "link": (string)}}
        ],
        "interview_questions": [(list string)],
        "resume_improvements": [
            {{"current": (string), "improved": (string), "reason": (string)}}
        ],
        "career_roadmap": {{
            "short_term": (string), "medium_term": (string), "long_term": (string)
        }},
        "salary_benchmark": (string),
        "final_assessment": (string),
        "confidence_level": "High/Medium"
    }}
    """
    try:
        print(f"📝 Sending analysis request...")
        
        # Call the ROBUST Sequential Logic
        response = generate_with_retry(None, prompt)
        
        try:
            analysis = json.loads(clean_json_text(response.text))
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            return generate_fallback_analysis(resume_text, role, role_category, resume_category)
        
        analysis['analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        analysis['role_applied'] = role
        analysis['industry_category'] = role_category
        analysis['detected_resume_category'] = resume_category
        if mismatch_warning: analysis['mismatch_warning'] = mismatch_warning
        print(f"✅ Analysis successful: {analysis.get('compatibility_score')}%")
        return analysis
    except Exception as e:
        print(f"❌ Final Analysis Error: {e}")
        return generate_fallback_analysis(resume_text, role, role_category, resume_category)

def generate_fallback_analysis(resume_text, role, category, detected_category=None):
    role_info = JOB_ROLES.get(role, {})
    role_skills = role_info.get('skills', [])
    resume_lower = resume_text.lower()
    present = [s for s in role_skills if s.lower() in resume_lower]
    missing = [s for s in role_skills if s.lower() not in resume_lower]
    match = int((len(present) / max(len(role_skills), 1)) * 100) if role_skills else 0
    
    return {
        "compatibility_score": match,
        "score_explanation": "Basic keyword analysis (AI unavailable).",
        "skill_analysis": { "present": present, "missing": missing, "match_percentage": match },
        "critical_gaps": [{"gap": s, "priority": "High", "impact": "Missing skill"} for s in missing[:3]],
        "professional_development": [{"title": f"Learn {missing[0] if missing else role}", "provider": "YouTube", "type": "Self-study", "duration": "Variable", "link": f"https://www.youtube.com/results?search_query=Learn+{missing[0] if missing else role}"}],
        "youtube_recommendations": [{"title": f"{role} Crash Course", "link": f"https://www.youtube.com/results?search_query={role}+crash+course"}],
        "interview_questions": ["Tell me about yourself.", "Strengths?", "Weaknesses?"],
        "resume_improvements": [{"current": "N/A", "improved": "N/A", "reason": "AI unavailable"}],
        "career_roadmap": { "short_term": "Learn basics", "medium_term": "Build projects", "long_term": "Senior role" },
        "salary_benchmark": role_info.get('salary_range', 'N/A'),
        "final_assessment": "Try again later for full AI analysis.",
        "confidence_level": "Low",
        "analysis_date": datetime.now().strftime('%Y-%m-%d')
    }

@app.route('/')
def home():
    categories = get_categories()
    return render_template('index.html', roles=JOB_ROLES.keys(), role_data=JOB_ROLES, categories=categories)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files['resume']
    role = request.form.get('role', '')
    jd_text = request.form.get('jd', '')
    
    if not role or file.filename == '': return jsonify({"error": "Missing data"}), 400
    
    try:
        resume_text = extract_text_from_file(file)
        if len(resume_text.strip()) < 50: return render_template('error.html', error="Resume empty/unreadable", suggestion="Upload clear file")
        session['analysis_id'] = str(uuid.uuid4())
        analysis = get_ai_feedback(resume_text, role, jd_text)
        session['analysis_data'] = analysis
        session['role'] = role
        return render_template('result.html', analysis=analysis, role=role, role_info=JOB_ROLES.get(role, {}))
    except Exception as e:
        print(f"❌ Error: {e}")
        return render_template('error.html', error=str(e), suggestion="Try again")

@app.route('/demo')
def demo():
    return render_template('result.html', analysis=generate_fallback_analysis("Demo", "Frontend Developer", "Technology"), role="Frontend Developer", role_info=JOB_ROLES["Frontend Developer"], is_demo=True)

@app.route('/download-report')
def download_report():
    analysis = session.get('analysis_data')
    if not analysis: return "No data", 400
    report_text = f"SkillBridge Report\nRole: {session.get('role')}\nScore: {analysis.get('compatibility_score')}%"
    return send_file(io.BytesIO(report_text.encode()), as_attachment=True, download_name="report.txt", mimetype='text/plain')

@app.route('/api/categories')
def get_categories_api():
    return jsonify({"categories": get_categories(), "roles": JOB_ROLES})

@app.errorhandler(404)
def not_found(e): return render_template('error.html', error="Page not found"), 404

if __name__ == '__main__':
    print("\n" + "="*60)
    print(f"🚀 SKILLBRIDGE AI - FINAL SEQUENTIAL LOGIC ACTIVATED")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)