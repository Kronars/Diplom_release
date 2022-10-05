import os
import sys

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

if __name__ == '__main__':
    """Конструкция для отладки кода"""
    from classes import Prop_stats
    from main_window import Ui_MainWindow
else:
    from modules.classes import Prop_stats
    from modules.main_window import Ui_MainWindow

class Ui_backend(Ui_MainWindow):
    """Обработка событий интерфейса"""
    def __init__(self) -> None:
        super().__init__()
        self.D_MAX = 20         # Диапазон значений слайдеров
        self.P_MAX = 14
        self.D_MIN = 2
        self.P_MIN = 0.7

        self.stats = Prop_stats(5, 5)              # Инициализация объекта винта

    def setupUi(self, MainWindow):
        """Инициализация обработки событий"""
        super().setupUi(MainWindow)

        self.mw = MainWindow                       # Оъект окна приложения

        self.graphWidget.setBackground('w')        # Белый фон для графиков
                                                   # Инициализация графиков
        self.plt1 = self.graphWidget.addPlot(row=0, col=0, 
                                x=np.arange(100), y=np.linspace(20, 120, 100))
        self.plt2 = self.graphWidget.addPlot(row=0, col=1, 
                                x=np.arange(20), y=np.linspace(20, 120, 20))
        self.thrust, self.power = 1, 1

        self.plt1.setTitle('Тяга винта', color='k')
        self.plt2.setTitle('Мощность для вращения', color='k')
        self.plt1.setLabels(left='Грамм силы', bottom='Оборотов в минуту')
        self.plt2.setLabels(left='Ватт', bottom='Оборотов в минуту')
        self.plt1.showGrid(True, True), self.plt2.showGrid(True, True)
                                                   # Установка значений слайдеров
        self.slider_d_vals = np.linspace(self.D_MIN, self.D_MAX, self.d_slider.maximum() + 1)
        self.slider_p_vals = np.linspace(self.P_MIN, self.P_MAX, self.p_slider.maximum() + 1)
                                                   # Подключение функций обработчиков событий к элементам интерфейса
        self.d_slider.sliderMoved.connect(self.sliders_control)
        self.p_slider.sliderMoved.connect(self.sliders_control)
        self.rpm_slider.sliderMoved.connect(self.calc_stats)

        self.d_num.editingFinished.connect(self.sliders_control)
        self.p_num.editingFinished.connect(self.sliders_control)
        self.rpm_num.editingFinished.connect(self.sliders_control)

        self.air_box.editingFinished.connect(self.calc_stats)

        self.pk_input.editingFinished.connect(self.coef_editing)
        self.tk_input.editingFinished.connect(self.coef_editing)

        self.d_assort_box.clicked.connect(self.combo_box_fill_control)
        self.p_assort_box.clicked.connect(self.combo_box_fill_control)
        self.dp_assort_box.clicked.connect(self.combo_box_fill_control)
        self.all_sort_box_fill()                   # Заполнение списка всех винтов

        self.selected_d_props.textActivated.connect(self.combo_box_clicked_control)
        self.selected_p_props.textActivated.connect(self.combo_box_clicked_control)
        self.selected_dp_props.textActivated.connect(self.combo_box_clicked_control)

        self.all_sort_box.textActivated.connect(self.combo_box_clicked_control)

        self.mass_spin_box.valueChanged.connect(self.calc_accel)
        self.amount_spin_box.valueChanged.connect(self.calc_accel)

    def ui_params(self):
        '''Параметры винта установленные в интерфейсе'''
        name = self.curr_prop_name.text()
        work_name = self.stats.file_name
        return (self.d_num.value(), self.p_num.value(), name, work_name)

    def update_ui_params(self):
        '''Устанавливает на слайдеры параметры из объекта пропа'''
        d, p = self.stats.d, self.stats.p
        d_val = int((d - self.D_MIN) * 10)
        p_val = int((p - self.P_MIN) * 100)

        self.d_num.setValue(d)
        self.p_num.setValue(p)

        self.d_slider.setValue(d_val)
        self.p_slider.setValue(p_val)

        self.curr_prop_name.setText(self.stats.name)

    def update_obj_by_name(self, name):
        '''Устанавливает в объект винта параметры из датасета'''
        self.stats.elect_by_name(name)

    def update_obj_params(self, params):
        '''Устанавливает в объект винта переданные параметры'''
        self.stats.elect_this(params)

    def coef_editing(self):
        """Обработчик событий от полей ввода коэффициентов"""
        params = (self.d_num.value(), self.p_num.value(), 'custom.txt', 'custom.txt')
        self.update_obj_params(params)
        self.curr_prop_name.setText(self.stats.name)
        self.calc_stats(custom_coef=True)

    def combo_box_clicked_control(self):
        """Обработчик событий от активации текста комбо боксов сортировки"""
        send_from = self.mw.sender().objectName()
        obj = getattr(self, send_from)
        selected = obj.currentText()
        self.update_obj_by_name(selected)
        self.update_ui_params()
        self.calc_stats()
        
    def combo_box_fill_control(self):
        """Заполнение комбо боксов названиями винтов"""
        d, p = self.ui_params()[:2]
        if self.dp_assort_box.isChecked():
            sorted_props = self.stats.two_val_sort(d, p)
            box = self.selected_dp_props
        elif self.d_assort_box.isChecked():
            sorted_props = self.stats.one_val_sort(d, 'diam')
            box = self.selected_d_props
        elif self.p_assort_box.isChecked():
            sorted_props = self.stats.one_val_sort(p, 'pitch')
            box = self.selected_p_props

        box.clear()
        box.addItems(sorted_props)
        
        self.update_obj_by_name(sorted_props[0]) #
        self.update_ui_params()
        self.calc_stats()
            
    def all_sort_box_fill(self):
        """Заполнение комбо бокса всех винтов названиями винтов"""
        self.all_sort_box.addItems(self.stats.data.index.to_list())

    def sliders_control(self):
        '''Устанавливает в объект винта параметры со слайдеров
        Управляет слайдерами диаметра и шага, устанавливает соответсвующие спин боксы
        Точность спин бокса диаметра до десятых, спин бокса шага - до сотых'''
        def set_spin_box_val(self):
            d_val = round(self.slider_d_vals[self.d_slider.sliderPosition()], 2)
            p_val = round(self.slider_p_vals[self.p_slider.sliderPosition()], 2)

            self.d_num.setValue(d_val)
            self.p_num.setValue(p_val)

        def set_sliders_val(self):
            d_val = int((self.d_num.value() - self.D_MIN) * 10)
            p_val = int((self.p_num.value() - self.P_MIN) * 100)

            self.d_slider.setValue(d_val)
            self.p_slider.setValue(p_val)

        send_from = self.mw.sender().objectName()
        sliders = ['d_slider', 'p_slider', 'rpm_slider']
        spinBox = ['d_num', 'p_num', 'rpm_num']
        if send_from in sliders:
            set_spin_box_val(self)
        elif send_from in spinBox:
            set_sliders_val(self)
        else:
            return None

        if send_from == 'rpm_slider':
            params = (self.d_num.value(), self.p_num.value(), self.stats.name, self.stats.file_name)
        else:
            params = (self.d_num.value(), self.p_num.value(), 'custom.txt', 'custom.txt')

        self.update_obj_params(params)
        self.curr_prop_name.setText(self.stats.name)
        self.calc_stats()

    def calc_accel(self):
        mass = self.mass_spin_box.value()
        prop_amount = self.amount_spin_box.value()
        thrust = float(self.thr_vals.text()[:-2])
        if thrust == 0:
            self.speed_label.setText(f'{thrust:.3f} / {mass:.3f} * 3.6 * {prop_amount} = 0 км/ч')
            return None
        speed = (self.thrust / mass) * 3.6 * prop_amount
        self.speed_label.setText(f'{thrust:.3f} / {mass:.2f} * 3.6 * {prop_amount} = {speed:.3f} км/ч')

    def calc_stats(self, custom_coef=False):
        """Рассчитывает на основе установленных в объект параметров силу тяги, 
        мощность и вызывает отображение графика и изображений"""
        curr_rpm = self.rpm_num.value()
        air = self.air_box.value()

        if custom_coef:
            tk = self.stats.get_k('custom.txt', curr_rpm, 'CT')
            pk = self.stats.get_k('custom.txt', curr_rpm, 'CP')
        else:
            tk = self.stats.get_k(self.stats.file_name, curr_rpm, 'CT')
            pk = self.stats.get_k(self.stats.file_name, curr_rpm, 'CP')

        tk, pk = tk * 10, pk * 10

        self.tk_input.setValue(tk)
        self.pk_input.setValue(pk)

        thrust = float(self.stats.calc_thrust(curr_rpm, air))
        power = float(self.stats.calc_power(curr_rpm, air))
        self.thrust, self.power = thrust, power
        self.thr_vals.setText(f'{thrust:.5f} Н')
        self.pwr_vals.setText(f'{power:.5f} Ватт')

        self.full_calc.setText(
f'''Расчёт тяги: {tk:.4f} * {air} * ({curr_rpm} / 60) ^ 2 * ({self.stats.d} / 39.37) ^ 4 = {thrust:.4f} Н
Расчёт мощности: {pk:.4f} * {air} * ({curr_rpm} / 60) ^ 3 * ({self.stats.d} / 39.37) ^ 5 = {power:.4f} Ватт''')

        self.display_plot(curr_rpm, thrust, power)
        if self.mw.sender().objectName() != 'rpm_slider':
            self.display_pics()
        self.calc_accel()

    def display_plot(self, rpm, thrust, power):
        """Отображает график изменения параметров винтов"""
        self.plt1.clear()
        self.plt2.clear()
        data = self.stats.exp_data(self.stats.file_name)
        exact_range = data.RPM.min() - 400, data.RPM.max() + 700

        thr_rpm_x = pg.TargetItem(
                pos=(rpm, thrust),
                size=12,
                movable=False,
                symbol='x',
                pen=pg.mkPen((255, 50, 50))
                )
        thr_rpm_x.setLabel(
            f'{thrust:.3f} Ньютонов\nпри {rpm} RPM',
            {"color": "#000000"})

        pow_prm_x = pg.TargetItem(
                pos=(rpm, power),
                size=12,
                movable=False,
                symbol='x',
                pen=pg.mkPen((255, 50, 50))
        )
        pow_prm_x.setLabel(
            f'{power:.4f} Ватт\nпри {rpm} RPM',
            {"color": "#000000"})

        self.plt1.addItem(thr_rpm_x)
        self.plt2.addItem(pow_prm_x)

        thr_x = np.arange(exact_range[0], exact_range[1], 50)
        
        thr_y = [self.stats.calc_thrust(rpm) for rpm in thr_x]
        pow_y = [self.stats.calc_power(rpm)  for rpm in thr_x]

        p1_pen = pg.mkPen((255, 183, 0), width=3)
        p2_pen = pg.mkPen((94, 255, 252), width=3)

        self.plt1.plot(thr_x, thr_y, pen=p1_pen)
        self.plt2.plot(thr_x, pow_y, pen=p2_pen)

    def display_pics(self):
        """Отображает изображения винтов, если они есть в датасете"""
        data = self.stats.data
        name = self.stats.name
        to_pics = self.stats.path_to_pics
        
        if name in ('custom.txt', 'custom'):
            self.side_prop.clear()
            self.front_prop.clear()
            return None

        res = data.loc[name]
        if isinstance(res.side_pic, float):
            self.side_prop.clear()
            self.front_prop.clear()
            return None

        side_pic  = os.path.join(to_pics, res.side_pic)
        front_pic = os.path.join(to_pics, res.front_pic)

        size = self.side_prop.size()

        side  = QtGui.QPixmap(side_pic).scaled(size, aspectRatioMode=QtCore.Qt.KeepAspectRatio)
        front = QtGui.QPixmap(front_pic).scaled(size, aspectRatioMode=QtCore.Qt.KeepAspectRatio)

        self.side_prop.setPixmap(side)
        self.front_prop.setPixmap(front)


if __name__ == '__main__':
    """Конструкция для отладки кода"""
    os.chdir(r'C:\Users\Senya\Prog_2\Diplom')
    app = QtWidgets.QApplication(sys.argv)
    mainWin = QtWidgets.QMainWindow()
    ui = Ui_backend()
    ui.setupUi(mainWin)
    mainWin.show()
    sys.exit(app.exec_())