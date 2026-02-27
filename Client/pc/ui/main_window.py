import os
import subprocess
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout,
                             QStackedLayout, QCalendarWidget, QListWidget,
                             QScrollArea, QGridLayout, QMessageBox, QCheckBox)
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings
import pyqtgraph as pg
import numpy as np
import sys

from api.auth_manager import AuthManager
from api.sync_service import SyncService
from local_db.data_manager import (select_daily_tasks, select_task_property_for_edit, select_underway_tasks,
                                   select_daily_task_complete, select_closest_tasks, select_capacity_parametrs,
                                   select_completed_tasks)
from ml.load import predict_capacity
from ui.task_create_view import TaskWindow
from ui.task_edit_view import EditWindow
from ui.analytics_view import  AnslitycWindow

def draw_circular_progress(ax, percentage, color="dodgerblue"):
    ax.clear()
    ax.pie([100], radius=1, colors=["lightgray"], startangle=90, counterclock=False)
    ax.pie([percentage, 100 - percentage],
           radius=1, colors=[color, "none"],
           startangle=90, counterclock=False,
           wedgeprops={'width': 0.15, 'edgecolor': 'none'})
    ax.text(0, 0, f"{percentage}%", ha="center", va="center",
            fontsize=16, color=color)
    ax.set(aspect="equal")

def make_round_pixmap(pixmap: QPixmap, size: int) -> QPixmap:
    scaled = pixmap.scaled(size, size)
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)

    painter.drawPixmap(0, 0, scaled)
    painter.end()

    return result

