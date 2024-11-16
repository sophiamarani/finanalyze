import google.generativeai as genai

class GeminiProcessor:
    
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro') # Optimized for text-only prompts
