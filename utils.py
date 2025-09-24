import os, sys

def resource_path(relative_path: str) -> str:
    """
    Возвращает путь к ресурсу как при разработке, так и из exe.
    """
    if hasattr(sys, "_MEIPASS"):  # PyInstaller запустил exe
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
