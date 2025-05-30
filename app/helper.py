import os
import json
import shutil
import time
import pandas as pd
import psutil
import multiprocessing
from pathlib import Path
import streamlit as st
import plotly.express as px
from utils.preprocessing import run_parallel_preprocessing
from utils.comparison import run_parallel_comparison, save_results_to_csv, compare_pair



RESULTS_CSV = "data/results/similarity_results.csv"
UPLOAD_DIR = "data/uploads"
PROGRESS_FILE = "data/progress.json"
PREPROCESSED_DIR = "data/preprocessed"
HIGHLIGHTED_RESULTS_FILE = "data/highlighted_results.json"
VALID_EXTENSIONS = {'.py', '.cpp', '.h', '.cc', '.cxx', '.java'}
MAX_FILE_SIZE_MB = 10


def clear_directory(directory):
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    except Exception as e:
        st.error(f"Error clearing directory {directory}: {e}")


def initialize_directories():
    for directory in [UPLOAD_DIR, PREPROCESSED_DIR, os.path.dirname(RESULTS_CSV)]:
        os.makedirs(directory, exist_ok=True)



def update_progress(completed, total, stage=""):
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "stage": stage,
                "completed_pairs": completed,
                "total_pairs": total
            }, f, ensure_ascii=False)
    except (IOError, OSError) as e:
        st.warning(f"Error writing progress: {e}")
        

def monitor_cpu_usage():
    try:
        return psutil.cpu_percent(interval=0.5), psutil.cpu_count(logical=True)
    except Exception:
        return 0.0, multiprocessing.cpu_count()


