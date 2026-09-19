# ==============================================================================
# 文件名: main.py
# 职责: 程序唯一入口，只负责 QApplication 启动与主窗口创建
# ==============================================================================
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from ui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()