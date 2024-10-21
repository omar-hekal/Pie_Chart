from PyQt5.QtWidgets import *
from PieChartTab import *
import sys
import pandas as pd

def main():
    app = QApplication(sys.argv)
    dlg = QMainWindow()
    data = pd.read_csv('pokemon.csv', index_col=0)

    wdg = wdgPieChartTab(data)
    tabs = QTabWidget()
    tabs.setMovable(True)
    tabs.addTab(wdg, "Pie Chart")

    dlg.setCentralWidget(tabs)
    dlg.resize(1900, 800)
    dlg.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
