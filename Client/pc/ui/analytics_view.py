from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import numpy as np


from local_db.data_manager import select_priority_counts, select_all_tasks, select_tasks_by_type, select_completed_by_types, \
    select_daily_tasks_underday


class AnslitycWindow(QWidget):
    def __init__(self, option):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.option = option
        self.initializeUI()

    def initializeUI(self):
        self.setGeometry(300,200,800,600)
        self.setWindowTitle("Self Productivity System")
        self.setUpMainWindow()
        self.show()

    def setUpMainWindow(self):
        self.priority_map = {
            "Casual": "Обычный",
            "Low": "Низкий",
            "Mid": "Средний",
            "High": "Высокий",
            "Extreme": "Критичный"
        }

        self.status_map = {
            "underway": "В работе",
            "completed": "Выполнено",
            "overdue":"Просрочено"
        }

        self.task_type_map = {
            "Other": "Другое",
            "Dust Cleaning": "Уборка",
            "Meeting": "Встреча",
            "Documentation": "Документация",
            "Customer Support": "Поддержка клиентов",
            "Code Bug Fix": "Исправление ошибок",
            "Research": "Исследование",
            "Feature Development": "Разработка функционала",
            "Optimization": "Оптимизация",
            "Deployment": "Развертывание",
            "Project Management": "Управление проектом"
        }

        option = self.option
        main_layout = QtWidgets.QVBoxLayout()
        match(option):
            case 1:
                category, tasks_count = select_priority_counts()
                russian_category = [self.priority_map.get(cat, cat) for cat in category]
                x = np.arange(len(russian_category))
                height = np.array(tasks_count)

                taked_tasks_praph = pg.PlotWidget(title="Количество задач по приоритету")
                taked_tasks_praph.setBackground('w')

                bg = pg.BarGraphItem(x=x, height=height, width=0.6, brush='skyblue')
                taked_tasks_praph.addItem(bg)

                ticks = [(i, cat) for i, cat in enumerate(russian_category)]
                taked_tasks_praph.getAxis('bottom').setTicks([ticks])
                graph = taked_tasks_praph
            case 2:
                status, tasks_count = select_all_tasks()
                russian_status = [self.status_map.get(stat, stat) for stat in status]
                x = np.arange(len(russian_status))
                height = np.array(tasks_count)
                coef_tasks_praph = pg.PlotWidget(title="Количество задач по статусу")
                coef_tasks_praph.setBackground('w')

                bg = pg.BarGraphItem(x=x, height=height, width=0.6, brush='skyblue')
                coef_tasks_praph.addItem(bg)

                ticks = [(i, cat) for i, cat in enumerate(russian_status)]
                coef_tasks_praph.getAxis('bottom').setTicks([ticks])
                graph = coef_tasks_praph
            case 3:
                types, tasks_count = select_tasks_by_type()
                russian_types = [self.task_type_map.get(t, t) for t in types]
                x = np.arange(len(russian_types))
                height = np.array(tasks_count)
                types_tasks_graph = pg.PlotWidget(title="Количество задач по типу")
                types_tasks_graph.setBackground('w')

                bg = pg.BarGraphItem(x=x, height=height, width=0.6, brush='skyblue')
                types_tasks_graph.addItem(bg)

                ticks = [(i, cat) for i, cat in enumerate(russian_types)]
                types_tasks_graph.getAxis('bottom').setTicks([ticks])
                graph = types_tasks_graph
            case 4:
                types, tasks_count = select_completed_by_types()
                russian_types = [self.task_type_map.get(t, t) for t in types]
                x = np.arange(len(russian_types))
                height = np.array(tasks_count)
                types_tasks_graph = pg.PlotWidget(title="Количество выполненных задач по типу")
                types_tasks_graph.setBackground('w')

                bg = pg.BarGraphItem(x=x, height=height, width=0.6, brush='skyblue')
                types_tasks_graph.addItem(bg)

                ticks = [(i, cat) for i, cat in enumerate(russian_types)]
                types_tasks_graph.getAxis('bottom').setTicks([ticks])
                graph = types_tasks_graph
            case 5:
                data = select_daily_tasks_underday()
                dates = [d.strftime("%m-%d") for d, _ in data]
                num_of_complete_tasks = [n for _, n in data]

                daily_underway = pg.PlotWidget(title="Количество задач в работе по дням")
                daily_underway.showGrid(x=True, y=True)

                x = list(range(len(dates)))
                daily_underway.plot(x, num_of_complete_tasks, pen=pg.mkPen(color='b', width=2), symbol='o', symbolSize=8,
                                 symbolBrush='b')

                daily_underway.getAxis('bottom').setTicks([list(zip(x, dates))])
                daily_underway.setLabel('left', 'Количество')
                daily_underway.setLabel('bottom', 'Дата')
                daily_underway.setBackground('w')

                graph = daily_underway

        main_layout.addWidget(graph)
        self.setLayout(main_layout)

