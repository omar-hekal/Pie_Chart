import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtChart import *
import pandas as pd
import time

class MainSlice(QPieSlice):
    def __init__(self, name: str,dataFrame: pd.DataFrame, breakDownCol: str):
        # dataFrame contain all rows that have the value of "name"
        super().__init__()
        self.setLabel(name)
        self.setLabelVisible()
        self.setValue(len(dataFrame))
        self.df = dataFrame

        self.breakDownCol = breakDownCol

    def getBreakDownSlices(self):
        self.breakDownSlices = []
        breakDownElements = self.df[self.breakDownCol].value_counts(dropna=True)

        for element in breakDownElements.index:
            slice = QPieSlice(element, breakDownElements[element])
            self.breakDownSlices.append(slice)

    def getStackedPieSeries(self):
        self.getBreakDownSlices()

        self.stackedPieSeries = QPieSeries()
        self.stackedPieSeries.setHoleSize(0.5)
        self.stackedPieSeries.setPieSize(0.7)

        for slice in self.breakDownSlices:
            self.stackedPieSeries.append(slice)

        self.stackedPieSeries.setPieStartAngle(self.startAngle())
        self.stackedPieSeries.setPieEndAngle(self.startAngle() + self.angleSpan())
        self.angleSpanChanged.connect(self.evt_angleChanged)

    def evt_angleChanged(self):
        startAngle = self.startAngle()
        endAngle = startAngle + self.angleSpan()

        self.stackedPieSeries.setPieStartAngle(startAngle)
        self.stackedPieSeries.setPieEndAngle(endAngle)


class wdgPieChart(QWidget):
    def __init__(self, type: str, mainCol, breakDownCol, filteredData: pd.DataFrame):
        super().__init__()
        self.mainCol = mainCol
        self.breakDownCol = breakDownCol
        self.type = type  # type : Stacked,  DrillDown

        self.data = filteredData
        self.mainColElements = list(self.data[mainCol].dropna().sort_values(axis = 0).unique())
        self.mainSlices = []
        self.current_main_slice = None

        self.setupUI()
        self.getMainSlices()
        self.createMainPieSeries()

    def setupUI(self):
        self.lytMain = QStackedLayout()

        # widget for main slices
        self.wdgMainSlices = Widget(self)
        self.wdgMainSlices.btnLeft.clicked.connect(lambda: self.evt_moveBackward(self.wdgMainSlices))
        self.wdgMainSlices.btnRight.clicked.connect(lambda: self.evt_moveForward(self.wdgMainSlices))
        self.lytMain.addWidget(self.wdgMainSlices)

        # widget for drill down slices
        if self.type == "DrillDown":
            self.wdgDrillDownSlices = Widget(self)
            self.wdgDrillDownSlices.lytMain.insertLayout(0, self.wdgDrillDownSlices.lytHistory)
            self.wdgDrillDownSlices.btnBackPage.setText(self.mainCol)
            self.wdgDrillDownSlices.btnBackPage.clicked.connect(lambda: self.lytMain.setCurrentIndex(0))
            self.wdgDrillDownSlices.btnLeft.clicked.connect(lambda: self.evt_moveBackward(self.wdgDrillDownSlices))
            self.wdgDrillDownSlices.btnRight.clicked.connect(lambda: self.evt_moveForward(self.wdgDrillDownSlices))
            self.lytMain.addWidget(self.wdgDrillDownSlices)

        self.setLayout(self.lytMain)

    def getMainSlices(self):
        # TODO: get main slices
        total = len(self.data)

        for element in self.mainColElements:
            df = self.data.loc[self.data[self.mainCol] == element]
            label = f"{element}  {round(len(df)/total*100, 2)}%"
            main_slice = MainSlice(name=label, dataFrame=df, breakDownCol=self.breakDownCol)
            self.mainSlices.append(main_slice)

        # sort slices
        self.mainSlices = sorted(self.mainSlices, key=lambda x: x.value(), reverse=True)

    def createMainPieSeries(self):
        # TODO: Create main pieSeries
        slices_per_chart = 7
        num_of_pages = len(self.mainSlices)//slices_per_chart + (((len(self.mainSlices) % slices_per_chart) > 0) & 1)  ## determine number of pages
        self.wdgMainSlices.lblPages.setText(str(num_of_pages))
        self.wdgMainSlices.lblCounter.setText("1")

        for pageNum in range(num_of_pages):
            mainSlicesSeries = QPieSeries()

            chart = QChart()
            chart.setAnimationOptions(QChart.AllAnimations)
            chart.addSeries(mainSlicesSeries)

            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)

            for i in range(slices_per_chart * pageNum, slices_per_chart * pageNum + slices_per_chart):
                if i == len(self.mainSlices):
                    break
                mainSlicesSeries.append(self.mainSlices[i])

                if self.type == 'Stacked':
                    self.mainSlices[i].getStackedPieSeries()
                    self.mainSlices[i].setLabelPosition(QPieSlice.LabelInsideNormal)
                    chart.addSeries(self.mainSlices[i].stackedPieSeries)
                    self.mainSlices[i].stackedPieSeries.hovered.connect(lambda slice, chk:self.evt_StackedSliceHovered(slice, chk))

                    for marker in chart.legend().markers(self.mainSlices[i].stackedPieSeries):
                        marker.setVisible(False)


            if self.type == 'DrillDown':
                mainSlicesSeries.clicked.connect(self.evt_DrillDownSliceClicked)
            else:
                mainSlicesSeries.setPieSize(0.5)

            self.wdgMainSlices.lytCharts.addWidget(chart_view)

        if num_of_pages == 1:
            self.wdgMainSlices.btnRight.setDisabled(True)

    def evt_StackedSliceHovered(self, slice:QPieSlice, chk):
        if chk:
            slice.setExploded(True)
            slice.setLabelVisible(True)
        else:
            slice.setExploded(False)
            slice.setLabelVisible(False)

    def evt_DrillDownSliceClicked(self, main_slice:MainSlice):
        # remove the content of lytCharts"QStackedLayout" of wdgBreakdownSlices
        for idx in range(self.wdgDrillDownSlices.lytCharts.count() - 1, -1, -1):
            self.wdgDrillDownSlices.lytCharts.takeAt(idx)

        main_slice.getBreakDownSlices()     # get the drillDown slices
        if len(main_slice.breakDownSlices) != 0:  # to check if the slice contain breakDown Slices if not when you click nothing happen
            self.wdgDrillDownSlices.btnLeft.setDisabled(True)
            self.lytMain.setCurrentIndex(1)
            self.wdgDrillDownSlices.lblCurrentPage.setText(main_slice.label())

            # get number of pages and set up the pages labels
            slices_per_chart = 20
            num_of_pages = len(main_slice.breakDownSlices) // slices_per_chart + (((len(main_slice.breakDownSlices) % slices_per_chart) > 0) & 1)
            print(f"{len(main_slice.breakDownSlices)} \t{num_of_pages}")
            self.wdgDrillDownSlices.lblPages.setText(str(num_of_pages))
            self.wdgDrillDownSlices.lblCounter.setText("1")

            # create the pages of DrillDown
            for pageNum in range(num_of_pages):
                series = QPieSeries()

                chart = QChart()
                chart.setAnimationOptions(QChart.AllAnimations)
                chart.legend().setAlignment(Qt.AlignRight)
                chart.addSeries(series)

                chart_view = QChartView(chart)
                chart_view.setRenderHint(QPainter.Antialiasing)

                for i in range(slices_per_chart * pageNum, slices_per_chart * pageNum + slices_per_chart):
                    if i == len(main_slice.breakDownSlices):
                        break
                    series.append(main_slice.breakDownSlices[i])
                self.wdgDrillDownSlices.lytCharts.addWidget(chart_view)

            if num_of_pages == 1:
                self.wdgDrillDownSlices.btnRight.setDisabled(True)
            else:
                self.wdgDrillDownSlices.btnRight.setEnabled(True)

    def evt_moveBackward(self, widget):
        pageNum = int(widget.lblCounter.text()) - 1
        widget.lblCounter.setText(str(pageNum))
        widget.lytCharts.setCurrentIndex(pageNum - 1)

        if pageNum == int(widget.lblPages.text()) - 1:
            widget.btnRight.setEnabled(True)
        if pageNum == 1:
            widget.btnLeft.setDisabled(True)

    def evt_moveForward(self, widget):
        pageNum = int(widget.lblCounter.text()) + 1
        widget.lblCounter.setText(str(pageNum))
        widget.lytCharts.setCurrentIndex(pageNum - 1)

        if widget.lblCounter.text() == "2":
            widget.btnLeft.setEnabled(True)
        if widget.lblCounter.text() == widget.lblPages.text():
            widget.btnRight.setDisabled(True)