def process_uploaded_files(uploaded_files):
    start_time = time.perf_counter()
    if not uploaded_files:
        st.info("Please upload code files to begin.")
        return False
    
    for file in uploaded_files:
        if Path(file.name).suffix.lower() not in VALID_EXTENSIONS:
            st.error(f"Invalid file type for {file.name}. Supported formats: {', '.join(VALID_EXTENSIONS)}")
            return False
        if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"File {file.name} exceeds {MAX_FILE_SIZE_MB}MB size limit.")
            return False
    
    total_files = len(uploaded_files)
    total_steps = total_files + 1
    progress_bar = st.progress(0)
    status_text = st.sidebar.empty()
    status_text.info("⏳ Uploading files...")
    
    uploaded_file_paths = []
    for i, file in enumerate(uploaded_files):
        safe_name = Path(file.name).name.replace("..", "").replace("/", "").replace("\\", "")
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(file_path, 'wb') as f:
            f.write(file.read())
        uploaded_file_paths.append(file_path)
        progress_bar.progress((i + 1) / total_steps)
        status_text.info(f"📤 Uploaded {i + 1}/{total_files} files...")
    
    st.sidebar.success(f"✅ Uploaded {total_files} files successfully.")
    
    status_text.info("⏳ Running preprocessing and comparison...")
    stage_times = {"Preprocessing": 0.0, "Comparison": 0.0, "Saving CSV": 0.0}
    stage_cpu = {"Preprocessing": 0.0, "Comparison": 0.0, "Saving CSV": 0.0}
    
    start_time = time.perf_counter()
    update_progress(0, total_files, "preprocessing")
    try:
        preprocessed_files = run_parallel_preprocessing()
        preprocessed_files = [out_path for _, out_path in preprocessed_files if out_path]
        if len(preprocessed_files) < len(uploaded_file_paths):
            update_progress(len(preprocessed_files), len(uploaded_file_paths), "preprocessing")
            progress_bar.progress((total_files + len(preprocessed_files) / len(uploaded_file_paths)) / total_steps)
            status_text.info(f"🔍 Preprocessing: {len(preprocessed_files)}/{len(uploaded_file_paths)} files...")
        cpu_usage, _ = monitor_cpu_usage()
        stage_times["Preprocessing"] = time.perf_counter() - start_time
        stage_cpu["Preprocessing"] = cpu_usage
    except Exception as e:
        st.error(f"Preprocessing failed: {e}")
        update_progress(0, 0, "error")
        return False
    
    if not preprocessed_files:
        st.error("No files preprocessed successfully.")
        update_progress(0, 0, "error")
        return False
    
    # Comparison
    total_pairs = (len(preprocessed_files) * (len(preprocessed_files) - 1)) // 2
    start_time = time.perf_counter()
    update_progress(0, total_pairs, "comparison")
    try:
        results = run_parallel_comparison(preprocessed_files)
        if len(results) < total_pairs:
            update_progress(len(results), total_pairs, "comparison")
            progress_bar.progress((total_files + len(results) / total_pairs) / total_steps)
            status_text.info(f"🔍 Comparison: {len(results)}/{total_pairs} pairs...")
        cpu_usage, _ = monitor_cpu_usage()
        stage_times["Comparison"] = time.perf_counter() - start_time
        stage_cpu["Comparison"] = cpu_usage
    except Exception as e:
        st.error(f"Comparison failed: {e}")
        update_progress(0, 0, "error")
        return False
    
    start_time = time.perf_counter()
    update_progress(0, 1, "saving_csv")
    try:
        save_results_to_csv(results, RESULTS_CSV)
        cpu_usage, cpu_cores = monitor_cpu_usage()
        stage_times["Saving CSV"] = time.perf_counter() - start_time
        stage_cpu["Saving CSV"] = cpu_usage
        update_progress(1, 1, "saving_csv")
        progress_bar.progress(1.0)
        status_text.success("✅ Processing completed.")
    except Exception as e:
        st.error(f"Saving results failed: {e}")
        update_progress(0, 0, "error")
        return False
    

    st.session_state.results_df = pd.read_csv(RESULTS_CSV)
    
    # Display metrics table and chart
    st.subheader("📊 Processing Metrics")
    metrics_df = pd.DataFrame({
        "Stage": list(stage_times.keys()),
        "Elapsed Time (s)": [round(t, 2) for t in stage_times.values()],
        "CPU Usage (%)": [round(c, 2) for c in stage_cpu.values()]
    })
    st.write("**Processing Times and CPU Usage**")
    st.table(metrics_df)
    
    fig = px.bar(
        metrics_df,
        x="Stage",
        y=["Elapsed Time (s)", "CPU Usage (%)"],
        barmode="group",
        title=f"Time (s) and CPU Usage (%) per Processing Stage (Total Cores: {cpu_cores})",
        labels={"value": "Metric Value", "variable": "Metric"},
        text_auto='.2f'
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(yaxis_title="Value", legend_title="Metric")
    st.plotly_chart(fig, use_container_width=True)
    
    st.write(f"Total processing time: {time.perf_counter() - start_time:.2f} seconds")
    return True



@st.cache_data
def read_file_content(file_name, use_preprocessed=True, preview_lines=500):
    """Read file content with preview option."""
    if use_preprocessed:
        file_path = Path(PREPROCESSED_DIR) / file_name
    else:
        file_path = Path(UPLOAD_DIR) / file_name
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()[:preview_lines]
            return "\n".join(lines), len(content.splitlines()) > preview_lines
    except Exception as e:
        return f"Error reading file {file_name}: {e}", False



@st.cache_data
def highlight_matching_text(file1_name, file2_name):
    """Highlight matching text using comparison.py's compare_pair function."""
    file1_path = Path(PREPROCESSED_DIR) / file1_name
    file2_path = Path(PREPROCESSED_DIR) / file2_name
    try:
        _, _, _, content1, content2, matching_blocks = compare_pair(file1_path, file2_path)
    except Exception as e:
        return f"Error comparing files: {e}", f"Error comparing files: {e}"
    highlighted1 = []
    highlighted2 = []
    pos1 = pos2 = 0
    for match in matching_blocks:
        a, b, size = match.a, match.b, match.size
        if pos1 < a:
            highlighted1.append(content1[pos1:a])
        if pos2 < b:
            highlighted2.append(content2[pos2:b])
        if size > 0:
            matching_text1 = content1[a:a + size]
            matching_text2 = content2[b:b + size]
            highlighted1.append(f'<span style="background-color: #FFFF99;">{matching_text1}</span>')
            highlighted2.append(f'<span style="background-color: #FFFF99;">{matching_text2}</span>')
        
        pos1 = a + size
        pos2 = b + size
    if pos1 < len(content1):
        highlighted1.append(content1[pos1:])
    if pos2 < len(content2):
        highlighted2.append(content2[pos2:])
    
    return "".join(highlighted1), "".join(highlighted2)


@st.cache_data
def prepare_pie_chart_data(_df, bins, labels):
    """Prepare data for pie chart."""
    range_categories = pd.cut(_df["Similarity %"], bins=bins, labels=labels, include_lowest=True)
    range_counts = range_categories.value_counts().sort_index()
    return range_counts, [f"{label} ({count})" for label, count in zip(range_counts.index, range_counts)]



def display_summary(df):
    """Display summary statistics."""
    start_time = time.perf_counter()
    st.subheader("📈 Summary Statistics")
    total_files = len(set(df["File 1"]).union(df["File 2"]))
    total_pairs = len(df)
    max_similarity = df["Similarity %"].max()
    high_similarity_pairs = len(df[df["Similarity %"] >= 80])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Files", total_files)
    col2.metric("Total Pairs Compared", total_pairs)
    col3.metric("Highest Similarity", f"{max_similarity:.2f}%")
    col4.metric("High Similarity Pairs (≥80%)", high_similarity_pairs)
    st.write(f"Time to render summary: {time.perf_counter() - start_time:.2f} seconds")


def display_max_plagiarism_per_file(df):
    with st.expander("Display each file's highest plagiarism match", expanded=False):
        start_time = time.perf_counter()
        st.subheader("🔍 Each File's Highest Plagiarism Match")
        file_similarities = pd.concat([
            df[["File 1", "File 2", "Similarity %"]].rename(columns={"File 1": "File", "File 2": "Matched With"}),
            df[["File 2", "File 1", "Similarity %"]].rename(columns={"File 2": "File", "File 1": "Matched With"})
        ])
        match_df = file_similarities.loc[file_similarities.groupby("File")["Similarity %"].idxmax()]
        match_df = match_df.sort_values(by="Similarity %", ascending=False).reset_index(drop=True)
        
        st.dataframe(match_df, use_container_width=True)
        
    st.download_button(
        label="📥 Download Highest Match Table",
        data=match_df.to_csv(index=False).encode('utf-8'),
        file_name=" highest_match_per_file.csv",
        mime='text/csv'
    )
    
    bins = [0, 20, 40, 60, 80, 100]
    labels = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%']
    range_counts, pie_labels = prepare_pie_chart_data(match_df, bins, labels)
    fig = px.pie(
        values=range_counts,
        names=pie_labels,
        title="Max Plagiarism per File Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    selected_file = st.selectbox("📄 Select a file to view more details:", match_df["File"].unique())
    if selected_file:
        st.session_state.selected_file = selected_file
        st.success(f"You selected: {selected_file}")
    
    if "selected_file" in st.session_state:
        selected_file = st.session_state.selected_file
        with st.expander(f"📄 Content of {selected_file}", expanded=False):
            content, is_truncated = read_file_content(selected_file, use_preprocessed=False)
            st.code(content, language="python" if selected_file.endswith('.py') else None)
            if is_truncated:
                st.warning("Content truncated to 500 lines. Download the file for full content.")
        
        with st.expander(f"🔍 Similarity Matches for {selected_file}"):
            subset = df[(df["File 1"] == selected_file) | (df["File 2"] == selected_file)]
            st.dataframe(subset.sort_values("Similarity %", ascending=False), use_container_width=True)
    
    st.write(f"Time to render max plagiarism per file: {time.perf_counter() - start_time:.2f} seconds")


def display_filtered_results(df):
    start_time = time.perf_counter()
    st.subheader("📊 Plagiarism Similarity Results")
    similarity_range = st.slider(
        "🎛️ Select similarity range (%)",
        min_value=0,
        max_value=100,
        value=(20, 60)  # default range shown
    )

    # Unpack the range into min and max
    min_similarity, max_similarity = similarity_range

    # Filter the dataframe using both bounds
    filtered_df = df[(df["Similarity %"] >= min_similarity) & (df["Similarity %"] <= max_similarity)]
        
    with st.expander("📋 File Pair Similarity Results", expanded=False):
        st.write("Click a file pair to view their contents with matching text highlighted.")
        for index, row in filtered_df.iterrows():
            file1, file2, similarity = row["File 1"], row["File 2"], row["Similarity %"]
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                if st.button(f"{file1} vs {file2}", key=f"pair_{file1}_{file2}_{index}"):
                    st.session_state.selected_pair = (file1, file2)
            with col2:
                st.write(f"{similarity:.2f}%")
            with col3:
                st.write("")
        
    st.download_button(
        label="📥 Download Filtered Results CSV",
        data=filtered_df.to_csv(index=False).encode('utf-8'),
        file_name="filtered_similarity_results.csv",
        mime='text/csv'
    )
    
    if "selected_pair" in st.session_state:
        file1, file2 = st.session_state.selected_pair
        with st.expander(f"📄 Comparison: {file1} vs {file2}", expanded=True):
            content1, _ = read_file_content(file1, use_preprocessed=False)
            content2, _ = read_file_content(file2, use_preprocessed=False)
            
            view_mode = st.radio("View Mode", ["Raw Content", "Highlighted Matches"], key=f"view_mode_{file1}_{file2}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"{file1}")
                if view_mode == "Raw Content":
                    st.code(content1, language="python" if file1.endswith('.py') else None)
                else:
                    highlighted1, _ = highlight_matching_text(file1, file2)
                    st.markdown(highlighted1, unsafe_allow_html=True)
            with col2:
                st.subheader(f"{file2}")
                if view_mode == "Raw Content":
                    st.code(content2, language="python" if file2.endswith('.py') else None)
                else:
                    _, highlighted2 = highlight_matching_text(file1, file2)
                    st.markdown(highlighted2, unsafe_allow_html=True)
    
    with st.expander("📊 Files Involved in High Similarity Matches", expanded=False):
        st.subheader("📊 Files Involved in High Similarity Matches")
        file_counts = pd.concat([filtered_df["File 1"], filtered_df["File 2"]]).value_counts()
        fig = px.bar(
            x=file_counts.values,
            y=file_counts.index,
            orientation='h',
            labels={"x": "Number of High Similarity Occurrences", "y": "File Name"},
            title="Files Involved in High Similarity Matches"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.write(f"Time to render filtered results: {time.perf_counter() - start_time:.2f} seconds")


def display_top_n_pairs(df):
    start_time = time.perf_counter()
    with st.expander("🔝 Top N Most Similar Pairs", expanded=False):
        st.subheader("🔝 Top N Most Similar Pairs")
        top_n = st.slider("Select Top N", 5, 50, 10)
        top_df = df.sort_values("Similarity %", ascending=False).head(top_n)
        st.dataframe(top_df.reset_index(drop=True))
        
        st.download_button(
            label="📥 Download Top Similar Pairs CSV",
            data=top_df.to_csv(index=False).encode('utf-8'),
            file_name="top_similar_pairs.csv",
            mime='text/csv'
        )
        st.write(f"Time to render top N pairs: {time.perf_counter() - start_time:.2f} seconds")



def display_file_similarities(df):
    """Display similarities for a specific file."""
    start_time = time.perf_counter()
    st.subheader("🔍 Check Similarities for a Specific File")
    file_list = sorted(set(df["File 1"]).union(df["File 2"]))
    selected_file = st.selectbox("Choose a file", file_list, key="file_selectbox")
    subset = df[(df["File 1"] == selected_file) | (df["File 2"] == selected_file)]
    st.dataframe(subset.sort_values("Similarity %", ascending=False))
    st.write(f"Time to render file similarities: {time.perf_counter() - start_time:.2f} seconds")
