import json
from sentence_transformers import SentenceTransformer
import time
import torch
from tqdm import tqdm

# --- Configuration ---
MODEL_NAME = 'multi-qa-mpnet-base-dot-v1'
# Input filename to process only reviews
INPUT_FILENAME = '1-2_filtered_review.json'
# Output filename
OUTPUT_FILENAME = '2-1_vector_embedded_review.jsonl'
ERROR_LOG_FILENAME = 'error_log_VE.txt'
BATCH_SIZE = 64
# Maximum text length (in characters) to process.
# Texts longer than this will be skipped to prevent model errors.
MAX_TEXT_LENGTH = 4096 
# --- End of Configuration ---

def get_total_lines(filename):
    """Quickly calculates the total number of lines in a file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for i, _ in enumerate(f, 1):
                pass
        return i
    except FileNotFoundError:
        return 0

def process_batch(model, data_list, text_list, outfile):
    """Embeds a batch of texts and writes them to the output file."""
    try:
        # Generate embeddings for the current batch of texts
        embeddings = model.encode(
            text_list, 
            convert_to_tensor=True, 
            show_progress_bar=False, # The main loop has its own progress bar
            batch_size=len(text_list)
        )

        # Move embeddings to CPU and convert to a standard Python list
        embeddings = embeddings.cpu().tolist()

        # Add the 'embedding' to each data object and write to the file
        for data, embedding in zip(data_list, embeddings):
            data['embedding'] = embedding
            outfile.write(json.dumps(data) + '\n')
            
    except Exception as e:
        # Handle potential errors during batch processing, like out-of-memory issues
        print(f"\nAn error occurred while processing a batch: {e}")
        # For simplicity, this script will skip the problematic batch.
        # You could add more robust logging here if needed.

def generate_embeddings():
    """
    Main function to read data, generate embeddings, and save the results.
    """
    # Check for GPU availability
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device.upper()}")

    # Load the Sentence Transformer model
    print(f"Loading model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME, device=device)
    print("Model loaded successfully!")

    # Pre-calculate the total number of lines for the progress bar
    total_lines = get_total_lines(INPUT_FILENAME)
    if total_lines == 0:
        print(f"Error: Input file '{INPUT_FILENAME}' not found or is empty.")
        return

    print(f"Found {total_lines} lines in '{INPUT_FILENAME}'.")

    # Open input, output, and error log files
    with open(INPUT_FILENAME, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILENAME, 'w', encoding='utf-8') as outfile, \
         open(ERROR_LOG_FILENAME, 'w', encoding='utf-8') as error_log:

        start_time = time.time()
        print(f"Starting file processing... (Batch Size: {BATCH_SIZE})")

        batch_data = []
        batch_texts = []

        # Use tqdm for a visual progress bar
        for i, line in enumerate(tqdm(infile, total=total_lines, desc="Processing Data"), 1):
            try:
                data_item = json.loads(line)
                text_to_embed = data_item.get('text')

                # --- Data Validation ---
                # Skip if text is missing or empty
                if not text_to_embed or not text_to_embed.strip():
                    error_log.write(f"Line {i}: Skipping due to empty text.\n")
                    continue
                
                # Skip if text is too long
                if len(text_to_embed) > MAX_TEXT_LENGTH:
                    error_log.write(f"Line {i}: Skipping due to excessive length ({len(text_to_embed)} chars).\n")
                    continue

                # Add valid data to the current batch
                batch_data.append(data_item)
                batch_texts.append(text_to_embed)

                # Process the batch when it's full
                if len(batch_texts) >= BATCH_SIZE:
                    process_batch(model, batch_data, batch_texts, outfile)
                    batch_data, batch_texts = [], [] # Reset the batch

            except Exception as e:
                # Log any other errors (e.g., malformed JSON)
                error_log.write(f"Line {i}: An error occurred - {e}\n")
                error_log.write(f"  --> Problematic line: {line.strip()}\n")

        # Process any remaining items in the last batch
        if batch_texts:
            process_batch(model, batch_data, batch_texts, outfile)

    end_time = time.time()
    print("-" * 40)
    print("All tasks completed!")
    print(f"Total processing time: {end_time - start_time:.2f} seconds")
    print(f"Results saved to: '{OUTPUT_FILENAME}'")
    print(f"Errors logged in: '{ERROR_LOG_FILENAME}'")

if __name__ == '__main__':
    # Check if tqdm is installed
    try:
        from tqdm import tqdm
    except ImportError:
        print("The 'tqdm' library is required. Please install it by running: pip install tqdm")
        exit()
        
    generate_embeddings()