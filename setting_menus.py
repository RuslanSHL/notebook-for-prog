from PyQt6.QtWidgets import (QApplication, QPushButton, QGridLayout, QWidget, QCheckBox,
                             QTabWidget, QDial, QLabel, QVBoxLayout, QLineEdit, QDialog, QDialogButtonBox,
                             QColorDialog, QFileDialog, QComboBox, QTextEdit, QFontDialog)
from PyQt6.QtGui import QColor, QIntValidator, QIcon
from PyQt6.QtCore import QSize

from sys import argv, exit


def choose_color():
    color_dialog = QColorDialog()
    if color_dialog.exec():
        return color_dialog.currentColor().name()


class HelpWindow(QDialog):
    '''Окно со справкой'''
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.text = text
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Справка')
        self.setWindowIcon(QIcon.fromTheme('help-faq'))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.help_text = QTextEdit(self)
        for i in self.text.split('\n'):
            self.help_text.append(i)
        self.help_text.setReadOnly(True)
        layout.addWidget(self.help_text)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept)
        layout.addWidget(self.buttonBox)


class StyleSettingWindow(QDialog):
    '''Окно для настройки стиля'''
    def __init__(self, parent=None, style_file=None):
        super().__init__(parent)
        self.style_file = style_file
        self.initUI() 
        self.update_style()
    
    def initUI(self):
        self.setWindowIcon(QIcon.fromTheme('emblem-system'))
        self.setWindowTitle('Настройка темы')
        layout = QGridLayout()
        self.setLayout(layout)

        self.color1_button = QPushButton(self)
        self.color1_button.clicked.connect(self.choose_color1)

        self.color2_button = QPushButton(self)
        self.color2_button.clicked.connect(self.choose_color2)

        self.color3_button = QPushButton(self)
        self.color3_button.clicked.connect(self.choose_color3)

        self.color1_label = QLabel('color1', self)
        self.color2_label = QLabel('color2', self)
        self.color3_label = QLabel('color3', self)

        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save_style)

        self.apply_button = QPushButton('Apply', self)
        self.apply_button.clicked.connect(self.apply_style)

        self.choose_style_box = QComboBox(self)
        self.choose_style_box.addItems(['Light', 'Dark'])
        self.choose_style_box.currentIndexChanged.connect(self.choose_style)

        self.font_button = QPushButton('Change font', self)
        self.font_button.clicked.connect(self.change_font)

        layout.addWidget(self.color1_button, 0, 1)
        layout.addWidget(self.color2_button, 1, 1)
        layout.addWidget(self.color3_button, 2, 1)

        layout.addWidget(self.color1_label, 0, 0)
        layout.addWidget(self.color2_label, 1, 0)
        layout.addWidget(self.color3_label, 2, 0)

        layout.addWidget(self.choose_style_box, 3, 0, 1, 2)

        layout.addWidget(self.font_button, 4, 0)

        layout.addWidget(self.save_button, 5, 0)
        layout.addWidget(self.apply_button, 5, 1)

    def update_style(self, current_style=None):
        '''load style from file and apply it'''
        if self.style_file:
            with open(self.style_file) as style:
                style_file = style.read()
                font, _current_style, colors_name, *styles, _ = style_file.split('\n', 5)
                self.current_font = font
                if current_style is None:
                    style = styles[int(_current_style) - 1].split()
                    self.current_style = int(_current_style)
                else:
                    self.current_style = current_style
                    # TODO изменить текущий элемент выбора стиля
                    style = styles[current_style - 1].split()
        else:
            style = ('#FFFFFF', '#FFFFFF', '#FFFFFF')
        self.color1_button.setStyleSheet(f'background: {style[0]}')
        self.color2_button.setStyleSheet(f'background: {style[1]}')
        self.color3_button.setStyleSheet(f'background: {style[2]}')
        self.color1, self.color2, self.color3 = style

    def choose_color1(self, e):
        self.color1 = choose_color()
        self.color1_button.setStyleSheet(f'background: {self.color1}')

    def choose_color2(self, e):
        self.color2 = choose_color()
        self.color2_button.setStyleSheet(f'background: {self.color2}')

    def choose_color3(self, e):
        self.color3 = choose_color()
        self.color3_button.setStyleSheet(f'background: {self.color3}')

    def save_style(self, e):
        with open(self.style_file) as style:
            style_file = style.readlines()
            style_file[0] = self.current_font + '\n'
            style_file[1] = str(self.current_style) + '\n'
            style_file[self.current_style + 2] = self.color1 + ' ' + self.color2 + ' ' + self.color3 + '\n'
        with open(self.style_file, 'w') as style:
            style.write(''.join(style_file))

    def apply_style(self, e):
        self.save_style(None)
        self.parent().update_style()

    def choose_style(self, e):
        self.update_style(e + 1)

    def change_font(self):
        font_dialog = QFontDialog(self)
        if font_dialog.exec():
            self.current_font = font_dialog.currentFont().toString()


