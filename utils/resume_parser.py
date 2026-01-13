import re
import PyPDF2
from docx import Document
from datetime import datetime

class ResumeParser:
    def __init__(self, text):
        self.text = text
        self.parsed_data = {}
        
    def parse(self):
        """Extract structured information from resume text"""
        self.parsed_data = {
            'contact': self.extract_contact_info(),
            'skills': self.extract_skills(),
            'experience': self.extract_experience(),
            'education': self.extract_education(),
            'summary': self.extract_summary(),
            'certifications': self.extract_certifications(),
            'projects': self.extract_projects()
        }
        return self.parsed_data
    
    def extract_contact_info(self):
        """Extract email, phone, and location"""
        contact = {}
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, self.text)
        if emails:
            contact['email'] = emails[0]
        
        # Phone
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',
            r'\b\d{10}\b'
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, self.text)
            if phones:
                contact['phone'] = phones[0]
                break
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.search(linkedin_pattern, self.text, re.IGNORECASE)
        if linkedin:
            contact['linkedin'] = linkedin.group()
        
        # GitHub
        github_pattern = r'github\.com/[\w-]+'
        github = re.search(github_pattern, self.text, re.IGNORECASE)
        if github:
            contact['github'] = github.group()
        
        return contact
    
    def extract_skills(self):
        """Extract technical skills"""
        common_skills = [
            # Programming Languages
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin',
            # Frontend
            'React', 'Angular', 'Vue', 'TypeScript', 'HTML', 'CSS', 'Sass', 'Tailwind', 'Bootstrap',
            # Backend
            'Node.js', 'Django', 'Flask', 'Spring', 'Express', 'Laravel', 'Ruby on Rails',
            # Databases
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQLite', 'Firebase',
            # DevOps
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Jenkins', 'Git', 'CI/CD', 'Terraform',
            # Data Science
            'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn',
            # Mobile
            'Android', 'iOS', 'React Native', 'Flutter', 'Xamarin',
            # Tools
            'Git', 'Jira', 'Confluence', 'Slack', 'Figma', 'Adobe XD', 'Photoshop'
        ]
        
        found_skills = []
        text_lower = self.text.lower()
        
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def extract_experience(self):
        """Extract work experience"""
        experience = []
        
        # Look for dates in various formats
        date_patterns = [
            r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b)',
            r'(\d{1,2}/\d{4})',
            r'(\b\d{4}\b)'
        ]
        
        lines = self.text.split('\n')
        current_exp = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if line might be a job title
            if any(title in line.lower() for title in [
                'engineer', 'developer', 'designer', 'manager', 'analyst', 'specialist',
                'intern', 'associate', 'director', 'lead', 'architect'
            ]):
                # Check if previous line was a company
                if i > 0 and len(lines[i-1].strip()) > 0:
                    current_exp['title'] = line
                    current_exp['company'] = lines[i-1].strip()
                
                # Look for dates in surrounding lines
                for j in range(max(0, i-3), min(len(lines), i+3)):
                    for pattern in date_patterns:
                        dates = re.findall(pattern, lines[j], re.IGNORECASE)
                        if dates and len(dates) >= 2:
                            current_exp['start_date'] = dates[0]
                            current_exp['end_date'] = dates[1] if len(dates) > 1 else 'Present'
                            break
                
                if current_exp:
                    experience.append(current_exp.copy())
                    current_exp = {}
        
        return experience
    
    def extract_education(self):
        """Extract education information"""
        education = []
        
        # Look for education keywords
        edu_keywords = ['university', 'college', 'institute', 'bachelor', 'master', 'phd', 'diploma']
        lines = self.text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in edu_keywords):
                education.append({
                    'institution': line.strip(),
                    'details': lines[i+1].strip() if i+1 < len(lines) else ''
                })
        
        return education
    
    def extract_summary(self):
        """Extract summary/objective"""
        summary_keywords = ['summary', 'objective', 'about', 'profile']
        lines = self.text.split('\n')
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in summary_keywords):
                # Take next few lines as summary
                summary_lines = []
                for j in range(i+1, min(i+5, len(lines))):
                    if lines[j].strip() and len(lines[j].strip()) > 10:
                        summary_lines.append(lines[j].strip())
                return ' '.join(summary_lines)
        
        return ''
    
    def extract_certifications(self):
        """Extract certifications"""
        cert_keywords = ['certified', 'certification', 'aws', 'azure', 'google cloud', 'scrum', 'pmp']
        certs = []
        lines = self.text.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in cert_keywords):
                certs.append(line.strip())
        
        return certs
    
    def extract_projects(self):
        """Extract projects"""
        projects = []
        
        # Look for project indicators
        proj_keywords = ['project', 'portfolio', 'github', 'developed', 'built', 'created']
        lines = self.text.split('\n')
        
        current_proj = {}
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in proj_keywords):
                if 'project' in line_lower or 'built' in line_lower:
                    current_proj['title'] = line.strip()
                elif current_proj:
                    if 'description' not in current_proj:
                        current_proj['description'] = line.strip()
                    else:
                        current_proj['description'] += ' ' + line.strip()
        
        if current_proj:
            projects.append(current_proj)
        
        return projects
    
    def get_keyword_density(self, keywords):
        """Calculate density of specific keywords"""
        text_lower = self.text.lower()
        total_words = len(text_lower.split())
        
        keyword_counts = {}
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            density = (count / max(total_words, 1)) * 10000  # per 10,000 words
            keyword_counts[keyword] = {
                'count': count,
                'density': round(density, 2)
            }
        
        return keyword_counts


# Main function to parse resume from file
def parse_resume(file):
    """Parse resume from file object (PDF or DOCX)"""
    filename = file.filename.lower()
    
    # Extract text from file
    if filename.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    elif filename.endswith(('.docx', '.doc')):
        from docx import Document
        doc = Document(file)
        text = '\n'.join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")
    
    # Parse the extracted text
    parser = ResumeParser(text)
    return parser.parse()