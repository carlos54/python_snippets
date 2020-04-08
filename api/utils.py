
import fitz 
import glob
import os
import secrets
import subprocess

def merge_pdf(dir_path:str) -> str:
    all_pdf = " ".join(glob.glob1(dir_path,"*.pdf"))
    if not all_pdf:
        raise IOError("Empty directory")

    file_merge = "".join(['merge_',secrets.token_hex(8),'.pdf'])
    p_res = subprocess.run(args=[
        f"python -m fitz join -o {file_merge} {all_pdf}"], 
        capture_output= True, shell=True, text=True, cwd=dir_path)
   
    if not p_res.returncode == 0:
        file_out = ""
        raise OSError(p_res.stderr)
    
    return os.path.join(dir_path,file_merge)
        