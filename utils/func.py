import json
import os

def _get_filename(filename) -> str:
    dir_name = 'static'
    os.makedirs(dir_name, exist_ok=True)
    return dir_name + '/' + filename

def write_to_file(filename, src):
    filename = _get_filename(filename)
    with open(filename,"w", encoding='utf8') as file:
        file.write(src)

def load_file(filename):
    filename = _get_filename(filename)
    with open(filename, "r", encoding='utf8') as file:
        src = file.read()
    return src

def write_to_file_json(filename, src):
    filename = _get_filename(filename)
    with open(filename,"w",encoding='utf8') as file:
        json.dump(src, file, indent=4, ensure_ascii=False)

def load_from_file_json(filename):
    filename = _get_filename(filename)
    with open(filename, encoding='utf8') as file:
        src=json.load(file)
    return src

def func_chunk_array(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]