class SettingBackground(QDialog):
    """Класс для настройки фона приложения"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.second_color = QColor('black')
        self.first_color = QColor('black')
        self.image = ''
        # Виджет вкладок
        tab_widget = QTabWidget(self)
        # кнопки
        QBtn = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Вкладка настройки цвета фона ###
        tab_choose_color = QWidget(self)
        choose_color_layout = QGridLayout(self)
        choose_color_layout.setSpacing(20)
        tab_choose_color.setLayout(choose_color_layout)

        # кнопка выбора цвета
        self.choose_color_button = QPushButton('Выбрать цвет фона', self)
        self.choose_color_button.clicked.connect(self.choose_color)
        # индикатор цвета
        self.current_color_label = QLabel(self)
        self.current_color_label.setStyleSheet('background: black')
        # checkbox добавление градиента
        self.add_gradient_checkbox = QCheckBox('Добавить градиент', self)
        self.add_gradient_checkbox.stateChanged.connect(self.add_gradient_enable)
        self.add_gradient_checkbox.setChecked(False)
        # изменение угла градиента
        self.set_gradient_angle = QDial()
        self.set_gradient_angle.setRange(0, 100)
        self.set_gradient_angle.setSingleStep(1)
        self.set_gradient_angle.valueChanged.connect(self.change_angle)
        # добавление второго цвета
        self.choose_second_color_button = QPushButton('Выбрать второй цвет', self)
        self.choose_second_color_button.clicked.connect(self.choose_second_color)
        # индикатор второго цвета
        self.current_second_color_label = QLabel(self)
        self.current_second_color_label.setStyleSheet('background: black')
        # Добавление виджетов в макет
        choose_color_layout.addWidget(self.choose_color_button, 0, 0, 1, 1)
        choose_color_layout.addWidget(self.current_color_label, 0, 1, 1, 1)
        choose_color_layout.addWidget(self.add_gradient_checkbox, 1, 0, 1, 1)
        choose_color_layout.addWidget(self.set_gradient_angle, 2, 0, 2, 1)
        choose_color_layout.addWidget(self.choose_second_color_button, 2, 1, 1, 1)
        choose_color_layout.addWidget(self.current_second_color_label, 3, 1, 1, 1)
        
        self.add_gradient_enable(False)
        tab_widget.addTab(tab_choose_color, "Выбрать цвет") 

        # Вкладка настройки выбора изображения ###
        tab_choose_image = QWidget(self)
        choose_image_layout = QGridLayout(self)
        tab_choose_image.setLayout(choose_image_layout)

        # кнопка выбора изображения
        choose_image_button = QPushButton('Выбрать изображение', self)
        choose_image_button.clicked.connect(self.choose_image)
        # checkbox блюр изображения
        self.blur_image_checkbox = QCheckBox('Блюр')
        # добавление виджетов в макет
        choose_image_layout.addWidget(choose_image_button, 0, 0, 1, 1)
        choose_image_layout.addWidget(self.blur_image_checkbox, 1, 0, 1, 1)

        tab_widget.addTab(tab_choose_image, "Выбрать изображение") 
        
        self.setLayout(QGridLayout())
        self.layout().addWidget(tab_widget)
        self.layout().addWidget(self.buttonBox)
        
    def choose_color(self) -> None:
        color_dialog = QColorDialog(self)
        if color_dialog.exec():
            self.first_color = color_dialog.currentColor()
            try:
                self.current_color_label.setStyleSheet(f'background: {self.first_color.name()}')
                if self.add_gradient_checkbox.isChecked():
                    self.set_gradient()
            except Exception as e:
                print(e)
            
    def add_gradient_enable(self, state: bool) -> None:
        """режим добавление градиента"""
        self.set_gradient_angle.setEnabled(state)
        self.choose_second_color_button.setEnabled(state)

    def choose_second_color(self) -> None:
        color_dialog = QColorDialog(self)
        if color_dialog.exec():
            self.second_color = color_dialog.currentColor()
            try:
                self.set_gradient()
            except Exception as e:
                print(e)

    def set_gradient(self):
        angle = self.set_gradient_angle.value() / 100
        self.gradient = f'background: qlineargradient(x1: {angle}, x2: {1 - angle}, y1: 0, y2: 1,\
                                                        stop: 0 {self.first_color.name()},\
                                                        stop: 1  {self.second_color.name()})'
        self.current_second_color_label.setStyleSheet(self.gradient)

    def choose_image(self):
        file_dialog = QFileDialog(self)
        if file_dialog.exec():
            self.image = file_dialog.selectedUrls()[0]
            print(self.image.toLocalFile())

    def blur_image(self):
        pass

    def has_gradient(self) -> bool:
        return self.add_gradient_checkbox.isChecked()

    def has_image(self) -> bool:
        return bool(self.image)

    def get_image(self) -> str:
        self.image_style = f'background-image: url({self.image.toLocalFile()});\
filter: blur(40px)'
        return self.image_style
    
    def get_gradient(self) -> str:
        return self.gradient

    def get_color(self) -> QColor:
        return self.first_color

    def change_angle(self, e):
        self.set_gradient()


class SettingSize(QDialog):
    '''Окно для настойки размера элемента заметки'''
    def __init__(self, size):
        super().__init__()
        self.initUI(size)

    def initUI(self, size):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.x_line = QLineEdit(str(size.width()), self)
        self.y_line = QLineEdit(str(size.height()), self)
        
        self.x_line.setValidator(QIntValidator())
        self.x_line.setPlaceholderText('Размер по x')
        
        self.y_line.setValidator(QIntValidator())
        self.y_line.setPlaceholderText('Размер по y')

        QBtn = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self.x_line)
        layout.addWidget(self.y_line)
        layout.addWidget(self.buttonBox)

    def apply(self):
        self.close()

    def get_size(self):
        return QSize(int(self.x_line.text()), int(self.y_line.text()))
    

if __name__ == '__main__':
    app = QApplication(argv)

    window = HelpWindow('''hi''')
    exit(window.exec())

    exit(app.exec())
