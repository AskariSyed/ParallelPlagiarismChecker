import os
import difflib
import itertools
from multiprocessing import Pool
import pandas as pd

def compare_pair(file1_path: str, file2_path: str) -> tuple:
    with open(file1_path, 'r', encoding='utf-8', errors='ignore') as f1:
        code1 = f1.read()
    with open(file2_path, 'r', encoding='utf-8', errors='ignore') as f2:
        code2 = f2.read()

    matcher = difflib.SequenceMatcher(None, code1, code2)
    score = round(matcher.ratio() * 100, 2)
    
    matching_blocks = matcher.get_matching_blocks()
    return (os.path.basename(file1_path), os.path.basename(file2_path), score, code1, code2, matching_blocks)

def generate_file_pairs(file_paths: list) -> list:
    return list(itertools.combinations(file_paths, 2))

def run_parallel_comparison(file_paths: list) -> list:
    pairs = generate_file_pairs(file_paths)
    with Pool() as pool:
        results = pool.starmap(compare_pair, pairs)
    return results 

def save_results_to_csv(results: list, output_path: str):
    df = pd.DataFrame(results, columns=['File 1', 'File 2', 'Similarity %', 'Code 1', 'Code 2', 'Matching Blocks'])
    df[['File 1', 'File 2', 'Similarity %']].to_csv(output_path, index=False)
    return df