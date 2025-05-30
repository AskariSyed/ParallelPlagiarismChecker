import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from pathlib import Path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.preprocessing import run_parallel_preprocessing
from helper import (
    clear_directory,
    initialize_directories,
    process_uploaded_files,
    display_summary,
    display_max_plagiarism_per_file,
    display_filtered_results,
    display_top_n_pairs,
    display_file_similarities
)

st.set_page_config(page_title="Parallel Code Plagiarism Checker", layout="wide")
st.title("🧪 Parallel Code Plagiarism Checker")


RESULTS_CSV = "data/results/similarity_results.csv"
UPLOAD_DIR = "data/uploads"
PROGRESS_FILE = "data/progress.json"
PREPROCESSED_DIR = "data/preprocessed"
HIGHLIGHTED_RESULTS_FILE = "data/highlighted_results.json"
VALID_EXTENSIONS = {'.py', '.cpp', '.h', '.cc', '.cxx', '.java'}
MAX_FILE_SIZE_MB = 10


def main():
    start_time = time.perf_counter()
    initialize_directories()
    
    st.sidebar.header("Upload Code Files")
    uploaded_files = st.sidebar.file_uploader(
        "Upload multiple code files (Python, C++, Java, etc.)",
        accept_multiple_files=True,
        help="Supported formats: .py, .cpp, .h, .cc, .cxx, .java"
    )
    if st.sidebar.button("Clear Uploaded Files"):
        clear_directory(UPLOAD_DIR)
        clear_directory(PREPROCESSED_DIR)
        
        clear_directory(os.path.dirname(RESULTS_CSV))
        if os.path.exists(HIGHLIGHTED_RESULTS_FILE):
            os.remove(HIGHLIGHTED_RESULTS_FILE)
        st.session_state.clear()
        st.sidebar.success("✅ Cleared all uploaded files and results.")
    
    if "results_df" not in st.session_state and process_uploaded_files(uploaded_files) and os.path.exists(RESULTS_CSV):
        st.session_state.results_df = pd.read_csv(RESULTS_CSV)
    
    if "results_df" in st.session_state:
        df = st.session_state.results_df
        display_summary(df)
        display_max_plagiarism_per_file(df)
        display_filtered_results(df)
        display_top_n_pairs(df)
        display_file_similarities(df)
    else:
        st.info("Upload files to generate results.")
    
    st.write(f"Total app runtime: {time.perf_counter() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()