
import fitz 
import glob
import os
import secrets
import subprocess
import fitz  # https://pymupdf.readthedocs.io/en/latest/
from contextlib import contextmanager
######
from mailing.resources.barcode import BarCodePosition, generate_barcode_image

@contextmanager
def open_pdf(file_path):
    doc = fitz.open(file_path)
    try:
        modify_ok = bool(doc.permissions & fitz.PDF_PERM_MODIFY)
        if doc.isPDF and modify_ok:
            yield doc
    finally:
        doc.saveIncr()
        doc.close()


def insert_barcode_in_pdf(pdf_file_path: str,
                          tmp_dir: str = "./temps/") -> None:
   
    #### inner function
    def insert_barcode(page, payload, barcode_position):
        _, _, w, h = page.CropBox
        #print(f"********CropBox{page.CropBox}")
        #print(f"********MediaBox {page.MediaBox}")
        #print(f"********barcaode {p.coordinate}")
        p = BarCodePosition(postion=barcode_position, page_height=h,
                            page_with=w)
       
        page_zone = fitz.Rect(p.x0, p.y0, p.x1, p.y1)
        img_path = generate_barcode_image(barcode_payload=payload,
                                          tmp_dir=tmp_dir)
      
        page.insertImage(rect=page_zone, filename=img_path,
                         keep_proportion=False)
    ####
    
    with open_pdf(pdf_file_path) as pdf:
        insert_barcode(pdf[0], "000", "up_right")#flag first page begin
        for i, page in enumerate(pdf):
           insert_barcode(page, str(i), "bottom_right")#flag page number

        insert_barcode(page, "999", "up_right")#flag last page
    



def merge_pdf(dir_path:str, file_name:str = None) -> str:
   
    all_pdf = " ".join(glob.glob1(dir_path,"*.pdf"))
    if not all_pdf :
        raise IOError("Empty directory")
    
    file_name = "".join(['merge_', secrets.token_hex(8),'.pdf']) if not file_name else file_name
    p_res = subprocess.run(args=[
        f"python -m fitz join -o {file_name} {all_pdf}"], 
        capture_output= True, shell=True, text=True, cwd=dir_path)
   
    if not p_res.returncode == 0:
        file_out = ""
        raise OSError(p_res.stderr)
    
    return os.path.join(dir_path,file_name)



def format_genre(lang:str, genre:str) -> str :
    decode = {
        ('fr', 'm'): "Monsieur",
        ('en', 'm'): "Mister"
    }
    return decode.get((lang.casefold(), genre.casefold()), 'not_define')
  
   

def format_date(lang:str, date:str) -> str :
    return "2099-12-31"
        