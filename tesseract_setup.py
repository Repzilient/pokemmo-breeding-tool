import sys
import os
import pytesseract

def get_base_path():
    """
    Returns the base path of the application.
    If frozen (exe), returns the temp folder (_MEIPASS).
    If dev (script), returns the script directory.
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def setup_tesseract():
    """
    Configures pytesseract to use the local Tesseract-OCR folder.
    Sets tesseract_cmd and TESSDATA_PREFIX.
    Returns the absolute path to tesseract.exe.
    """
    base_path = get_base_path()
    
    # Path to Tesseract executalbe
    tesseract_dir = os.path.join(base_path, "Tesseract-OCR")
    tesseract_exe = os.path.join(tesseract_dir, "tesseract.exe")
    tessdata_dir = os.path.join(tesseract_dir, "tessdata")

    # Configure pytesseract
    pytesseract.pytesseract.tesseract_cmd = tesseract_exe
    
    # Configure TESSDATA_PREFIX environment variable so Tesseract can find language data
    # This is crucial for frozen builds where relative paths might fail
    os.environ["TESSDATA_PREFIX"] = tessdata_dir
    
    return tesseract_exe

def verify_tesseract_available():
    """
    Checks if the configured Tesseract executable actually exists.
    Returns True if found, False otherwise.
    """
    # Recalculate path to be sure we are checking the same thing we configured
    base_path = get_base_path()
    tesseract_exe = os.path.join(base_path, "Tesseract-OCR", "tesseract.exe")
    
    return os.path.exists(tesseract_exe) and os.path.isfile(tesseract_exe)
