import os
import numpy as np
import pandas as pd

class Data_access:
    """Класс доступа к данным, при инициализации считывается сводная таблица винтов"""
    def __init__(self):
        work_dir = os.getcwd()                 # Текущая рабочая директория для взаимодействия с файлами
                                               #  Директории с данными датасета
        self.path_to_prop_spec   = os.path.join(work_dir, 'data', 'prop_spec.csv')
        self.path_to_Thrust_data = os.path.join(work_dir, 'data', 'Thrust_data')
        self.path_to_custom_prop = os.path.join(self.path_to_Thrust_data, 'custom.txt')
        self.path_to_plots       = os.path.join(work_dir, 'data')
        self.path_to_pics        = os.path.join(work_dir, 'data', 'Prop_pics')

        self.check_path = lambda x: os.path.exists(x)       # Функция для удобства проверки существования файлов

        self.data = Data_access.summary_table(self)         # Считывание сводной таблицы
        
    def summary_table(self) -> pd.DataFrame:
        data = pd.read_csv(self.path_to_prop_spec, delimiter='\t', index_col=[4])
        return data

    def exp_data(self, work_name):
        '''Получить данные с подробной статистикой конкретного винта - коээфиценты тяги и мощности'''
        path = os.path.join(self.path_to_Thrust_data, work_name)
        if self.check_path(path):
            with open(path, 'r') as inf:
                txt = inf.readlines()
            table = [i.split() for i in txt]
            return pd.DataFrame(table[1:], columns=table[0], dtype='float')
        else:
            return pd.read_csv(self.path_to_custom_prop, delimiter='\t')   # Если винта нет в датасете, используется 
                                                                           # сгенерированный файл по средним знчениям всех файлов

class Prop(Data_access):
    '''Создаёт объект винта, хранит в себе параметры винта
    Содержит функции сортировки и подбора винтов'''
    def __init__(self, d: float, p: float, rpm=5000, tk=0.16, pk=0.1):
        '''Параметры:
        '''
        super().__init__()
        self.d = float(d)
        self.p = float(p)
        self.rpm = int(rpm)
        self.tk = float(tk)
        self.pk = float(pk)

        self.selection = [[d, p, 'custom', 'custom.txt']]
        self.name = 'custom'
        self.file_name = 'custom.txt'

    def current_params(self):
        """Кортеж текущих параметров винта"""
        return (self.d, self.p, self.name, self.file_name)

    def elect_this(self, data):
        """Устанавливает переданный список\кортеж парметров винта в объект
        Принимает в формате [диаметр, шаг, название для пользователя, имя файла со статистикой]"""
        self.d = data[0]
        self.p = data[1]
        self.name = data[2]
        self.file_name = data[3]
        self.tk = Prop.get_k(self, self.file_name, self.rpm, 'CT')
        self.pk = Prop.get_k(self, self.file_name, self.rpm, 'CP')

    def elect_by_name(self, name):
        """Устанавливает параметры винта найдённые в датасете по его названию
        Если не находит возвращает None"""
        if self.data[self.data.index.isin([name])].shape[0]:
            prp = self.data.loc[name]
            self.elect_this([prp.diam, prp.pitch, name, prp.stats_detail_file])

    def get_k(self, name, rpm, coef):
        """Получает и интерполирует коэффициент винта из датасета. 
        CT - Коэффициент тяги
        CP - Коэффициент мощности"""
        data = self.exp_data(name)
        x = data.RPM
        y = data[coef]
        k = np.interp(rpm, x, y)
        return k

    def one_val_sort(self, val, param, limit=20) -> list:
        '''Сортирует по одному указанному параметру
        'diam' - сортировка по диаметру
        'pitch' - сортировка по шагу
        Возвращает список сортированных пропов'''
        selection = self.data.sort_values(by=[param], key=lambda x: abs(val - x))
        return selection.index[:limit].to_list()

    def two_val_sort(self, d, p, limit=20) -> list:
        """Сортирует по дельте обоих переданных параметров
        Возвращает список сортированных пропов"""
        def delta_sort(x):
            return abs((d if x.name == 'diam' else p) - x)

        selection = self.data.sort_values(by=['diam', 'pitch'], key=delta_sort)
        return selection.index[:limit].to_list()

class Prop_stats(Prop):
    '''Считает статисику находящегося в объекте винта'''
    def __init__(self, d: float, p: float, rpm=5000, tk=0.16, pk=0.1):
        super().__init__(d, p)
        self.d_m = self.d / 39.37    # Перевод дюймов в единицы СИ
        self.air_density = 1.2754
        
    def inf(self) -> str:
        """Информация о текщем винте"""
        return f'Диаметр {self.d}, шаг, {self.p} имя {self.file_name}'

    def calc_thrust(self, rpm, air=1.2754):
        """Расчёт тяги винта"""
        rpm = int(rpm)
        self.d_m = self.d / 39.37
        tk = self.get_k(self.file_name, rpm, 'CT')
        tk *= 10
        thrust = tk * air * (rpm / 60) ** 2 * self.d_m ** 4
        return thrust
    
    def calc_power(self, rpm, air=1.2754):
        """Расчёт мощности винта"""
        rpm = int(rpm)
        self.d_m = self.d / 39.37
        pk = self.get_k(self.file_name, rpm, 'CP')
        pk *= 10
        return pk * air * (rpm / 60) ** 3 * self.d_m ** 5