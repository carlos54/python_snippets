import fitz
from api.barcode import generate_barcode_image, BarCodePosition

print( fitz.PaperSize("A4"))

#print(f"********{}")

src_pdf_filename = '/share/src/statec/mailing/test/temps/d5d705f211b4d3f7/tuto2.pdf'
dst_pdf_filename = '/share/src/statec/mailing/test/temps/d5d705f211b4d3f7/tuto2_out.pdf'
img_filename = '/share/src/statec/mailing/test/temps/d5d705f211b4d3f7/15a96672c53c4ca8.png'

# http://pymupdf.readthedocs.io/en/latest/rect/
# Set position and size according to your needs


img_rect = fitz.Rect(100, 100, 120, 120)

document = fitz.open(src_pdf_filename)

page = document[0]
page.insertImage(img_rect, filename=img_filename)
document.save(dst_pdf_filename)

document.close()
"""
barcode = BarCodePosition(postion="up_left",
                          x_margin=0,
                          y_margin=0,
                          barcode_width=20,
                          barcode_heigth=10)


param = {'name' :'./temps/380e247ac3b59b94.png',
         **barcode.coordinate
        } 


document = FPDF()
document.add_page()
document.set_font('Arial', size=12)
document.cell(w=0, txt="hello world")
document.image(**param)

document.output("./temps/hello_world.pdf")
"""
"""
options = {
    'quiet': '',
    'page-size': 'Letter',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'custom-header' : [
        ('Accept-Encoding', 'gzip')
    ],
    'cookie': [
        ('cookie-name1', 'cookie-value1'),
        ('cookie-name2', 'cookie-value2'),
    ],
    'no-outline': None
}

print('top')
pdfkit.from_url('http://google.com', './temps/gooele_out.pdf')

print('fin google')


pdfkit.from_file('./temps/123grapesjs/index.html', './temps/123grapesjs/index_out.pdf', options=options) 
print('fin infile')
"""