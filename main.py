import os
import sys
import json
import time
from pathlib import Path
import psutil
from utils.preprocessing import run_parallel_preprocessing
from utils.comparison import run_parallel_comparison, save_results_to_csv

UPLOAD_DIR = "data/uploads"
PREPROCESSED_DIR = "data/preprocessed"
RESULTS_CSV = "data/results/similarity_results.csv"
PROGRESS_FILE = "data/progress.json"

def update_progress(completed, total, stage="", elapsed_time=0.0, cpu_usage=0.0, cpu_cores=0):
    """Write progress, timing, and CPU usage to a JSON file for Streamlit."""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "stage": stage,
                "completed_pairs": completed,
                "total_pairs": total,
                "elapsed_time_seconds": round(elapsed_time, 2),
                "cpu_usage_percent": round(cpu_usage, 2),
                "cpu_cores_used": cpu_cores
            }, f, ensure_ascii=False)
    except (IOError, OSError) as e:
        print(f"Error writing progress to {PROGRESS_FILE}: {e}")

def monitor_cpu_usage():
    """Get current CPU usage and number of cores."""
    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_count(logical=True)
        return cpu_usage, cpu_cores
    except Exception as e:
        print(f"Error monitoring CPU: {e}")
        return 0.0, psutil.cpu_count(logical=True) if hasattr(psutil, 'cpu_count') else 0

def main():
    """Main function to preprocess, compare files, and track time/CPU usage."""
    # Initialize directories
    try:
        os.makedirs(PREPROCESSED_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(RESULTS_CSV), exist_ok=True)
    except OSError as e:
        print(f"Failed to create directories: {e}")
        update_progress(0, 0, "error")
        return

    # Get uploaded files
    uploaded_files = [
        os.path.join(UPLOAD_DIR, f) for f in os.listdir(UPLOAD_DIR)
        if os.path.isfile(os.path.join(UPLOAD_DIR, f)) and Path(f).suffix.lower() in {'.py', '.cpp', '.h', '.cc', '.cxx', '.java'}
    ]
    
    if not uploaded_files:
        print("No valid files found in upload directory.")
        update_progress(0, 0, "error")
        return
    
    print(f"Found {len(uploaded_files)} files to preprocess.")
    
    # Preprocessing stage
    start_time = time.perf_counter()
    update_progress(0, len(uploaded_files), "preprocessing")
    try:
        preprocessed_files = run_parallel_preprocessing()
        preprocessed_files = [out_path for _, out_path in preprocessed_files if out_path]
        for i, _ in enumerate(preprocessed_files, 1):
            cpu_usage, cpu_cores = monitor_cpu_usage()
            elapsed_time = time.perf_counter() - start_time
            update_progress(i, len(uploaded_files), "preprocessing", elapsed_time, cpu_usage, cpu_cores)
    except Exception as e:
        print(f"Preprocessing failed: {e}")
        update_progress(0, 0, "error")
        return

    if not preprocessed_files:
        print("No files preprocessed successfully.")
        update_progress(0, 0, "error")
        return

    # Comparison stage
    total_pairs = (len(preprocessed_files) * (len(preprocessed_files) - 1)) // 2
    print(f"Comparing {total_pairs} file pairs in parallel...")
    start_time = time.perf_counter()
    update_progress(0, total_pairs, "comparison")
    try:
        results = run_parallel_comparison(preprocessed_files)
        for i, _ in enumerate(results, 1):
            cpu_usage, cpu_cores = monitor_cpu_usage()
            elapsed_time = time.perf_counter() - start_time
            update_progress(i, total_pairs, "comparison", elapsed_time, cpu_usage, cpu_cores)
    except Exception as e:
        print(f"Comparison failed: {e}")
        update_progress(0, 0, "error")
        return

    # Saving results stage
    print("Saving results to CSV...")
    start_time = time.perf_counter()
    update_progress(0, 1, "saving_csv")
    try:
        save_results_to_csv(results, RESULTS_CSV)
        cpu_usage, cpu_cores = monitor_cpu_usage()
        elapsed_time = time.perf_counter() - start_time
        update_progress(1, 1, "saving_csv", elapsed_time, cpu_usage, cpu_cores)
    except Exception as e:
        print(f"Failed to save results: {e}")
        update_progress(0, 0, "error")
        return

    # Completion
    cpu_usage, cpu_cores = monitor_cpu_usage()
    elapsed_time = time.perf_counter() - start_time
    print("✅ All steps completed. View the results in the Streamlit dashboard.")
    update_progress(1, 1, "completed", elapsed_time, cpu_usage, cpu_cores)

if __name__ == '__main__':
    # Ensure UTF-8 encoding for console output
    if sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')
    main()