import json
import google.generativeai as genai
import time
import os
from datetime import datetime

# --- Configuration ---

"""
# It's recommended to use environment variables for security.
API_KEY = os.getenv("GEMINI_API_KEY") 

# For simplicity, we will type in our API key in this project.
"""

# PASTE YOUR API KEY HERE:
API_KEY = "???" # Sanitary Flag gmail ID, payment unlinked, created by Jinhyeok

# The name of your JSON file from the Yelp dataset
FILE_PATH = '3-1_retrieved_review.json' 

# The number of top reviews to select for each restaurant
TOP_K = 3   

# The output file path for the summaries
OUTPUT_FILE_PATH = '4-1_LLM_initial_summary.json'

# The file path for logging errors
ERROR_LOG_FILE = 'error_log_LLM.txt'

# Delay of 2.5 seconds between calls to stay within the 30 RPM free limit
DELAY_BETWEEN_CALLS = 2.5

# --- Functions ---

def load_reviews(file_path):
    """Loads reviews from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file '{file_path}'.")
        return None

def get_top_reviews(reviews_data, k):
    """Selects the top k reviews for each business based on similarity score."""
    top_reviews = {}
    for business_id, reviews in reviews_data.items():
        # Sort reviews by 'similarity_score' in descending order
        sorted_reviews = sorted(reviews, key=lambda x: x['similarity_score'], reverse=True)
        top_reviews[business_id] = sorted_reviews[:k]
    return top_reviews

def summarize_reviews_with_gemini(model, reviews):
    """
    Summarizes a list of reviews using the provided Gemini model instance.
    This function will now raise an exception on failure, to be handled by the main loop.
    """

    # This is the prompt that is fed to the LLM
    prompt_text = """Your task is to analyze the following customer feedback for sanitation information and generate a summary.

Your entire response MUST follow these rules strictly:
1.  Begin the response with ONLY ONE of the following emojis: 🔴 (significant sanitation issues), 🟡 (minor sanitation issues), or 🟢 (no/positive sanitation issues).
2.  Do NOT include any introductory text, titles, or conversational phrases before the emoji.
3.  After the emoji, write a single, cohesive paragraph of 2-3 short sentences.
4.  Phrase the summary as a direct, objective statement about the establishment. Avoid referencing the source of the information (e.g., do not use words like 'reviews', 'customers', 'reviewers').

Here is a perfect example of the required output format:
"🔴
This establishment faces notable sanitation challenges. Reported issues include chefs handling food without gloves, tables being left dirty, and unclean restrooms."

Now, process the following feedback:"""

    for i, review in enumerate(reviews, 1):
        prompt_text += f"Review {i}: {review['text']}\n"
    
    # The 'generate_content' call can raise various exceptions (e.g., rate limit, server error)
    response = model.generate_content(prompt_text)
    return response.text

def log_error(log_file, business_id, error):
    """Logs detailed error information to a text file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_type = type(error).__name__
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"--- ERROR LOG ---\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Business ID: {business_id}\n")
        f.write(f"Error Type: {error_type}\n")
        f.write(f"Error Details: {error}\n\n")

# --- Main Script ---

if __name__ == "__main__":
    all_reviews_data = load_reviews(FILE_PATH)

    if all_reviews_data:
        # Configure the Gemini API
        genai.configure(api_key=API_KEY)

        # 30 RPM
        model = genai.GenerativeModel('gemini-2.0-flash-lite')

        top_reviews_per_restaurant = get_top_reviews(all_reviews_data, TOP_K)
        
        # --- Get user input for sample size ---
        num_to_process = 0
        while True:
            sample_input = input(f"Enter the number of restaurants to process (or press Enter to process all {len(top_reviews_per_restaurant)}): ")
            if not sample_input:
                num_to_process = len(top_reviews_per_restaurant)
                break
            try:
                num_to_process = int(sample_input)
                if 0 < num_to_process <= len(top_reviews_per_restaurant):
                    break
                else:
                    print(f"Please enter a number between 1 and {len(top_reviews_per_restaurant)}.")
            except ValueError:
                print("Invalid input. Please enter a whole number.")
        
        # Get the items to process based on user input
        items_to_process = list(top_reviews_per_restaurant.items())[:num_to_process]
        total_restaurants_to_process = len(items_to_process)
        
        # --- Use a list of dictionaries for structured output ---
        all_results = []
        
        print(f"\nStarting to process {total_restaurants_to_process} restaurants using Gemini...")

        for i, (business_id, reviews) in enumerate(items_to_process):
            print(f"Processing restaurant {i + 1}/{total_restaurants_to_process} (ID: {business_id})... ", end="")
            
            try:
                # --- Handle API calls and errors within the loop ---
                summary = summarize_reviews_with_gemini(model, reviews)
                result = {
                    "business_id": business_id,
                    "status": "success",
                    "summary": summary.strip()
                }
                print("Success")

            except Exception as e:
                # If an error occurs, log it and create an error entry
                print(f"Error")
                log_error(ERROR_LOG_FILE, business_id, e)
                result = {
                    "business_id": business_id,
                    "status": "error",
                    "summary": "ERROR"
                }

            all_results.append(result)
            
            # Sleep only if it's not the last item
            if i < total_restaurants_to_process - 1:
                time.sleep(DELAY_BETWEEN_CALLS)
        
        # Save the structured results to the output file
        with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=4)
        
        print(f"\nAll done! Summaries have been saved to '{OUTPUT_FILE_PATH}'")
        print(f"Errors, if any, have been logged to '{ERROR_LOG_FILE}'")