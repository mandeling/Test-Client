# -*- coding: utf-8 -*-
import sys
from UI import *


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QWidget()
    ui = MyClientWindow(win)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
