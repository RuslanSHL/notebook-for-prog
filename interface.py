from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QToolBar,
                             QScrollArea, QLayout,
                             QMenu, QLineEdit, QLabel, QToolButton)
from PyQt6.QtCore import Qt, QSize, QPoint, QRect, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QFont
from sys import argv, exit
from datetime import date

from database import DataBase
from note_editor1 import NoteEditor
from setting_menus import StyleSettingWindow, HelpWindow


LIGHT_BLUE_THEME = {' neytral_color': '#E9EDE3',
                    ' focus_color': '#0594FA',
                    ' dark_focus_color': '#023E68'}


def format_style(style: dict, style_sheet: str) -> str:
    '''Функция для создания таблицы стилей'''
    for k, v in style.items():
        style_sheet = style_sheet.replace(k, v)
    return style_sheet


class FileButton(QToolButton):
    '''Класс для размещения файла'''
    doubleClicked = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self, text, type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = args[-1] if args else None

        # настройка кнопки
        self.setText(text)
        self.setIcon(QIcon('icons/folder.png' if type == 'folders' else 'icons/note.png'))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        # таймер для двойного клика
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(250)
        super().clicked.connect(self.checkDoubleClick)
    
    def connect_id_file(self, id_file):
        '''ИД файла из БД'''
        self.id_file = id_file

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        delete = menu.addAction('Удалить')
        cut = menu.addAction('Вырезать')
        action = menu.exec(self.mapToGlobal(e.pos()))
        if action == delete:
            self.parent.database.delete_file(self.id_file)
        elif action == cut:
            self.parent.cut_file = self.id_file
        self.parent.update()
        
    @pyqtSlot()
    def checkDoubleClick(self):
        self.clicked.emit()
        if self.timer.isActive():
            self.doubleClicked.emit()
            self.timer.stop()
        else:
            self.timer.start()


class FileSystemLayout(QLayout):
    '''Макет для размещения кнопок файлов'''
    def __init__(self, parent=None):
        super().__init__(parent)

        self._items_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def deleteWidgets(self):
        item = self.takeAt(0)
        item.deleteLater()
        while item:
            item = self.takeAt(0)
            item.deleteLater()
            
    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        
        return self.do_layout(QRect(0, 0, self.geometry().width(), 0))

    def takeAt(self, index):
        if 0 <= index < len(self._items_list):
            return self._items_list.pop(index)

        return None

    def itemAt(self, index):
        if 0 <= index < len(self._items_list):
            return self._items_list[index]

        return None

    def count(self):
        return len(self._items_list)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.do_layout(rect)

    def addItem(self, item):
        self._items_list.append(item)

    def do_layout(self, rect, no_test=True):
        spacing = self.spacing()
        x = rect.x() + spacing
        y = rect.y() + spacing
        for item in self._items_list:
            if x + item.sizeHint().width() + spacing > rect.right():
                y += spacing + item.sizeHint().height()
                x = rect.x() + spacing
            if no_test:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x += item.sizeHint().width() + spacing
        
        return QSize(x, y)
        