class MainWindow(QWidget):
    deadline_str = pyqtSignal(str)
    def __init__(self, token):
        super().__init__()
        self.mainScreen = QWidget()
        self.calendarScreen = QWidget()
        self.taskListScreen = QWidget()
        self.statisticScreen = QWidget()
        self.initializeUI()
        self.token = token
        self.sync_service = SyncService(token=self.token)
        QTimer.singleShot(1000, self.run_auto_sync)

        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(15 * 60 * 1000)
        self.sync_timer.timeout.connect(self.run_auto_sync)
        self.sync_timer.start()

    def initializeUI(self):
        self.setMinimumSize(800,600)
        self.setWindowTitle("Self Productivity System")
        self.setUpMainWindow()
        self.setUpCalendarScreen()
        self.setUpTaskListScreen()
        self.setUpStatisticScreen()
        self.setUpStackedLayout()
        self.show()

    def setUpMainWindow(self):
        main_layout = QVBoxLayout(self.mainScreen)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        upper_layout = QHBoxLayout()
        upper_layout.setSpacing(20)

        ava_calendar_layout = QVBoxLayout()
        pic_source = "ui/pic.png"
        try:
            pic_label = QLabel()
            pic_pixmap = QPixmap(pic_source)
            if not pic_pixmap.isNull():
                round_pix = make_round_pixmap(pic_pixmap, 240)
                pic_label.setPixmap(round_pix)
                pic_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ava_calendar_layout.addWidget(pic_label)
        except Exception as e:
            print(f"Ошибка загрузки фото: {e}")

        self.Sync = QPushButton("Синхронизировать данные")
        self.Sync.clicked.connect(self.syncro)

        Lout = QPushButton("Выйти из аккаунта")
        Lout.clicked.connect(self.handle_logout)

        ava_calendar_layout.addWidget(self.Sync)
        ava_calendar_layout.addWidget(Lout)
        ava_calendar_layout.addStretch()

        three_buttons_layout = QVBoxLayout()
        calendar = QPushButton("Запланировать задачу")
        calendar.clicked.connect(self.goToCalendarScreen)
        task_list = QPushButton("Список задач")
        task_list.clicked.connect(self.goToTaskListScreen)
        stats = QPushButton("Статистика")
        stats.clicked.connect(self.goToStatisticScreen)

        three_buttons_layout.addWidget(calendar)
        three_buttons_layout.addWidget(task_list)
        three_buttons_layout.addWidget(stats)
        three_buttons_layout.addStretch()

        self.closest_tasks_widget = QWidget()
        self.cls_tsk_layout = QVBoxLayout(self.closest_tasks_widget)
        self.cls_tsk_layout.setContentsMargins(0, 0, 0, 0)
        self.cls_tsk_layout.setSpacing(8)
        self.cls_tsk_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        upper_layout.addLayout(ava_calendar_layout, 1)
        upper_layout.addLayout(three_buttons_layout, 1)
        upper_layout.addWidget(self.closest_tasks_widget, 2)

        self.refresh_closest_tasks()

        self.cap = build_capacity_graph()
        self.compl_tasks = build_complete_task_graph()

        self.cap_stat_layout = QHBoxLayout()
        self.cap_stat_layout.addWidget(self.compl_tasks)
        self.cap_stat_layout.addWidget(self.cap)


        main_layout.addLayout(upper_layout)
        main_layout.addLayout(self.cap_stat_layout)

        self.mainScreen.setLayout(main_layout)
    def setUpCalendarScreen(self):
        calendar_layout = QVBoxLayout(self.calendarScreen)
        description_label = QLabel("Для добавления задачи нажмите на желаемую дату и на кнопку 'Добавить задачу'",self)
        description_label.setStyleSheet("""QLabel {
            border: 2px solid #4a90e2;   /* рамка */
            border-radius: 6px;           /* скруглённые углы */
            padding: 6px;                 /* отступы от текста */
            color: #2e3440;               /* цвет текста */
            font-weight: bold;            /* жирный текст */
            font-size: 14px;              /* размер шрифта */
            qproperty-alignment: 'AlignCenter';  /* выравнивание по центру */
            background-color: #f8fafc; 
            }""")
        back_button = QPushButton("Вернуться", self)
        back_button.clicked.connect(self.goToMainScreen)

        upper_layout = QHBoxLayout()
        upper_layout.addWidget(description_label)
        upper_layout.addWidget(back_button)


        bottom_layout = QHBoxLayout()
        self.calend = QCalendarWidget(self)
        self.calend.selectionChanged.connect(self.dateSelect)

        date_info_layout = QVBoxLayout()
        add_tasks_button = QPushButton("Добавить задачу", self)
        add_tasks_button.clicked.connect(self.openTaskCreator)
        self.date_info_list = QListWidget(self)
        date_info_layout.addWidget(add_tasks_button)
        date_info_layout.addWidget(self.date_info_list)



        bottom_layout.addWidget(self.calend)
        bottom_layout.addLayout(date_info_layout)
        calendar_layout.addLayout(upper_layout)
        calendar_layout.addLayout(bottom_layout)


        self.calendarScreen.setLayout(calendar_layout)
    def setUpTaskListScreen(self):


        tasklist_layout = QVBoxLayout(self.taskListScreen)

        description_label = QLabel("Выберите задачу информацию о которой хотите уточнить", self)
        description_label.setStyleSheet("""QLabel {
            border: 2px solid #4a90e2;   /* рамка */
            border-radius: 6px;           /* скруглённые углы */
            padding: 6px;                 /* отступы от текста */
            color: #2e3440;               /* цвет текста */
            font-weight: bold;            /* жирный текст */
            font-size: 14px;              /* размер шрифта */
            qproperty-alignment: 'AlignCenter';  /* выравнивание по центру */
            background-color: #f8fafc; 
            }""")
        back_button = QPushButton("Вернуться", self)
        back_button.clicked.connect(self.goToMainScreen)

        self.show_completed_cb = QCheckBox("Показать выполненные", self)
        self.show_completed_cb.setStyleSheet("""QCheckBox::indicator:checked {
                                                                background-color: #2e7d32; 
                                                                border: 2px solid #2e7d32;
                                                            }""")
        self.show_completed_cb.stateChanged.connect(self.refreshTaskList)

        upper_layout = QHBoxLayout()
        upper_layout.addWidget(description_label)
        upper_layout.addWidget(self.show_completed_cb)
        upper_layout.addWidget(back_button)

        bottom_layout = QHBoxLayout()

        self.task_scroll = QScrollArea()
        self.task_scroll.setWidgetResizable(True)

        self.task_container = QWidget()
        self.scroll_layout = QGridLayout(self.task_container)
        self.task_scroll.setWidget(self.task_container)

        bottom_layout.addWidget(self.task_scroll)

        tasklist_layout.addLayout(upper_layout)
        tasklist_layout.addLayout(bottom_layout)

        self.refreshTaskList()
    def setUpStatisticScreen(self):
        statistic_layout = QVBoxLayout(self.statisticScreen)

        description_label = QLabel("Выберите статистику которую хотите увидеть", self)
        description_label.setStyleSheet("""QLabel {
            border: 2px solid #4a90e2;   /* рамка */
            border-radius: 6px;           /* скруглённые углы */
            padding: 6px;                 /* отступы от текста */
            color: #2e3440;               /* цвет текста */
            font-weight: bold;            /* жирный текст */
            font-size: 14px;              /* размер шрифта */
            qproperty-alignment: 'AlignCenter';  /* выравнивание по центру */
            background-color: #f8fafc; 
            }""")
        back_button = QPushButton("Вернуться", self)
        back_button.clicked.connect(self.goToMainScreen)

        upper_layout = QHBoxLayout()
        upper_layout.addWidget(description_label)
        upper_layout.addWidget(back_button)

        bottom_layout = QHBoxLayout()

        task_category_button = QPushButton("Категории задач по приоритету", self)
        task_category_button.clicked.connect(lambda: self.openStatistic(1))
        over_under_compl_button = QPushButton("Просрочено|Выполнено|В работе", self)
        over_under_compl_button.clicked.connect(lambda: self.openStatistic(2))
        task_types_button = QPushButton("Все задачи по типу", self)
        task_types_button.clicked.connect(lambda: self.openStatistic(3))
        compl_by_types_button = QPushButton("Выполненые задачи по типу", self)
        compl_by_types_button.clicked.connect(lambda: self.openStatistic(4))
        over_by_types_button = QPushButton("Тренд работы", self)
        over_by_types_button.clicked.connect(lambda: self.openStatistic(5))


        statistic_layout.addLayout(upper_layout)
        statistic_layout.addWidget(task_category_button)
        statistic_layout.addWidget(over_under_compl_button)
        statistic_layout.addWidget(over_under_compl_button)
        statistic_layout.addWidget(task_types_button)
        statistic_layout.addWidget(compl_by_types_button)
        statistic_layout.addWidget(over_by_types_button)
        statistic_layout.addLayout(bottom_layout)

        self.statisticScreen.setLayout(statistic_layout)
    def setUpStackedLayout(self):
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.addWidget(self.mainScreen)
        self.stacked_layout.addWidget(self.calendarScreen)
        self.stacked_layout.addWidget(self.taskListScreen)
        self.stacked_layout.addWidget(self.statisticScreen)
        self.setLayout(self.stacked_layout)

    def goToCalendarScreen(self):
        self.stacked_layout.setCurrentWidget(self.calendarScreen)
    def goToTaskListScreen(self):
        self.refreshTaskList()
        self.stacked_layout.setCurrentWidget(self.taskListScreen)
    def goToStatisticScreen(self):
        self.stacked_layout.setCurrentWidget(self.statisticScreen)
    def goToMainScreen(self):
        new_close_task = select_closest_tasks()
        while self.cls_tsk_layout.count():
            item = self.cls_tsk_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        cls_task_label = QLabel("Задачи дедлайн которых наступит скоро", self)
        cls_task_label.setStyleSheet("""QLabel {
                    border: 2px solid #4a90e2;   /* рамка */
                    border-radius: 6px;           /* скруглённые углы */
                    padding: 6px;                 /* отступы от текста */
                    color: #2e3440;               /* цвет текста */
                    font-weight: bold;            /* жирный текст */
                    font-size: 14px;              /* размер шрифта */
                    qproperty-alignment: 'AlignCenter';  /* выравнивание по центру */
                    background-color: #f8fafc; 
                    }""")
        self.cls_tsk_layout.addWidget(cls_task_label)
        for title, description in new_close_task:
            lbl = QLabel(f"{title}\n{description}", self)
            lbl.setStyleSheet("""QLabel {
            border: 2px solid #4a90e2;   /* рамка */
            border-radius: 6px;           /* скруглённые углы */
            padding: 6px;                 /* отступы от текста */
            color: #2e3440;               /* цвет текста */
            font-weight: bold;            /* жирный текст */
            font-size: 14px;              /* размер шрифта */
            qproperty-alignment: 'AlignCenter';  /* выравнивание по центру */
            background-color: #f8fafc; 
            }""")
            self.cls_tsk_layout.addWidget(lbl)

        new_fig = build_complete_task_graph()
        self.cap_stat_layout.replaceWidget(self.compl_tasks, new_fig)
        self.compl_tasks.deleteLater()
        self.compl_tasks = new_fig

        new_cap = build_capacity_graph()
        self.cap_stat_layout.replaceWidget(self.cap, new_cap)
        self.cap.deleteLater()
        self.cap = new_cap

        self.stacked_layout.setCurrentWidget(self.mainScreen)

    def openTaskCreator(self):
        selected_date = self.calend.selectedDate().toPyDate()
        selected_date = str(selected_date)
        self.task_creator = TaskWindow(deadline_str= selected_date)
        self.task_creator.task_saved.connect(self.addTaskToList)
        self.task_creator.show()
    def dateSelect(self):
        date_select = self.calend.selectedDate().toPyDate()
        self.date_info_list.clear()
        self.date_info_list.addItem("Задачи,запланированные на: " + str(date_select) + "\n")
        daily_task_list = select_daily_tasks(date_select)
        self.priority_map = {
            "Авто": "Auto",
            "Обычный": "Casual",
            "Низкий": "Low",
            "Средний": "Mid",
            "Высокий": "High",
            "Критичный": "Extreme"
        }
        self.reverse_priority_map = {v: k for k, v in self.priority_map.items()}
        for title, dash, priority in daily_task_list:
            russian_priority = self.reverse_priority_map.get(priority, priority)
            self.date_info_list.addItem(f"{title}{dash}{russian_priority}")
    def addTaskToList(self,title,priority):
        russian_priority = self.reverse_priority_map.get(priority, priority)
        self.date_info_list.addItem(f"{title} — {russian_priority}")

    def openTaskEditor(self, text):
        params = select_task_property_for_edit(text)
        title = params[0]
        description = params[1]
        t_type = params[2]
        deadline_full = params[3]
        deadline = deadline_full.date()
        priority = params[4]
        self.task_editor = EditWindow(title,description,t_type,deadline,priority,parent=self)
        self.task_editor.show()
    def refreshTaskList(self):
        grid = QWidget()
        scroll_layout = QGridLayout(grid)

        if hasattr(self, 'show_completed_cb') and self.show_completed_cb.isChecked():
            tasks = select_completed_tasks()
            btn_color = "#2e7d32"
        else:
            tasks = select_underway_tasks()
            btn_color = "#4a90e2"

        for i, title in enumerate(tasks):
            task_btn = QPushButton(str(title), self)
            task_btn.setStyleSheet(f"QPushButton {{ background-color: {btn_color}; padding: 10px; }}")
            task_btn.clicked.connect(lambda _, t=title: self.openTaskEditor(t))
            scroll_layout.addWidget(task_btn, i, 0)

        scroll_layout.setRowStretch(len(tasks), 1)
        self.task_scroll.setWidget(grid)

    def openStatistic(self, op):
        self.ststistic_show  =  AnslitycWindow(op)
        self.ststistic_show.show()

    def refresh_closest_tasks(self):
        while self.cls_tsk_layout.count():
            item = self.cls_tsk_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                del item

        top_tasks = select_closest_tasks()

        cls_task_label = QLabel("Задачи, дедлайн которых скоро")
        cls_task_label.setStyleSheet("""
            QLabel {
                border: 2px solid #4a90e2;
                border-radius: 6px;
                padding: 8px;
                color: #2e3440;
                font-weight: bold;
                font-size: 14px;
                qproperty-alignment: 'AlignCenter';
                background-color: #eef2f7;
            }
        """)
        self.cls_tsk_layout.addWidget(cls_task_label)

        if not top_tasks:
            empty_label = QLabel("Все задачи выполнены! ✨")
            empty_label.setStyleSheet(
                "color: #7f8c9a; font-style: italic; padding: 10px; qproperty-alignment: 'AlignCenter';")
            self.cls_tsk_layout.addWidget(empty_label)
        else:
            for title, description in top_tasks:
                task_card = QLabel(
                    f"<b>{title}</b><br><span style='font-size:11px; color:#4c566a;'>{description}</span>")

                task_card.setWordWrap(True)
                task_card.setMinimumHeight(50)
                task_card.setMaximumHeight(80)

                task_card.setStyleSheet("""
                    QLabel {
                        border: 1px solid #d0d7de;
                        border-radius: 8px;
                        padding: 10px;
                        color: #2e3440;
                        background-color: white;
                    }
                    QLabel:hover {
                        border: 1px solid #4a90e2;
                        background-color: #f0f7ff;
                    }
                """)
                self.cls_tsk_layout.addWidget(task_card)

        self.cls_tsk_layout.addStretch(1)



    def handle_logout(self):
        if hasattr(self, 'sync_timer'):
            self.sync_timer.stop()

        try:
            from local_db import data_manager
            data_manager.engine.dispose()

            db_path = data_manager.get_db_path()

            settings = QSettings("MyCompany", "SystemOfUserProductivity")
            settings.remove("last_sync_time")
            settings.sync()

            AuthManager.clear_session()

            if os.path.exists(db_path):
                import time
                time.sleep(0.1)
                os.remove(db_path)
                print(f"✅ База удалена полностью: {db_path}")

        except Exception as e:
            print(f"⚠️ Ошибка при выходе: {e}")

        print("🔄 Перезапуск приложения...")
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable] + sys.argv[1:])
            sys.exit(0)
        else:
            os.execl(sys.executable, sys.executable, *sys.argv)
    def syncro(self):
        token = AuthManager.get_valid_token()
        if not token:
            QMessageBox.warning(self, "Ошибка", "Нужна авторизация")
            return

        self.Sync.setEnabled(False)
        sync_service = SyncService(token)
        success, message = sync_service.run_sync()

        if success:
            QMessageBox.information(self, "Успех", message)
            self.refresh_closest_tasks()
        else:
            QMessageBox.critical(self, "Ошибка", f"Синхронизация не удалась: {message}")

        self.Sync.setEnabled(True)

    def run_auto_sync(self):
        print("🔄 Запуск автоматической синхронизации...")
        success, message = self.sync_service.run_sync()

        if success:
            print(f"✅ Авто-синхронизация: {message}")
            self.refresh_closest_tasks()
        else:
            print(f"❌ Ошибка авто-синхронизации: {message}")



