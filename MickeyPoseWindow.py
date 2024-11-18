#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MickeyPoseWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.7.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

import os
import cv2
import time
import shutil
import threading
import numpy as np
import tkinter as tk
from ultralytics import YOLO
from tkinter import ttk, filedialog, messagebox
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

def get_program_path():
	path = os.path.dirname(os.path.abspath(__file__))
	#path = os.path.dirname(os.path.realpath(sys.executable))
	return path

def auto_close_messagebox(title, content, delay):
	popup = tk.Tk()
	popup.withdraw()
	popup.wm_attributes('-topmost', 1)
	popup.after(delay * 1000, popup.destroy)
	messagebox.showinfo(title, content)
	popup.mainloop()

class ImgQtyDialog(QDialog):
	def __init__(self):
		super().__init__()
		self.setWindowTitle(u"Total Image Qty")
		self.resize(200, 30)
		self.spinbox = QSpinBox()
		self.spinbox.setMinimum(1)
		self.spinbox.setMaximum(99999)
		self.spinbox.setValue(100)
		self.imageQty = 100
		self.button = QPushButton(u"OK")
		self.button.clicked.connect(self.close)
		self.spinbox.valueChanged.connect(self.slot_value_changed)
		layout = QVBoxLayout()
		layout.addWidget(self.spinbox)
		layout.addWidget(self.button)
		self.setLayout(layout)

	def slot_value_changed(self):
		self.imageQty = self.spinbox.value()

class Label:
	def __init__(self, name = 0, box = None, labelPts = [], width = 1, height = 1):
		self.name = name
		self.box = box
		self.labelPts = labelPts
		self.width = width
		self.height = height

	def labelText(self):
		text = str(self.name) + " " + str(round(self.box[0], 6)) + " " + str(round(self.box[1], 6)) + " " + str(round(self.box[2], 6)) + " " + str(round(self.box[3], 6))
		if self.labelPts is not None:
			for item in self.labelPts:
				text += " " + str(round(item[0], 6)) + " " + str(round(item[1], 6)) + " " + str(round(item[2], 6))
		print("Label Text : {}.".format(text))
		return text

	def update_box(self, centerX = None, centerY = None, width = None, height = None, islock = None):
		if centerX is not None:
			self.box[0] = centerX / self.width
		if centerY is not None:
			self.box[1] = centerY / self.height
		if width is not None:
			self.box[2] = width / self.width
		if height is not None:
			self.box[3] = height / self.height
		if islock is not None:
			self.box[4] = islock

	def update_pt(self, line, centerX = None, centerY = None, flag = None, islock = None):
		if centerX is not None:
			self.labelPts[line][0] = centerX / self.width
		if centerY is not None:
			self.labelPts[line][1] = centerY / self.height
		if flag is not None:
			self.labelPts[line][2] = flag
		if islock is not None:
			self.labelPts[line][3] = islock

label_list = []

class MyRectItem(QGraphicsRectItem):
	def __init__(self, rect, fid, row, islock = False, *args, **kwargs):
		super(MyRectItem, self).__init__(rect, *args, **kwargs)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
		self.setAcceptHoverEvents(True)
		self.flag = None
		self.offset = None
		self.fid = fid
		self.row = row
		self.islock = islock
		pen = QPen()
		pen.setWidth(3)
		if self.islock:
			pen.setBrush(QBrush(QColor(255, 0, 255)))
		else:
			pen.setBrush(QBrush(QColor(0, 0, 255)))
		self.setPen(pen)
	
	def itemChange(self, change, value: QPointF):
		if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
			label_list[self.fid][self.row].update_box(centerX = self.rect().x() + self.rect().width() / 2 + value.x(),
											centerY = self.rect().y() + self.rect().height() / 2 + value.y())
		return super(MyRectItem, self).itemChange(change, value)
	
	def hoverMoveEvent(self, event):
		if self.islock:
			return
		self.setCursor(QCursor(Qt.CrossCursor))
		item_rect = self.rect()
		item_bottom_right = item_rect.bottomRight()
		hover_pos = event.pos()
		if item_rect.contains(hover_pos):
			distance = (item_bottom_right - hover_pos).manhattanLength()
			if distance < 20:
				self.flag = "Size"
				self.setCursor(QCursor(Qt.SizeFDiagCursor))
			else:
				self.flag = "None"
				self.setCursor(QCursor(Qt.CrossCursor))
		super(MyRectItem, self).hoverMoveEvent(event)
	
	def mousePressEvent(self, event):
		if self.islock:
			return
		if not event.button() == Qt.LeftButton and not event.button() == Qt.MiddleButton:
			return
		if event.button() == Qt.MiddleButton:
			pen = QPen()
			pen.setWidth(3)
			pen.setBrush(QBrush(QColor(255, 0, 255)))
			self.setPen(pen)
			self.islock = True
			label_list[self.fid][self.row].update_box(islock = self.islock)
		item_rect = self.rect()
		item_bottom_right = item_rect.bottomRight()
		click_pos = event.scenePos()
		if item_rect.contains(click_pos):
			distance = (item_bottom_right - click_pos).manhattanLength()
			if distance < 20:
				self.flag = "Size"
				self.offset = event.pos()
				return
		return super(MyRectItem, self).mousePressEvent(event)
	
	def mouseDoubleClickEvent(self, event: QMouseEvent):
		if event.button() == Qt.MouseButton.RightButton:
			self.flag = None
			self.offset = None
			self.islock = False
			pen = QPen()
			pen.setWidth(3)
			pen.setBrush(QBrush(QColor(0, 0, 255)))
			self.setPen(pen)
			label_list[self.fid][self.row].update_box(islock = self.islock)
		else:
			super(MyRectItem, self).mouseDoubleClickEvent(event)
	
	def mouseMoveEvent(self, event):
		if self.islock:
			return
		if self.flag == "Size":
			new_width = event.pos().x() - self.rect().x() if event.pos().x() - self.rect().x() > 0 else 1
			new_height = event.pos().y() - self.rect().y() if event.pos().y() - self.rect().y() > 0 else 1
			self.setRect(self.rect().x(), self.rect().y(), new_width, new_height)
			'''
			label_list[self.fid][self.row].update_box(centerX = self.rect().x() + new_width / 2,
											centerY = self.rect().y() + new_height / 2,
											width = new_width, height = new_height)
			'''
			label = label_list[self.fid][self.row]
			label_list[self.fid][self.row].update_box(centerX = label.box[0] * label.width - (label.box[2] * label.width - new_width) / 2,
														centerY = label.box[1] * label.height - (label.box[3] * label.height - new_height) / 2,
														width = new_width, height = new_height)
			return
		return super(MyRectItem, self).mouseMoveEvent(event)
	
	def mouseReleaseEvent(self, event):
		if self.islock:
			return
		self.flag = None
		return super(MyRectItem, self).mouseReleaseEvent(event)

