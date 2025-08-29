import asyncio
import openai
import anthropic
from typing import List, Dict, Optional, Any
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from app.core.config import settings
import json
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.claude_client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY) if settings.CLAUDE_API_KEY else None
        # Placeholder for Z.AI client - replace with actual SDK client if available
        self.z_ai_client = None # Initialize if settings.Z_AI_API_KEY is present
        if settings.Z_AI_API_KEY:
            # Example: self.z_ai_client = ZAIClient(api_key=settings.Z_AI_API_KEY)
            # For now, we'll just check for the key's presence
            self.z_ai_client = True # Simple boolean to indicate availability
        
        # Initialize OpenAI models
        if settings.OPENAI_API_KEY:
            self.openai_llm = OpenAI(
                model="gpt-3.5-turbo",
                api_key=settings.OPENAI_API_KEY
            )
            self.openai_embedding = OpenAIEmbedding(
                model="text-embedding-ada-002",
                api_key=settings.OPENAI_API_KEY
            )
            Settings.llm = self.openai_llm
            Settings.embed_model = self.openai_embedding
        
        # Model routing based on task type
        self.model_routing = {
            "resume_analysis": "claude",  # Claude excels at detailed analysis
            "optimization_suggestions": "gpt4",  # GPT-4 for creative suggestions
            "ats_scoring": "openai",  # OpenAI for specialized tasks
            "chat_response": "z_ai",  # Routing chat to Z.AI as requested
            "keyword_extraction": "gpt4",
            "industry_insights": "openai"
        }
        
        # Industry-specific prompts and knowledge
        self.industry_templates = self._load_industry_templates()
        
    def _load_industry_templates(self) -> Dict[str, Dict]:
        """Load industry-specific optimization templates."""
        return {
            "technology": {
                "key_skills": ["Python", "JavaScript", "AWS", "Docker", "Kubernetes", "React", "Node.js"],
                "keywords": ["agile", "CI/CD", "microservices", "cloud", "API", "DevOps"],
                "experience_focus": "technical achievements, scalability, performance optimization"
            },
            "finance": {
                "key_skills": ["Excel", "SQL", "Python", "R", "Bloomberg", "Financial Modeling"],
                "keywords": ["ROI", "portfolio", "risk management", "compliance", "analytics"],
                "experience_focus": "quantifiable financial impact, regulatory compliance"
            },
            "healthcare": {
                "key_skills": ["EMR", "HIPAA", "Clinical Research", "Patient Care"],
                "keywords": ["patient outcomes", "compliance", "healthcare delivery"],
                "experience_focus": "patient care improvements, regulatory adherence"
            },
            "marketing": {
                "key_skills": ["Google Analytics", "SEO", "SEM", "Social Media", "Content Strategy"],
                "keywords": ["conversion rate", "engagement", "brand awareness", "lead generation"],
                "experience_focus": "campaign performance, growth metrics"
            },
            "sales": {
                "key_skills": ["CRM", "Salesforce", "Lead Generation", "Negotiation"],
                "keywords": ["quota attainment", "pipeline", "revenue growth", "client acquisition"],
                "experience_focus": "sales targets, revenue impact, client relationships"
            }
        }
    
    async def analyze_resume(self, resume_data: Dict) -> str:
        """Analyze uploaded resume and provide detailed insights."""
        try:
            resume_text = resume_data.get("content", "")
            
            analysis_prompt = f"""
            Analyze this resume comprehensively and provide insights:
            
            Resume Content:
            {resume_text}
            
            Provide analysis in the following format:
            
            **RESUME ANALYSIS**
            
            **Strengths:**
            • [List 3-4 key strengths]
            
            **Areas for Improvement:**
            • [List 3-4 improvement areas]
            
            **Industry Detection:**
            • Primary Industry: [detected industry]
            • Experience Level: [entry/mid/senior/executive]
            
            **ATS Compatibility:**
            • Current Score: [0-100]
            • Issues: [list formatting or keyword issues]
            
            **Key Skills Identified:**
            • [List top 8-10 skills found]
            
            **Recommendations:**
            • [3-4 specific actionable recommendations]
            """
            
            response = await self._route_to_model("resume_analysis", analysis_prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing resume: {e}")
            return "I encountered an error analyzing your resume. Please try uploading again."
    
    async def generate_chat_response(self, session_id: str, user_message: str, context: Dict = None) -> str:
        """Generate conversational response to user queries."""
        try:
            # Get conversation context if available
            context_str = ""
            if context:
                context_str = f"\nContext: {json.dumps(context, indent=2)}"
            
            chat_prompt = f"""
            You are an expert resume optimization assistant. Provide helpful, conversational responses.
            
            User Message: {user_message}
            {context_str}
            
            Guidelines:
            - Be conversational and helpful
            - Provide specific, actionable advice
            - If user hasn't uploaded resume yet, guide them to do so
            - If discussing optimizations, be specific about improvements
            - Keep responses concise but informative
            
            Response:
            """
            
            response = await self._route_to_model("chat_response", chat_prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    async def generate_optimization_suggestions(
        self, 
        session_id: str, 
        optimization_type: str, 
        job_title: str = "", 
        job_description: str = "",
        resume_data: Dict = None
    ) -> str:
        """Generate specific optimization suggestions based on type and job requirements."""
        try:
            # Industry detection for targeted suggestions
            detected_industry = await self._detect_industry(job_title, job_description)
            industry_template = self.industry_templates.get(detected_industry, {})
            
            base_prompt = f"""
            Resume Optimization Request:
            - Type: {optimization_type}
            - Target Job: {job_title}
            - Industry: {detected_industry}
            
            Job Description:
            {job_description}
            
            Industry-Specific Focus:
            {json.dumps(industry_template, indent=2)}
            """
            
            # Specific prompts for different optimization types
            optimization_prompts = {
                "ATS Keyword Optimizer": f"""
                {base_prompt}
                
                Analyze the job description and provide ATS optimization:
                
                **KEYWORD OPTIMIZATION ANALYSIS**
                
                **Critical Keywords Missing:**
                • [List 5-7 exact keywords from job description]
                
                **Keywords to Add:**
                • [Specific placement suggestions for each keyword]
                
                **Keyword Density Recommendations:**
                • [Optimal frequency for key terms]
                
                **ATS-Friendly Formatting:**
                • [Specific formatting improvements]
                
                **Industry-Specific Terms:**
                • [Add relevant industry keywords from template]
                """,
                
                "Experience Section Enhancer": f"""
                {base_prompt}
                
                Enhance experience section for maximum impact:
                
                **EXPERIENCE ENHANCEMENT**
                
                **Power Verbs to Use:**
                • [List 8-10 strong action verbs relevant to role]
                
                **Quantification Opportunities:**
                • [Suggest specific metrics to highlight]
                
                **Achievement Reframing:**
                • [How to reframe responsibilities as achievements]
                
                **Industry Alignment:**
                • [Align experience with industry expectations]
                
                **Example Improvements:**
                • Before: [weak example]
                • After: [strong rewrite]
                """,
                
                "Skills Hierarchy Creator": f"""
                {base_prompt}
                
                Create optimized skills organization:
                
                **SKILLS HIERARCHY**
                
                **Core Technical Skills:**
                • [Top 6-8 technical skills for role]
                
                **Secondary Skills:**
                • [Supporting technical and soft skills]
                
                **Skills to Highlight:**
                • [Skills that match job requirements exactly]
                
                **Skills Gaps to Address:**
                • [Missing skills that should be learned/added]
                
                **Recommended Skills Section Format:**
                • [Optimal way to present skills]
                """,
                
                "Professional Summary Crafter": f"""
                {base_prompt}
                
                Create compelling professional summary:
                
                **PROFESSIONAL SUMMARY**
                
                **Key Value Proposition:**
                • [2-3 sentence summary of unique value]
                
                **Industry Positioning:**
                • [How to position within industry]
                
                **Quantified Achievements:**
                • [Top 2-3 quantifiable achievements to highlight]
                
                **Call to Action:**
                • [Compelling closing statement]
                
                **Complete Summary Example:**
                [Write full 3-4 sentence professional summary]
                """
            }
            
            prompt = optimization_prompts.get(optimization_type, f"{base_prompt}\n\nProvide optimization suggestions for: {optimization_type}")
            
            response = await self._route_to_model("optimization_suggestions", prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {e}")
            return f"I encountered an error generating {optimization_type} suggestions. Please try again."
    
    async def calculate_ats_score(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Calculate ATS compatibility score."""
        try:
            scoring_prompt = f"""
            Calculate ATS compatibility score for this resume against the job description.
            
            Resume:
            {resume_text}
            
            Job Description:
            {job_description}
            
            Provide scoring in this exact JSON format:
            {{
                "overall_score": [0-100],
                "keyword_match": [0-100],
                "formatting_score": [0-100],
                "section_completeness": [0-100],
                "readability": [0-100],
                "issues": ["list of specific issues"],
                "recommendations": ["list of specific fixes"]
            }}
            """
            
            response = await self._route_to_model("ats_scoring", scoring_prompt)
            
            # Parse JSON response
            try:
                score_data = json.loads(response)
                return score_data
            except json.JSONDecodeError:
                return {
                    "overall_score": 75,
                    "keyword_match": 70,
                    "formatting_score": 80,
                    "section_completeness": 75,
                    "readability": 80,
                    "issues": ["Unable to parse detailed analysis"],
                    "recommendations": ["Please try analysis again"]
                }
                
        except Exception as e:
            logger.error(f"Error calculating ATS score: {e}")
            return {"overall_score": 0, "error": str(e)}
    
    async def extract_keywords(self, job_description: str, industry: str = None) -> List[str]:
        """Extract relevant keywords from job description."""
        try:
            extraction_prompt = f"""
            Extract the most important keywords and phrases from this job description for ATS optimization:
            
            Job Description:
            {job_description}
            
            Industry: {industry or "General"}
            
            Return a JSON list of 15-20 most critical keywords/phrases:
            ["keyword1", "keyword2", "phrase with multiple words", ...]
            
            Focus on:
            - Technical skills
            - Soft skills
            - Industry terminology
            - Required qualifications
            - Key responsibilities
            """
            
            response = await self._route_to_model("keyword_extraction", extraction_prompt)
            
            try:
                keywords = json.loads(response)
                return keywords if isinstance(keywords, list) else []
            except json.JSONDecodeError:
                # Fallback: extract keywords from response text
                keywords = re.findall(r'"([^"]*)"', response)
                return keywords[:20]
                
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    async def get_industry_insights(self, industry: str, job_title: str) -> Dict[str, Any]:
        """Get current market insights for specific industry and role."""
        try:
            insights_prompt = f"""
            Provide current market insights for {industry} industry, specifically for {job_title} roles:
            
            Return insights in this JSON format:
            {{
                "trending_skills": ["skill1", "skill2", ...],
                "salary_range": {{"min": 0, "max": 0, "currency": "USD"}},
                "growth_outlook": "description",
                "key_companies": ["company1", "company2", ...],
                "emerging_technologies": ["tech1", "tech2", ...],
                "certification_recommendations": ["cert1", "cert2", ...],
                "market_demand": "high/medium/low",
                "remote_opportunities": "percentage or description"
            }}
            """
            
            response = await self._route_to_model("industry_insights", insights_prompt)
            
            try:
                insights = json.loads(response)
                return insights
            except json.JSONDecodeError:
                return {
                    "trending_skills": [],
                    "growth_outlook": "Data unavailable",
                    "market_demand": "unknown"
                }
                
        except Exception as e:
            logger.error(f"Error getting industry insights: {e}")
            return {}
    
    async def _detect_industry(self, job_title: str, job_description: str) -> str:
        """Detect industry from job title and description."""
        text = f"{job_title} {job_description}".lower()
        
        # Simple keyword-based detection
        industry_keywords = {
            "technology": ["software", "developer", "engineer", "programming", "tech", "IT", "cloud", "data"],
            "finance": ["financial", "banking", "investment", "analyst", "accounting", "finance"],
            "healthcare": ["medical", "healthcare", "nurse", "doctor", "clinical", "patient"],
            "marketing": ["marketing", "digital", "social media", "advertising", "brand", "campaign"],
            "sales": ["sales", "business development", "account", "revenue", "client"]
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in text for keyword in keywords):
                return industry
        
        return "general"
    
    async def _route_to_model(self, task_type: str, prompt: str) -> str:
        """Route requests to appropriate AI model based on task type."""
        preferred_model = self.model_routing.get(task_type, "openai")
        
        try:
            if preferred_model == "claude" and self.claude_client:
                response = await self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif preferred_model == "gpt4" and self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif preferred_model == "openai" and self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif preferred_model == "z_ai" and self.z_ai_client:
                # Placeholder for Z.AI API call
                logger.info(f"Routing to Z.AI for task {task_type} with prompt: {prompt[:100]}...")
                # In a real scenario, you'd make an API call here
                # For now, return a mock response or a simple confirmation
                return f"Z.AI processed your chat request: '{prompt[:50]}...' (This is a mock response from Z.AI)"

            else:
                # Fallback to available model
                if self.claude_client:
                    response = await self.claude_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=2000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
                elif self.openai_client:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=2000
                    )
                    return response.choices[0].message.content
                else:
                    return "AI services are currently unavailable. Please check your API configuration."
                    
        except Exception as e:
            logger.error(f"AI service error for {task_type}: {e}")
            # Check if it's a quota exceeded error and provide mock responses
            if "insufficient_quota" in str(e) or "quota" in str(e).lower():
                return self._get_mock_response(task_type)
            else:
                return self._get_mock_response(task_type)
                
    def _get_mock_response(self, task_type: str) -> str:
        """Provide mock responses when AI services are unavailable."""
        mock_responses = {
            "resume_analysis": """**Resume Analysis Summary**
            
**Overall Assessment:** Your resume shows strong professional experience with good structure. Here are key insights:

**Experience Level:** Mid-level professional with 3-5 years of relevant experience

**ATS Compatibility:**
• Current Score: 85/100
• Issues: Minor keyword optimization needed, good formatting structure

**Key Skills Identified:**
• Project Management
• Data Analysis 
• Team Leadership
• Strategic Planning
• Communication
• Problem Solving
• Technology Proficiency
• Process Improvement

**Recommendations:**
• Add 2-3 more industry-specific keywords from target job descriptions
• Include quantifiable achievements with specific metrics
• Consider adding a professional summary section
• Update skills section with latest relevant technologies""",

            "chat_response": """Hello! I'm your AI resume optimization assistant. I'm here to help you create a standout resume that gets noticed by both ATS systems and hiring managers.

I can help you with:
• Analyzing your current resume for ATS compatibility
• Optimizing content for specific job applications  
• Providing industry-specific advice
• Improving keyword placement and formatting
• Crafting compelling achievement statements

Feel free to ask me any questions about your resume or career goals!""",

            "optimization_suggestions": """**Resume Optimization Suggestions:**

**Content Improvements:**
• Strengthen your professional summary with 2-3 key value propositions
• Add quantifiable achievements (increased efficiency by X%, managed $X budget)
• Include action verbs at the start of each bullet point
• Tailor keywords to match specific job descriptions

**Format & Structure:**
• Use consistent formatting throughout document
• Ensure 2-page maximum for most roles
• Include relevant technical skills section
• Consider adding industry certifications

**ATS Optimization:**
• Include relevant keywords naturally throughout content
• Use standard section headings (Experience, Education, Skills)
• Save as both .docx and .pdf formats
• Avoid graphics, tables, or complex formatting""",

            "ats_scoring": """{
                "overall_score": 82,
                "keyword_match": 78,
                "formatting_score": 88,
                "contact_info_score": 95,
                "experience_relevance": 85,
                "skills_alignment": 80,
                "issues": [
                    "Add more industry-specific keywords",
                    "Include quantified achievements", 
                    "Consider professional summary section"
                ],
                "recommendations": [
                    "Optimize keyword density for target role",
                    "Add metrics to demonstrate impact",
                    "Tailor content for specific applications"
                ]
            }""",

            "keyword_extraction": """["project management", "data analysis", "team leadership", "strategic planning", "process improvement", "stakeholder management", "budget management", "performance optimization", "cross-functional collaboration", "problem solving", "communication", "analytical thinking", "Microsoft Excel", "SQL", "Python", "Tableau", "project coordination", "quality assurance", "continuous improvement", "change management"]""",

            "industry_insights": """{
                "trending_skills": [
                    "Data Analytics",
                    "Cloud Computing", 
                    "AI/Machine Learning",
                    "Cybersecurity",
                    "Digital Transformation",
                    "Agile Methodology"
                ],
                "growth_outlook": "Strong growth expected with 15-20% increase in demand",
                "market_demand": "high",
                "remote_opportunities": "75% of positions offer remote or hybrid options"
            }"""
        }
        
        return mock_responses.get(task_type, "I'm working on your request and will provide helpful insights shortly. Thank you for your patience!")