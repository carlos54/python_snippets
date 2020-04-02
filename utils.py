import treepoem  # type: ignore
import os
import secrets
import re

CONFIG = {'TMPFOLDER': "./temps/"}


def generate_barcode(
        codebar_payload: str,
        codebar_format: str = "interleaved2of5") -> str:
    """return path image of codebar who encapsulate the string value
    in config TMPFOLDER .png file codebar

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


def insert_barcode(pdf_file_path: str):
    if not isinstance(pdf_file_path, str):
        raise TypeError("TypeError, pdf_file_path : str expected")
    
    if not os.path.exists(pdf_file_path):
        raise OSError
    
    