class MyPointItem(QGraphicsEllipseItem):
	def __init__(self, radius, fid, row, line, flag = 1, islock = False, *args, **kwargs):
		super().__init__(-radius, -radius, 2 * radius, 2 * radius, *args, **kwargs)
		self.setFlag(QGraphicsItem.ItemIsMovable)
		self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
		self.fid = fid
		self.row = row
		self.line = line
		self.flag = flag
		self.islock = islock
		pen = QPen()
		pen.setWidth(3)
		pen.setBrush(QBrush(QColor(0, 0, 0)))
		self.setPen(pen)
		if self.flag == 1:
			self.setBrush(QColor(0, 0, 255))
		elif self.flag == 2:
			self.setBrush(QColor(0, 255, 0))
		else:
			self.setBrush(QColor(255, 0, 0))
		if self.islock:
			pen = QPen()
			pen.setWidth(3)
			pen.setBrush(QBrush(QColor(255, 0, 255)))
			self.setPen(pen)
			self.setBrush(QColor(255, 0, 255))
	
	def mousePressEvent(self, event: QMouseEvent):
		if event.button() == Qt.MiddleButton:
			pen = QPen()
			pen.setWidth(3)
			pen.setBrush(QBrush(QColor(255, 0, 255)))
			self.setPen(pen)
			self.setBrush(QColor(255, 0, 255))
			self.islock = True
			label_list[self.fid][self.row].update_pt(self.line, islock = self.islock)
		else:
			super().mousePressEvent(event)
	
	def mouseMoveEvent(self, event: QMouseEvent):
		if self.islock:
			return
		if event.buttons() & Qt.LeftButton:
			self.setPos(self.scenePos() + event.screenPos() - event.lastScreenPos())
			label_list[self.fid][self.row].update_pt(self.line, centerX = self.pos().x(), centerY = self.pos().y())
		super().mouseMoveEvent(event)
	
	def mouseDoubleClickEvent(self, event: QMouseEvent):
		if event.button() == Qt.MouseButton.RightButton:
			pen = QPen()
			pen.setWidth(3)
			pen.setBrush(QBrush(QColor(0, 0, 0)))
			self.setPen(pen)
			if self.flag == 1:
				self.setBrush(QColor(0, 0, 255))
			elif self.flag == 2:
				self.setBrush(QColor(0, 255, 0))
			else:
				self.setBrush(QColor(255, 0, 0))
			self.islock = False
			label_list[self.fid][self.row].update_pt(self.line, islock = self.islock)
			return
		if self.islock:
			return
		if self.flag == 1:
			self.setBrush(QColor(0, 255, 0))
			self.flag = 2
		elif self.flag == 2:
			self.setBrush(QColor(255, 0, 0))
			self.flag = 0
		else:
			self.setBrush(QColor(0, 0, 255))
			self.flag = 1
		label_list[self.fid][self.row].update_pt(self.line, flag = self.flag)
		super().mouseDoubleClickEvent(event)

class ProgressThread(QThread):
	progressUpdate = Signal(int)
	windowDisable = Signal(bool)
	
	def __init__(self):
		super().__init__()
		self.progress = None
		self.window = True
	
	def set_data(self, data):
		self.progress = data
	
	def set_window(self, data):
		self.window = data
	
	def run(self):
		if self.progress is None:
			return
		self.progressUpdate.emit(self.progress)
		self.windowDisable.emit(self.window)

