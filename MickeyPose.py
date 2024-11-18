#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import art
text = "MICKEYPOSE"
art_text = art.text2art(text)
print(art_text)
print(u"PROGRAM INITIALIZING, PLEASE WAIT...")
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow
from MickeyPoseWindow import *
from multiprocessing import Process, freeze_support

class MainWindow(QMainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

if __name__ == "__main__":
	freeze_support()
	app = QApplication(sys.argv)
	app.setWindowIcon(QIcon(get_program_path() + r'\config\logo.ico'))
	window = MainWindow()
	window.show()
	print(u"\nPROGRAM SUCCESSFULLY LAUNCHED.")
	sys.exit(app.exec())