class MainWindow(QMainWindow):
    '''Главное окно для работы с файловой системой'''
    def __init__(self):
        super().__init__()
        self.now_directory = 0
        self.focus_file = None
        self.files_buttons = []
        self.cut_file = None
        
        # настройка окна
        self.setWindowTitle('Записная книжка для программиста')
        self.resize(QSize(1000, 500))
        # применение стиля
        self.update_style()
        # создание menubar
        menu = self.menuBar()
        file_menu = menu.addMenu('Файл')
        button_change_database = QAction('Подключить другую базу данных', self)
        file_menu.addAction(button_change_database)
        
        button_main = QAction('Главная', self)
        menu.addAction(button_main)
        button_main.triggered.connect(self.show_toolbar_main)

        setting_button = QAction('Вид', self)
        menu.addAction(setting_button)
        setting_button.triggered.connect(self.setting_style)
        
        help_button = QAction('Справка', self)
        menu.addAction(help_button)
        help_button.triggered.connect(self.open_help)

        # создание toolbar_main
        self.toolbar_main = QToolBar('Панель инструментов')
        self.addToolBar(self.toolbar_main)
        #  действия для toolbar_main
        self.add_note_action = QAction('Добавить запись')
        self.add_note_action.triggered.connect(self.add_note)
        self.add_direction_action = QAction('Добавить папку')
        self.add_direction_action.triggered.connect(self.add_direction)
        self.past_file_action = QAction('Вставить')
        self.past_file_action.triggered.connect(self.paste_file)
        # добавление в toolbar_main
        self.toolbar_main.addAction(self.add_note_action)
        self.toolbar_main.addAction(self.add_direction_action)
        # создание toolbar_files
        toolbar_files = QToolBar('Файл')
        self.addToolBar(toolbar_files)
        self.file_name = QLineEdit(self)
        self.file_name.editingFinished.connect(self.change_file_name)
        self.file_theme = QLineEdit(self)
        self.file_theme.editingFinished.connect(self.change_file_theme)
        self.file_date = QLabel(self)
        self.file_type = QLabel(self)
        # добавление в toolbar_files
        toolbar_files.addWidget(self.file_name)
        toolbar_files.addSeparator()
        toolbar_files.addWidget(self.file_theme)
        toolbar_files.addSeparator()
        toolbar_files.addWidget(self.file_date)
        toolbar_files.addSeparator()
        toolbar_files.addWidget(self.file_type)

        # создание toolbar_for_move
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        toolbar_for_move = QToolBar('Перемещение')
        toolbar_for_move.setMovable(False)
        self.return_up_action = QAction('^', self)
        self.return_up_action.triggered.connect(self.return_up_function)
        self.return_up_action.setShortcut(QKeySequence('Alt+up'))

        self.now_path = QLabel(self)
        self.now_path.setObjectName('pathLabel')

        # добавление в toolbar_for_move
        toolbar_for_move.addAction(self.return_up_action)
        toolbar_for_move.addWidget(self.now_path)
        
        self.addToolBar(toolbar_for_move)

        # создание рабочей зоны
        widget = QWidget()
        work_area_scroll = QScrollArea()
        self.work_area_grid = FileSystemLayout()
        
        widget.setLayout(self.work_area_grid)

        work_area_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        work_area_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        work_area_scroll.setWidgetResizable(True)
        work_area_scroll.setWidget(widget)
        
        self.setCentralWidget(work_area_scroll)

        # подключение базы данных
        self.database = DataBase('db.db')
        self.load_from_database_directory(self.now_directory)
        self.return_up_action.setEnabled(self.now_directory)

    def update_style(self):
        '''Обновить стиль'''
        with open('./viewerLightStyle.qss') as style:
            style_file = style.read()
            font, current_style, colors_name, *styles, style = style_file.split('\n', 5)
            _font = QFont()
            _font.fromString(font)
            self.setStyleSheet(format_style(dict(zip(colors_name.split(), styles[int(current_style) - 1].split())), 
                               style))
            QApplication.instance().setFont(_font)

    def show_toolbar_main(self):
        '''Переключение видимости toolbar_main'''
        self.toolbar_main.setVisible(self.toolbar_main.isHidden())

    def open_help(self):
        '''Справка для пользователя'''
        with open('helps/viewer.txt', encoding='utf-8') as file:
            help_text = file.read()
        help_window = HelpWindow(help_text, self)
        if help_window.exec():
            pass

    def setting_style(self):
        '''Настройка стиля'''
        setting_window = StyleSettingWindow(self, './viewerLightStyle.qss')
        if setting_window.exec():
            pass

    def load_from_database_directory(self, directory_id: int) -> list:
        '''Загрузить записи и папки из папки directory_id'''
        data = self.database.get_content_folder(directory_id)
        # очистка от старых файлов
        self.work_area_grid.__del__()
        for i in self.files_buttons:
            i.deleteLater()
        self.files_buttons = []
        for i in data:
            button = FileButton(i[0], i[3], self)
            button.doubleClicked.connect(lambda x=i[-1]: self.doubleclick_on_file_button(x))
            button.clicked.connect(lambda x=i[-1]: self.click_on_file_button(x))
            button.connect_id_file(i[-1])
            button.setMinimumSize(QSize(50, 50))
            button.setMaximumSize(QSize(60, 60))
            self.files_buttons.append(button)
            self.work_area_grid.addWidget(button)
        self.set_now_path()

    def set_now_path(self):
        '''Установить текущий путь к папке'''
        directory_id = self.now_directory
        path = ''
        while directory_id:
            path = self.database.info_about_folder(directory_id)[1] + '/' + path
            directory_id = self.database.get_parent_file(directory_id)
        path = ':/' + path
        self.now_path.setText(path)
            
    def doubleclick_on_file_button(self, id_file):
        type_of_file = self.database.get_type_file(id_file)
        if type_of_file == 'folders':
            self.now_directory = int(id_file)
            self.load_from_database_directory(id_file)
            self.return_up_action.setEnabled(self.now_directory)
        else:
            try:
                note_editor = NoteEditor(self, note_id=id_file)
                note_editor.load_note(self.database.get_note_content(id_file))
                note_editor.show()
            except Exception:
                pass

    def click_on_file_button(self, id_file):
        type_of_file = self.database.get_type_file(id_file)
        self.focus_file = id_file
        if type_of_file == 'folders':
            _, name, date, theme, _ = self.database.info_about_folder(id_file)
            self.file_name.setText(name)
            self.file_theme.setText(theme)
            self.file_date.setText(date)
            self.file_type.setText(type_of_file)
        else:
            date, theme, name, _ = self.database.info_about_note(id_file)
            self.file_name.setText(name)
            self.file_theme.setText(theme)
            self.file_date.setText(date)
            self.file_type.setText(type_of_file)

    def return_up_function(self):
        if self.now_directory:
            self.now_directory = self.database.get_parent_file(self.now_directory)
            self.return_up_action.setEnabled(self.now_directory)
            self.load_from_database_directory(self.now_directory)

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.NoDropShadowWindowHint)

        menu.addAction(self.add_direction_action)
        menu.addAction(self.add_note_action)
        menu.addAction(self.past_file_action)
        menu.exec(self.mapToGlobal(e.pos()))
            
    def update(self):
        self.load_from_database_directory(self.now_directory)
        super().update()

    def add_direction(self):
        '''Создать папку'''
        self.database.add_folder(date.today().strftime('%Y-%m-%d'), 'new folder', 'theme', self.now_directory)
        self.update()
        
    def add_note(self):
        '''Создать запись'''
        self.database.add_note(date.today().strftime('%Y-%m-%d'), 'new note', 'theme', self.now_directory)
        self.load_from_database_directory(self.now_directory)

    def paste_file(self):
        '''Вставить вырезанный файл'''
        if self.cut_file:
            self.database.remove_file(self.cut_file, self.now_directory)
            self.update()

    def save_note(self, type, coords, size, content, args='', note_id=1):
        '''Сохранить запись'''
        self.database.add_note_content(note_id=note_id, args=args, coords=str(coords),
                                       size=str(size), content=content, type=type)

    def change_file_name(self):
        '''Изменить имя файла'''
        if self.focus_file:
            self.database.change_file_name(self.focus_file, self.file_name.text())
            self.update()
        
    def change_file_theme(self):
        '''Изменить тему файла'''
        if self.focus_file:
            self.database.change_file_theme(self.focus_file, self.file_theme.text())
            self.update()


app = QApplication(argv)
window = MainWindow()
window.show()
exit(app.exec())
