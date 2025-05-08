import os
from utils.preprocessing import run_parallel_preprocessing
from utils.comparison import run_parallel_comparison, save_results_to_csv

# Define paths
UPLOAD_DIR = "data/uploads"
PREPROCESSED_DIR = "data/preprocessed"
RESULTS_CSV = "data/results/similarity_results.csv"

def main():
    # Ensure directories exist
    if not os.path.exists(PREPROCESSED_DIR):
        os.makedirs(PREPROCESSED_DIR)
    if not os.path.exists(os.path.dirname(RESULTS_CSV)):
        os.makedirs(os.path.dirname(RESULTS_CSV))

    # Step 1: List uploaded files
    uploaded_files = [os.path.join(UPLOAD_DIR, f) for f in os.listdir(UPLOAD_DIR)
                      if os.path.isfile(os.path.join(UPLOAD_DIR, f))]

    # Step 2: Preprocess files in parallel
    try:
        print("Preprocessing files...")
        preprocessed_files = run_parallel_preprocessing()  # Use run_parallel_preprocessing instead of preprocess_all
    except Exception as e:
        print(f"Error during preprocessing: {e}")
        exit(1)

    # Extract preprocessed file paths
    preprocessed_files = [out_path for _, out_path in preprocessed_files if out_path]

    # Step 3: Run parallel comparison
    try:
        print("Comparing files in parallel...")
        results = run_parallel_comparison(preprocessed_files)
    except Exception as e:
        print(f"Error during comparison: {e}")
        exit(1)

    # Step 4: Save to CSV
    try:
        print("Saving results to CSV...")
        save_results_to_csv(results, RESULTS_CSV)
    except Exception as e:
        print(f"Error saving results to CSV: {e}")
        exit(1)

    print("✅ All steps completed. View the results in the Streamlit dashboard.")

if __name__ == '__main__':
    main()
