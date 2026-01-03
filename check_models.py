import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- Setup ---
# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env file.")
else:
    try:
        # Configure the client library with your API key
        genai.configure(api_key=api_key)

        print("--- Available Google Generative AI Models ---")
        # List the available models
        for m in genai.list_models():
            # Check if the model supports the 'generateContent' method
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
        print("---------------------------------------------")
        print("\nPlease identify a model from the list above (e.g., 'models/gemini-1.5-flash-latest', 'models/text-bison-001', etc.).")
        print("We will use this name in the application configuration.")

    except Exception as e:
        print(f"An error occurred while trying to list the models: {e}")
        print("Please ensure your GOOGLE_API_KEY is correct and has the 'Generative Language API' enabled in your Google Cloud project.")
