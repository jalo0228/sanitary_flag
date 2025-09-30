import json

# --- 1. FILE CONFIGURATION ---
# Input files from the Yelp Dataset
BUSINESS_INPUT_FILE = 'yelp_academic_dataset_business.json'
REVIEW_INPUT_FILE = 'yelp_academic_dataset_review.json'

# Output files that will be generated
BUSINESS_OUTPUT_FILE = '1-1_filtered_business.json'
REVIEW_OUTPUT_FILE = '1-2_filtered_review.json'


# --- 2. FILTERING FUNCTIONS ---

def filter_businesses(target_state, target_categories):
    """
    Filters the business dataset based on state and categories.
    Returns a set of matching business IDs and processing statistics.
    """
    print(f"Step 1/2: Filtering businesses in '{BUSINESS_INPUT_FILE}'...")
    business_ids_to_keep = set()
    lines_processed, lines_skipped = 0, 0

    try:
        with open(BUSINESS_INPUT_FILE, 'r', encoding='utf-8') as infile, \
             open(BUSINESS_OUTPUT_FILE, 'w', encoding='utf-8') as outfile:

            for line in infile:
                lines_processed += 1
                try:
                    business_data = json.loads(line)
                    if business_data.get('state') == target_state and business_data.get('is_open') == 1:
                        categories = business_data.get('categories')
                        if categories:
                            category_list = {cat.strip() for cat in categories.split(',')}
                            if not target_categories.isdisjoint(category_list):
                                business_id = business_data.get('business_id')
                                if business_id:
                                    business_ids_to_keep.add(business_id)
                                    filtered_data = {
                                        'business_id': business_id, 'name': business_data.get('name'),
                                        'address': business_data.get('address'), 'city': business_data.get('city'),
                                        'state': business_data.get('state'), 'postal_code': business_data.get('postal_code')
                                    }
                                    outfile.write(json.dumps(filtered_data) + '\n')
                except json.JSONDecodeError:
                    lines_skipped += 1
                    continue
        
        print(f"- Successfully created '{BUSINESS_OUTPUT_FILE}'.\n")
        stats = {'processed': lines_processed, 'skipped': lines_skipped, 'matched': len(business_ids_to_keep)}
        return business_ids_to_keep, stats

    except FileNotFoundError:
        print(f"ERROR: Input file '{BUSINESS_INPUT_FILE}' not found. Aborting.")
        return None, {'processed': 0, 'skipped': 0, 'matched': 0}

def filter_reviews(business_ids):
    """
    Filters reviews based on a set of business_ids and saves them to an output file.
    Returns processing statistics.
    """
    print(f"Step 2/2: Filtering reviews...")
    
    # Initialize statistics counters
    stats = {'processed': 0, 'skipped': 0, 'matched': 0}

    if not business_ids:
        print("- No business IDs to filter by. Skipping.")
        open(REVIEW_OUTPUT_FILE, 'w').close() # Create an empty file
        return stats

    with open(REVIEW_OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        # Process the review file
        try:
            print(f"- Processing '{REVIEW_INPUT_FILE}'...")
            with open(REVIEW_INPUT_FILE, 'r', encoding='utf-8') as infile:
                for line in infile:
                    stats['processed'] += 1
                    try:
                        data = json.loads(line)
                        if data.get('business_id') in business_ids:
                            stats['matched'] += 1
                            filtered_item = {
                                'business_id': data.get('business_id'), 'user_id': data.get('user_id'),
                                'text': data.get('text'), 'date': data.get('date')
                            }
                            outfile.write(json.dumps(filtered_item) + '\n')
                    except (json.JSONDecodeError, KeyError):
                        stats['skipped'] += 1
                        continue
        except FileNotFoundError:
            print(f"WARNING: Review file '{REVIEW_INPUT_FILE}' not found. Skipping.")

    print(f"- Successfully created '{REVIEW_OUTPUT_FILE}'.\n")
    return stats


# --- 3. MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    print("--- Yelp Dataset Filter ---")
    
    state_input = input("Enter state abbreviation (e.g., PA). Press Enter for default [IL]: ").strip().upper()
    target_state = state_input if state_input else 'IL'

    category_input = input("Enter comma-separated categories. Press Enter for default [Cafes,Bars,Restaurants]: ").strip()
    if not category_input:
        target_categories = {'Cafes', 'Bars', 'Restaurants'}
    else:
        target_categories = {cat.strip() for cat in category_input.split(',')}

    print("\nStarting Filtering Process...")
    
    # Step 1: Filter businesses
    filtered_ids, business_stats = filter_businesses(target_state, target_categories)
    
    # Step 2: Filter reviews
    review_stats = filter_reviews(filtered_ids) if filtered_ids is not None else None

    # Step 3: Print summary
    if filtered_ids is not None and review_stats is not None:
        print("--- Processing Summary ---")
        print(f"Filter Criteria:")
        print(f" - State: {target_state}")
        print(f" - Categories: {', '.join(target_categories)}")
        print("-" * 30)
        print("Business File:")
        print(f" - Lines Processed: {business_stats['processed']:,}")
        print(f" - Lines Skipped (Error): {business_stats['skipped']:,}")
        print(f" - Matched Businesses Found: {business_stats['matched']:,}")
        print("-" * 30)
        print("Review File:")
        print(f" - Reviews Processed: {review_stats['processed']:,}")
        print(f" - Reviews Skipped (Error): {review_stats['skipped']:,}")
        print(f" - Total Reviews Saved: {review_stats['matched']:,}")
        print("--- All tasks completed successfully! ---")
    else:
        print("--- Process halted due to an error. ---")