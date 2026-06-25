# -*- coding: utf-8 -*-
# !/usr/bin/env python

import os
import numpy as np
import pandas as pd
import xlsxwriter
from units.functions import *
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QPixmap, QStandardItem, QImage
from PyQt6.QtWidgets import QTableWidgetItem, QLabel, QTableWidget, QApplication, QMainWindow, QTableWidgetItem, QMessageBox

class Ui_ColorDif(object):
    def __init__(self):
        self.rowcie = 0
        self.rowrgb = 0
        self.referencecie = []
        self.referencergb = []

    def setupUi(self, ColorDif):
        ColorDif.setObjectName("ColorDif")
        ColorDif.resize(938, 600)
        self.centralwidget = QtWidgets.QWidget(ColorDif)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.tableWidget_result = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget_result.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        self.tableWidget_result.setObjectName("tableWidget_result")
        self.tableWidget_result.setColumnCount(0)
        self.tableWidget_result.setRowCount(0)
        self.gridLayout_2.addWidget(self.tableWidget_result, 8, 0, 1, 4)
        self.gridLayout_1 = QtWidgets.QGridLayout()
        self.gridLayout_1.setObjectName("gridLayout_1")
        self.label_capture = QtWidgets.QLabel(self.centralwidget)
        self.label_capture.setMinimumSize(QtCore.QSize(320, 240))
        self.label_capture.setMaximumSize(QtCore.QSize(320, 240))
        self.label_capture.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ForbiddenCursor))
        self.label_capture.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.label_capture.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.label_capture.setText("")
        self.label_capture.setObjectName("label_capture")
        self.gridLayout_1.addWidget(self.label_capture, 1, 1, 1, 1)
        self.label_refcapture = QtWidgets.QLabel(self.centralwidget)
        self.label_refcapture.setEnabled(True)
        self.label_refcapture.setMinimumSize(QtCore.QSize(320, 240))
        self.label_refcapture.setMaximumSize(QtCore.QSize(320, 240))
        self.label_refcapture.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ForbiddenCursor))
        self.label_refcapture.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.label_refcapture.setText("")
        self.label_refcapture.setObjectName("label_refcapture")
        self.gridLayout_1.addWidget(self.label_refcapture, 1, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")
        self.gridLayout_1.addWidget(self.label_4, 0, 0, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setObjectName("label_5")
        self.gridLayout_1.addWidget(self.label_5, 0, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout_1, 1, 3, 1, 1)
        self.gridLayout_0 = QtWidgets.QGridLayout()
        self.gridLayout_0.setObjectName("gridLayout_0")
        self.pushButton_capture = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_capture.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_capture.setObjectName("pushButton_capture")
        self.pushButton_capture.clicked.connect(self.capture)
        self.gridLayout_0.addWidget(self.pushButton_capture, 3, 1, 1, 1)
        self.spinBox_capture = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBox_capture.setObjectName("spinBox_capture")
        self.gridLayout_0.addWidget(self.spinBox_capture, 3, 0, 1, 1)
        self.comboBox_colorspace = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox_colorspace.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.comboBox_colorspace.setMouseTracking(False)
        self.comboBox_colorspace.setTabletTracking(False)
        self.comboBox_colorspace.setFocusPolicy(QtCore.Qt.FocusPolicy.WheelFocus)
        self.comboBox_colorspace.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.DefaultContextMenu)
        self.comboBox_colorspace.setAcceptDrops(False)
        self.comboBox_colorspace.setObjectName("comboBox_colorspace")
        self.comboBox_colorspace.addItem("")
        self.comboBox_colorspace.addItem("")
        self.gridLayout_0.addWidget(self.comboBox_colorspace, 1, 0, 1, 1)
        self.comboBox_delta = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox_delta.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.comboBox_delta.setObjectName("comboBox_delta")
        self.comboBox_delta.addItem("")
        self.comboBox_delta.addItem("")
        self.comboBox_delta.addItem("")
        self.comboBox_delta.addItem("")
        self.gridLayout_0.addWidget(self.comboBox_delta, 1, 1, 1, 1)
        self.pushButton_tablereset = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_tablereset.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_tablereset.setObjectName("pushButton_tablereset")
        self.pushButton_tablereset.clicked.connect(self.tablewidgit_clear)
        self.gridLayout_0.addWidget(self.pushButton_tablereset, 5, 0, 1, 1)
        self.checkBox_refcapture = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox_refcapture.setObjectName("checkBox_refcapture")
        self.gridLayout_0.addWidget(self.checkBox_refcapture, 4, 0, 1, 1)
        self.pushButton_tablesave = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_tablesave.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_tablesave.setObjectName("pushButton_tablesave")
        self.pushButton_tablesave.clicked.connect(self.tablewidget_save)
        self.gridLayout_0.addWidget(self.pushButton_tablesave, 5, 1, 1, 1)
        self.pushButton_setref = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_setref.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_setref.setObjectName("pushButton_setref")
        self.pushButton_setref.clicked.connect(self.reference_capture)
        self.gridLayout_0.addWidget(self.pushButton_setref, 4, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setMaximumSize(QtCore.QSize(16777215, 22))
        self.label_3.setObjectName("label_3")
        self.gridLayout_0.addWidget(self.label_3, 2, 0, 1, 2)
        self.gridLayout_2.addLayout(self.gridLayout_0, 1, 0, 2, 3)
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 5, 0, 1, 2)
        self.tableWidget_reference = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget_reference.setMinimumSize(QtCore.QSize(0, 0))
        self.tableWidget_reference.setMaximumSize(QtCore.QSize(16777215, 55))
        self.tableWidget_reference.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.tableWidget_reference.setGridStyle(QtCore.Qt.PenStyle.SolidLine)
        self.tableWidget_reference.setRowCount(0)
        self.tableWidget_reference.setColumnCount(0)
        self.tableWidget_reference.setObjectName("tableWidget_reference")
        self.tableWidget_reference.horizontalHeader().setDefaultSectionSize(100)
        self.tableWidget_reference.verticalHeader().setDefaultSectionSize(30)
        self.gridLayout_2.addWidget(self.tableWidget_reference, 5, 3, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 6, 0, 1, 1)
        ColorDif.setCentralWidget(self.centralwidget)

        self.retranslateUi(ColorDif)
        QtCore.QMetaObject.connectSlotsByName(ColorDif)

    def retranslateUi(self, ColorDif):
        _translate = QtCore.QCoreApplication.translate
        ColorDif.setWindowTitle(_translate("ColorDif", "ColorDif"))
        self.label_4.setText(_translate("ColorDif", "Reference Measurement:"))
        self.label_5.setText(_translate("ColorDif", "Measurement:"))
        self.pushButton_capture.setText(_translate("ColorDif", "Snap"))
        self.comboBox_colorspace.setItemText(0, _translate("ColorDif", "CIE-Lab/LCH"))
        self.comboBox_colorspace.setItemText(1, _translate("ColorDif", "RGB"))
        self.comboBox_delta.setItemText(0, _translate("ColorDif", "delta_e_cie1976"))
        self.comboBox_delta.setItemText(1, _translate("ColorDif", "delta_e_cie1994"))
        self.comboBox_delta.setItemText(2, _translate("ColorDif", "delta_e_cie2000"))
        self.comboBox_delta.setItemText(3, _translate("ColorDif", "delta_e_cmc"))
        self.pushButton_tablereset.setText(_translate("ColorDif", "Reset"))
        self.checkBox_refcapture.setText(_translate("ColorDif", "Set Referans"))
        self.pushButton_tablesave.setText(_translate("ColorDif", "Table Save"))
        self.pushButton_setref.setText(_translate("ColorDif", "Set Ref"))
        self.label_3.setText(_translate("ColorDif", "Delta_e _... only CIE-Lab / LCH"))
        self.label.setText(_translate("ColorDif", "Reference Measurement:"))
        self.label_2.setText(_translate("ColorDif", "Measurement:"))

    def tablewidgit_clear(self):
        self.rowcie = 0
        self.rowrgb = 0
        self.referencecie = []
        self.referencergb = []
        self.label_capture.clear()
        self.label_refcapture.clear()
        self.tableWidget_result.clear()
        self.tableWidget_reference.clear()
        self.tableWidget_result.setRowCount(0)
        self.tableWidget_reference.setRowCount(0)
        self.tableWidget_result.setColumnCount(0)
        self.tableWidget_reference.setColumnCount(0)

    def reference_capture(self):
        if self.checkBox_refcapture.isChecked():
            self.capture_reference()
        else:
            msg_setref = QMessageBox()
            msg_setref.setIcon(QMessageBox.Icon.Warning)
            msg_setref.setWindowTitle("Warning!")
            msg_setref.setText("Please mark the reference!")
            msg_setref.exec()

    def tablewidget_save(self):
        if self.tableWidget_reference.rowCount() == 0 or self.tableWidget_result.rowCount() == 0:
            msg_setref = QMessageBox()
            msg_setref.setIcon(QMessageBox.Icon.Warning)
            msg_setref.setWindowTitle("Warning!")
            msg_setref.setText("Please measure first!")
            msg_setref.exec()
        else:
            group = []
            group_ref = []
            for row in range(0,self.tableWidget_result.rowCount()):
                group_row=[]
                for column in range(0,self.tableWidget_result.columnCount()):
                    item = self.tableWidget_result.item(row, column).text()
                    group_row.append(item)
                group.append(group_row)
            if self.checkBox_refcapture.isChecked():
                [(group_ref.append([self.tableWidget_reference.item(0, column).text()])) for column in range(self.tableWidget_reference.columnCount())]
            path = os.getcwd()
            if self.checkBox_refcapture.isChecked() and self.comboBox_colorspace.currentText() == 'RGB':
                df1 = pd.DataFrame(group_ref,index=["Name", "R*", "G*", "B*"])
                df2 = pd.DataFrame(group,columns=["Name", "R*", "G*", "B*", "Dr*", "Dg*", "Db*"])
                df1 = df1.T
                writer = pd.ExcelWriter(path + '/output.xlsx', engine='xlsxwriter')
                df1.to_excel(writer, sheet_name='Sheet1')
                df2.to_excel(writer, sheet_name='Sheet1', startrow=2)
                writer.close()
                print("Saved to:\n{}/output.xlsx".format(path))
            elif not self.checkBox_refcapture.isChecked() and self.comboBox_colorspace.currentText() == 'RGB':
                df1 = pd.DataFrame(group,columns=["Name", "R*", "G*", "B*"])
                writer = pd.ExcelWriter(path + '/output.xlsx', engine='xlsxwriter')
                df1.to_excel(writer, sheet_name='Sheet1')
                writer.close()
                print("Saved to:\n{}/output.xlsx".format(path))
            elif self.checkBox_refcapture.isChecked() and self.comboBox_colorspace.currentText() == 'CIE-Lab/LCH':
                df1 = pd.DataFrame(group_ref,index=["Name", "L*", "a*", "b*", "C*", "h*"])
                df2 = pd.DataFrame(group,columns=["Name", "L*", "a*", "b*", "C*", "h*", "DL*", "Da*", "Db*", "DC*", "DH*", "DE*"])
                df1 = df1.T
                writer = pd.ExcelWriter(path + '/output.xlsx', engine='xlsxwriter')
                df1.to_excel(writer, sheet_name='Sheet1')
                df2.to_excel(writer, sheet_name='Sheet1', startrow=2)
                writer.close()
                print("Saved to:\n{}/output.xlsx".format(path))
            elif not self.checkBox_refcapture.isChecked() and self.comboBox_colorspace.currentText() == 'CIE-Lab/LCH':
                df1 = pd.DataFrame(group,columns=["Name", "L*", "a*", "b*", "C*", "h*"])
                writer = pd.ExcelWriter(path + '/output.xlsx', engine='xlsxwriter')
                df1.to_excel(writer, sheet_name='Sheet1')
                writer.close()
                print("Saved to:\n{}/output.xlsx".format(path))

    def capture_reference(self):
        self.rowcie = 0
        self.rowrgb = 0
        frame, resize, h, w = VideoOperation()
        self.label_refcapture.setPixmap(QtGui.QPixmap.fromImage(QImage(resize, h, w, QImage.Format.Format_RGB888)))
        if self.comboBox_colorspace.currentText() == 'RGB':
            rgb_calculator = RgbCalculator(frame)
            self.referencergb = [rgb_calculator[0], rgb_calculator[1], rgb_calculator[2]]
            self.tableWidget_reference.setColumnCount(4)
            self.tableWidget_reference.setRowCount(1)
            self.tableWidget_reference.setHorizontalHeaderLabels(["Name", "R*", "G*", "B*"])
            self.tableWidget_reference.setVerticalHeaderLabels(["Ref"])
            self.tableWidget_reference.setItem(0, 0, QTableWidgetItem('{}'.format(self.spinBox_capture.value())))
            self.tableWidget_reference.setItem(0, 1, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[0])))
            self.tableWidget_reference.setItem(0, 2, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[1])))
            self.tableWidget_reference.setItem(0, 3, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[2])))
        else:
            LabCH_calculator = LabCHCalculator(frame)
            self.referencecie = [LabCH_calculator[0], LabCH_calculator[1], LabCH_calculator[2], LabCH_calculator[3], LabCH_calculator[4]]
            self.tableWidget_reference.setColumnCount(6)
            self.tableWidget_reference.setRowCount(1)
            self.tableWidget_reference.setHorizontalHeaderLabels(["Name", "L*", "a*", "b*", "C*", "HS*"])
            self.tableWidget_reference.setVerticalHeaderLabels(["Ref"])
            self.tableWidget_reference.setItem(0, 0, QTableWidgetItem('Ref-{}'.format(self.spinBox_capture.value())))
            self.tableWidget_reference.setItem(0, 1, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[0])))
            self.tableWidget_reference.setItem(0, 2, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[1])))
            self.tableWidget_reference.setItem(0, 3, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[2])))
            self.tableWidget_reference.setItem(0, 4, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[3])))
            self.tableWidget_reference.setItem(0, 5, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[4])))

    def capture(self):
        if self.comboBox_colorspace.currentText() == 'RGB':
            if self.checkBox_refcapture.isChecked() and len(self.referencergb) != 0:
                frame, resize, h, w = VideoOperation()
                rgb_calculator = RgbCalculator(frame)
                self.tableWidget_result.setColumnCount(7)
                self.tableWidget_result.setRowCount(self.rowrgb + 1)
                self.tableWidget_result.setHorizontalHeaderLabels(["Name", "R*", "G*", "B*", "Dr*", "Dg*", "Db*"])
                self.tableWidget_result.setItem(self.rowrgb, 0, QTableWidgetItem('{}'.format(self.spinBox_capture.value())))
                self.tableWidget_result.setItem(self.rowrgb, 1, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[0])))
                self.tableWidget_result.setItem(self.rowrgb, 2, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[1])))
                self.tableWidget_result.setItem(self.rowrgb, 3, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[2])))
                self.tableWidget_result.setItem(self.rowrgb, 4, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[0] - self.referencergb[0])))
                self.tableWidget_result.setItem(self.rowrgb, 5, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[1] - self.referencergb[1])))
                self.tableWidget_result.setItem(self.rowrgb, 6, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[2] - self.referencergb[2])))
                self.label_capture.setPixmap(QtGui.QPixmap.fromImage(QImage(resize, h, w, QImage.Format.Format_RGB888)))
                self.rowrgb = self.rowrgb + 1
            elif (not self.checkBox_refcapture.isChecked()) and len(self.referencergb) == 0:
                frame, resize, h, w = VideoOperation()
                rgb_calculator = RgbCalculator(frame)
                self.tableWidget_result.setColumnCount(4)
                self.rowrgb = self.rowrgb + 1
                self.tableWidget_result.setRowCount(self.rowrgb)
                self.tableWidget_result.setHorizontalHeaderLabels(["Name", "R*", "G*", "B*"])
                self.tableWidget_result.setItem(self.rowrgb - 1, 0, QTableWidgetItem('{}'.format(self.spinBox_capture.value())))
                self.tableWidget_result.setItem(self.rowrgb - 1, 1, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[0])))
                self.tableWidget_result.setItem(self.rowrgb - 1, 2, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[1])))
                self.tableWidget_result.setItem(self.rowrgb - 1, 3, QTableWidgetItem('{0:.4f}'.format(rgb_calculator[2])))
                self.label_capture.setPixmap(QtGui.QPixmap.fromImage(QImage(resize, h, w, QImage.Format.Format_RGB888)))
            else:
                msg_setref = QMessageBox()
                msg_setref.setIcon(QMessageBox.Icon.Warning)
                msg_setref.setWindowTitle("Warning!")
                msg_setref.setText("The reference measurement has been made but not marked.")
                msg_setref.exec()
        else:
            if self.checkBox_refcapture.isChecked() and len(self.referencecie) != 0:
                frame, resize, h, w = VideoOperation()
                LabCH_calculator = LabCHCalculator(frame)
                self.tableWidget_result.setColumnCount(12)
                self.tableWidget_result.setRowCount(self.rowcie + 1)
                delta_calculator = DeltaCalculator(self.referencecie, LabCH_calculator, self.comboBox_delta.currentText())
                self.tableWidget_result.setHorizontalHeaderLabels(["Name", "L*", "a*", "b*", "C*", "h*", "DL*", "Da*", "Db*", "DC*", "DH*", "DE*"])
                self.tableWidget_result.setItem(self.rowcie, 0, QTableWidgetItem('{}'.format(self.spinBox_capture.value())))
                self.tableWidget_result.setItem(self.rowcie, 1, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[0])))
                self.tableWidget_result.setItem(self.rowcie, 2, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[1])))
                self.tableWidget_result.setItem(self.rowcie, 3, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[2])))
                self.tableWidget_result.setItem(self.rowcie, 4, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[3])))
                self.tableWidget_result.setItem(self.rowcie, 5, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[4])))
                self.tableWidget_result.setItem(self.rowcie, 6, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[0] - self.referencecie[0])))
                self.tableWidget_result.setItem(self.rowcie, 7, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[1] - self.referencecie[1])))
                self.tableWidget_result.setItem(self.rowcie, 8, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[2] - self.referencecie[2])))
                self.tableWidget_result.setItem(self.rowcie, 9, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[3] - self.referencecie[3])))
                self.tableWidget_result.setItem(self.rowcie, 10, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[4] - self.referencecie[4])))
                self.tableWidget_result.setItem(self.rowcie, 11, QTableWidgetItem('{0:.4f}'.format(delta_calculator)))
                self.label_capture.setPixmap(QtGui.QPixmap.fromImage(QImage(resize, h, w, QImage.Format.Format_RGB888)))
                self.rowcie = self.rowcie + 1
            elif not self.checkBox_refcapture.isChecked() and len(self.referencecie) == 0:
                frame, resize, h, w = VideoOperation()
                LabCH_calculator = LabCHCalculator(frame)
                self.tableWidget_result.setColumnCount(6)
                self.rowcie = self.rowcie + 1
                self.tableWidget_result.setRowCount(self.rowcie)
                self.tableWidget_result.setHorizontalHeaderLabels(["Name", "L*", "a*", "b*", "C*", "h*"])
                self.tableWidget_result.setItem(self.rowcie - 1, 0, QTableWidgetItem('{}'.format(self.spinBox_capture.value())))
                self.tableWidget_result.setItem(self.rowcie - 1, 1, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[0])))
                self.tableWidget_result.setItem(self.rowcie - 1, 2, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[1])))
                self.tableWidget_result.setItem(self.rowcie - 1, 3, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[2])))
                self.tableWidget_result.setItem(self.rowcie - 1, 4, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[3])))
                self.tableWidget_result.setItem(self.rowcie - 1, 5, QTableWidgetItem('{0:.4f}'.format(LabCH_calculator[4])))
                self.label_capture.setPixmap(QtGui.QPixmap.fromImage(QImage(resize, h, w, QImage.Format.Format_RGB888)))
            else:
                msg_setref = QMessageBox()
                msg_setref.setIcon(QMessageBox.Icon.Warning)
                msg_setref.setWindowTitle("Warning!")
                msg_setref.setText("The reference measurement has been made but not marked..")
                msg_setref.exec()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ColorDif = QtWidgets.QMainWindow()
    ui = Ui_ColorDif()
    ui.setupUi(ColorDif)
    ColorDif.show()
    sys.exit(app.exec())
