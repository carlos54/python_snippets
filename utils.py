

def insert_barcode(pdf_file_path: str):
    
    #pdf = fpdf.Fpdf()
    #pdf.add_page()
    #pdf.set_font('Arial', 'B', 16)
    #pdf.cell(40, 10, 'Hello World!')
    #pdf.output('./temps/tuto1.pdf', 'F')

    """      
    if not isinstance(pdf_file_path, str):
            raise TypeError("TypeError, codebar_payload : str expected")
        
        if not os.path.exists(pdf_file_path):
            raise OSError
                            
        doc_pdf = fitz.open(pdf_file_path) 
    
        codebar_position = fitz.Rect(1,1,1,1)
        print(codebar_position.getArea('px'))
        
        for i, page in enumerate(doc_pdf):
            # codebare info numero de page en attendant de savoir quoi mettre
            codebar = generate_barcode(codebar_payload=str(i))
            page.insertImage(codebar_position, filename=codebar)

        doc.save() 
        """
    
