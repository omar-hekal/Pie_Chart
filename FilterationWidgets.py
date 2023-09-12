from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import pandas as pd

"""
    Every Class has a special func called getFilteredData return data after filtration
"""

class CategoryFiltrationWidget(QWidget):
    def __init__(self, data: pd.DataFrame, filtrationCol):
        super().__init__()
        self.data = data
        self.filtrationCol = filtrationCol

        self.elements = set(self.data[self.filtrationCol].value_counts(dropna=True).index)
        self.selectedElements = set()

        completer = QCompleter(self.elements)

        self.lytUpper = QHBoxLayout()
        self.lineCategory = QLineEdit()
        self.lineCategory.setCompleter(completer)

        self.btnEnter = QPushButton('+')
        self.btnEnter.setMaximumWidth(30)
        self.btnEnter.setMinimumWidth(30)
        self.btnEnter.clicked.connect(self.evt_btnEnterClicked)

        self.lytUpper.addWidget(self.lineCategory, 9)
        self.lytUpper.addWidget(self.btnEnter, 1)

        self.lstWidget = QListWidget()
        self.lstWidget.setAlternatingRowColors(True)
        self.lstWidget.setSelectionMode(QListWidget.MultiSelection)
        self.lstWidget.setSelectionBehavior(QListWidget.SelectItems)

        self.lytLower = QHBoxLayout()
        self.btnRemove = QPushButton("Remove")
        self.btnRemove.clicked.connect(self.evt_btnRemoveClicked)
        self.lytLower.addStretch(9)
        self.lytLower.addWidget(self.btnRemove)

        self.lytMain = QVBoxLayout()
        self.lytMain.addLayout(self.lytUpper, 1)
        self.lytMain.addWidget(self.lstWidget, 8)
        self.lytMain.addLayout(self.lytLower, 1)

        self.setLayout(self.lytMain)

    def evt_btnEnterClicked(self):
        category = self.lineCategory.text()
        if category in self.selectedElements:
            QMessageBox.critical(self, 'Error', 'Already Added')
        elif category in self.elements:
            self.lstWidget.addItem(category)
            self.lineCategory.setText("")
            self.selectedElements.add(category)
        else:
            QMessageBox.critical(self, 'Error', 'This Category is not in the column')

    def evt_btnRemoveClicked(self):
        for item in self.lstWidget.selectedItems():
            self.selectedElements.remove(item.text())
            self.lstWidget.takeItem(self.lstWidget.row(item))

    def getFilteredData(self) -> pd.DataFrame:
        filteredData = self.data.loc[self.data[self.filtrationCol].isin(self.selectedElements)]
        return filteredData

class NumericFiltrationWidget(QWidget):
    def __init__(self, data: pd.DataFrame, filtrationCol):
        super().__init__()
        self.data = data
        maxValue = data[filtrationCol].max()
        minValue = data[filtrationCol].min()
        self.filtrationCol = filtrationCol

        self.lytMain = QFormLayout()
        self.spinMin = QDoubleSpinBox()
        self.spinMin.setRange(minValue, maxValue)
        self.spinMin.setValue(minValue)
        self.spinMin.setSingleStep(100)

        self.spinMax = QDoubleSpinBox()
        self.spinMax.setRange(minValue, maxValue)
        self.spinMax.setValue(maxValue)
        self.spinMax.setSingleStep(100)

        self.lytMain.addRow('Min', self.spinMin)
        self.lytMain.addRow('Max', self.spinMax)

        self.setLayout(self.lytMain)

    def getFilteredData(self) -> pd.DataFrame:
        minValue = self.spinMin.value()
        maxValue = self.spinMax.value()
        filteredData = self.data.loc[(self.data[self.filtrationCol] <= maxValue) & (self.data[self.filtrationCol] >= minValue)]
        return filteredData

class TimeFiltrationWidget(QWidget):
    def __init__(self, data: pd.DataFrame, filtrationCol):
        super().__init__()
        self.data = data
        self.filtrationCol = filtrationCol

        # change the column to the type of timeDelta to make it easier to work with it
        self.data[filtrationCol] = pd.to_timedelta(self.data[filtrationCol])


        self.lytMain = QFormLayout()
        self.timeFrom = QTimeEdit()
        self.timeFrom.setDisplayFormat("hh:mm:ss")
        self.timeTo = QTimeEdit()
        self.timeTo.setDisplayFormat("hh:mm:ss")
        self.lytMain.addRow("From", self.timeFrom)
        self.lytMain.addRow("To", self.timeTo)

        self.setLayout(self.lytMain)


    def getFilteredData(self) -> pd.DataFrame:
        fromTime = self.timeFrom.time()
        toTime = self.timeTo.time()

        fromTime = pd.Timedelta(hours=fromTime.hour(), minutes=fromTime.minute(), seconds=fromTime.second())
        toTime = pd.Timedelta(hours=toTime.hour(), minutes=toTime.minute(), seconds=toTime.second())

        filteredData = self.data.loc[(self.data[self.filtrationCol] >= fromTime) & (self.data[self.filtrationCol] <= toTime)]
        return filteredData

class DateFiltrationWidget(QWidget):
    def __init__(self, data: pd.DataFrame, filtrationCol):
        super().__init__()
        self.data = data
        self.filtrationCol = filtrationCol

        # change the column to the type of timeDelta to make it easier to work with it
        self.data[filtrationCol] = pd.to_datetime(self.data[filtrationCol])

        min = self.data[filtrationCol].min()
        max = self.data[filtrationCol].max()

        minDate = QDate(min.year, min.month, min.day)
        maxDate = QDate(max.year, max.month, max.day)

        self.lytMain = QFormLayout()
        self.dateFrom = QDateEdit()
        self.dateFrom.setDate(minDate)
        self.dateFrom.setDisplayFormat("dd-MM-yyyy")
        self.dateFrom.setCalendarPopup(True)
        self.dateFrom.setDateRange(minDate, maxDate)

        self.dateTo = QDateEdit()
        self.dateTo.setDate(maxDate)
        self.dateTo.setDisplayFormat("dd-MM-yyyy")
        self.dateTo.setCalendarPopup(True)
        self.dateTo.setDateRange(minDate, maxDate)

        self.lytMain.addRow("From", self.dateFrom)
        self.lytMain.addRow("To", self.dateTo)

        self.setLayout(self.lytMain)

    def getFilteredData(self) -> pd.DataFrame:
        fromDate = self.dateFrom.date()
        toDate = self.dateTo.date()

        fromDate = pd.Timestamp(day=fromDate.day(), month=fromDate.month(), year=fromDate.year())
        toDate = pd.Timestamp(day=toDate.day(), month=toDate.month(), year=toDate.year())

        filteredData = self.data.loc[(self.data[self.filtrationCol] >= fromDate) & (self.data[self.filtrationCol] <= toDate)]
        return filteredData


if __name__ == '__main__':

    app = QApplication(sys.argv)
    dlg = QDialog()

    data = pd.read_csv('../activity_table.csv', index_col=0)

    l = QVBoxLayout()
    d = DateFiltrationWidget(data, 'Date')
    l.addWidget(d)
    dlg.resize(300, 100)

    dlg.setLayout(l)
    dlg.show()
    sys.exit(app.exec_())
