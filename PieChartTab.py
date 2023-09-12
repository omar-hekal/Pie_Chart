from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pandas as pd
import sys
import PieChartWidget
import FilterationWidgets

class wdgPieChartTab(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setupUI()

    def setupUI(self):
        # GroupBox of Type
        self.gbxType = QGroupBox()
        self.lytType = QHBoxLayout()
        self.gbxType.setTitle("Type of Chart")
        self.rbtDrillDown = QRadioButton('DrillDown')
        self.rbtDrillDown.setChecked(True)
        self.rbtStacked = QRadioButton('Stacked')
        self.lytType.addWidget(self.rbtDrillDown)
        self.lytType.addWidget(self.rbtStacked)
        self.gbxType.setLayout(self.lytType)

        self.lytComboBoxes = QFormLayout()
        self.lytComboBoxes.setFormAlignment(Qt.AlignCenter)
        self.lytComboBoxes.setLabelAlignment(Qt.AlignRight)

        self.cmbAccording = QComboBox()
        self.cmbAccording.addItems(getCategoryColumnNames(self.data, ['Time', 'Date', 'Summary of Operations']))
        self.cmbBreakDown = QComboBox()
        self.cmbBreakDown.addItems(getCategoryColumnNames(self.data, ['Time', 'Date', 'Summary of Operations']))
        self.cmbBreakDown.setCurrentIndex(1)

        self.cmbFiltration = QComboBox()
        self.filtrationSeries = getAllColNamesAndTypes(self.data, ['Summary of Operations'])
        self.cmbFiltration.addItem('None')
        self.cmbFiltration.addItems(self.filtrationSeries.index)
        self.cmbFiltration.currentTextChanged.connect(self.evt_cmbFiltrationChanged)

        self.lytComboBoxes.addRow("According to", self.cmbAccording)
        self.lytComboBoxes.addRow("Break Down", self.cmbBreakDown)
        self.lytComboBoxes.addRow("Filtered By", self.cmbFiltration)

        self.lytFiltration = QVBoxLayout()

        self.btnSubmit = QPushButton('Submit')

        self.lytLeft = QVBoxLayout()
        self.lytLeft.addWidget(self.gbxType, 3)
        self.lytLeft.addLayout(self.lytComboBoxes, 40)
        self.lytLeft.addLayout(self.lytFiltration, 50)
        self.lytLeft.addWidget(self.btnSubmit, 3)

        self.lytRight = QVBoxLayout()

        self.btnSubmit.clicked.connect(self.evt_btnSubmitClicked)
        self.lytMain = QHBoxLayout()
        self.lytMain.addLayout(self.lytLeft, 1)
        self.lytMain.addLayout(self.lytRight, 9)
        self.setLayout(self.lytMain)

    def evt_cmbFiltrationChanged(self, text):
        # remove the previous Filtration Widget
        while self.lytFiltration.count():
            child = self.lytFiltration.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if text == 'None':
            pass
        elif 'Time' in text or 'time' in text:
            self.wdgFiltration = FilterationWidgets.TimeFiltrationWidget(self.data, text)
            self.lytFiltration.addWidget(self.wdgFiltration)
        elif 'Date' in text or 'date' in text:
            self.wdgFiltration = FilterationWidgets.DateFiltrationWidget(self.data, text)
            self.lytFiltration.addWidget(self.wdgFiltration)
        elif self.filtrationSeries[text] == 'object':
            self.wdgFiltration = FilterationWidgets.CategoryFiltrationWidget(self.data, text)
            self.wdgFiltration.btnEnter.setDefault(True)
            self.btnSubmit.setDefault(False)
            self.lytFiltration.addWidget(self.wdgFiltration)
        elif "int" in str(self.filtrationSeries[text]) or "float" in str(self.filtrationSeries[text]):
            self.wdgFiltration = FilterationWidgets.NumericFiltrationWidget(self.data, text)
            self.lytFiltration.addWidget(self.wdgFiltration)

    def checkInputData(self):
        string = ""
        if self.cmbAccording.currentText() == self.cmbBreakDown.currentText():
            string += "-The Main column and Breakdown column are the same.\n"

        if self.cmbFiltration.currentText() == 'None':
            pass

        elif self.filtrationSeries[self.cmbFiltration.currentText()] == 'object':
            if "Time" in self.cmbFiltration.currentText() or "time" in self.cmbFiltration.currentText():
                if self.wdgFiltration.timeFrom.time() > self.wdgFiltration.timeTo.time():
                    string += "-Wrong Input Time\n"
            elif "Date" in self.cmbFiltration.currentText() or "date" in self.cmbFiltration.currentText():
                if self.wdgFiltration.dateFrom.date() > self.wdgFiltration.dateTo.date():
                    string += "-Wrong Input Date\n"
            elif self.wdgFiltration.lstWidget.count() == 0:
                string += "-Nothing is selected in the filtration.\n"

        elif "int" in str(self.filtrationSeries[self.cmbFiltration.currentText()]) or "float" in str(self.filtrationSeries[self.cmbFiltration.currentText()]):
            if self.wdgFiltration.spinMin.value() > self.wdgFiltration.spinMax.value():
                string += "-Wrong input in filtration.\n"

        return string


    def evt_btnSubmitClicked(self):
        # remove the previous Chart Widget
        while self.lytRight.count():
            child = self.lytRight.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        errors = self.checkInputData()
        if errors == "":
            if self.rbtDrillDown.isChecked():
                type = 'DrillDown'
            else:
                type = 'Stacked'

            mainCol = self.cmbAccording.currentText()
            breakDownCol = self.cmbBreakDown.currentText()

            if self.cmbFiltration.currentText() == 'None':
                data = self.data
            else:
                data = self.wdgFiltration.getFilteredData()

            # check if the data is empty or not
            if data.empty:
                QMessageBox.critical(self, "Error", "There is no Data because of Filtration")
            else:
                wdgChart = PieChartWidget.wdgPieChart(type, mainCol, breakDownCol, data)
                self.lytRight.addWidget(wdgChart)

        else:
            QMessageBox.critical(self, 'Error', errors)

def getAllColNamesAndTypes(data: pd.DataFrame, ExcludedCols: list) -> pd.Series:
    dataTypes = data.dtypes
    dataTypes.drop(labels=ExcludedCols, inplace=True)
    return dataTypes

def getCategoryColumnNames(data: pd.DataFrame, ExcludedCols: list) -> list:
    dataTypes = data.dtypes
    colNames = []
    for type in dataTypes.index:
        if type not in ExcludedCols and dataTypes[type] == 'object':
            colNames.append(type)
    return colNames

## excluded: 'Time', 'Date', 'Summary of Operations'


if __name__ == "__main__":

    app = QApplication(sys.argv)
    dlg = QMainWindow()
    data = pd.read_csv('../activity_table.csv', index_col=0)

    wdg = wdgPieChartTab(data)
    tabs = QTabWidget()
    tabs.setMovable(True)
    tabs.addTab(wdg, "Pie Chart")

    dlg.setCentralWidget(tabs)
    dlg.resize(1900, 800)
    dlg.show()

    sys.exit(app.exec_())
