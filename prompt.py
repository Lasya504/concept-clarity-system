def build_prompt(term, language='en'):
    return f"""
You are a scientific tutor who excels at making complex concepts clear.

Explain the following term in simple language.

Include:
1. Definition
2. How it works
3. Why it matters
4. A relatable analogy
5. Two related scientific terms
6. One real-life example

Also generate a short quiz to test understanding.

Return ONLY valid JSON in this format:

{{
 "term": "{term}",
 "explanation": "...",
 "related_terms": ["term1","term2"],
 "real_life_example": "...",

 "quiz_question": "A conceptual question about the term",

 "quiz_options": [
   "Option A",
   "Option B",
   "Option C",
   "Option D"
 ],

 "correct_answer": "One of the options"
}}

Term: {term}
Language: {language}
"""