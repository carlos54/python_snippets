import os
import secrets
import re
import treepoem  # type: ignore
from typing import Dict
CONFIG = {'TMPFOLDER': "./temps/"}


def generate_image(
        codebar_payload: str,
        codebar_format: str = "interleaved2of5") -> str:
    """return path image of codebar who encapsulate
    the string value codebar_payload
    TMPFOLDER .png file codebar.

    codebar_format = ["qrcode",
                      "azteccode",
                      "pdf417",
                      "interleaved2of5",
                      "code128",
                      "code39"]
    formated in interleaved2of5 by default
    :Example:
        >>> generate_barcode(codebar_payload="10015")
        ./temps/fahlfhaks8f787.png
    """

    if not isinstance(codebar_payload, str):
        raise TypeError("TypeError, codebar_payload : str expected")

    if not codebar_payload:
        raise ValueError("ValueError, codebar_payload is empty")

    regex = re.compile(r'[@_!#$%^&*()<>?/\|}{~:]')
    if not(regex.search(codebar_payload) is None):
        raise ValueError(
            "ValueError, codebar_payload : no special caractere allowed")

    if not isinstance(codebar_format, str):
        raise TypeError("TypeError, codebar_format : str expected")
    format_allowed = ["qrcode",
                      "azteccode",
                      "pdf417",
                      "interleaved2of5",
                      "code128",
                      "code39"]
    if codebar_format not in format_allowed:
        raise ValueError("ValueError, codebar_format not supported")

    folder_path = CONFIG.get('TMPFOLDER', "./temps/")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    if not os.path.exists(folder_path):
        raise OSError

    file_name = ''.join([secrets.token_hex(8), ".png"])
    file_path = ''.join([folder_path, file_name])
    try:
        codebar_image = treepoem.generate_barcode(barcode_type=codebar_format,
                                                  data=codebar_payload)
        codebar_image.convert('1').save(file_path)
    except BaseException:
        file_path = ""

    return file_path


class BarCodePosition:
    page_with = 210
    page_height = 297

    def __init__(self, postion: str, with_codebar: int = 20,
                 heigth_codebar: int = 10, x_margin: int = 1,
                 y_margin: int = 1) -> None:
        self.heigth_codebar = heigth_codebar
        self.with_codebar = with_codebar
        self.x = 0
        self.y = 0
        self.x_margin = x_margin
        self.y_margin = y_margin

        postion = postion.casefold()
        if postion == "up_left":
            __calculate_up_left()
        elif postion == "up_right":
            __calculate_up_right()
        elif postion == "bottom_left":
            __calculate_bottom_left()
        else:
            __calculate_bottom_right()

    @property
    def coordinate() -> Dict[str, int]:
        return {'x': self.x,
                'y': self.y,
                'w': self.with_codebar,
                'h': self.heigth_codebar}

    def __calculate_up_left() -> None:
        self.x = 0 + x_margin
        self.y = 0 + y_margin

    def __calculate_up_right() -> None:
        self.x = self.page_with - (self.x_margin + self.with_codebar)
        self.y = 0 + self.y_margin

    def __calculate_bottom_left() -> None:
        self.x = 0 + self.x_margin
        self.y = self.page_height - (self.y_margin + self.heigth_codebar)

    def __calculate_bottom_right() -> None:
        self.x = self.page_with - (self.x_margin + self.with_codebar)
        self.y = self.page_height - (self.y_margin + self.heigth_codebar)
