# -*- coding: utf-8 -*-
"""Скрипт сборки EXE через PyInstaller."""
import PyInstaller.__main__
import os
import customtkinter

project = os.path.dirname(os.path.abspath(__file__))
ctk_path = os.path.dirname(customtkinter.__file__)
poppler = os.path.join(project, 'poppler', 'poppler-25.12.0', 'Library', 'bin')

print(f"Project: {project}")
print(f"CTk: {ctk_path}")
print(f"Poppler: {poppler}")
print("Starting build...")

PyInstaller.__main__.run([
    'GOST_gui.py',
    '--name=GOST_Processor',
    '--windowed',
    '--noconfirm',
    '--clean',
    f'--add-data={os.path.join(project, "modules")};modules',
    f'--add-data={poppler};poppler',
    f'--add-data={ctk_path};customtkinter',
    '--hidden-import=customtkinter',
    '--hidden-import=pyodbc',
    '--hidden-import=fitz',
    '--hidden-import=pymupdf',
    '--collect-all=customtkinter',
])
