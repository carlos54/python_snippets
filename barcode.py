import os
import secrets
import re
import treepoem  # type: ignore
from typing import Dict
import fitz  # https://pymupdf.readthedocs.io/en/latest/
from contextlib import contextmanager


@contextmanager
def open_pdf(filepath):
    doc = fitz.open(src_pdf_filename)
    try:
        yield doc
    finally:
        document.saveIncr()
        document.close()


def insert_barcode_in_pdf(pdf_file_path: str, barcode_payload: str,
                          barcode_position: BarCodePosition,
                          page_ref: int = 0,
                          barcode_format: str = "interleaved2of5",
                          tmp_dir: str = "./temps/") -> None:

    img_path = generate_barcode_image(barcode_payload=barcode_payload,
                                      barcode_format=barcode_format)
    if not img_path:
        raise ValueError(
            "No barcode avalaible, debug generate_barcode_image()")

    page_zone = fitz.Rect(p.x0, p.y0, p.x1, p.y1)

    with open_pdf(pdf_file_path) as pdf:
        page = pdf.loadPage(page_ref)
        page.insertImage(rect=page_zone,
                         filename=img_path, keep_proportion=False)


def generate_barcode_image(
        barcode_payload: str,
        barcode_format: str = "interleaved2of5",
        tmp_dir: str = "./temps/") -> str:
    """return path image of barcode who encapsulate
    the string value barcode_payload
    TMPFOLDER .png file barcode.

    barcode_format = ["qrcode",
                      "azteccode",
                      "pdf417",
                      "interleaved2of5",
                      "code128",
                      "code39"]
    formated in interleaved2of5 by default
    :Example:
        >>> generate_barcode(barcode_payload="10015")
        ./temps/fahlfhaks8f787.png
    """

    if not isinstance(barcode_payload, str):
        raise TypeError("TypeError, barcode_payload : str expected")

    if not barcode_payload:
        raise ValueError("ValueError, barcode_payload is empty")

    regex = re.compile(r'[@_!#$%^&*()<>?/\|}{~:]')
    if not(regex.search(barcode_payload) is None):
        raise ValueError(
            "ValueError, barcode_payload : no special caractere allowed")

    if not isinstance(barcode_format, str):
        raise TypeError("TypeError, barcode_format : str expected")
    format_allowed = ["qrcode",
                      "azteccode",
                      "pdf417",
                      "interleaved2of5",
                      "code128",
                      "code39"]
    if barcode_format not in format_allowed:
        raise ValueError("ValueError, barcode_format not supported")

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    if not os.path.exists(tmp_dir):
        raise OSError

    file_name = ''.join([secrets.token_hex(8), ".png"])
    file_path = ''.join([tmp_dir, file_name])
    try:
        barcode_image = treepoem.generate_barcode(barcode_type=barcode_format,
                                                  data=barcode_payload)
        barcode_image.convert('1').save(file_path)

        if not os.path.isfile(file_path):
            raise BaseException("error during barcode generation")

    except BaseException:
        file_path = ""

    return file_path


class BarCodePosition:
    """
    Postion barcode on pdf page doc according to fpdf librairy
    postion available : up_left, up_right, bottom_left, bottom_right
    REM : Do not generate the barcode, see generate_barcode_image()
    :Example:
        >>> barcode = BarCodePosition(postion="up_left",
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
    page_with = 595
    page_height = 842

    def __init__(self, postion: str = "up_left", barcode_width: int = 50,
                 barcode_heigth: int = 25, x_margin: int = 1,
                 y_margin: int = 1) -> None:
        self.barcode_heigth = barcode_heigth
        self.barcode_width = barcode_width
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.x_margin = x_margin
        self.y_margin = y_margin

        postion = postion.casefold()
        if postion == "up_left":
            self.__calculate_up_left()
        elif postion == "up_right":
            self.__calculate_up_right()
        elif postion == "bottom_left":
            self.__calculate_bottom_left()
        else:
            self.__calculate_bottom_right()

    @property
    def coordinate(self) -> Dict[str, int]:
        return dict(x0=self.x0,
                    x1=self.x1,
                    y0=self.y0,
                    y1=self.y1)

    def __calculate_up_left(self) -> None:
        self.x0 = 0 + self.x_margin
        self.x1 = self.x0 + self.barcode_width

        self.y0 = 0 + self.y_margin
        self.y1 = self.y0 + self.barcode_heigth

    def __calculate_up_right(self) -> None:
        self.x0 = self.page_with - (self.x_margin + self.barcode_width)
        self.x1 = self.x0 + self.barcode_width

        self.y0 = 0 + self.y_margin
        self.y1 = self.y0 + self.barcode_heigth

    def __calculate_bottom_left(self) -> None:
        self.x0 = 0 + self.x_margin
        self.x1 = self.x0 + self.barcode_width

        self.y0 = self.page_height - (self.y_margin + self.barcode_heigth)
        self.y1 = self.y0 + self.barcode_heigth

    def __calculate_bottom_right(self) -> None:
        self.x0 = self.page_with - (self.x_margin + self.barcode_width)
        self.x1 = self.x0 + self.barcode_width

        self.y0 = self.page_height - (self.y_margin + self.barcode_heigth)
        self.y1 = self.y0 + self.barcode_heigth
