import re
import PyPDF2
from docx import Document
import textstat
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import io
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Download required NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class ResumeProcessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
        # Industry-specific keywords database
        self.industry_keywords = {
            'technology': {
                'programming': ['python', 'java', 'javascript', 'react', 'angular', 'nodejs', 'sql', 'mongodb', 'docker', 'kubernetes', 'aws', 'azure', 'git', 'agile', 'scrum', 'ci/cd', 'machine learning', 'ai', 'data science', 'api', 'microservices', 'devops'],
                'soft_skills': ['problem-solving', 'teamwork', 'communication', 'leadership', 'collaboration', 'critical thinking', 'innovation', 'adaptability'],
                'certifications': ['aws certified', 'azure certified', 'google cloud', 'cissp', 'comptia', 'certified scrum master', 'pmp'],
                'action_verbs': ['developed', 'implemented', 'designed', 'architected', 'optimized', 'automated', 'scaled', 'migrated', 'deployed', 'integrated']
            },
            'marketing': {
                'skills': ['digital marketing', 'seo', 'sem', 'social media', 'content marketing', 'email marketing', 'analytics', 'google ads', 'facebook ads', 'conversion optimization', 'a/b testing', 'crm', 'marketing automation'],
                'tools': ['google analytics', 'hubspot', 'mailchimp', 'salesforce', 'hootsuite', 'canva', 'photoshop', 'wordpress'],
                'soft_skills': ['creativity', 'strategic thinking', 'communication', 'project management', 'data analysis', 'brand management'],
                'action_verbs': ['launched', 'increased', 'generated', 'managed', 'created', 'analyzed', 'optimized', 'drove', 'executed', 'coordinated']
            },
            'finance': {
                'skills': ['financial analysis', 'budgeting', 'forecasting', 'risk management', 'investment analysis', 'portfolio management', 'financial modeling', 'valuation', 'accounting', 'auditing', 'compliance', 'treasury management'],
                'tools': ['excel', 'bloomberg', 'sap', 'quickbooks', 'tableau', 'power bi', 'python', 'r', 'sql'],
                'certifications': ['cfa', 'cpa', 'frm', 'caia', 'series 7', 'series 66'],
                'action_verbs': ['analyzed', 'evaluated', 'managed', 'optimized', 'forecasted', 'assessed', 'monitored', 'advised', 'structured', 'executed']
            },
            'healthcare': {
                'skills': ['patient care', 'clinical assessment', 'medical records', 'hipaa compliance', 'electronic health records', 'medical terminology', 'quality assurance', 'infection control', 'care coordination'],
                'tools': ['epic', 'cerner', 'meditech', 'allscripts', 'emr systems'],
                'certifications': ['bls', 'acls', 'rn', 'lpn', 'cna', 'medical license', 'board certification'],
                'action_verbs': ['administered', 'assessed', 'documented', 'coordinated', 'monitored', 'educated', 'collaborated', 'implemented', 'evaluated', 'managed']
            }
        }
        
        # ATS-friendly formatting requirements
        self.ats_requirements = {
            'sections': ['experience', 'education', 'skills', 'summary', 'contact'],
            'date_formats': [r'\d{4}-\d{4}', r'\d{4}-present', r'\d{1,2}/\d{4}', r'\w+\s\d{4}'],
            'phone_formats': [r'\(\d{3}\)\s\d{3}-\d{4}', r'\d{3}-\d{3}-\d{4}', r'\d{3}\.\d{3}\.\d{4}'],
            'email_format': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""

    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc_file = io.BytesIO(file_bytes)
            doc = Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return ""

    def parse_resume(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parse resume content and extract structured information"""
        # Extract text based on file type
        if filename.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(file_bytes)
        elif filename.lower().endswith(('.docx', '.doc')):
            text = self.extract_text_from_docx(file_bytes)
        else:
            text = file_bytes.decode('utf-8', errors='ignore')

        if not text.strip():
            return {"error": "Could not extract text from resume"}

        # Analyze the resume content
        analysis = self.analyze_resume_content(text)
        return analysis

    def analyze_resume_content(self, text: str) -> Dict[str, Any]:
        """Perform comprehensive resume analysis"""
        text_lower = text.lower()
        
        # Basic metrics
        word_count = len(text.split())
        sentence_count = len(sent_tokenize(text))
        readability = textstat.flesch_reading_ease(text)
        
        # Extract sections
        sections = self.extract_sections(text)
        
        # Extract contact information
        contact_info = self.extract_contact_info(text)
        
        # Detect industry
        detected_industry = self.detect_industry(text_lower)
        
        # Analyze keywords for detected industry
        keyword_analysis = self.analyze_keywords(text_lower, detected_industry)
        
        # Check ATS compatibility
        ats_score = self.calculate_ats_score(text, sections, contact_info, keyword_analysis)
        
        # Generate specific recommendations
        recommendations = self.generate_recommendations(
            text, sections, contact_info, keyword_analysis, detected_industry, ats_score
        )
        
        return {
            'text': text,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'readability_score': readability,
            'sections': sections,
            'contact_info': contact_info,
            'detected_industry': detected_industry,
            'keyword_analysis': keyword_analysis,
            'ats_score': ats_score,
            'recommendations': recommendations,
            'strengths': self.identify_strengths(text, sections, keyword_analysis),
            'weaknesses': self.identify_weaknesses(text, sections, contact_info, keyword_analysis)
        }

    def extract_sections(self, text: str) -> Dict[str, str]:
        """Extract different sections from resume"""
        sections = {}
        text_lines = text.split('\n')
        current_section = None
        section_content = []
        
        section_headers = {
            'experience': ['experience', 'work history', 'employment', 'professional experience', 'work experience'],
            'education': ['education', 'academic background', 'qualifications'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise'],
            'summary': ['summary', 'profile', 'objective', 'professional summary', 'career objective'],
            'projects': ['projects', 'key projects', 'notable projects'],
            'certifications': ['certifications', 'certificates', 'licenses']
        }
        
        for line in text_lines:
            line_lower = line.lower().strip()
            
            # Check if line is a section header
            section_found = False
            for section_key, headers in section_headers.items():
                if any(header in line_lower for header in headers):
                    if current_section and section_content:
                        sections[current_section] = '\n'.join(section_content)
                    current_section = section_key
                    section_content = []
                    section_found = True
                    break
            
            if not section_found and current_section:
                section_content.append(line)
        
        # Add the last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content)
        
        return sections

    def extract_contact_info(self, text: str) -> Dict[str, Any]:
        """Extract contact information"""
        contact_info = {
            'email': None,
            'phone': None,
            'linkedin': None,
            'github': None
        }
        
        # Email
        email_match = re.search(self.ats_requirements['email_format'], text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Phone
        for pattern in self.ats_requirements['phone_formats']:
            phone_match = re.search(pattern, text)
            if phone_match:
                contact_info['phone'] = phone_match.group()
                break
        
        # LinkedIn
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text.lower())
        if linkedin_match:
            contact_info['linkedin'] = linkedin_match.group()
        
        # GitHub
        github_match = re.search(r'github\.com/[\w-]+', text.lower())
        if github_match:
            contact_info['github'] = github_match.group()
        
        return contact_info

    def detect_industry(self, text: str) -> str:
        """Detect the industry based on resume content"""
        industry_scores = {}
        
        for industry, keywords in self.industry_keywords.items():
            score = 0
            for category, keyword_list in keywords.items():
                for keyword in keyword_list:
                    if keyword.lower() in text:
                        score += text.count(keyword.lower())
            industry_scores[industry] = score
        
        # Return industry with highest score
        if industry_scores:
            return max(industry_scores, key=industry_scores.get)
        return 'general'

    def analyze_keywords(self, text: str, industry: str) -> Dict[str, Any]:
        """Analyze keyword density and relevance"""
        if industry not in self.industry_keywords:
            return {'score': 50, 'found_keywords': [], 'missing_keywords': []}
        
        industry_data = self.industry_keywords[industry]
        found_keywords = []
        missing_keywords = []
        total_possible = 0
        
        for category, keywords in industry_data.items():
            for keyword in keywords:
                total_possible += 1
                if keyword.lower() in text:
                    found_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)
        
        keyword_score = (len(found_keywords) / total_possible) * 100 if total_possible > 0 else 0
        
        return {
            'score': min(100, keyword_score),
            'found_keywords': found_keywords[:20],  # Top 20
            'missing_keywords': missing_keywords[:10],  # Top 10 missing
            'total_found': len(found_keywords),
            'total_possible': total_possible
        }

    def calculate_ats_score(self, text: str, sections: Dict, contact_info: Dict, keyword_analysis: Dict) -> float:
        """Calculate ATS compatibility score"""
        score = 0
        max_score = 100
        
        # Section presence (40 points)
        required_sections = ['experience', 'education', 'skills']
        section_score = (len([s for s in required_sections if s in sections]) / len(required_sections)) * 40
        score += section_score
        
        # Contact information (20 points)
        contact_score = 0
        if contact_info['email']: contact_score += 10
        if contact_info['phone']: contact_score += 10
        score += contact_score
        
        # Keyword relevance (30 points)
        keyword_score = (keyword_analysis['score'] / 100) * 30
        score += keyword_score
        
        # Format and readability (10 points)
        format_score = 10
        if len(text.split()) < 200: format_score -= 3  # Too short
        if len(text.split()) > 800: format_score -= 2   # Too long
        score += format_score
        
        return min(max_score, score)

    def identify_strengths(self, text: str, sections: Dict, keyword_analysis: Dict) -> List[str]:
        """Identify resume strengths"""
        strengths = []
        
        if keyword_analysis['score'] > 70:
            strengths.append("Strong industry keyword optimization")
        
        if len(sections) >= 5:
            strengths.append("Well-structured with comprehensive sections")
        
        if 'experience' in sections and len(sections['experience'].split()) > 100:
            strengths.append("Detailed work experience descriptions")
        
        if any(verb in text.lower() for verb in ['achieved', 'increased', 'improved', 'reduced', 'generated']):
            strengths.append("Includes quantifiable achievements")
        
        if len(text.split()) > 300:
            strengths.append("Adequate length and detail")
        
        return strengths

    def identify_weaknesses(self, text: str, sections: Dict, contact_info: Dict, keyword_analysis: Dict) -> List[str]:
        """Identify resume weaknesses"""
        weaknesses = []
        
        if not contact_info['email']:
            weaknesses.append("Missing email address")
        
        if not contact_info['phone']:
            weaknesses.append("Missing phone number")
        
        if keyword_analysis['score'] < 40:
            weaknesses.append("Insufficient industry-relevant keywords")
        
        if 'summary' not in sections:
            weaknesses.append("Missing professional summary section")
        
        if len(text.split()) < 250:
            weaknesses.append("Resume content too brief")
        
        if not any(char.isdigit() for char in text):
            weaknesses.append("No quantified achievements or metrics")
        
        return weaknesses

    def generate_recommendations(self, text: str, sections: Dict, contact_info: Dict, 
                               keyword_analysis: Dict, industry: str, ats_score: float) -> List[Dict]:
        """Generate specific, actionable recommendations"""
        recommendations = []
        
        # Keyword recommendations
        if keyword_analysis['score'] < 60:
            missing_keywords = keyword_analysis['missing_keywords'][:5]
            recommendations.append({
                'type': 'keywords',
                'priority': 'high',
                'title': 'Add Industry Keywords',
                'description': f"Include these relevant keywords: {', '.join(missing_keywords)}",
                'action': 'keyword_optimization',
                'keywords': missing_keywords
            })
        
        # Contact information
        if not contact_info['email'] or not contact_info['phone']:
            missing_contact = []
            if not contact_info['email']: missing_contact.append('email')
            if not contact_info['phone']: missing_contact.append('phone number')
            
            recommendations.append({
                'type': 'contact',
                'priority': 'high',
                'title': 'Add Missing Contact Information',
                'description': f"Include your {' and '.join(missing_contact)}",
                'action': 'add_contact_info'
            })
        
        # Section recommendations
        missing_sections = []
        for required in ['experience', 'education', 'skills', 'summary']:
            if required not in sections:
                missing_sections.append(required)
        
        if missing_sections:
            recommendations.append({
                'type': 'structure',
                'priority': 'medium',
                'title': 'Add Missing Sections',
                'description': f"Include these sections: {', '.join(missing_sections)}",
                'action': 'add_sections',
                'sections': missing_sections
            })
        
        # Quantification recommendations
        if not re.search(r'\d+%|\$\d+|\d+\+', text):
            recommendations.append({
                'type': 'content',
                'priority': 'medium',
                'title': 'Add Quantifiable Achievements',
                'description': 'Include specific numbers, percentages, and metrics to demonstrate impact',
                'action': 'add_metrics',
                'examples': ['Increased sales by 25%', 'Managed team of 10+', 'Reduced costs by $50K']
            })
        
        # Action verb recommendations
        weak_verbs = ['responsible for', 'duties included', 'worked on']
        if any(verb in text.lower() for verb in weak_verbs):
            strong_verbs = self.industry_keywords.get(industry, {}).get('action_verbs', [])
            recommendations.append({
                'type': 'content',
                'priority': 'low',
                'title': 'Strengthen Action Verbs',
                'description': 'Replace weak phrases with strong action verbs',
                'action': 'improve_verbs',
                'suggestions': strong_verbs[:8]
            })
        
        return recommendations

# Example usage and testing
if __name__ == "__main__":
    processor = ResumeProcessor()
    
    # Test with sample text
    sample_text = """
    John Doe
    john.doe@email.com
    (555) 123-4567
    
    Professional Summary
    Software engineer with 5 years of experience in Python and web development.
    
    Experience
    Software Developer at Tech Corp (2020-2023)
    - Developed web applications using Python and Django
    - Worked with databases and API integration
    - Collaborated with team members on various projects
    
    Education
    Bachelor of Science in Computer Science
    University of Technology (2016-2020)
    
    Skills
    Python, JavaScript, HTML, CSS, Git
    """
    
    result = processor.analyze_resume_content(sample_text)
    print(f"ATS Score: {result['ats_score']:.1f}")
    print(f"Industry: {result['detected_industry']}")
    print(f"Recommendations: {len(result['recommendations'])}")
    for rec in result['recommendations']:
        print(f"- {rec['title']}: {rec['description']}")