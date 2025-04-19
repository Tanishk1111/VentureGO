import asyncio
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from config import API_KEY

# Configure Gemini
genai.configure(api_key=API_KEY)

def analyze_sentiment(text: str) -> Dict[str, float]:
    """Analyze sentiment in interview responses"""
    negative_words = [
        "no", "not", "never", "disagree", "bad", "difficult", 
        "problem", "issue", "challenging", "worried", "concerned",
        "unsure", "unclear", "unfortunately", "fail"
    ]
    
    positive_words = [
        "yes", "agree", "good", "great", "excellent", "success", 
        "opportunity", "excited", "confident", "proven", "growth",
        "improvement", "innovative", "solution", "profit"
    ]
    
    # Count occurrences of positive and negative words
    negative_count = sum(1 for word in text.lower().split() if word in negative_words)
    positive_count = sum(1 for word in text.lower().split() if word in positive_words)
    
    # Calculate sentiment score
    total = negative_count + positive_count
    if total == 0:
        return {"score": 0, "magnitude": 0}
        
    score = (positive_count - negative_count) / total
    magnitude = total / len(text.split())
    
    return {
        "score": score,
        "magnitude": magnitude
    }

async def analyze_single_response(question: str, actual: str, expected: str) -> str:
    """Analyze a single interview response using Gemini"""
    prompt = f"""
    Evaluate this VC interview response:
    
    Question: {question}
    
    Expected answer criteria: {expected}
    
    Candidate's actual answer: {actual}
    
    Provide detailed feedback on:
    1. How well the answer meets investor expectations
    2. Strength of the business understanding demonstrated
    3. Specific improvements that would make the answer more compelling
    4. Score (1-10) with justification
    
    Be specific about what was good and what could be better.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(prompt)
        
        return response.text if hasattr(response, 'text') else str(response)
    except Exception as e:
        print(f"Error analyzing response: {e}")
        return "Analysis error: Could not process this response."

async def analyze_responses(responses: List[str], expected: List[str], questions: List[str]) -> Dict[str, Any]:
    """Analyze interview responses and generate feedback"""
    # Generate individual feedback for each response
    tasks = []
    for i, (question, actual, expected_ans) in enumerate(zip(questions, responses, expected)):
        tasks.append(analyze_single_response(question, actual, expected_ans))
    
    individual_feedback = await asyncio.gather(*tasks)
    
    # Organize individual feedback into a dictionary
    detailed_feedback = {}
    for i, feedback in enumerate(individual_feedback):
        detailed_feedback[f"question_{i+1}"] = feedback
    
    # Generate overall summary
    try:
        combined_feedback = "\n\n".join([
            f"Question {i+1}: {questions[i]}\nResponse: {responses[i]}\nFeedback: {feedback}"
            for i, feedback in enumerate(individual_feedback)
        ])
        
        summary_prompt = f"""
        Based on this detailed VC interview feedback, provide a concise executive summary 
        of the candidate's performance:
        
        {combined_feedback[:4000]}  # Limit to avoid token limits
        
        Include:
        1. Overall assessment (1-10 score)
        2. Key strengths with specific examples
        3. Top 3 areas for improvement
        4. Final recommendation to investors
        
        Format your response as a VC partner would deliver feedback.
        """
        
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        summary_response = model.generate_content(summary_prompt)
        summary_text = summary_response.text if hasattr(summary_response, 'text') else str(summary_response)
        
        # Extract score from summary if present
        score = None
        for line in summary_text.split('\n'):
            if 'score' in line.lower():
                try:
                    # Try to extract a number from the line
                    import re
                    numbers = re.findall(r'\b(\d+)/10\b|\b(\d+) out of 10\b|\bscore.*?(\d+)\b', line.lower())
                    if numbers:
                        # Flatten the results and get the first match
                        flattened = [n for group in numbers for n in group if n]
                        if flattened:
                            score = float(flattened[0])
                except:
                    pass
    except Exception as e:
        print(f"Error generating summary: {e}")
        summary_text = "Could not generate interview summary."
        score = None
    
    return {
        "detailed_feedback": detailed_feedback,
        "summary": summary_text,
        "score": score
    }
