import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from collections import Counter
import math
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class JobMatcher:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
        # Job requirement patterns
        self.requirement_patterns = {
            'experience': [
                r'(\d+)[\+]?\s*years?\s*(?:of\s*)?(?:experience|exp)',
                r'(\d+)[\+]?\s*years?\s*(?:in|with|of)',
                r'minimum\s*(\d+)\s*years?',
                r'at\s*least\s*(\d+)\s*years?'
            ],
            'education': [
                r'bachelor[\'s]?\s*(?:degree)?(?:\s*in\s*[\w\s]+)?',
                r'master[\'s]?\s*(?:degree)?(?:\s*in\s*[\w\s]+)?',
                r'phd|doctorate',
                r'associate[\'s]?\s*degree',
                r'high\s*school|diploma'
            ],
            'skills': [
                r'(?:experience\s*(?:in|with)|proficient\s*(?:in|with)|knowledge\s*(?:of|in))\s*([\w\s,.-]+)',
                r'(?:must\s*have|required|mandatory)[:,]?\s*([\w\s,.-]+)',
                r'(?:preferred|nice\s*to\s*have|bonus)[:,]?\s*([\w\s,.-]+)'
            ]
        }
        
        # Skill categories for better matching
        self.skill_categories = {
            'programming_languages': [
                'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 
                'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql'
            ],
            'web_technologies': [
                'html', 'css', 'react', 'angular', 'vue', 'nodejs', 'express', 
                'django', 'flask', 'spring', 'asp.net', 'bootstrap'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 
                'cassandra', 'oracle', 'sql server', 'dynamodb'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'google cloud', 'gcp', 'heroku', 'digitalocean', 
                'kubernetes', 'docker', 'terraform'
            ],
            'tools_frameworks': [
                'git', 'jenkins', 'docker', 'kubernetes', 'ansible', 'puppet', 
                'chef', 'nagios', 'prometheus', 'grafana'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'tensorflow', 'pytorch', 
                'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'tableau', 'power bi'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem-solving', 
                'critical thinking', 'project management', 'agile', 'scrum'
            ]
        }

    def parse_job_description(self, job_text: str) -> Dict[str, Any]:
        """Parse job description to extract requirements and keywords"""
        job_text_lower = job_text.lower()
        
        # Extract basic information
        job_info = {
            'raw_text': job_text,
            'word_count': len(job_text.split()),
            'requirements': {
                'experience': self.extract_experience_requirements(job_text),
                'education': self.extract_education_requirements(job_text),
                'skills': self.extract_skill_requirements(job_text)
            },
            'keywords': self.extract_keywords(job_text_lower),
            'job_level': self.determine_job_level(job_text_lower),
            'industry': self.detect_job_industry(job_text_lower),
            'benefits': self.extract_benefits(job_text),
            'company_info': self.extract_company_info(job_text)
        }
        
        return job_info

    def extract_experience_requirements(self, job_text: str) -> Dict[str, Any]:
        """Extract experience requirements from job description"""
        experience_info = {
            'min_years': 0,
            'max_years': None,
            'specific_experience': [],
            'level': 'entry'
        }
        
        job_text_lower = job_text.lower()
        
        # Extract years of experience
        years_found = []
        for pattern in self.requirement_patterns['experience']:
            matches = re.findall(pattern, job_text_lower)
            for match in matches:
                try:
                    years = int(match)
                    years_found.append(years)
                except ValueError:
                    continue
        
        if years_found:
            experience_info['min_years'] = min(years_found)
            if len(set(years_found)) > 1:
                experience_info['max_years'] = max(years_found)
        
        # Determine experience level
        if experience_info['min_years'] == 0:
            experience_info['level'] = 'entry'
        elif experience_info['min_years'] <= 2:
            experience_info['level'] = 'junior'
        elif experience_info['min_years'] <= 5:
            experience_info['level'] = 'mid'
        else:
            experience_info['level'] = 'senior'
        
        # Extract specific experience requirements
        experience_phrases = re.findall(
            r'experience\s*(?:in|with|of)\s*([\w\s,.-]+?)(?:\.|,|;|\n|$)', 
            job_text_lower
        )
        experience_info['specific_experience'] = [
            phrase.strip() for phrase in experience_phrases if len(phrase.strip()) > 3
        ]
        
        return experience_info

    def extract_education_requirements(self, job_text: str) -> Dict[str, Any]:
        """Extract education requirements"""
        education_info = {
            'degree_required': False,
            'degree_level': None,
            'preferred_fields': [],
            'certifications': []
        }
        
        job_text_lower = job_text.lower()
        
        # Check for degree requirements
        for pattern in self.requirement_patterns['education']:
            if re.search(pattern, job_text_lower):
                education_info['degree_required'] = True
                if 'bachelor' in pattern:
                    education_info['degree_level'] = 'bachelor'
                elif 'master' in pattern:
                    education_info['degree_level'] = 'master'
                elif 'phd' in pattern or 'doctorate' in pattern:
                    education_info['degree_level'] = 'doctorate'
                break
        
        # Extract preferred fields
        field_matches = re.findall(
            r'(?:bachelor|master|degree)(?:[\'s]?)?\s*in\s*([\w\s]+)', 
            job_text_lower
        )
        education_info['preferred_fields'] = [
            field.strip() for field in field_matches if len(field.strip()) > 2
        ]
        
        # Extract certifications
        cert_patterns = [
            r'certified?\s*(?:in\s*)?([\w\s]+)',
            r'certification\s*(?:in\s*)?([\w\s]+)',
            r'license\s*(?:in\s*)?([\w\s]+)'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, job_text_lower)
            education_info['certifications'].extend([
                match.strip() for match in matches if len(match.strip()) > 2
            ])
        
        return education_info

    def extract_skill_requirements(self, job_text: str) -> Dict[str, Any]:
        """Extract skill requirements and categorize them"""
        skills_info = {
            'required_skills': [],
            'preferred_skills': [],
            'categorized_skills': {},
            'skill_frequency': {}
        }
        
        job_text_lower = job_text.lower()
        
        # Extract skills using patterns
        all_skills = []
        
        # Required skills patterns
        required_patterns = [
            r'(?:required|must\s*have|mandatory)[:,]?\s*([^.]+)',
            r'(?:experience\s*(?:in|with)|proficient\s*(?:in|with))[:,]?\s*([^.]+)'
        ]
        
        for pattern in required_patterns:
            matches = re.findall(pattern, job_text_lower)
            for match in matches:
                skills = self.parse_skill_list(match)
                skills_info['required_skills'].extend(skills)
                all_skills.extend(skills)
        
        # Preferred skills patterns
        preferred_patterns = [
            r'(?:preferred|nice\s*to\s*have|bonus|plus)[:,]?\s*([^.]+)',
            r'(?:familiarity\s*with|knowledge\s*of)[:,]?\s*([^.]+)'
        ]
        
        for pattern in preferred_patterns:
            matches = re.findall(pattern, job_text_lower)
            for match in matches:
                skills = self.parse_skill_list(match)
                skills_info['preferred_skills'].extend(skills)
                all_skills.extend(skills)
        
        # Categorize skills
        for category, category_skills in self.skill_categories.items():
            skills_info['categorized_skills'][category] = []
            for skill in all_skills:
                for cat_skill in category_skills:
                    if cat_skill in skill.lower():
                        skills_info['categorized_skills'][category].append(skill)
                        break
        
        # Calculate skill frequency
        skills_info['skill_frequency'] = dict(Counter(all_skills))
        
        return skills_info

    def parse_skill_list(self, skill_text: str) -> List[str]:
        """Parse a comma-separated list of skills"""
        # Remove common connectors and clean up
        skill_text = re.sub(r'\band\b|\bor\b', ',', skill_text)
        skills = [skill.strip() for skill in skill_text.split(',')]
        
        # Filter out very short or generic terms
        filtered_skills = []
        for skill in skills:
            if len(skill) > 2 and skill not in ['etc', 'experience', 'knowledge', 'work']:
                filtered_skills.append(skill)
        
        return filtered_skills[:10]  # Limit to 10 skills per match

    def extract_keywords(self, job_text: str) -> Dict[str, Any]:
        """Extract and rank keywords from job description"""
        # Tokenize and remove stop words
        tokens = word_tokenize(job_text.lower())
        tokens = [token for token in tokens if token.isalpha() and token not in self.stop_words]
        
        # Calculate word frequencies
        word_freq = Counter(tokens)
        
        # Extract important phrases (2-3 word combinations)
        words = job_text.lower().split()
        phrases = []
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(phrase) > 6 and not any(stop in phrase for stop in self.stop_words):
                phrases.append(phrase)
        
        phrase_freq = Counter(phrases)
        
        return {
            'top_words': dict(word_freq.most_common(20)),
            'top_phrases': dict(phrase_freq.most_common(10)),
            'total_unique_words': len(word_freq),
            'total_words': sum(word_freq.values())
        }

    def determine_job_level(self, job_text: str) -> str:
        """Determine job seniority level"""
        senior_indicators = ['senior', 'lead', 'principal', 'staff', 'architect', 'manager', 'director']
        junior_indicators = ['junior', 'entry', 'associate', 'intern', 'graduate']
        mid_indicators = ['mid', 'intermediate']
        
        job_text_lower = job_text.lower()
        
        if any(indicator in job_text_lower for indicator in senior_indicators):
            return 'senior'
        elif any(indicator in job_text_lower for indicator in junior_indicators):
            return 'junior'
        elif any(indicator in job_text_lower for indicator in mid_indicators):
            return 'mid'
        else:
            return 'mid'  # Default assumption

    def detect_job_industry(self, job_text: str) -> str:
        """Detect industry based on job description"""
        industry_keywords = {
            'technology': ['software', 'developer', 'engineer', 'programming', 'coding', 'tech', 'api', 'database'],
            'finance': ['finance', 'banking', 'investment', 'portfolio', 'trading', 'financial', 'accounting'],
            'healthcare': ['healthcare', 'medical', 'hospital', 'patient', 'clinical', 'health', 'medicine'],
            'marketing': ['marketing', 'advertising', 'campaign', 'brand', 'digital', 'social media', 'content'],
            'sales': ['sales', 'business development', 'account', 'client', 'customer', 'revenue'],
            'consulting': ['consulting', 'consultant', 'advisory', 'strategy', 'business analyst']
        }
        
        industry_scores = {}
        for industry, keywords in industry_keywords.items():
            score = sum(job_text.count(keyword) for keyword in keywords)
            industry_scores[industry] = score
        
        if industry_scores:
            return max(industry_scores, key=industry_scores.get)
        return 'general'

    def extract_benefits(self, job_text: str) -> List[str]:
        """Extract benefits and perks from job description"""
        benefits = []
        benefit_patterns = [
            r'(?:benefits?|perks?)[:,]?\s*([^.]+)',
            r'(?:we\s*offer|offering)[:,]?\s*([^.]+)',
            r'(?:health|medical|dental|vision|insurance|401k|pto|vacation)'
        ]
        
        for pattern in benefit_patterns:
            matches = re.findall(pattern, job_text.lower())
            for match in matches:
                if isinstance(match, str):
                    benefits.extend([b.strip() for b in match.split(',') if b.strip()])
        
        return benefits[:10]  # Limit to 10 benefits

    def extract_company_info(self, job_text: str) -> Dict[str, Any]:
        """Extract company information from job description"""
        company_info = {
            'size_indicators': [],
            'company_type': None,
            'location': None
        }
        
        # Size indicators
        size_patterns = [
            r'(\d+[\+]?)\s*(?:employees?|people|team\s*members)',
            r'(?:startup|small\s*business|enterprise|fortune\s*\d+)',
            r'(?:growing|established|leading|global)'
        ]
        
        for pattern in size_patterns:
            matches = re.findall(pattern, job_text.lower())
            company_info['size_indicators'].extend(matches)
        
        # Company type
        if any(word in job_text.lower() for word in ['startup', 'early stage']):
            company_info['company_type'] = 'startup'
        elif any(word in job_text.lower() for word in ['enterprise', 'fortune', 'established']):
            company_info['company_type'] = 'enterprise'
        else:
            company_info['company_type'] = 'mid-size'
        
        return company_info

    def calculate_match_score(self, resume_analysis: Dict, job_analysis: Dict) -> Dict[str, Any]:
        """Calculate detailed match score between resume and job"""
        match_details = {
            'overall_score': 0,
            'category_scores': {},
            'strengths': [],
            'gaps': [],
            'recommendations': []
        }
        
        # Experience match (30% of total score)
        experience_score = self.calculate_experience_match(
            resume_analysis, job_analysis['requirements']['experience']
        )
        match_details['category_scores']['experience'] = experience_score
        
        # Skills match (40% of total score)
        skills_score = self.calculate_skills_match(
            resume_analysis, job_analysis['requirements']['skills']
        )
        match_details['category_scores']['skills'] = skills_score
        
        # Education match (15% of total score)
        education_score = self.calculate_education_match(
            resume_analysis, job_analysis['requirements']['education']
        )
        match_details['category_scores']['education'] = education_score
        
        # Industry alignment (15% of total score)
        industry_score = self.calculate_industry_match(
            resume_analysis, job_analysis
        )
        match_details['category_scores']['industry'] = industry_score
        
        # Calculate overall score
        match_details['overall_score'] = (
            experience_score * 0.30 +
            skills_score * 0.40 +
            education_score * 0.15 +
            industry_score * 0.15
        )
        
        # Generate insights
        match_details.update(self.generate_match_insights(
            resume_analysis, job_analysis, match_details['category_scores']
        ))
        
        return match_details

    def calculate_experience_match(self, resume: Dict, job_requirements: Dict) -> float:
        """Calculate experience match score"""
        # This is a simplified calculation
        # In a real system, you'd parse experience from resume sections
        resume_experience = resume.get('detected_industry', '')
        
        if job_requirements['min_years'] == 0:
            return 90  # Entry level, high match
        elif job_requirements['min_years'] <= 3:
            return 75  # Junior/mid level
        else:
            return 60   # Senior level - harder match
        
    def calculate_skills_match(self, resume: Dict, job_skills: Dict) -> float:
        """Calculate skills match score"""
        resume_keywords = resume.get('keyword_analysis', {}).get('found_keywords', [])
        resume_keywords_lower = [kw.lower() for kw in resume_keywords]
        
        required_skills = [skill.lower() for skill in job_skills.get('required_skills', [])]
        preferred_skills = [skill.lower() for skill in job_skills.get('preferred_skills', [])]
        
        # Calculate matches
        required_matches = sum(1 for skill in required_skills 
                             if any(skill in res_skill for res_skill in resume_keywords_lower))
        preferred_matches = sum(1 for skill in preferred_skills 
                              if any(skill in res_skill for res_skill in resume_keywords_lower))
        
        # Calculate score
        required_score = (required_matches / len(required_skills) * 80) if required_skills else 80
        preferred_score = (preferred_matches / len(preferred_skills) * 20) if preferred_skills else 20
        
        return min(100, required_score + preferred_score)

    def calculate_education_match(self, resume: Dict, job_education: Dict) -> float:
        """Calculate education match score"""
        if not job_education.get('degree_required', False):
            return 100  # No degree required
        
        # Simplified - assume some education match
        return 75

    def calculate_industry_match(self, resume: Dict, job: Dict) -> float:
        """Calculate industry alignment score"""
        resume_industry = resume.get('detected_industry', '')
        job_industry = job.get('industry', '')
        
        if resume_industry == job_industry:
            return 100
        elif resume_industry in ['technology', 'general'] or job_industry in ['technology', 'general']:
            return 70  # Tech is transferable
        else:
            return 50   # Different industries

    def generate_match_insights(self, resume: Dict, job: Dict, scores: Dict) -> Dict[str, Any]:
        """Generate actionable insights from match analysis"""
        insights = {
            'strengths': [],
            'gaps': [],
            'recommendations': []
        }
        
        # Identify strengths
        if scores['skills'] >= 80:
            insights['strengths'].append("Strong skills alignment with job requirements")
        if scores['experience'] >= 80:
            insights['strengths'].append("Experience level matches job expectations")
        if scores['industry'] >= 80:
            insights['strengths'].append("Strong industry background for this role")
        
        # Identify gaps
        if scores['skills'] < 60:
            insights['gaps'].append("Missing several key technical skills")
        if scores['experience'] < 60:
            insights['gaps'].append("Experience level below job requirements")
        if scores['education'] < 60:
            insights['gaps'].append("Education requirements not fully met")
        
        # Generate recommendations
        job_skills = job['requirements']['skills']
        resume_keywords = set(kw.lower() for kw in resume.get('keyword_analysis', {}).get('found_keywords', []))
        
        missing_required = []
        for skill in job_skills.get('required_skills', [])[:5]:  # Top 5
            if not any(skill.lower() in kw for kw in resume_keywords):
                missing_required.append(skill)
        
        if missing_required:
            insights['recommendations'].append({
                'type': 'add_skills',
                'priority': 'high',
                'title': 'Add Missing Required Skills',
                'description': f"Consider adding these skills: {', '.join(missing_required)}",
                'skills': missing_required
            })
        
        # Experience recommendations
        if scores['experience'] < 70:
            insights['recommendations'].append({
                'type': 'highlight_experience',
                'priority': 'medium',
                'title': 'Emphasize Relevant Experience',
                'description': "Highlight projects and achievements that demonstrate the required experience level"
            })
        
        return insights

# Example usage
if __name__ == "__main__":
    matcher = JobMatcher()
    
    sample_job = """
    Software Engineer - Backend Development
    
    We are looking for a talented Backend Software Engineer with 3+ years of experience 
    to join our growing team. The ideal candidate will have strong experience in Python, 
    Django, and PostgreSQL.
    
    Requirements:
    - Bachelor's degree in Computer Science or related field
    - 3+ years of experience in backend development
    - Proficiency in Python, Django, REST APIs
    - Experience with PostgreSQL and database design
    - Knowledge of Docker and AWS
    - Strong problem-solving and communication skills
    
    Preferred:
    - Experience with microservices architecture
    - Familiarity with Redis and Elasticsearch
    - DevOps experience
    
    Benefits:
    - Competitive salary
    - Health insurance
    - 401k matching
    - Flexible work arrangements
    """
    
    job_analysis = matcher.parse_job_description(sample_job)
    print("Job Analysis:")
    print(f"Industry: {job_analysis['industry']}")
    print(f"Experience required: {job_analysis['requirements']['experience']['min_years']} years")
    print(f"Required skills: {job_analysis['requirements']['skills']['required_skills']}")
    print(f"Job level: {job_analysis['job_level']}")