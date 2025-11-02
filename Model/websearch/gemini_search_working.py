"""
Simple Gemini Web Search using google.generativeai
This works with standard Gemini API - no special access needed!
"""

import os
import google.generativeai as genai

# Configure API
GEMINI_API_KEY = ""

genai.configure(api_key=GEMINI_API_KEY)

def search_with_gemini(query, model_name="gemini-2.0-flash-exp"):
    """
    Use Gemini to answer questions (Gemini has built-in knowledge up to recent data)
    
    Args:
        query (str): The question or search query
        model_name (str): Gemini model to use
        
    Returns:
        str: The answer from Gemini
    """
    
    print(f"\n🔍 Query: {query}")
    print("⏳ Asking Gemini...")
    
    try:
        # Create the model
        model = genai.GenerativeModel(model_name)
        
        # Enhanced prompt to get web-like answers
        enhanced_query = f"""You are a helpful assistant with access to up-to-date information. 
Please answer the following question accurately and provide relevant details:

{query}

If you're not certain about current information, please say so."""
        
        # Generate response
        response = model.generate_content(enhanced_query)
        
        print("\n✅ Answer:")
        print("=" * 70)
        print(response.text)
        print("=" * 70)
        
        return response.text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def search_with_sources(query):
    """
    Use Gemini to answer with explicit request for sources
    """
    print(f"\n🔍 Query: {query}")
    print("⏳ Asking Gemini for answer with sources...")
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # Prompt that asks for sources
        prompt = f"""Answer this question and provide sources/references where possible:

{query}

Please structure your answer with:
1. A clear answer
2. Key points
3. Sources or references (if applicable)"""
        
        response = model.generate_content(prompt)
        
        print("\n✅ Answer with Sources:")
        print("=" * 70)
        print(response.text)
        print("=" * 70)
        
        return response.text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🌐 Gemini Search Assistant (Using google.generativeai)")
    print("=" * 70)
    
    # Example queries
    examples = [
        "What is the YouTube Analytics API and how do I use it?",
        "What are the latest features in Google Cloud Platform 2024?",
        "Compare YouTube Shorts vs TikTok for business marketing",
        "How to optimize YouTube Shorts for maximum views?"
    ]
    
    print("\n📋 Running example searches...\n")
    
    for i, query in enumerate(examples, 1):
        print(f"\n{'='*70}")
        print(f"Example {i}")
        print('='*70)
        search_with_gemini(query)
        
        if i < len(examples):
            input("\nPress Enter to continue to next example...")
    
    print("\n\n🎯 Interactive Mode")
    print("=" * 70)
    print("Ask your own questions (or type 'quit' to exit)")
    
    while True:
        user_query = input("\n❓ Your question: ").strip()
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not user_query:
            continue
        
        search_with_gemini(user_query)
