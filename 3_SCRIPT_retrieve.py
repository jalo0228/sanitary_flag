import json
from sentence_transformers import SentenceTransformer, util
import torch
from collections import defaultdict
from tqdm import tqdm
import time

# --- Settings ---
# Model to use (must be the same as the one used for embedding)
MODEL_NAME = 'multi-qa-mpnet-base-dot-v1'

# Input and output filenames
INPUT_FILENAME = '2-1_vector_embedded_review.jsonl'
OUTPUT_FILENAME = '3-1_retrieved_review.json'
# --- End of Settings ---


def sort_and_clean_reviews(search_query):
    """
    Reads embedded reviews from a JSONL file, sorts all reviews for each
    business_id by their similarity to a given query, removes the 'embedding'
    field, and saves the result to a single JSON file.
    """
    # 1. Check for GPU availability and load the model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Loading '{MODEL_NAME}' model using '{device.upper()}' device...")
    model = SentenceTransformer(MODEL_NAME, device=device)
    print("Model loaded successfully.")

    # 2. Restructure data: Group reviews by business_id
    reviews_by_business = defaultdict(list)
    
    print(f"Reading and grouping data from '{INPUT_FILENAME}'...")
    with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
        for line in f:
            review_data = json.loads(line)
            if 'embedding' in review_data and review_data['embedding']:
                reviews_by_business[review_data['business_id']].append(review_data)
    print(f"Found {len(reviews_by_business)} unique businesses.")

    # 3. Convert the search query into a vector
    print(f"Encoding the search query: '{search_query}'")
    query_embedding = model.encode(search_query, convert_to_tensor=True, device=device)

    # 4. Calculate similarity, sort, and clean up for each business
    final_results = {}
    print("Calculating review similarity scores and sorting for each business...")
    
    for business_id, reviews_list in tqdm(reviews_by_business.items(), desc="Processing businesses"):
        
        corpus_embeddings = [review['embedding'] for review in reviews_list]
        corpus_tensor = torch.tensor(corpus_embeddings, device=device)
        
        # Calculate cosine similarity between the query and all reviews for this business
        cos_scores = util.cos_sim(query_embedding, corpus_tensor)[0]
        
        for i, review in enumerate(reviews_list):
            review['similarity_score'] = cos_scores[i].item()
            
        # Sort reviews by the calculated similarity score in descending order
        sorted_reviews = sorted(reviews_list, key=lambda x: x['similarity_score'], reverse=True)
        
        # Remove the 'embedding' field and keep only the necessary fields
        cleaned_reviews = []
        for review in sorted_reviews:
            cleaned_review = {
                'business_id': review.get('business_id'),
                'user_id': review.get('user_id'),
                'text': review.get('text'),
                'date': review.get('date'),
                'similarity_score': review.get('similarity_score')
            }
            cleaned_reviews.append(cleaned_review)
       
        # Store the cleaned list of reviews in the final results dictionary
        final_results[business_id] = cleaned_reviews

    # 5. Save the final results to the output file
    print(f"\nAll processing is complete. Saving results to '{OUTPUT_FILENAME}'...")
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
        
    print("Task complete!")


if __name__ == '__main__':
    # Set the default query
    default_query = "The place was disgusting, from the sticky tables and dirty floors to the filthy bathrooms."
    
    # Prompt the user to enter a query
    user_input = input(f"Enter a search query (or press Enter to use default):\n> ")
    
    # Check if the user provided input or just pressed Enter
    if user_input.strip():
        search_query = user_input
    else:
        search_query = default_query
        print("No query entered. Using the default query.")

    start_time = time.time()
    # Pass the selected query to the main function
    sort_and_clean_reviews(search_query)
    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")