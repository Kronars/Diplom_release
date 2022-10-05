import sys
from PyQt5 import QtWidgets
from modules.ui_interaction import Ui_backend

# pyuic5 C:\Users\Senya\Prog_2\Diplom\main_win.ui -o C:\Users\Senya\Prog_2\Diplom\modules\main_window.py

if __name__ == '__main__':                    # Управляющая конструкция
    app = QtWidgets.QApplication(sys.argv)    # Создание объектов приложения
    mainWin = QtWidgets.QMainWindow()
    ui = Ui_backend()
    ui.setupUi(mainWin)                       # Инициализация интерфейса
    mainWin.show()                            # Отображение интерфейса
    sys.exit(app.exec_())                     # Вход в цикл выполнения приложения