def build_complete_task_graph():
    data = select_daily_task_complete()
    if not data:
        data = []

    dates = [d.strftime("%m-%d") for d, _ in data]
    num_of_complete_tasks = [n for _, n in data]

    plot_widget = pg.PlotWidget(title="Выполненные задачи")
    plot_widget.showGrid(x=True, y=True)

    x = list(range(len(dates)))
    plot_widget.plot(x, num_of_complete_tasks, pen=pg.mkPen(color='b', width=2), symbol='o', symbolSize=8,
                     symbolBrush='b')

    plot_widget.getAxis('bottom').setTicks([list(zip(x, dates))])
    plot_widget.setLabel('left', 'Количество')
    plot_widget.setLabel('bottom', 'Дата')
    plot_widget.setBackground( 'w')
    return plot_widget


def build_capacity_graph():
    active_tasks, avg_priority, max_priority, avg_hours_to_deadline, overdue_tasks = select_capacity_parametrs()
    if (active_tasks, avg_priority, max_priority, avg_hours_to_deadline, overdue_tasks) == (0, 0, 0, 0, 0):
        percentage = 0
    else:
        percentage =  predict_capacity(active_tasks, avg_priority, max_priority, avg_hours_to_deadline, overdue_tasks)

    pw = pg.PlotWidget()
    pw.setAspectLocked()
    pw.hideAxis('bottom')
    pw.hideAxis('left')
    pw.setBackground('w')

    radius = 1.0
    num_points = 100

    theta_bg = np.linspace(0, 2 * np.pi, num_points)
    x_bg = radius * np.cos(theta_bg)
    y_bg = radius * np.sin(theta_bg)
    pw.plot(x_bg, y_bg, pen=pg.mkPen(color=(200, 200, 200), width=20))

    theta_fg = np.linspace(0, 2 * np.pi * (percentage / 100), num_points)
    x_fg = radius * np.cos(theta_fg)
    y_fg = radius * np.sin(theta_fg)

    pw.plot(x_fg, y_fg, pen=pg.mkPen(color=(0, 200, 0), width=20))

    font = QFont("Arial", 24, QFont.Weight.Bold)
    text = pg.TextItem(f"{percentage:.0f}%", anchor=(0.5, 0.5), color=(0, 0, 0))
    text.setFont(font)
    pw.addItem(text)
    text.setPos(0, 0)

    return pw

