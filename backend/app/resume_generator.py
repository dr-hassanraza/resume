from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from jinja2 import Template
import io
import json
from typing import Dict, List, Any
from dataclasses import dataclass
import re

@dataclass
class PersonalInfo:
    name: str
    email: str
    phone: str
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""

@dataclass
class Experience:
    title: str
    company: str
    location: str
    start_date: str
    end_date: str
    achievements: List[str]
    
@dataclass
class Education:
    degree: str
    institution: str
    location: str
    graduation_date: str
    gpa: str = ""
    relevant_coursework: List[str] = None

@dataclass
class ResumeData:
    personal_info: PersonalInfo
    summary: str
    experience: List[Experience]
    education: List[Education]
    skills: Dict[str, List[str]]
    certifications: List[str] = None
    projects: List[Dict] = None
    languages: List[str] = None

class ResumeGenerator:
    def __init__(self):
        self.industry_templates = {
            'technology': {
                'color_scheme': {
                    'primary': HexColor('#2E86AB'),
                    'secondary': HexColor('#A23B72'),
                    'accent': HexColor('#F18F01'),
                    'text': HexColor('#2D3748')
                },
                'sections_order': ['summary', 'experience', 'skills', 'education', 'projects', 'certifications'],
                'emphasis': 'skills_and_projects',
                'font_style': 'modern'
            },
            'finance': {
                'color_scheme': {
                    'primary': HexColor('#1A365D'),
                    'secondary': HexColor('#2A69AC'),
                    'accent': HexColor('#63B3ED'),
                    'text': HexColor('#2D3748')
                },
                'sections_order': ['summary', 'experience', 'education', 'skills', 'certifications'],
                'emphasis': 'experience_first',
                'font_style': 'professional'
            },
            'marketing': {
                'color_scheme': {
                    'primary': HexColor('#B83280'),
                    'secondary': HexColor('#D53F8C'),
                    'accent': HexColor('#FBB6CE'),
                    'text': HexColor('#2D3748')
                },
                'sections_order': ['summary', 'experience', 'skills', 'education', 'projects'],
                'emphasis': 'creative_layout',
                'font_style': 'creative'
            },
            'healthcare': {
                'color_scheme': {
                    'primary': HexColor('#1A202C'),
                    'secondary': HexColor('#2D3748'),
                    'accent': HexColor('#4A5568'),
                    'text': HexColor('#2D3748')
                },
                'sections_order': ['summary', 'experience', 'education', 'certifications', 'skills'],
                'emphasis': 'certifications_important',
                'font_style': 'conservative'
            }
        }
        
        # ATS-optimized formatting guidelines
        self.ats_guidelines = {
            'fonts': ['Arial', 'Calibri', 'Times New Roman'],
            'font_sizes': {'title': 16, 'section_header': 14, 'body': 11, 'contact': 10},
            'margins': {'top': 0.5, 'bottom': 0.5, 'left': 0.5, 'right': 0.5},
            'line_spacing': 1.15,
            'section_spacing': 0.2
        }

    def parse_existing_resume(self, resume_text: str, analysis: Dict) -> ResumeData:
        """Parse existing resume content into structured format"""
        sections = analysis.get('sections', {})
        contact_info = analysis.get('contact_info', {})
        
        # Extract personal information
        lines = resume_text.split('\n')
        name = self.extract_name(lines)
        
        personal_info = PersonalInfo(
            name=name or "Your Name",
            email=contact_info.get('email', ''),
            phone=contact_info.get('phone', ''),
            linkedin=contact_info.get('linkedin', ''),
            github=contact_info.get('github', '')
        )
        
        # Extract summary
        summary = self.clean_section_content(sections.get('summary', ''))
        if not summary:
            summary = "Professional summary will be generated based on your experience."
        
        # Parse experience
        experience = self.parse_experience(sections.get('experience', ''))
        
        # Parse education
        education = self.parse_education(sections.get('education', ''))
        
        # Parse skills
        skills = self.parse_skills(sections.get('skills', ''), analysis)
        
        # Parse certifications
        certifications = self.parse_certifications(sections.get('certifications', ''))
        
        # Parse projects
        projects = self.parse_projects(sections.get('projects', ''))
        
        return ResumeData(
            personal_info=personal_info,
            summary=summary,
            experience=experience,
            education=education,
            skills=skills,
            certifications=certifications,
            projects=projects
        )

    def extract_name(self, lines: List[str]) -> str:
        """Extract name from resume lines"""
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and not any(char in line.lower() for char in ['@', 'phone', 'email', 'linkedin']):
                words = line.split()
                if len(words) >= 2 and all(word.isalpha() for word in words[:2]):
                    return line
        return ""

    def clean_section_content(self, content: str) -> str:
        """Clean and format section content"""
        if not content:
            return ""
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return ' '.join(lines)

    def parse_experience(self, experience_text: str) -> List[Experience]:
        """Parse experience section into structured format"""
        if not experience_text:
            return []
        
        experiences = []
        current_job = {}
        current_achievements = []
        
        lines = experience_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a job title/company line
            if self.is_job_header(line):
                # Save previous job if exists
                if current_job:
                    experiences.append(Experience(
                        title=current_job.get('title', ''),
                        company=current_job.get('company', ''),
                        location=current_job.get('location', ''),
                        start_date=current_job.get('start_date', ''),
                        end_date=current_job.get('end_date', 'Present'),
                        achievements=current_achievements.copy()
                    ))
                
                # Parse new job header
                current_job = self.parse_job_header(line)
                current_achievements = []
            else:
                # This is likely an achievement/responsibility
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    current_achievements.append(line[1:].strip())
                elif current_achievements:  # Continuation of previous achievement
                    current_achievements[-1] += ' ' + line
                else:
                    current_achievements.append(line)
        
        # Add the last job
        if current_job:
            experiences.append(Experience(
                title=current_job.get('title', ''),
                company=current_job.get('company', ''),
                location=current_job.get('location', ''),
                start_date=current_job.get('start_date', ''),
                end_date=current_job.get('end_date', 'Present'),
                achievements=current_achievements.copy()
            ))
        
        return experiences

    def is_job_header(self, line: str) -> bool:
        """Determine if line is a job title/company header"""
        # Look for company indicators or date patterns
        date_pattern = r'\d{4}|present|current'
        company_indicators = ['inc', 'corp', 'llc', 'ltd', 'company', 'technologies', 'solutions']
        
        return (re.search(date_pattern, line, re.IGNORECASE) or 
                any(indicator in line.lower() for indicator in company_indicators))

    def parse_job_header(self, line: str) -> Dict:
        """Parse job header line into components"""
        job_info = {}
        
        # Try to extract dates
        date_matches = re.findall(r'\b\d{4}(?:\s*-\s*(?:\d{4}|present|current))?\b', line, re.IGNORECASE)
        if date_matches:
            date_range = date_matches[0]
            if '-' in date_range:
                dates = date_range.split('-')
                job_info['start_date'] = dates[0].strip()
                job_info['end_date'] = dates[1].strip()
            else:
                job_info['start_date'] = date_range
                job_info['end_date'] = 'Present'
            
            # Remove dates from line
            line = re.sub(r'\b\d{4}(?:\s*-\s*(?:\d{4}|present|current))?\b', '', line, flags=re.IGNORECASE)
        
        # Split remaining parts - typically "Title at Company" or "Company - Title"
        parts = re.split(r'\s+at\s+|\s+-\s+|\s+\|\s+', line, flags=re.IGNORECASE)
        if len(parts) >= 2:
            job_info['title'] = parts[0].strip()
            job_info['company'] = parts[1].strip()
        else:
            job_info['title'] = line.strip()
            job_info['company'] = ''
        
        return job_info

    def parse_education(self, education_text: str) -> List[Education]:
        """Parse education section"""
        if not education_text:
            return []
        
        educations = []
        lines = education_text.split('\n')
        current_education = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for degree information
            degree_keywords = ['bachelor', 'master', 'phd', 'doctorate', 'associate', 'certificate']
            if any(keyword in line.lower() for keyword in degree_keywords):
                if current_education:
                    educations.append(Education(**current_education))
                
                current_education = {'degree': line}
            elif 'university' in line.lower() or 'college' in line.lower() or 'institute' in line.lower():
                current_education['institution'] = line
            elif re.search(r'\d{4}', line):
                current_education['graduation_date'] = line
            else:
                if 'location' not in current_education:
                    current_education['location'] = line
        
        if current_education:
            educations.append(Education(
                degree=current_education.get('degree', ''),
                institution=current_education.get('institution', ''),
                location=current_education.get('location', ''),
                graduation_date=current_education.get('graduation_date', ''),
                gpa=current_education.get('gpa', '')
            ))
        
        return educations

    def parse_skills(self, skills_text: str, analysis: Dict) -> Dict[str, List[str]]:
        """Parse and categorize skills"""
        if not skills_text:
            # Use found keywords from analysis
            found_keywords = analysis.get('keyword_analysis', {}).get('found_keywords', [])
            return {'technical': found_keywords[:10], 'soft_skills': []}
        
        # Clean and split skills
        skills_text = re.sub(r'[•\-*]', '', skills_text)
        skills = [skill.strip() for skill in re.split(r'[,\n;]', skills_text) if skill.strip()]
        
        # Categorize skills
        technical_indicators = ['programming', 'software', 'language', 'framework', 'database', 'tool']
        technical_skills = []
        soft_skills = []
        
        for skill in skills:
            if any(indicator in skill.lower() for indicator in technical_indicators):
                technical_skills.append(skill)
            else:
                # Check if it's a known technical skill
                known_tech = ['python', 'java', 'javascript', 'sql', 'aws', 'docker', 'kubernetes']
                if any(tech in skill.lower() for tech in known_tech):
                    technical_skills.append(skill)
                else:
                    soft_skills.append(skill)
        
        return {
            'technical': technical_skills,
            'soft_skills': soft_skills
        }

    def parse_certifications(self, cert_text: str) -> List[str]:
        """Parse certifications"""
        if not cert_text:
            return []
        
        cert_text = re.sub(r'[•\-*]', '', cert_text)
        certifications = [cert.strip() for cert in cert_text.split('\n') if cert.strip()]
        return certifications

    def parse_projects(self, projects_text: str) -> List[Dict]:
        """Parse projects section"""
        if not projects_text:
            return []
        
        projects = []
        lines = projects_text.split('\n')
        current_project = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Project title usually doesn't start with bullet points
            if not line.startswith(('•', '-', '*')):
                if current_project:
                    projects.append(current_project)
                current_project = {'name': line, 'description': ''}
            else:
                # Project description
                current_project['description'] += line[1:].strip() + ' '
        
        if current_project:
            projects.append(current_project)
        
        return projects

    def optimize_content(self, resume_data: ResumeData, recommendations: List[Dict], 
                        industry: str) -> ResumeData:
        """Apply optimizations based on recommendations"""
        optimized_data = resume_data
        
        for rec in recommendations:
            if rec['action'] == 'keyword_optimization':
                optimized_data = self.add_keywords(optimized_data, rec['keywords'], industry)
            elif rec['action'] == 'add_metrics':
                optimized_data = self.add_quantifiable_achievements(optimized_data)
            elif rec['action'] == 'improve_verbs':
                optimized_data = self.improve_action_verbs(optimized_data, rec.get('suggestions', []))
        
        return optimized_data

    def add_keywords(self, resume_data: ResumeData, keywords: List[str], industry: str) -> ResumeData:
        """Add relevant keywords to appropriate sections"""
        # Add keywords to skills section
        if 'technical' not in resume_data.skills:
            resume_data.skills['technical'] = []
        
        for keyword in keywords:
            if keyword not in resume_data.skills['technical']:
                resume_data.skills['technical'].append(keyword)
        
        # Enhance summary with keywords
        keyword_phrase = f"Experienced in {', '.join(keywords[:3])}"
        if keyword_phrase not in resume_data.summary:
            resume_data.summary = f"{keyword_phrase}. {resume_data.summary}"
        
        return resume_data

    def add_quantifiable_achievements(self, resume_data: ResumeData) -> ResumeData:
        """Add sample metrics to achievements"""
        metrics_examples = [
            "resulting in 25% increase in efficiency",
            "improving performance by 30%",
            "serving 1000+ users daily",
            "managing $100K+ budget",
            "leading team of 5+ members"
        ]
        
        for i, exp in enumerate(resume_data.experience):
            for j, achievement in enumerate(exp.achievements):
                if not re.search(r'\d+%|\$\d+|\d+\+', achievement):
                    # Add a metric if none exists
                    metric = metrics_examples[j % len(metrics_examples)]
                    resume_data.experience[i].achievements[j] = f"{achievement}, {metric}"
        
        return resume_data

    def improve_action_verbs(self, resume_data: ResumeData, strong_verbs: List[str]) -> ResumeData:
        """Replace weak verbs with strong action verbs"""
        weak_to_strong = {
            'responsible for': strong_verbs[0] if strong_verbs else 'managed',
            'worked on': strong_verbs[1] if len(strong_verbs) > 1 else 'developed',
            'helped with': strong_verbs[2] if len(strong_verbs) > 2 else 'assisted',
            'duties included': strong_verbs[3] if len(strong_verbs) > 3 else 'executed'
        }
        
        for exp in resume_data.experience:
            for i, achievement in enumerate(exp.achievements):
                for weak, strong in weak_to_strong.items():
                    if weak in achievement.lower():
                        exp.achievements[i] = achievement.replace(weak, strong)
        
        return resume_data

    def generate_pdf_resume(self, resume_data: ResumeData, industry: str = 'technology') -> bytes:
        """Generate a professional PDF resume"""
        buffer = io.BytesIO()
        
        # Get industry template
        template = self.industry_templates.get(industry, self.industry_templates['technology'])
        colors_scheme = template['color_scheme']
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles for different sections
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors_scheme['primary'],
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        section_style = ParagraphStyle(
            'CustomSection',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors_scheme['primary'],
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        contact_style = ParagraphStyle(
            'ContactStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=0
        )
        
        # Build content
        content = []
        
        # Header - Name and Contact Information
        content.append(Paragraph(resume_data.personal_info.name, title_style))
        
        contact_info = []
        if resume_data.personal_info.email:
            contact_info.append(resume_data.personal_info.email)
        if resume_data.personal_info.phone:
            contact_info.append(resume_data.personal_info.phone)
        if resume_data.personal_info.linkedin:
            contact_info.append(resume_data.personal_info.linkedin)
        
        if contact_info:
            content.append(Paragraph(" | ".join(contact_info), contact_style))
        
        content.append(Spacer(1, 12))
        
        # Professional Summary
        if resume_data.summary:
            content.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
            content.append(Paragraph(resume_data.summary, body_style))
            content.append(Spacer(1, 12))
        
        # Experience
        if resume_data.experience:
            content.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
            
            for exp in resume_data.experience:
                # Job title and company
                job_header = f"<b>{exp.title}</b>"
                if exp.company:
                    job_header += f" | {exp.company}"
                if exp.start_date or exp.end_date:
                    date_range = f"{exp.start_date} - {exp.end_date}"
                    job_header += f" | {date_range}"
                
                content.append(Paragraph(job_header, body_style))
                
                # Achievements
                for achievement in exp.achievements:
                    content.append(Paragraph(f"• {achievement}", body_style))
                
                content.append(Spacer(1, 8))
        
        # Skills
        if resume_data.skills:
            content.append(Paragraph("TECHNICAL SKILLS", section_style))
            
            for category, skills_list in resume_data.skills.items():
                if skills_list:
                    category_title = category.replace('_', ' ').title()
                    skills_text = f"<b>{category_title}:</b> {', '.join(skills_list)}"
                    content.append(Paragraph(skills_text, body_style))
            
            content.append(Spacer(1, 12))
        
        # Education
        if resume_data.education:
            content.append(Paragraph("EDUCATION", section_style))
            
            for edu in resume_data.education:
                edu_text = f"<b>{edu.degree}</b>"
                if edu.institution:
                    edu_text += f" | {edu.institution}"
                if edu.graduation_date:
                    edu_text += f" | {edu.graduation_date}"
                
                content.append(Paragraph(edu_text, body_style))
            
            content.append(Spacer(1, 12))
        
        # Projects
        if resume_data.projects:
            content.append(Paragraph("KEY PROJECTS", section_style))
            
            for project in resume_data.projects:
                project_text = f"<b>{project['name']}</b>"
                if project.get('description'):
                    project_text += f": {project['description']}"
                content.append(Paragraph(project_text, body_style))
            
            content.append(Spacer(1, 12))
        
        # Certifications
        if resume_data.certifications:
            content.append(Paragraph("CERTIFICATIONS", section_style))
            
            for cert in resume_data.certifications:
                content.append(Paragraph(f"• {cert}", body_style))
        
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_optimized_resume(self, original_text: str, analysis: Dict, 
                                industry: str = 'technology') -> Dict[str, Any]:
        """Generate a complete optimized resume with before/after comparison"""
        
        # Parse original resume
        original_data = self.parse_existing_resume(original_text, analysis)
        
        # Apply optimizations
        recommendations = analysis.get('recommendations', [])
        optimized_data = self.optimize_content(original_data, recommendations, industry)
        
        # Generate PDF
        pdf_bytes = self.generate_pdf_resume(optimized_data, industry)
        
        return {
            'original_data': original_data,
            'optimized_data': optimized_data,
            'pdf_bytes': pdf_bytes,
            'improvements': self.get_improvement_summary(original_data, optimized_data),
            'template_used': industry
        }

    def get_improvement_summary(self, original: ResumeData, optimized: ResumeData) -> Dict[str, Any]:
        """Generate summary of improvements made"""
        improvements = {
            'keywords_added': 0,
            'metrics_added': 0,
            'sections_enhanced': [],
            'formatting_improved': True
        }
        
        # Count keyword additions
        orig_skills = len(original.skills.get('technical', []))
        opt_skills = len(optimized.skills.get('technical', []))
        improvements['keywords_added'] = max(0, opt_skills - orig_skills)
        
        # Count achievements with metrics
        orig_metrics = 0
        opt_metrics = 0
        
        for exp in original.experience:
            for ach in exp.achievements:
                if re.search(r'\d+%|\$\d+|\d+\+', ach):
                    orig_metrics += 1
        
        for exp in optimized.experience:
            for ach in exp.achievements:
                if re.search(r'\d+%|\$\d+|\d+\+', ach):
                    opt_metrics += 1
        
        improvements['metrics_added'] = max(0, opt_metrics - orig_metrics)
        
        # Enhanced sections
        if improvements['keywords_added'] > 0:
            improvements['sections_enhanced'].append('Skills')
        if improvements['metrics_added'] > 0:
            improvements['sections_enhanced'].append('Experience')
        
        return improvements

# Testing the resume generator
if __name__ == "__main__":
    generator = ResumeGenerator()
    
    # Sample resume data
    sample_personal = PersonalInfo(
        name="John Doe",
        email="john.doe@email.com", 
        phone="(555) 123-4567",
        linkedin="linkedin.com/in/johndoe"
    )
    
    sample_experience = [
        Experience(
            title="Software Developer",
            company="Tech Corp",
            location="San Francisco, CA",
            start_date="2020",
            end_date="Present",
            achievements=[
                "Developed web applications using Python and Django",
                "Improved application performance by 30%",
                "Led a team of 5 developers"
            ]
        )
    ]
    
    sample_education = [
        Education(
            degree="Bachelor of Science in Computer Science",
            institution="University of Technology",
            location="San Francisco, CA",
            graduation_date="2020"
        )
    ]
    
    sample_skills = {
        'technical': ['Python', 'JavaScript', 'React', 'Django', 'SQL'],
        'soft_skills': ['Leadership', 'Communication', 'Problem-solving']
    }
    
    sample_resume = ResumeData(
        personal_info=sample_personal,
        summary="Software engineer with 3+ years of experience in full-stack development.",
        experience=sample_experience,
        education=sample_education,
        skills=sample_skills
    )
    
    # Generate PDF
    pdf_bytes = generator.generate_pdf_resume(sample_resume, 'technology')
    
    # Save to file for testing
    with open('sample_resume.pdf', 'wb') as f:
        f.write(pdf_bytes)
    
    print("Sample resume generated successfully!")
    print(f"PDF size: {len(pdf_bytes)} bytes")