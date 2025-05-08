import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import subprocess
import shutil  # For deleting folders

# --- Setup ---
st.set_page_config(page_title="Parallel Code Plagiarism Checker", layout="centered")
st.title("🧪 Parallel Code Plagiarism Checker")

RESULTS_CSV = "data/results/similarity_results.csv"
UPLOAD_DIR = "data/uploads"

# --- Utility to Clear Old Files ---
def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

# --- Clear Uploads and Results on Startup ---
if os.path.exists(UPLOAD_DIR):
    clear_directory(UPLOAD_DIR)
else:
    os.makedirs(UPLOAD_DIR)

if os.path.exists(os.path.dirname(RESULTS_CSV)):
    clear_directory(os.path.dirname(RESULTS_CSV))

# --- Upload Files ---
st.sidebar.header("Upload Code Files")
uploaded_files = st.sidebar.file_uploader(
    "Upload multiple code files (Python, C++, Java, etc.)",
    accept_multiple_files=True
)

# --- Handle Uploads ---
if uploaded_files:
    for file in uploaded_files:
        with open(os.path.join(UPLOAD_DIR, file.name), 'wb') as f:
            f.write(file.read())
    st.sidebar.success("✅ Files uploaded successfully.")

    # --- Trigger Backend ---
    try:
        st.sidebar.info("⏳ Running backend comparison...")
        subprocess.run(["python", "../main.py"], check=True)
        st.sidebar.success("✅ Backend finished. Results generated.")
    except subprocess.CalledProcessError as e:
        st.error(f"Backend processing error: {e}")
        st.stop()

# --- If Results Exist ---
if os.path.exists(RESULTS_CSV):
    df = pd.read_csv(RESULTS_CSV)

    st.subheader("📊 Plagiarism Similarity Results")

    # Filter by threshold
    threshold = st.slider("🎛️ Show file pairs with similarity ≥", min_value=0, max_value=100, value=80)
    filtered_df = df[df["Similarity %"] >= threshold]
    st.dataframe(filtered_df, use_container_width=True)

    # Download button
    st.download_button(
        "📥 Download Filtered Results CSV",
        data=filtered_df.to_csv(index=False).encode('utf-8'),
        file_name="filtered_similarity_results.csv",
        mime="text/csv"
    )

    # --- Pie Chart: Distribution of Plagiarism Levels ---
    st.subheader("🥧 Plagiarism Level Distribution")
    bins = [0, 20, 40, 60, 80, 100]
    labels = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%']
    df['Plagiarism Range'] = pd.cut(df["Similarity %"], bins=bins, labels=labels, include_lowest=True)
    range_counts = df['Plagiarism Range'].value_counts().sort_index()

    fig1, ax1 = plt.subplots()
    ax1.pie(range_counts, labels=range_counts.index, autopct='%1.1f%%', startangle=140)
    ax1.axis('equal')
    st.pyplot(fig1)

    # --- Horizontal Bar Chart: Files Most Frequently Involved ---
    st.subheader("📊 Files Involved in High Similarity Matches")
    file_counts = pd.concat([filtered_df["File 1"], filtered_df["File 2"]]).value_counts()

    fig2, ax2 = plt.subplots(figsize=(10, len(file_counts) // 1.2))
    sns.barplot(x=file_counts.values, y=file_counts.index, ax=ax2, palette="Blues_d")
    ax2.set_xlabel("Number of High Similarity Occurrences")
    ax2.set_ylabel("File Name")
    st.pyplot(fig2)

    # --- Top-N Most Similar Pairs ---
    st.subheader("🔝 Top N Most Similar Pairs")
    top_n = st.slider("Select Top N", 5, 50, 10)
    top_df = df.sort_values("Similarity %", ascending=False).head(top_n)

    st.dataframe(top_df.reset_index(drop=True))

    # Optional download
    st.download_button(
        "📥 Download Top Similar Pairs CSV",
        data=top_df.to_csv(index=False).encode('utf-8'),
        file_name="top_similar_pairs.csv",
        mime='text/csv'
    )

    # --- Optional: Select a File to See All Similarities ---
    st.subheader("🔍 Check Similarities for a Specific File")
    file_list = sorted(set(df["File 1"]).union(df["File 2"]))
    selected_file = st.selectbox("Choose a file", file_list)

    subset = df[(df["File 1"] == selected_file) | (df["File 2"] == selected_file)]
    st.dataframe(subset.sort_values("Similarity %", ascending=False))

else:
    st.info("Upload files and run the backend (main.py) to generate results.")
