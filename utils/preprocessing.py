import os
import re
from multiprocessing import Pool, freeze_support

# === LANGUAGE-SPECIFIC BOILERPLATE REMOVAL ===

def remove_python_boilerplate(code):
    code = re.sub(r'#.*', '', code)
    code = re.sub(r'^\s*import .*', '', code, flags=re.MULTILINE)
    code = re.sub(r'^\s*from .* import .*', '', code, flags=re.MULTILINE)
    return normalize_code(code)

def remove_cpp_boilerplate(code):
    code = re.sub(r'//.*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'^\s*#include.*', '', code, flags=re.MULTILINE)
    code = re.sub(r'^\s*using namespace.*;', '', code, flags=re.MULTILINE)
    return normalize_code(code)

def remove_java_boilerplate(code):
    code = re.sub(r'//.*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'^\s*import .*;', '', code, flags=re.MULTILINE)
    code = re.sub(r'^\s*package .*;', '', code, flags=re.MULTILINE)
    return normalize_code(code)

def normalize_code(code):
    code = code.lower()
    code = re.sub(r'\s+', ' ', code) 
    return code.strip()


def preprocess_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        ext = os.path.splitext(file_path)[1]
        if ext == '.py':
            cleaned_code = remove_python_boilerplate(code)
        elif ext in ['.cpp', '.h', '.cc', '.cxx']:
            cleaned_code = remove_cpp_boilerplate(code)
        elif ext == '.java':
            cleaned_code = remove_java_boilerplate(code)
        else:
            cleaned_code = normalize_code(code)
        base_name = os.path.basename(file_path)
        out_path = os.path.join('data', 'preprocessed', base_name)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_code)

        return (file_path, out_path)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return (file_path, None)

def run_parallel_preprocessing():
    input_dir = os.path.join('data', 'uploads')
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(('.py', '.cpp', '.java', '.h'))]

    os.makedirs(os.path.join('data', 'preprocessed'), exist_ok=True)

    with Pool() as pool:
        results = pool.map(preprocess_file, files)

    return results

if __name__ == '__main__':
    freeze_support()
    run_parallel_preprocessing()