class Widget(QWidget):    # special Widget for multiPage chart
    def __init__(self, parent):
        super().__init__(parent)

        self.lytHistory = QHBoxLayout()
        self.btnBackPage = QPushButton("")
        self.btnBackPage.setStyleSheet("QPushButton{color: blue;}")
        self.btnBackPage.setFlat(True)
        self.btnBackPage.adjustSize()
        self.lblPointer = QLabel("/")
        self.lblCurrentPage = QLabel("")
        self.lytHistory.addWidget(self.btnBackPage)
        self.lytHistory.addWidget(self.lblPointer)
        self.lytHistory.addWidget(self.lblCurrentPage)
        self.lytHistory.addStretch()

        self.lytLeft = QVBoxLayout()
        self.btnLeft = QPushButton('<<')
        self.btnLeft.setDisabled(True)
        self.lytLeft.addStretch()
        self.lytLeft.addWidget(self.btnLeft)
        self.lytLeft.addStretch()

        self.lytCharts = QStackedLayout()

        self.lytRight = QVBoxLayout()
        self.btnRight = QPushButton('>>')
        self.lytRight.addStretch()
        self.lytRight.addWidget(self.btnRight)
        self.lytRight.addStretch()

        self.lytUpper = QHBoxLayout()
        self.lytUpper.addLayout(self.lytLeft)
        self.lytUpper.addLayout(self.lytCharts)
        self.lytUpper.addLayout(self.lytRight)

        self.lytLower = QHBoxLayout()
        self.lblCounter = QLabel()
        self.lblSlash = QLabel('/')
        self.lblPages = QLabel()
        self.lytLower.addStretch()
        self.lytLower.addWidget(self.lblCounter)
        self.lytLower.addWidget(self.lblSlash)
        self.lytLower.addWidget(self.lblPages)
        self.lytLower.addStretch()

        self.lytMain = QVBoxLayout()
        self.lytMain.addLayout(self.lytUpper)
        self.lytMain.addLayout(self.lytLower)

        self.setLayout(self.lytMain)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # DrillDown, Stacked
    # wdg = wdgPieChart('DrillDown','Major OP', 'Rig', pd.read_csv('activity_table.csv'))
    wdg = wdgPieChart('DrillDown','Rig', 'Major OP', pd.read_csv('../activity_table.csv'))

    dlg = QMainWindow()
    dlg.setCentralWidget(wdg)
    dlg.resize(1500, 900)
    dlg.show()
    sys.exit(app.exec_())