class Ui_MainWindow(object):
	work_dir = get_program_path() + u"\\Model-" + time.strftime('%Y%m%d%H%M%S')
	img_list = []
	model = model = YOLO(get_program_path() + r'\config\best.pt')

	def setupUi(self, MainWindow):
		if not MainWindow.objectName():
			MainWindow.setObjectName(u"MainWindow")
		icon = QIcon(get_program_path() + r'\config\logo.ico')
		MainWindow.setWindowIcon(icon)
		MainWindow.resize(1100, 600)
		MainWindow.setUnifiedTitleAndToolBarOnMac(False)
		MainWindow.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
		MainWindow.setFixedSize(MainWindow.width(), MainWindow.height())
		self.actionAdd_Images = QAction(MainWindow)
		self.actionAdd_Images.setObjectName(u"actionAdd_Images")
		self.actionImport_Dataset = QAction(MainWindow)
		self.actionImport_Dataset.setObjectName(u"actionImport_Dataset")
		self.actionGenerate_Images_from_Video = QAction(MainWindow)
		self.actionGenerate_Images_from_Video.setObjectName(u"actionGenerate_Images_from_Video")
		self.actionRemove_Selected_Images = QAction(MainWindow)
		self.actionRemove_Selected_Images.setObjectName(u"actionRemove_Selected_Images")
		self.actionDelete_All_Images = QAction(MainWindow)
		self.actionDelete_All_Images.setObjectName(u"actionDelete_All_Images")
		self.actionAdd_Box_And_Points = QAction(MainWindow)
		self.actionAdd_Box_And_Points.setObjectName(u"actionAdd_Box_And_Points")
		self.actionDelete_Box_And_Points = QAction(MainWindow)
		self.actionDelete_Box_And_Points.setObjectName(u"actionDelete_Box_And_Points")
		self.centralwidget = QWidget(MainWindow)
		self.centralwidget.setObjectName(u"centralwidget")
		self.gridLayout = QGridLayout(self.centralwidget)
		self.gridLayout.setObjectName(u"gridLayout")
		self.groupBox = QGroupBox(self.centralwidget)
		self.groupBox.setObjectName(u"groupBox")
		self.groupBox.setMinimumSize(QSize(550, 0))
		self.gridLayout_2 = QGridLayout(self.groupBox)
		self.gridLayout_2.setObjectName(u"gridLayout_2")
		self.graphicsScene = QGraphicsScene()
		self.graphicsView = QGraphicsView(self.groupBox)
		self.graphicsView.setObjectName(u"graphicsView")
		self.graphicsView.setScene(self.graphicsScene)
		self.graphicsView.resizeEvent = self.onResizeEvent
		self.gridLayout_2.addWidget(self.graphicsView, 0, 0, 1, 1)
		self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)
		MainWindow.setCentralWidget(self.centralwidget)
		self.menubar = QMenuBar(MainWindow)
		self.menubar.setObjectName(u"menubar")
		self.menubar.setGeometry(QRect(0, 0, 900, 21))
		self.menuFile = QMenu(self.menubar)
		self.menuFile.setObjectName(u"menuFile")
		self.menuEdit = QMenu(self.menubar)
		self.menuEdit.setObjectName(u"menuEdit")
		MainWindow.setMenuBar(self.menubar)
		self.toolbar = QToolBar(MainWindow)
		self.toolbar.setObjectName(u"toolbar")
		self.toolbar.setWindowTitle('Tool Bar')
		self.toolbar.setGeometry(QRect(0, 0, 900, 21))
		self.toolbar.addAction(self.actionAdd_Box_And_Points)
		self.toolbar.addAction(self.actionDelete_Box_And_Points)
		MainWindow.addToolBar(self.toolbar)
		self.statusbar = QStatusBar(MainWindow)
		self.statusbar.setObjectName(u"statusbar")
		self.progressbar = QProgressBar()
		self.statusbar.addWidget(self.progressbar)
		MainWindow.setStatusBar(self.statusbar)
		self.dockWidget = QDockWidget(MainWindow)
		self.dockWidget.setObjectName(u"dockWidget")
		self.dockWidget.setMinimumWidth(150)
		self.dockWidgetContents = QWidget()
		self.dockWidgetContents.setObjectName(u"dockWidgetContents")
		self.gridLayout_3 = QGridLayout(self.dockWidgetContents)
		self.gridLayout_3.setObjectName(u"gridLayout_3")
		self.listWidget = QListWidget(self.dockWidgetContents)
		self.listWidget.setObjectName(u"listWidget")
		self.gridLayout_3.addWidget(self.listWidget, 0, 0, 1, 1)
		self.dockWidget.setWidget(self.dockWidgetContents)
		MainWindow.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockWidget)
		self.dockWidget_2 = QDockWidget(MainWindow)
		self.dockWidget_2.setObjectName(u"dockWidget_2")
		self.dockWidgetContents_2 = QWidget()
		self.dockWidgetContents_2.setObjectName(u"dockWidgetContents_2")
		self.gridLayout_4 = QGridLayout(self.dockWidgetContents_2)
		self.gridLayout_4.setObjectName(u"gridLayout_4")
		self.listWidget_2 = QListWidget(self.dockWidgetContents_2)
		self.listWidget_2.setObjectName(u"listWidget_2")
		self.gridLayout_4.addWidget(self.listWidget_2, 0, 0, 1, 1)
		self.dockWidget_2.setWidget(self.dockWidgetContents_2)
		MainWindow.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockWidget_2)
		self.dockWidget_3 = QDockWidget(MainWindow)
		self.dockWidget_3.setObjectName(u"dockWidget_3")
		self.dockWidgetContents_4 = QWidget()
		self.dockWidgetContents_4.setObjectName(u"dockWidgetContents_4")
		self.gridLayout_5 = QGridLayout(self.dockWidgetContents_4)
		self.gridLayout_5.setObjectName(u"gridLayout_5")
		self.treeWidget = QTreeWidget(self.dockWidgetContents_4)
		self.treeWidget.setColumnWidth(0, 150)
		self.treeWidget.setObjectName(u"treeWidget")
		self.treeWidget.setColumnCount(3)
		self.treeWidget.setHeaderLabels([u"Key", u"Value", u"Control"])
		top_item = QTreeWidgetItem(self.treeWidget)
		top_item.setText(0, u"Model")
		child_item1 = QTreeWidgetItem(top_item)
		child_item1.setText(0, u"Work Dir")
		child_item2 = QTreeWidgetItem(top_item)
		child_item2.setText(0, u"Train Qty")
		child_item3 = QTreeWidgetItem(top_item)
		child_item3.setText(0, u"Val Qty")
		child_item4 = QTreeWidgetItem(top_item)
		child_item4.setText(0, u"Points Qty")
		child_item5 = QTreeWidgetItem(top_item)
		child_item5.setText(0, u"Train.py")
		child_item6 = QTreeWidgetItem(top_item)
		child_item6.setText(0, u"Mouse.yaml")
		child_item7 = QTreeWidgetItem(top_item)
		child_item7.setText(0, u"epochs")
		child_item8 = QTreeWidgetItem(top_item)
		child_item8.setText(0, u"imgsz")
		button1 = QPushButton('1. Load Data')
		self.treeWidget.setItemWidget(top_item, 1, button1)
		button1.clicked.connect(self.on_load_data_button_clicked)
		button4 = QPushButton('2. Start Traning')
		self.treeWidget.setItemWidget(top_item, 2, button4)
		button4.clicked.connect(self.on_start_training_button_clicked)
		button2 = QPushButton('Choose')
		self.treeWidget.setItemWidget(child_item1, 2, button2)
		button2.clicked.connect(self.on_choose_button_clicked)
		button3 = QPushButton('Edit')
		self.treeWidget.setItemWidget(child_item5, 2, button3)
		button3.clicked.connect(self.on_edit_yaml_button_clicked)
		button4 = QPushButton('Edit')
		self.treeWidget.setItemWidget(child_item6, 2, button4)
		button4.clicked.connect(self.on_edit_py_button_clicked)
		lineedit1 = QLineEdit()
		self.treeWidget.setItemWidget(child_item1, 1, lineedit1)
		lineedit1.setText(self.work_dir)
		lineedit1.setReadOnly(True)
		os.makedirs(self.work_dir, exist_ok = True)
		lineedit2 = QLineEdit()
		lineedit2.setReadOnly(True)
		self.treeWidget.setItemWidget(child_item5, 1, lineedit2)
		lineedit3 = QLineEdit()
		lineedit3.setReadOnly(True)
		self.treeWidget.setItemWidget(child_item6, 1, lineedit3)
		spinbox1 = QSpinBox()
		spinbox1.setMaximum(99999)
		spinbox1.setAlignment(Qt.AlignRight)
		self.treeWidget.setItemWidget(child_item2, 1, spinbox1)
		spinbox2 = QSpinBox()
		spinbox2.setMaximum(99999)
		spinbox2.setAlignment(Qt.AlignRight)
		self.treeWidget.setItemWidget(child_item3, 1, spinbox2)
		spinbox3 = QSpinBox()
		spinbox3.setMaximum(99999)
		spinbox3.setAlignment(Qt.AlignRight)
		spinbox3.setValue(8)
		self.treeWidget.setItemWidget(child_item4, 1, spinbox3)
		spinbox4 = QSpinBox()
		spinbox4.setMinimum(1)
		spinbox4.setMaximum(99999)
		spinbox4.setAlignment(Qt.AlignRight)
		spinbox4.setValue(200)
		self.treeWidget.setItemWidget(child_item7, 1, spinbox4)
		spinbox5 = QSpinBox()
		spinbox5.setMinimum(100)
		spinbox5.setMaximum(99999)
		spinbox5.setAlignment(Qt.AlignRight)
		spinbox5.setValue(320)
		self.treeWidget.setItemWidget(child_item8, 1, spinbox5)
		self.treeWidget.expandAll()
		shutil.copy2(get_program_path() + r"/config/yolov8n-pose.pt", self.work_dir + r"/yolov8n-pose.pt")
		shutil.copy2(get_program_path() + r"/config/mouse.yaml", self.work_dir + r"/mouse.yaml")
		shutil.copy2(get_program_path() + r"/config/train.py", self.work_dir + r"/train.py")
		shutil.copy2(get_program_path() + r"/config/train.bat", self.work_dir + r"/train.bat")
		lineedit2.setText(self.work_dir + r"\mouse.yaml")
		lineedit3.setText(self.work_dir + r"\train.py")
		self.gridLayout_5.addWidget(self.treeWidget, 0, 0, 1, 1)
		self.dockWidget_3.setWidget(self.dockWidgetContents_4)
		self.dockWidget_3.setMinimumWidth(380)
		MainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget_3)
		self.dockWidget_4 = QDockWidget(MainWindow)
		self.dockWidget_4.setObjectName(u"dockWidget_4")
		self.dockWidgetContents_5 = QWidget()
		self.dockWidgetContents_5.setObjectName(u"dockWidgetContents_5")
		self.gridLayout_6 = QGridLayout(self.dockWidgetContents_5)
		self.gridLayout_6.setObjectName(u"gridLayout_6")
		self.tabWidget = QTabWidget(self.dockWidgetContents_5)
		self.tabWidget.setObjectName(u"tabWidget")
		self.tab = QWidget()
		self.tab.setObjectName(u"tab")
		self.gridLayout_7 = QGridLayout(self.tab)
		self.gridLayout_7.setObjectName(u"gridLayout_7")
		self.textEdit = QTextEdit(self.tab)
		self.textEdit.setObjectName(u"textEdit")
		self.gridLayout_7.addWidget(self.textEdit, 0, 0, 1, 1)
		self.tabWidget.addTab(self.tab, "")
		self.tab_2 = QWidget()
		self.tab_2.setObjectName(u"tab_2")
		self.gridLayout_8 = QGridLayout(self.tab_2)
		self.gridLayout_8.setObjectName(u"gridLayout_8")
		self.textEdit_2 = QTextEdit(self.tab_2)
		self.textEdit_2.setObjectName(u"textEdit_2")
		self.textEdit_2.setReadOnly(True)
		content = ""
		with open(get_program_path() + r'\config\Readme.txt', 'r') as file:
			content = file.read()
		self.textEdit_2.setText(content)
		self.gridLayout_8.addWidget(self.textEdit_2, 0, 0, 1, 1)
		self.tabWidget.addTab(self.tab_2, "")
		self.gridLayout_6.addWidget(self.tabWidget, 0, 0, 1, 1)
		self.dockWidget_4.setWidget(self.dockWidgetContents_5)
		MainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget_4)
		self.menubar.addAction(self.menuFile.menuAction())
		self.menubar.addAction(self.menuEdit.menuAction())
		self.menuFile.addAction(self.actionAdd_Images)
		self.menuFile.addAction(self.actionImport_Dataset)
		self.menuFile.addAction(self.actionGenerate_Images_from_Video)
		self.menuFile.addSeparator()
		self.menuFile.addAction(self.actionRemove_Selected_Images)
		self.menuFile.addAction(self.actionDelete_All_Images)
		self.menuEdit.addAction(self.actionAdd_Box_And_Points)
		self.menuEdit.addAction(self.actionDelete_Box_And_Points)
		self.retranslateUi(MainWindow)
		self.actionAdd_Images.triggered.connect(self.slot_add_images)
		self.actionImport_Dataset.triggered.connect(self.slot_import_dataset)
		self.actionRemove_Selected_Images.setShortcut("Ctrl+Shift+D")
		self.actionRemove_Selected_Images.triggered.connect(self.slot_remove_images)
		self.actionDelete_All_Images.triggered.connect(self.slot_delete_all_images)
		self.actionGenerate_Images_from_Video.triggered.connect(self.slot_generate_images)
		self.actionAdd_Box_And_Points.setShortcut("Ctrl+A")
		self.actionDelete_Box_And_Points.setShortcut("Ctrl+D")
		self.actionAdd_Box_And_Points.triggered.connect(self.slot_add_box_and_points)
		self.actionDelete_Box_And_Points.triggered.connect(self.slot_delete_box_and_points)
		self.listWidget.itemClicked.connect(self.slot_image_item_clicked)
		self.listWidget.currentItemChanged.connect(self.slot_image_item_clicked)
		self.listWidget_2.itemClicked.connect(self.slot_label_item_clicked)
		self.listWidget_2.currentItemChanged.connect(self.slot_label_item_clicked)
		self.tabWidget.setCurrentIndex(0)
		self.progressThread = ProgressThread()
		self.progressThread.progressUpdate.connect(self.update_progress_bar)
		self.progressThread.windowDisable.connect(self.update_window)

	def retranslateUi(self, MainWindow):
		MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MickeyPose", None))
		self.actionAdd_Images.setText(QCoreApplication.translate("MainWindow", u"Add Images", None))
		self.actionImport_Dataset.setText(QCoreApplication.translate("MainWindow", u"Import Dataset", None))
		self.actionGenerate_Images_from_Video.setText(QCoreApplication.translate("MainWindow", u"Generate Images from Video", None))
		self.actionRemove_Selected_Images.setText(QCoreApplication.translate("MainWindow", u"Delete Selected Images", None))
		self.actionDelete_All_Images.setText(QCoreApplication.translate("MainWindow", u"Delete All Images", None))
		self.actionAdd_Box_And_Points.setText(QCoreApplication.translate("MainWindow", u"Add Box and Points", None))
		self.actionDelete_Box_And_Points.setText(QCoreApplication.translate("MainWindow", u"Delete Box and Points", None))
		self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Canvas", None))
		self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
		self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
		self.dockWidget.setWindowTitle(QCoreApplication.translate("MainWindow", u"Image List", None))
		self.dockWidget_2.setWindowTitle(QCoreApplication.translate("MainWindow", u"Label List", None))
		self.dockWidget_3.setWindowTitle(QCoreApplication.translate("MainWindow", u"Model and Dataset", None))
		self.dockWidget_4.setWindowTitle(QCoreApplication.translate("MainWindow", u"Label Text and Tips", None))
		self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Label Text", None))
		self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Tips", None))

	def update_progress_bar(self, progress):
		self.progressbar.setValue(progress)

	def update_window(self, data):
		self.set_window_enable(data)

	def slot_add_images(self):
		file_types = [('jpg', '*.jpg'), ('jpeg', '*.jpeg'), ('png', '*.png'), ('bmp', '*.bmp'), ('All files', '*')]
		file_paths = filedialog.askopenfilenames(filetypes = file_types)
		if len(file_paths) == 0:
			return
		count = len(self.img_list)
		indexStart = count
		for file_path in file_paths:
			self.img_list.append(file_path)
			count += 1
			item = QListWidgetItem(str(count))
			self.listWidget.addItem(item)
			item_2 = QListWidgetItem(str(count))
			self.listWidget_2.addItem(item_2)
		indexEnd = count
		parent_item = self.treeWidget.topLevelItem(0)
		if parent_item:
			child_item1 = parent_item.child(1)
			spinbox1 = self.treeWidget.itemWidget(child_item1, 1)
			spinbox1.setValue(count * 0.9)
			child_item2 = parent_item.child(2)
			spinbox2 = self.treeWidget.itemWidget(child_item2, 1)
			spinbox2.setValue(int(count * 0.1))
		thread = threading.Thread(target = self.load_images, args = (indexStart, indexEnd))
		thread .start()
		parent_item = self.treeWidget.topLevelItem(0)
		if parent_item:
			child_item = parent_item.child(3)
			self.treeWidget.itemWidget(child_item, 1).setEnabled(False)
		self.set_window_enable(False)
		auto_close_messagebox(u"INFO", u"Data Processing, Please Wait...", 5)

	def list_images(self, directory):
		for filename in os.listdir(directory):
			ext = os.path.splitext(filename)[1]
			if ext.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
				yield os.path.join(directory, filename)

	def slot_import_dataset(self):
		folder_selected = filedialog.askdirectory()
		if folder_selected == "":
			return
		index_start = len(self.img_list)
		index_end = index_start
		for image_path in self.list_images(folder_selected + r"\images\train"):
			label_path = folder_selected + r"\\labels\\train\\" + os.path.splitext(os.path.basename(image_path))[0] + ".txt"
			if not os.path.isfile(label_path):
				print("Data Error: Label File Lost.")
				continue
			self.img_list.append(image_path)
			index_end += 1 
			with open(label_path, 'r') as file:
				tmp_label_list = []
				lines = file.readlines()
				for line in lines:
					if line == "":
						continue
					line_list = line.split(" ")
					if len(line_list) < 8:
						print("Data Error: Too Few Parameters.")
					tmpLabel = Label()
					tmpLabel.name = int(line[0])
					tmpLabel.box = [float(line_list[1]), float(line_list[2]), float(line_list[3]), float(line_list[4]), False]
					tmpLabelPts = []
					for it in range(int((len(line_list) - 5) / 3)):
						if 7 + it * 3 > len(line_list) - 1:
							print("Data Error: Too Few Parameters.")
							break
						pt = [float(line_list[5 + it * 3]), float(line_list[6 + it * 3]), int(line_list[7 + it * 3]), False]
						tmpLabelPts.append(pt)
					tmpLabel.labelPts = tmpLabelPts.copy()
					tmpLabelPts.clear()
					tmp_label_list.append(tmpLabel)
				label_list.append(tmp_label_list)
		for image_path in self.list_images(folder_selected + r"\images\val"):
			label_path = folder_selected + r"\\labels\\val\\" + os.path.splitext(os.path.basename(image_path))[0] + ".txt"
			if not os.path.isfile(label_path):
				print("Data Error: Label File Lost.")
				continue
			self.img_list.append(image_path)
			index_end += 1
			with open(label_path, 'r') as file:
				tmp_label_list = []
				lines = file.readlines()
				for line in lines:
					if line == "":
						continue
					line_list = line.split(" ")
					if len(line_list) < 8:
						print("Data Error: Too Few Parameters.")
					tmpLabel = Label()
					tmpLabel.name = int(line[0])
					tmpLabel.box = [float(line_list[1]), float(line_list[2]), float(line_list[3]), float(line_list[4]), False]
					tmpLabelPts = []
					for it in range(int((len(line_list) - 5) / 3)):
						if 7 + it * 3 > len(line_list) - 1:
							print("Data Error: Too Few Parameters.")
							break
						pt = [float(line_list[5 + it * 3]), float(line_list[6 + it * 3]), int(line_list[7 + it * 3]), False]
						tmpLabelPts.append(pt)
					tmpLabel.labelPts = tmpLabelPts.copy()
					tmpLabelPts.clear()
					tmp_label_list.append(tmpLabel)
				label_list.append(tmp_label_list)
		for it in range(index_start, index_end):
			item = QListWidgetItem(str(it + 1))
			self.listWidget.addItem(item)
			item_2 = QListWidgetItem(str(it + 1))
			self.listWidget_2.addItem(item_2)

	def set_window_enable(self, enable):
		self.menubar.setEnabled(enable)
		self.toolbar.setEnabled(enable)
		self.groupBox.setEnabled(enable)
		self.dockWidget.setEnabled(enable)
		self.dockWidget_2.setEnabled(enable)
		self.dockWidget_3.setEnabled(enable)
		self.dockWidget_4.setEnabled(enable)

	def slot_remove_images(self):
		if self.listWidget.count() == 0:
			return
		if len(self.listWidget.selectedItems()) == 0:
			messagebox.showinfo(title = 'INFO', message = 'Please Select the Image to be Deleted.')
		del self.img_list[int(self.listWidget.currentItem().text()) - 1]
		del label_list[int(self.listWidget.currentItem().text()) - 1]
		self.listWidget.clear()
		self.listWidget_2.clear()
		self.graphicsView.scene().clear()
		for it in range(len(self.img_list)):
			item = QListWidgetItem(str(it + 1))
			self.listWidget.addItem(item)
			item_2 = QListWidgetItem(str(it + 1))
			self.listWidget_2.addItem(item_2)

	def slot_delete_all_images(self):
		if self.listWidget.count() == 0:
			return
		self.img_list.clear()
		label_list.clear()
		self.listWidget.clear()
		self.listWidget_2.clear()
		self.graphicsView.scene().clear()

	def slot_image_item_clicked(self, item):
		if item is None:
			return
		self.graphicsScene.clear()
		self.graphicsScene.setSceneRect(0, 0, self.graphicsView.size().width(), self.graphicsView.size().height())
		pixmap = QPixmap(self.img_list[int(item.text()) - 1])
		resized_pixmap = pixmap.scaled(self.graphicsView.size().width(), self.graphicsView.size().height(), Qt.KeepAspectRatio)
		self.graphicsScene.addPixmap(resized_pixmap)
		fid = int(item.text()) - 1
		row = 0
		for label in label_list[fid]:
			label.width = resized_pixmap.width()
			label.height = resized_pixmap.height()
			box = label.box
			rect = QRectF(label.width * (box[0] - box[2] / 2),
							label.height * (box[1] - box[3] / 2),
							label.width * box[2],
							label.height * box[3])
			rect_item = MyRectItem(rect, fid = fid, row = row, islock = box[4])
			self.graphicsScene.addItem(rect_item)
			text_item = QGraphicsSimpleTextItem(str(row + 1))
			font = QFont('Arial', 10)
			font.setBold(True)
			text_item.setFont(font)
			text_item.setBrush(QBrush(QColor(255, 0, 0)))
			text_item.setParentItem(rect_item)
			rectTmp = rect_item.boundingRect()
			text_item.setPos(rectTmp.x(), rectTmp.y() - 13)
			tmpPts = label.labelPts.copy()
			for it in range(len(tmpPts)):
				pt = MyPointItem(5, fid = fid, row = row, line = it, flag = tmpPts[it][2], islock = tmpPts[it][3])
				self.graphicsScene.addItem(pt)
				pt.setPos(tmpPts[it][0] * label.width, tmpPts[it][1] * label.height)
				text_item = QGraphicsSimpleTextItem(str(row + 1) + "." + str(it + 1))
				font = QFont('Arial', 8)
				font.setBold(True)
				text_item.setFont(font)
				text_item.setBrush(QBrush(QColor(255, 0, 0)))
				text_item.setParentItem(pt)
				rectTmp = pt.boundingRect()
				text_item.setPos(rectTmp.x() + 3, rectTmp.y() - 13)
			row += 1

	def slot_label_item_clicked(self, item):
		if item is None:
			return
		fid = int(item.text()) - 1
		text = ""
		for label in label_list[fid]:
			text += label.labelText() + "\n"
		self.textEdit.setText(text[:-1])

	def slot_generate_images(self):
		dialog = ImgQtyDialog()
		dialog.exec()
		qty = dialog.imageQty if dialog.imageQty > 0 else 1
		file_types = [('mp4', '*.mp4'), ('avi', '*.avi'), ('wmv', '*.wmv'), ('mov', '*.mov'), ('mpeg', '*.mepg'), ('All files', '*')]
		file_paths = filedialog.askopenfilenames(filetypes = file_types, multiple = False)
		for file_path in file_paths:
			thread = threading.Thread(target = self.cut_video, args = (file_path, qty))
			thread .start()
			self.set_window_enable(False)
			return

	def cut_video(self, filePath, imgCount):
		destDir = os.path.dirname(filePath) + u"/IMAGES-" + time.strftime('%Y%m%d%H%M%S')
		os.makedirs(destDir, exist_ok = True)
		cap = cv2.VideoCapture(filePath)
		width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
		height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
		fps = cap.get(cv2.CAP_PROP_FPS)
		frameCount = cap.get(cv2.CAP_PROP_FRAME_COUNT)
		step = int(frameCount / imgCount - 1) if int(frameCount / imgCount - 1) > 1 else 1
		ret, frame = cap.read()
		x, y, w, h = cv2.selectROI(u"Select ROI", frame, False)
		cv2.destroyAllWindows()
		count = 0
		icount = 0
		auto_close_messagebox(u"INFO", u"Data Processing, Please Wait...", 5)
		while True:
			ret, frame = cap.read()
			if not ret:
				break
			count += 1
			if count % step == 0:
				icount += 1
				if icount > imgCount:
					break
				roi = frame[y : y + h, x : x + w]
				filename = destDir + u"/img_" + str(icount) + ".jpg"
				cv2.imwrite(filename, roi)
				progress = int(100 * icount / imgCount)
				self.progressThread.set_data(progress)
				self.progressThread.set_window(False)
				self.progressThread.start()
		cap.release()
		cv2.destroyAllWindows()
		self.progressThread.set_data(0)
		self.progressThread.set_window(True)
		self.progressThread.start()
		auto_close_messagebox(u"INFO", u"IMAGES PATH : {}".format(destDir), 5)

	def load_images(self, indexStart, indexEnd):
		parent_item = self.treeWidget.topLevelItem(0)
		ptCount = 0
		if parent_item:
			child_item = parent_item.child(3)
			spinbox = self.treeWidget.itemWidget(child_item, 1)
			ptCount = spinbox.value()
		for item in range(indexStart, indexEnd):
			image = cv2.imread(self.img_list[item])
			height, width, _ = image.shape
			results = self.model.predict(source = image, imgsz = 320, conf = 0.5, max_det = 8, verbose = False)
			tmpLabels = []
			for result in results:
				boxes = result.boxes.xywh
				scores = result.boxes.conf
				classes = result.boxes.cls
				class_names = [self.model.names[int(cls)] for cls in classes]
				for box, score, class_name in zip(boxes, scores, class_names):
					if class_name == 'mouse_whole':
						print(f'Class: {class_name}, Score: {score:.2f}, Box: {box}.')
						tmpLabel = Label()
						tmpLabel.box = [float(box[0] / width), float(box[1] / height), float(box[2] / width), float(box[3] / height), False]
						tmpPts = []
						for it in range(ptCount):
							x = tmpLabel.box[0] - 0.5 * tmpLabel.box[2] + it * tmpLabel.box[2] / ptCount
							y = tmpLabel.box[1]
							tmpPts.append([x, y, 1, False])
						tmpLabel.labelPts = tmpPts.copy()
						tmpPts.clear()
						tmpLabels.append(tmpLabel)
			if len(tmpLabels) == 0:
				tmpLabel = Label()
				tmpLabel.box = [0.5, 0.5, 0.1, 0.1, False]
				tmpPts = []
				for it in range(ptCount):
					x = tmpLabel.box[0] - 0.5 * tmpLabel.box[2] + it * tmpLabel.box[2] / ptCount
					y = tmpLabel.box[1]
					tmpPts.append([x, y, 1, False])
				tmpLabel.labelPts = tmpPts.copy()
				tmpPts.clear()
				tmpLabels.append(tmpLabel)
			label_list.append(tmpLabels)
			progress = int(100 * (item - indexStart + 1) / (indexEnd - indexStart))
			self.progressThread.set_data(progress)
			self.progressThread.set_window(False)
			self.progressThread.start()
		self.progressThread.set_data(0)
		self.progressThread.set_window(True)
		self.progressThread.start()

	def onResizeEvent(self, event: QResizeEvent):
		return

	def on_choose_button_clicked(self):
		folder_selected = filedialog.askdirectory()
		if folder_selected != "":
			parent_item = self.treeWidget.topLevelItem(0)
			if parent_item:
				child_item = parent_item.child(0)
				lineedit = self.treeWidget.itemWidget(child_item, 1)
				lineedit.setText(folder_selected)
				child_item2 = parent_item.child(4)
				lineedit2 = self.treeWidget.itemWidget(child_item2, 1)
				lineedit2.setText(folder_selected + r"/mouse.yaml")
				child_item3 = parent_item.child(5)
				lineedit3 = self.treeWidget.itemWidget(child_item3, 1)
				lineedit3.setText(folder_selected + r"/train.py")
				self.work_dir = folder_selected
				shutil.copy2(get_program_path() + r"/config/yolov8n-pose.pt", self.work_dir + r"/yolov8n-pose.pt")
				shutil.copy2(get_program_path() + r"/config/mouse.yaml", self.work_dir + r"/mouse.yaml")
				shutil.copy2(get_program_path() + r"/config/train.py", self.work_dir + r"/train.py")
				shutil.copy2(get_program_path() + r"/config/train.bat", self.work_dir + r"/train.bat")

	def on_load_data_button_clicked(self):
		if len(self.img_list) == 0 or len(label_list) == 0:
			messagebox.showerror(title = 'ERROR', message = 'Image List is Empty.')
			return
		parent_item = self.treeWidget.topLevelItem(0)
		trainQty = 0
		valQty = 0
		ptCount = 0
		if parent_item:
			child_item = parent_item.child(0)
			lineedit = self.treeWidget.itemWidget(child_item, 1)
			if lineedit.text() == "":
				messagebox.showerror(title = 'ERROR', message = 'Work Dir is Empty.')
				return
			child_item2 = parent_item.child(1)
			spinbox1 = self.treeWidget.itemWidget(child_item2, 1)
			if spinbox1.value() > len(self.img_list) or spinbox1.value() == 0:
				messagebox.showerror(title = 'ERROR', message = 'Incorrect Train Qty.')
				return
			trainQty = spinbox1.value()
			child_item3 = parent_item.child(2)
			spinbox2 = self.treeWidget.itemWidget(child_item3, 1)
			if spinbox2.value() > len(self.img_list) or spinbox2.value() == 0:
				messagebox.showerror(title = 'ERROR', message = 'Incorrect Val Qty.')
				return
			valQty = spinbox2.value()
			child_item3 = parent_item.child(3)
			spinbox3 = self.treeWidget.itemWidget(child_item3, 1)
			ptCount = spinbox3.value()
		print("Work Dir : {}".format(self.work_dir))
		os.makedirs(self.work_dir + r"/images", exist_ok = True)
		os.makedirs(self.work_dir + r"/images/train", exist_ok = True)
		os.makedirs(self.work_dir + r"/images/val", exist_ok = True)
		os.makedirs(self.work_dir + r"/labels", exist_ok = True)
		os.makedirs(self.work_dir + r"/labels/train", exist_ok = True)
		os.makedirs(self.work_dir + r"/labels/val", exist_ok = True)
		timestamp = time.strftime('%Y%m%d%H%M%S')
		for it in range(trainQty):
			shutil.copy2(self.img_list[it], self.work_dir + r"/images/train/" + str(it + 1) + "-" + timestamp + os.path.splitext(self.img_list[it])[1])
			with open(self.work_dir + r"/labels/train/" + str(it + 1) + "-" + timestamp + ".txt", "w") as file:
				text = ""
				for label in label_list[it]:
					text += label.labelText() + "\n"
				file.write(text[:-1])
		for it in range(valQty):
			shutil.copy2(self.img_list[- it - 1], self.work_dir + r"/images/val/" + str(len(self.img_list) - it) + "-" + timestamp + os.path.splitext(self.img_list[- it - 1])[1])
			with open(self.work_dir + r"/labels/val/" + str(len(label_list) - it) + "-" + timestamp + ".txt", "w") as file:
				text = ""
				for label in label_list[- it - 1]:
					text += label.labelText() + "\n"
				file.write(text[:-1])
		content = ""
		with open(self.work_dir + r"\mouse.yaml", 'r') as file:
			content = file.read()
		content = content.replace("$path$", os.path.normpath(self.work_dir).replace('\\', '/'))
		content = content.replace("$pt$", str(ptCount))
		with open(self.work_dir + r"\mouse.yaml", 'w') as file:
			file.write(content)
		messagebox.showinfo(title = 'INFO', message = 'Data File Created Successfully, Path : {}'.format(self.work_dir))

	def on_edit_yaml_button_clicked(self):
		os.system(r"notepad " + self.work_dir + r"\mouse.yaml")

	def on_edit_py_button_clicked(self):
		os.system(r"notepad " + self.work_dir + r"\train.py")

	def on_start_training_button_clicked(self):
		parent_item = self.treeWidget.topLevelItem(0)
		epochs = 200
		imgsz = 320
		if parent_item:
			child_item1 = parent_item.child(6)
			spinbox1 = self.treeWidget.itemWidget(child_item1, 1)
			if spinbox1.value() == 0:
				messagebox.showerror(title = 'ERROR', message = 'Incorrect epochs.')
				return
			epochs = spinbox1.value()
			child_item2 = parent_item.child(7)
			spinbox2 = self.treeWidget.itemWidget(child_item2, 1)
			if spinbox2.value() == 0:
				messagebox.showerror(title = 'ERROR', message = 'Incorrect epochs.')
				return
			imgsz = spinbox2.value()
		content = ""
		with open(self.work_dir + r"\train.py", 'r') as file:
			content = file.read()
		content = content.replace("$epochs$", str(epochs))
		content = content.replace("$imgsz$", str(imgsz))
		with open(self.work_dir + r"\train.py", 'w') as file:
			file.write(content)
		thread = threading.Thread(target = self.run_model)
		thread .start()
		auto_close_messagebox(u"INFO", u"Start Training, Please Minimize the Window and Wait...", 2)
	
	def run_model(self):
		os.chdir(os.path.normpath(self.work_dir))
		os.system(os.path.normpath(self.work_dir) + r"\train.bat")

	def slot_add_box_and_points(self):
		if len(self.img_list) == 0 or self.listWidget.currentItem() is None:
			messagebox.showinfo(title = 'INFO', message = 'Please Click Image List to Select an Image.')
			return
		fid = int(self.listWidget.currentItem().text()) - 1
		parent_item = self.treeWidget.topLevelItem(0)
		ptCount = 0
		if parent_item:
			child_item = parent_item.child(3)
			spinbox = self.treeWidget.itemWidget(child_item, 1)
			ptCount = spinbox.value()
		tmpLabel = Label()
		tmpLabel.box = [0.5, 0.5, 0.1, 0.1, False]
		tmpPts = []
		for it in range(ptCount):
			x = tmpLabel.box[0] - 0.5 * tmpLabel.box[2] + it * tmpLabel.box[2] / ptCount
			y = tmpLabel.box[1]
			tmpPts.append([x, y, 1, False])
		tmpLabel.labelPts = tmpPts.copy()
		tmpPts.clear()
		label_list[fid].append(tmpLabel)
		self.slot_image_item_clicked(self.listWidget.currentItem())

	def slot_delete_box_and_points(self):
		if len(self.img_list) == 0 or self.listWidget.currentItem() is None:
			messagebox.showinfo(title = 'INFO', message = 'Please Click Image List to Select an Image.')
			return
		fid = int(self.listWidget.currentItem().text()) - 1
		if len(label_list[fid]) == 1:
			messagebox.showinfo(title = 'INFO', message = 'At Least One Set of Box and Points Should be Retained.')
			return
		else:
			label_list[fid].pop()
		self.slot_image_item_clicked(self.listWidget.currentItem())
