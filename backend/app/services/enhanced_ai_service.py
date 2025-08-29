import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
import anthropic
from app.core.config import settings
from app.services.ai_service import AIService

class EnhancedAIService(AIService):
    def __init__(self):
        super().__init__()
        self.conversation_memory = {}
        
    async def generate_enhanced_response(self, message: str, context: Dict, session_id: str) -> Dict[str, Any]:
        """Generate enhanced response with context awareness and suggestions."""
        
        # Build context from conversation history
        conversation_context = self.conversation_memory.get(session_id, [])
        
        enhanced_prompt = f"""
        You are an expert resume optimization AI assistant. Generate a helpful response with:
        
        User Message: {message}
        Context: {json.dumps(context, indent=2)}
        Conversation History: {json.dumps(conversation_context[-5:], indent=2)}
        
        Provide a structured response in this JSON format:
        {{
            "message": "Your helpful response",
            "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
            "actions": [
                {{"label": "Action Name", "action": "action_id", "description": "What this does"}},
            ],
            "confidence": 0.9,
            "follow_up_questions": ["question 1", "question 2"]
        }}
        
        Guidelines:
        - Be conversational yet professional
        - Provide actionable suggestions
        - Include relevant follow-up questions
        - Keep responses concise but informative
        - Use emojis sparingly but effectively
        """
        
        try:
            response = await self._route_to_model("chat_response", enhanced_prompt)
            
            # Try to parse as JSON, fallback to simple response
            try:
                parsed_response = json.loads(response)
                
                # Store in conversation memory
                if session_id not in self.conversation_memory:
                    self.conversation_memory[session_id] = []
                
                self.conversation_memory[session_id].extend([
                    {"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()},
                    {"role": "assistant", "content": parsed_response["message"], "timestamp": datetime.utcnow().isoformat()}
                ])
                
                return parsed_response
                
            except json.JSONDecodeError:
                return {
                    "message": response,
                    "suggestions": [],
                    "actions": [],
                    "confidence": 0.8
                }
                
        except Exception as e:
            return {
                "message": "I apologize, but I'm experiencing some technical difficulties. Please try again.",
                "suggestions": ["Try rephrasing your question", "Upload a resume to get started"],
                "actions": [],
                "confidence": 0.1
            }

    async def enhanced_resume_analysis(self, resume_data: Dict) -> Dict[str, Any]:
        """Perform comprehensive resume analysis with visual data."""
        
        content = resume_data.get("content", "")
        
        analysis_prompt = f"""
        Perform a comprehensive analysis of this resume:
        
        Resume Content:
        {content}
        
        Provide analysis in this JSON format:
        {{
            "overall_score": 85,
            "summary": "Brief overview of the resume quality",
            "strengths": ["strength 1", "strength 2", "strength 3"],
            "weaknesses": ["weakness 1", "weakness 2"],
            "score_breakdown": {{
                "formatting": 90,
                "content_quality": 80,
                "keywords": 75,
                "experience": 85,
                "skills": 88,
                "education": 92
            }},
            "skills_analysis": {{
                "technical_skills": ["Python", "JavaScript", "React"],
                "soft_skills": ["Leadership", "Communication"],
                "missing_skills": ["Docker", "AWS"],
                "skill_strength": {{
                    "Python": 95,
                    "JavaScript": 85,
                    "React": 80
                }}
            }},
            "industry_detection": {{
                "primary": "Technology",
                "confidence": 0.95,
                "secondary": ["Software Development", "Web Development"]
            }},
            "experience_level": {{
                "level": "Mid-Level",
                "years": 5,
                "confidence": 0.9
            }},
            "ats_compatibility": {{
                "score": 78,
                "issues": ["Missing keywords", "Complex formatting"],
                "improvements": ["Add more industry keywords", "Simplify formatting"]
            }},
            "recommendations": [
                {{
                    "type": "content",
                    "priority": "high",
                    "title": "Add Quantifiable Achievements",
                    "description": "Include specific metrics and numbers",
                    "example": "Increased team productivity by 25%"
                }},
                {{
                    "type": "keywords",
                    "priority": "medium", 
                    "title": "Optimize Keywords",
                    "description": "Add relevant industry terms",
                    "keywords": ["API", "Database", "Agile"]
                }}
            ],
            "next_steps": [
                "Review recommendations above",
                "Upload job description for targeted optimization",
                "Generate optimized version"
            ]
        }}
        """
        
        try:
            response = await self._route_to_model("resume_analysis", analysis_prompt)
            analysis = json.loads(response)
            return analysis
            
        except Exception as e:
            return {
                "overall_score": 70,
                "summary": "Analysis completed with limited data",
                "error": str(e)
            }

    async def generate_enhanced_optimizations(self, session_id: str, optimization_type: str, job_description: str = "") -> Dict[str, Any]:
        """Generate detailed optimizations with before/after examples."""
        
        optimization_prompt = f"""
        Generate detailed optimization suggestions for: {optimization_type}
        
        Job Description: {job_description}
        
        Provide response in this JSON format:
        {{
            "optimizations": [
                {{
                    "section": "Professional Summary",
                    "current": "Current text...",
                    "improved": "Improved text...",
                    "explanation": "Why this is better",
                    "impact": "Expected improvement",
                    "keywords_added": ["keyword1", "keyword2"]
                }}
            ],
            "score_improvement": {{
                "before": 75,
                "after": 88,
                "improvement": 13,
                "breakdown": {{
                    "keywords": +5,
                    "content": +4,
                    "formatting": +2,
                    "ats": +2
                }}
            }},
            "before_after": {{
                "key_changes": [
                    "Added quantifiable achievements",
                    "Improved keyword density",
                    "Enhanced action verbs"
                ],
                "word_count": {{
                    "before": 450,
                    "after": 485
                }},
                "keyword_density": {{
                    "before": 2.1,
                    "after": 3.4
                }}
            }},
            "implementation_guide": [
                "Step 1: Update professional summary",
                "Step 2: Revise experience section", 
                "Step 3: Add relevant keywords"
            ]
        }}
        """
        
        try:
            response = await self._route_to_model("optimization_suggestions", optimization_prompt)
            return json.loads(response)
            
        except Exception as e:
            return {
                "optimizations": [],
                "score_improvement": {"improvement": 0},
                "error": str(e)
            }

    async def analyze_job_match(self, session_id: str, job_description: str) -> Dict[str, Any]:
        """Analyze how well resume matches job requirements."""
        
        # Get resume data from session context (simplified for demo)
        match_prompt = f"""
        Analyze job match compatibility:
        
        Job Description: {job_description}
        
        Provide detailed matching analysis in JSON format:
        {{
            "overall_score": 82,
            "compatibility_level": "High",
            "strengths": [
                "Strong technical skills match",
                "Relevant experience in similar roles",
                "Education aligns with requirements"
            ],
            "gaps": [
                "Missing AWS experience",
                "No project management experience",
                "Limited team leadership examples"
            ],
            "skills_match": {{
                "technical": {{
                    "matched": ["Python", "React", "SQL"],
                    "missing": ["Docker", "Kubernetes"],
                    "score": 85
                }},
                "soft": {{
                    "matched": ["Communication", "Problem Solving"],
                    "missing": ["Leadership", "Mentoring"],
                    "score": 75
                }}
            }},
            "experience_match": {{
                "years_required": "3-5 years",
                "years_candidate": "4 years",
                "relevance_score": 90,
                "similar_roles": ["Software Developer", "Frontend Developer"]
            }},
            "keyword_match": {{
                "total_keywords": 25,
                "matched_keywords": 18,
                "missing_keywords": ["DevOps", "CI/CD", "Microservices"],
                "match_percentage": 72
            }},
            "recommendations": [
                {{
                    "priority": "high",
                    "action": "Add AWS certification or experience",
                    "impact": "Would increase match score by 8%"
                }},
                {{
                    "priority": "medium",
                    "action": "Highlight any leadership examples",
                    "impact": "Would increase match score by 5%"
                }}
            ],
            "probability_estimates": {{
                "interview_chance": 75,
                "hire_probability": 60,
                "factors": [
                    "Strong technical match",
                    "Good experience level",
                    "Some skill gaps"
                ]
            }}
        }}
        """
        
        try:
            response = await self._route_to_model("ats_scoring", match_prompt)
            return json.loads(response)
            
        except Exception as e:
            return {
                "overall_score": 0,
                "error": str(e)
            }

    async def get_daily_tips(self) -> List[Dict[str, str]]:
        """Get daily resume optimization tips."""
        
        tips_prompt = """
        Provide 3 actionable resume tips for today in JSON format:
        [
            {
                "title": "Tip Title",
                "description": "Detailed explanation",
                "example": "Concrete example",
                "category": "keywords|formatting|content|strategy"
            }
        ]
        """
        
        try:
            response = await self._route_to_model("chat_response", tips_prompt)
            return json.loads(response)
        except:
            return [
                {
                    "title": "Use Action Verbs",
                    "description": "Start bullet points with strong action verbs",
                    "example": "Developed, Implemented, Managed, Led",
                    "category": "content"
                }
            ]

    async def get_real_time_insights(self, industry: str, role: str) -> Dict[str, Any]:
        """Get real-time market insights for industry and role."""
        
        insights_prompt = f"""
        Provide current market insights for {role} in {industry}:
        
        Return JSON format:
        {{
            "market_demand": "High/Medium/Low",
            "salary_trends": {{
                "range": "$80,000 - $120,000",
                "growth": "+5% YoY"
            }},
            "hot_skills": ["skill1", "skill2", "skill3"],
            "emerging_trends": ["trend1", "trend2"],
            "job_outlook": "Positive growth expected",
            "remote_opportunities": "High",
            "top_employers": ["Company A", "Company B"],
            "recommendations": [
                "Focus on cloud technologies",
                "Develop leadership skills"
            ]
        }}
        """
        
        try:
            response = await self._route_to_model("industry_insights", insights_prompt)
            return json.loads(response)
        except Exception as e:
            return {"error": str(e)}

    async def generate_interview_prep(self, job_description: str, resume_data: Dict) -> Dict[str, Any]:
        """Generate interview preparation based on job match."""
        
        prep_prompt = f"""
        Generate interview preparation based on job match:
        
        Job Description: {job_description}
        
        Return comprehensive interview prep in JSON:
        {{
            "likely_questions": [
                {{
                    "question": "Tell me about your experience with...",
                    "category": "technical",
                    "difficulty": "medium",
                    "tips": "Focus on specific examples"
                }}
            ],
            "technical_topics": ["Topic 1", "Topic 2"],
            "behavioral_scenarios": [
                "Describe a challenging project",
                "How do you handle tight deadlines"
            ],
            "questions_to_ask": [
                "What does success look like in this role?",
                "What are the biggest challenges facing the team?"
            ],
            "preparation_checklist": [
                "Research company values",
                "Prepare STAR method examples",
                "Practice technical concepts"
            ]
        }}
        """
        
        try:
            response = await self._route_to_model("chat_response", prep_prompt)
            return json.loads(response)
        except Exception as e:
            return {"error": str(e)}