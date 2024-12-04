from PyQt6.QtWidgets import (QApplication, QMainWindow, QToolBar, QToolButton, QWidget,
                             QSizePolicy, QPushButton, QScrollArea, QColorDialog,
                             QFileDialog, QSpinBox, QTextEdit, QMenu, QLabel)
from PyQt6.QtGui import (QDrag, QAction, QPixmap, QColor, QPainter, QPen, QFont)
from PyQt6.QtCore import Qt, QSize, QRect, QPoint, QMimeData, QByteArray, QBuffer, QIODevice

from setting_menus import SettingSize, SettingBackground, StyleSettingWindow, HelpWindow
from highlighter import PythonSyntaxHighlighterInBlockCode, PythonSyntaxHighlighter

from urllib.request import Request, urlopen
from sys import argv
import os


def format_style(style: dict, style_sheet: str) -> str:
    '''Создать таблицу стилей'''
    for k, v in style.items():
        style_sheet = style_sheet.replace(k, v)
    return style_sheet


class CodeLabel(QWidget):
    """Виджет размещения кода"""
    def __init__(self, position_point: QPoint, *args, text=''):
        super().__init__(*args)
        self.last_pos = QPoint()
        self.position_point = position_point
        # настрока и создание label
        self.setEnabled(False)
        self.label = NoteTextEdit(self)
        self.highlighter = PythonSyntaxHighlighter(self.label.document())
        self.label.setText(text)
        self.setMinimumSize(50, 50)
        self.label.setEnabled(False)
        self.setGeometry(QRect(position_point, self.label.sizeHint()))
        
    def setGeometry(self, e):
        self.label.resize(e.size())
        super().setGeometry(e)

    def resize(self, e):
        self.label.resize(e)
        super().resize(e)
        
    def mouseReleaseEvent(self, e):
        # для активации label
        if self.isEnabled():
            if e.button() == Qt.MouseButton.LeftButton:
                self.label.setEnabled(True)
                self.label.setFocus()
        else:
            self.setEnabled(True)
            self.raise_()

    def mouseMoveEvent(self, e):
        # для перетаскивания
        if e.buttons() == Qt.MouseButton.LeftButton:
            if e.modifiers() == Qt.KeyboardModifier.AltModifier:
                pos = self.parent().mapFromGlobal(e.globalPosition().toPoint())
                if (pos.x() < 0 or self.parent().size().width() < pos.x() or
                   pos.y() < 0 or self.parent().size().height() < pos.y()):
                    return
                
                if (self.last_pos.x() < 10 or self.last_pos.y() < 10 or self.last_pos.x() > self.size().width() - 10 or
                   self.last_pos.y() > self.size().height() - 10):
                    
                    geometry = self.geometry()
                    if self.last_pos.x() < 10:
                        geometry.setLeft(pos.x())
                    elif self.last_pos.x() > self.size().width() - 10:
                        geometry.setRight(pos.x())
                        self.last_pos.setX(geometry.size().width())
                    if self.last_pos.y() < 10:
                        geometry.setTop(pos.y())
                    elif self.last_pos.y() > self.size().height() - 10:
                        geometry.setBottom(pos.y())
                        self.last_pos.setY(geometry.size().height())
                    self.setGeometry(geometry)
                
                else:
                    self.move(pos - self.last_pos)

    def mousePressEvent(self, e):
        self.last_pos = e.pos()

    def keyPressEvent(self, e):
        if e.key() == 16777216:
            # esc
            self.label.setEnabled(False)
            self.parent().do_layout()

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        move_back = menu.addAction('Сдвинуть назад')
        move_forward = menu.addAction('Сдвинуть вперёд')
        min_resize = menu.addAction('Уменьшить')
        resize = menu.addAction('Изменить размер')
        start = menu.addAction('Запустить код')
        menu.addAction('Изменить язык')
        delete = menu.addAction('Удалить')
        action = menu.exec(self.mapToGlobal(e.pos()))
        if action == move_back:
            self.parent().move_element_back(self)
        elif action == start:
            with open('.time_files/.code.py', 'w') as file:
                file.write(self.label.toPlainText())
            os.system('start .time_files/.code.py')
        elif action == move_forward:
            self.parent().move_element_forward(self)
        elif action == min_resize:
            self.resize(self.minimumSize())
            self.label.resize(self.minimumSize())
        elif action == resize:
            size_dialog = SettingSize(self.size())
            if size_dialog.exec():
                self.resize(size_dialog.get_size())
                self.label.resize(self.size())
        elif action == delete:
            self.parent().delete_element(self)

    def disable(self):
        """Потеря фокуса"""
        self.setEnabled(False)
        self.label.setEnabled(False)

    def info(self) -> dict:
        """Получение информации для сохранения"""
        result = {'content': bytes(self.label.toPlainText(), encoding='utf-8'),
                  'size': (self.size().width(), self.size().height()),
                  'coords': self.geometry().getCoords()[:2]}
        return result


class File(QLabel):
    """Виджет хранения файла"""
    def __init__(self, position_point: QPoint, *args, file=None):
        super().__init__(*args)
        self.last_pos = QPoint()
        self.position_point = position_point
        self.file = file
        if file:
            try:
                with open(file, 'rb') as opened_file:
                    self.file = opened_file.read()
            except Exception:
                pass
        # настрока и создание label
        self.setEnabled(False)
        self.setText(file.split('/')[-1])
        self.name = file.split('/')[-1]
        self.setMinimumSize(50, 50)
        self.setGeometry(QRect(position_point, self.sizeHint()))
        
    def mouseReleaseEvent(self, e):
        # для активации
        self.setEnabled(True)
        self.raise_()

    def mouseMoveEvent(self, e):
        # для перетаскивания
        if e.buttons() == Qt.MouseButton.LeftButton:
            if e.modifiers() == Qt.KeyboardModifier.AltModifier:
                pos = self.parent().mapFromGlobal(e.globalPosition().toPoint())
                if (pos.x() < 0 or self.parent().size().width() < pos.x() 
                   or pos.y() < 0 or self.parent().size().height() < pos.y()):
                    return
                else:
                    self.move(pos - self.last_pos)

    def mousePressEvent(self, e):
        self.last_pos = e.pos()

    def keyPressEvent(self, e):
        if e.key() == 16777216:
            # esc
            self.parent().do_layout()

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        move_back = menu.addAction('Сдвинуть назад')
        move_forward = menu.addAction('Сдвинуть вперёд')
        open_file = menu.addAction('Открыть файл')
        is_image = menu.addAction('Отобразить как изображение')
        is_text = menu.addAction('Отобразить как тект')
        is_code = menu.addAction('Отобразить как код')
        delete = menu.addAction('Удалить')
        action = menu.exec(self.mapToGlobal(e.pos()))
        if action == move_back:
            self.parent().move_element_back(self)
        elif action == move_forward:
            self.parent().move_element_forward(self)
        elif action == open_file:
            self.open()
        elif action == is_image:
            self.convert_to_image()
        elif action == is_text:
            self.convert_to_text()
        elif action == is_code:
            self.convert_to_code()
        elif action == delete:
            self.parent().delete_element(self)

    def disable(self):
        """Потеря фокуса"""
        self.setEnabled(False)

    def open(self):
        """Для открытия файла"""
        with open('.time_files/' + self.name, 'wb') as file:
            file.write(self.file)
        os.system('start .time_files/' + self.name)

    def convert_to_image(self):
        """Отобразить файл как изображение"""
        try:
            self.parent().add_image(self.pos(),
                                    image=self.file)
            self.parent().delete_element(self)
        except Exception:
            pass

    def convert_to_text(self):
        """Отобразить файл как текстовую заметку"""
        try:
            self.parent().add_note(self.pos(), text=self.file.decode('utf-8'))
            self.parent().delete_element(self)
        except Exception:
            pass

    def convert_to_code(self):
        """Отобразить файл как код"""
        try:
            self.parent().add_code(self.pos(), text=self.file.decode('utf-8'))
            self.parent().delete_element(self)
        except Exception:
            pass

    def set_file(self, content_of_file: bytes):
        """Загрузка информации файла"""
        self.file = content_of_file

    def set_args(self, name='file'):
        """Загрузка аргументов"""
        self.name = name
        self.setText(name)
        self.resize(QSize(self.sizeHint()))

    def info(self) -> dict:
        """Информация для сохранения"""
        result = {'content': self.file,
                  'size': (self.size().width(), self.size().height()),
                  'coords': self.geometry().getCoords()[:2],
                  'args': str({"name": self.text()})}
        return result


class ImageLabel(QLabel):
    """Виджет для размещения картинок"""
    def __init__(self, point, *args, image=None, url=None):
        super().__init__(*args)
        self.last_pos = QPoint(0, 0)
        self.enabled = True
        # настройка и создание label
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.image = b''
        if url is not None:
            pixmap = QPixmap(url)
            self.image = url
        elif image is not None:
            pixmap = QPixmap()
            pixmap.loadFromData(image)
            self.image = image
        self.label.setPixmap(pixmap) 
        self.setGeometry(QRect(point, self.label.sizeHint()))
        self.setMinimumSize(50, 50)

    def setGeometry(self, e):
        self.label.resize(e.size())
        super().setGeometry(e)

    def resize(self, e):
        self.label.resize(e)
        super().resize(e)
        
    def mouseReleaseEvent(self, e):
        self.setEnabled(True)
        self.raise_()

    def mousePressEvent(self, e):
        self.last_pos = e.pos()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            if e.modifiers() == Qt.KeyboardModifier.AltModifier:
                pos = self.parent().mapFromGlobal(e.globalPosition().toPoint())
                if (pos.x() < 0 or self.parent().size().width() < pos.x() 
                   or pos.y() < 0 or self.parent().size().height() < pos.y()):
                    return
                
                if (self.last_pos.x() < 10 or self.last_pos.y() < 10 or self.last_pos.x() > self.size().width() - 10 
                   or self.last_pos.y() > self.size().height() - 10):
                    
                    geometry = self.geometry()
                    if self.last_pos.x() < 10:
                        geometry.setLeft(pos.x())
                    elif self.last_pos.x() > self.size().width() - 10:
                        geometry.setRight(pos.x())
                        self.last_pos.setX(geometry.size().width())
                    if self.last_pos.y() < 10:
                        geometry.setTop(pos.y())
                    elif self.last_pos.y() > self.size().height() - 10:
                        geometry.setBottom(pos.y())
                        self.last_pos.setY(geometry.size().height())
                    self.setGeometry(geometry)
                
                else:
                    self.move(pos - self.last_pos)

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        move_back = menu.addAction('Сдвинуть назад')
        move_forward = menu.addAction('Сдвинуть вперёд')
        min_resize = menu.addAction('Уменьшить')
        resize = menu.addAction('Изменить размер')
        delete = menu.addAction('Удалить')
        action = menu.exec(self.mapToGlobal(e.pos()))
        if action == move_back:
            self.parent().move_element_back(self)
        elif action == move_forward:
            self.parent().move_element_forward(self)
        elif action == min_resize:            
            self.resize(self.minimumSize())
            self.label.resize(self.minimumSize())
        elif action == resize:
            size_dialog = SettingSize(self.size())
            if size_dialog.exec():
                self.resize(size_dialog.get_size())
                self.label.resize(size_dialog.get_size())
        elif action == delete:
            self.parent().delete_element(self)

    def disable(self):
        """Потеря фокуса"""
        self.setEnabled(False)

    def setEnabled(self, s):
        self.enabled = s

    def isEnabled(self):
        return self.enabled

    def info(self) -> dict:
        """Информация для сохранения"""
        result = {'content': self.image, 
                  'size': (self.size().width(), self.size().height()),
                  'coords': self.geometry().getCoords()[:2]}
        return result
        

class NoteTextEdit(QTextEdit):
    """Поле ввода текста"""
    def mouseReleaseEvent(self, e):
        # передача клика
        self.parent().mouseReleaseEvent(e)
        super().mouseReleaseEvent(e)
        
    def mouseMoveEvent(self, e):
        # передача передвижения и расширения
        if e.buttons() == Qt.MouseButton.LeftButton:
            if e.modifiers() == Qt.KeyboardModifier.AltModifier:
                self.parent().mouseMoveEvent(e)
        elif (e.pos().x() < 20 and e.pos().y() < 20 
              or e.pos().x() > self.size().width() - 10 and e.pos().y() > self.size().height() - 20):
            # верхний левый угол и нижний правый
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif (e.pos().x() < 20 and e.pos().y() > self.size().height() - 20 
              or e.pos().y() < 10 and e.pos().x() > self.size().width() - 20):
            # левый нижний угол и правый верхний угол
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif e.pos().x() < 20 or e.pos().x() > self.size().width() - 20:
            # левая сторона и правая сторона
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif e.pos().y() < 20 or e.pos().y() > self.size().height() - 20:
            # верхняя сторона и нижняя сторона
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        # для перетаскивания
        self.parent().mousePressEvent(e)
        super().mousePressEvent(e)


class NoteLabel(QWidget):
    """Виджет размещения текста"""
    def __init__(self, position_point: QPoint, *args, text=''):
        super().__init__(*args)
        self.last_pos = QPoint()
        self.position_point = position_point
        # настрока и создание label
        self.setEnabled(False)
        self.label = NoteTextEdit(self)
        self.highlighter = PythonSyntaxHighlighterInBlockCode(self.label.document())
        self.label.setText(text)
        self.setMinimumSize(50, 50)
        self.label.setEnabled(False)
        self.setGeometry(QRect(position_point, self.label.sizeHint()))
        
    def setGeometry(self, e):
        self.label.resize(e.size())
        super().setGeometry(e)

    def resize(self, e):
        self.label.resize(e)
        super().resize(e)

    def mouseReleaseEvent(self, e):
        # для активации label
        if self.isEnabled():
            if e.button() == Qt.MouseButton.LeftButton:
                self.label.setEnabled(True)
                self.label.setFocus()
        else:
            self.setEnabled(True)
            self.raise_()

    def mouseMoveEvent(self, e):
        # для перетаскивания
        if e.buttons() == Qt.MouseButton.LeftButton:
            if e.modifiers() == Qt.KeyboardModifier.AltModifier:
                pos = self.parent().mapFromGlobal(e.globalPosition().toPoint())
                if (pos.x() < 0 or self.parent().size().width() < pos.x() 
                   or pos.y() < 0 or self.parent().size().height() < pos.y()):
                    return
                
                if (self.last_pos.x() < 10 or self.last_pos.y() < 10 or self.last_pos.x() > self.size().width() - 10 
                   or self.last_pos.y() > self.size().height() - 10):
                    
                    geometry = self.geometry()
                    if self.last_pos.x() < 10:
                        geometry.setLeft(pos.x())
                    elif self.last_pos.x() > self.size().width() - 10:
                        geometry.setRight(pos.x())
                        self.last_pos.setX(geometry.size().width())
                    if self.last_pos.y() < 10:
                        geometry.setTop(pos.y())
                    elif self.last_pos.y() > self.size().height() - 10:
                        geometry.setBottom(pos.y())
                        self.last_pos.setY(geometry.size().height())
                    self.setGeometry(geometry)
                
                else:
                    self.move(pos - self.last_pos)

    def mousePressEvent(self, e):
        self.last_pos = e.pos()

    def keyPressEvent(self, e):
        if e.key() == 16777216:
            # esc
            self.label.setEnabled(False)
            self.parent().do_layout()

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        move_back = menu.addAction('Сдвинуть назад')
        move_forward = menu.addAction('Сдвинуть вперёд')
        min_resize = menu.addAction('Уменьшить')
        resize = menu.addAction('Изменить размер')
        delete = menu.addAction('Удалить')
        action = menu.exec(self.mapToGlobal(e.pos()))
        if action == move_back:
            self.parent().move_element_back(self)
        elif action == move_forward:
            self.parent().move_element_forward(self)
        elif action == min_resize:
            self.resize(self.minimumSize())
            self.label.resize(self.minimumSize())
        elif action == resize:
            size_dialog = SettingSize(self.size())
            if size_dialog.exec():
                self.resize(size_dialog.get_size())
                self.label.resize(self.size())
        elif action == delete:
            self.parent().delete_element(self)

    def disable(self):
        """Потеря фокуса"""
        self.setEnabled(False)
        self.label.setEnabled(False)

    def info(self) -> dict:
        """Получения информации для сохранения"""
        result = {'content': bytes(self.label.toPlainText(), encoding='utf-8'),
                  'size': (self.size().width(), self.size().height()),
                  'coords': self.geometry().getCoords()[:2]}
        return result

            
class Canvas(QWidget):
    """Главный холст
    paint_canvas - холст для рисования"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = self.parent()
        self.layout = []
        self.items = {}
        self.add_notes_mode = False
        self.add_files_mode = False
        self.add_codes_mode = False
        
        # настройка холста
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.resize(QSize(2000, 1000))
        self.setStyleSheet("Canvas#main {background-color: white);}")

        # холст для рисования
        self.paint_canvas = PaintCanvas(self)
        self.layout.append(self.paint_canvas)

        self.do_layout()

    def mouseReleaseEvent(self, e):
        if self.add_notes_mode:
            self.add_note(e.pos())
        elif self.add_files_mode:
            self.add_file(e.pos())
        elif self.add_codes_mode:
            self.add_code(e.pos())
        elif not self.paint_canvas.drawing_mode:
            for k in self.layout:
                if k != self.paint_canvas:
                    if e.pos() in self.items[k]():
                        self.do_layout()
                        k.mouseReleaseEvent(e)

    def dragEnterEvent(self, e):
        e.accept()
                    
    def dropEvent(self, e):
        if e.mimeData().parent():
            if e.mimeData().parent().is_file:
                file_dialog = QFileDialog(self)
                if file_dialog.exec():
                    e.mimeData().setUrls(file_dialog.selectedUrls())

        if e.mimeData().hasUrls():
            url = e.mimeData().urls()[0]
            if url.isLocalFile():
                self.add_file(QPoint(int(e.position().x()), int(e.position().y())),
                              file=url.toLocalFile())
            else:
                try:
                    request_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0)\
Gecko/20100101 Firefox/92.0'}
                    req = Request(url.toString(), headers=request_headers)
                    data = urlopen(req).read()
                except Exception:
                    return
                self.add_image(QPoint(int(e.position().x()), int(e.position().y())),
                               image=data)
        elif e.mimeData().parent().is_text:
            self.add_note(e.position().toPoint(),
                          text=e.mimeData().text())
        elif e.mimeData().parent().is_code:
            self.add_code(e.position().toPoint(),
                          text=e.mimeData().text())

    def do_layout(self):
        """Отображение элементов заметок по слоям"""
        for i in self.layout:
            i.disable()
            i.show()
            i.raise_()
        self.setFocus()

    def set_add_notes_mode(self, add_notes_mode: bool):
        """Режим добавления заметок"""
        self.add_notes_mode = add_notes_mode

    def set_add_files_mode(self, add_files_mode: bool):
        """Режим добавления файлов"""
        self.add_files_mode = add_files_mode

    def set_add_codes_mode(self, add_codes_mode: bool):
        """Режим добавления блоков кода"""
        self.add_codes_mode = add_codes_mode

    def add_note(self, pos: QPoint(), text='') -> NoteLabel:
        """Создание поля для текстовой заметки"""
        new_label = NoteLabel(pos, self, text=text)
        new_label.show()
        self.items[new_label] = new_label.geometry
        self.layout.append(new_label)
        self.do_layout()
        return new_label

    def add_code(self, pos: QPoint(), text='') -> CodeLabel:
        """Создание поля для кода"""
        new_label = CodeLabel(pos, self, text=text)
        new_label.show()
        self.items[new_label] = new_label.geometry
        self.layout.append(new_label)
        self.do_layout()
        return new_label

    def add_image(self, pos, image=None, url=None) -> ImageLabel:
        """Создание картинки"""
        lb = ImageLabel(pos, self, image=image, url=url)
        lb.show()
        self.layout.append(lb)
        self.items[lb] = lb.geometry
        self.do_layout()
        return lb

    def add_file(self, pos, file=None) -> File:
        """Создание файла"""
        if file is None:
            file_dialog = QFileDialog(self)
            if file_dialog.exec():
                file = file_dialog.selectedUrls()[0].toLocalFile()
            else:
                return
        f = File(pos, self, file=file)
        f.show()
        self.layout.append(f)
        self.items[f] = f.geometry
        self.do_layout()
        return f
        
    def move_element_back(self, element):
        """Переместить элемент на задний фон"""
        index = self.layout.index(element)
        if index - 1 >= 0:
            self.layout[index - 1], self.layout[index] = self.layout[index], self.layout[index - 1]
            self.do_layout()

    def move_element_forward(self, element):
        """Переместить элемент на передний фон"""
        index = self.layout.index(element)
        if index + 1 < len(self.layout):
            self.layout[index + 1], self.layout[index] = self.layout[index], self.layout[index + 1]
            self.do_layout()
        
    def delete_element(self, element):
        """Удалить элемент с холста"""
        print(self.items)
        element.deleteLater()
        self.layout.remove(element)
        del self.items[element]
        self.do_layout()

    def keyPressEvent(self, e):
        # esc
        if e.key() == 16777216:
            self.do_layout()
            self.parent.set_cursor()

    def set_paint_canvas(self, content):
        '''Установить холст рисования'''
        del self.layout[0]
        self.paint_canvas.set_content(content)
        self.layout.append(self.paint_canvas)

    def set_args(self, fone=None, size=None):
        '''Установить дополнительные настройки'''
        if fone:
            self.setStyleSheet(fone)
        if size:
            size = eval(size)
            self.resize(*size)
            self.paint_canvas.resize(QSize(*size))
        
    
class PaintCanvas(QLabel):
    """Холст для рисования"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.parent = args[-1]
        self.drawing_mode = False
        self.last_coords = None
        self.erase_mode = False
        
        # настройка холста
        self.setFocus()
        pixmap = QPixmap(2000, 1000)
        pixmap.fill(QColor('transparent'))
        self.setPixmap(pixmap)
        
        # создание и настройка кисти
        self.pen = QPen(QColor('black'), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

    def resize(self, e):
        self.setPixmap(self.pixmap().scaled(e))
        super().resize(e)            

    def mouseMoveEvent(self, e):
        # рисование
        if self.drawing_mode:
            if self.last_coords is None:
                self.last_coords = e.position()
                return
            canvas = self.pixmap()
            painter = QPainter(canvas)
            if not self.erase_mode:
                painter.setPen(self.pen)
                painter.drawLine(self.last_coords, e.position())
            else:
                width = self.pen.width()
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.eraseRect(QRect(e.position().toPoint() - QPoint(width // 2, width // 2),
                                        QSize(width, width)))
            painter.end()
            self.setPixmap(canvas)
            self.last_coords = e.position()

    def mouseReleaseEvent(self, e):
        if self.drawing_mode:
            self.last_coords = None
        else:
            super().mouseReleaseEvent(e)

    def mousePressEvent(self, e):
        self.parent.do_layout()
        self.raise_()

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        move_back = menu.addAction('Сдвинуть назад')
        move_forward = menu.addAction('Сдвинуть вперёд')
        action = menu.exec(self.mapToGlobal(e.pos()))
        if action == move_back:
            self.parent.move_element_back(self)
        elif action == move_forward:
            self.parent.move_element_forward(self)

    def set_drawing_mode(self, drawing_mode: bool) -> None:
        """Изменение режима рисования"""
        self.drawing_mode = drawing_mode

    def set_color(self, color: str):
        """Изменение цвета кисти"""
        self.pen.setColor(QColor(color))

    def set_width(self, width: int):
        """Изменение толщины кисти"""
        self.pen.setWidth(width)

    def set_erase_mode(self, state: bool):
        """Изменение режима ластика"""
        self.erase_mode = state

    def set_pen_mode(self, state: bool):
        """Изменение режима ручки"""
        self.erase_mode = not state

    def disable(self):
        pass

    def info(self) -> dict:
        """Информация для сохранения"""
        ba = QByteArray()
        buff = QBuffer(ba)
        buff.open(QIODevice.OpenModeFlag.WriteOnly) 
        self.pixmap().save(buff, "PNG")
        result = {'content': ba.data(),
                  'size': (self.size().width(), self.size().height()),
                  'coords': self.geometry().getCoords()[:3],
                  'args': str({'fone': self.parent.styleSheet(),
                               'size': str((self.parent.size().width(), self.parent.size().height()))})}
        return result

    def set_content(self, content):
        """Загрузка изображения"""
        ba = QByteArray(content)
        buff = QBuffer(ba)
        buff.open(QIODevice.OpenModeFlag.WriteOnly)
        
        pix = QPixmap()
        pix.loadFromData(ba)
        self.setPixmap(pix)
        

class AddContentButton(QToolButton):
    """класс кнопок с возможностью добавить контент, перетащив их на холст"""
    def __init__(self, *args, is_text=False, is_code=False, is_file=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = True
        self.is_text = is_text
        self.is_code = is_code
        self.is_file = is_file
        
    def mouseMoveEvent(self, e):
        if self.state:
            mimeData = QMimeData()
            mimeData.setParent(self)
            if self.is_text or self.is_code:
                mimeData.setText('')
            drag = QDrag(self)
            drag.setMimeData(mimeData)

            drag.exec(Qt.DropAction.MoveAction)
            
    def setDragMode(self, state):
        """Переключить возможность перетаскивания"""
        self.state = state


class NoteEditor(QMainWindow):
    """Класс редактора заметок"""
    def __init__(self, viewer, *args, note_id=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.note_id = note_id
        self.viewer = viewer
        # настройка окна
        self.setWindowTitle('Note editor')
        self.setGeometry(100, 100, 800, 600)

        # приминение стиля
        self.update_style()
        # создание и настройка основного тулабара ###
        # создание основного тулбара
        main_toolbar = QToolBar('Инструменты')
        self.addToolBar(main_toolbar)
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)

        # действие режима рисования
        self.drawing_mode_action = QAction('Режим рисования', self)
        self.drawing_mode_action.setCheckable(True)
        self.drawing_mode_action.toggled.connect(self.toggle_drawing_mode)
        # дейсвтие создание текстового поля
        self.create_text_action = QAction('Создать текстовое поле', self)
        self.create_text_action.setCheckable(True)
        self.create_text_action.toggled.connect(self.toggle_create_text)
        # действие создание файла
        self.create_file_action = QAction('Добавить файл', self)
        self.create_file_action.setCheckable(True)
        self.create_file_action.toggled.connect(self.add_file)
        # действие создание блока кода
        self.create_code_action = QAction('Добавить код', self)
        self.create_code_action.setCheckable(True)
        self.create_code_action.toggled.connect(self.add_code)
        # действие настройки фона холста
        change_canvas_fone_action = QAction('Изменить фон', self)
        change_canvas_fone_action.triggered.connect(self.change_canvas_fone)
        # действие изменения размера холста
        change_canvas_size_action = QAction('Изменить размер', self)
        change_canvas_size_action.triggered.connect(self.change_canvas_size)
        # действие режима ластика
        self.erase_mode_action = QAction('Ластик', self)
        self.erase_mode_action.setCheckable(True)
        self.erase_mode_action.toggled.connect(self.set_erase_mode)
        # действие режима ручки
        self.pen_mode_action = QAction('Ручка', self)
        self.pen_mode_action.setCheckable(True)
        self.pen_mode_action.toggled.connect(self.set_pen_mode)

        # кнопка сохранения
        save_button = QToolButton(self)
        save_button.setText('Сохранить')
        save_button.clicked.connect(self.save)
        # кнопка переключения режима рисования
        drawing_mode_button = AddContentButton(self)
        drawing_mode_button.setDragMode(False)
        drawing_mode_button.setCheckable(True)
        drawing_mode_button.setText('Рисовать')
        drawing_mode_button.setDefaultAction(self.drawing_mode_action)
        # кнопка создания текстового поля
        create_text_button = AddContentButton(self, is_text=True)
        create_text_button.setCheckable(True)
        create_text_button.setText('Текстовое поле')
        create_text_button.setDefaultAction(self.create_text_action)
        # кнопка добавление файла
        create_file_button = AddContentButton(self, is_file=True)
        create_file_button.setCheckable(True)
        create_file_button.setText('Добавить файл')
        create_file_button.setDefaultAction(self.create_file_action)
        # кнопка создания блока кода
        create_code_button = AddContentButton(self, is_code=True)
        create_code_button.setCheckable(True)
        create_code_button.setText('Код')
        create_code_button.setDefaultAction(self.create_code_action)
        # меню и кнопка настройки холста
        setting_canvas_button = QToolButton(self)
        setting_canvas_button.setText('Настройка холста   ')
        setting_canvas_menu = QMenu(setting_canvas_button)
        setting_canvas_button.setMenu(setting_canvas_menu)
        setting_canvas_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        # добавление действий в меню
        setting_canvas_menu.addAction(change_canvas_fone_action)
        setting_canvas_menu.addAction(change_canvas_size_action)
        # кнопка справки
        help_button = QPushButton(self)
        help_button.setText('Справка')
        help_button.clicked.connect(self.open_help)
        # кнопка настройки
        setting_button = QPushButton(self)
        setting_button.setText('Настройки')
        setting_button.clicked.connect(self.open_setting)
        
        # промежуток
        space = QWidget(self)
        space.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # добавление элементов в main_toolbar
        main_toolbar.addWidget(save_button)
        main_toolbar.addWidget(drawing_mode_button)
        main_toolbar.addWidget(create_text_button)
        main_toolbar.addWidget(create_file_button)
        main_toolbar.addWidget(create_code_button)
        main_toolbar.addWidget(setting_canvas_button)
        main_toolbar.addWidget(space)
        main_toolbar.addWidget(help_button)
        main_toolbar.addWidget(setting_button)
        
        # Создание и настройка paint_toolbar ###
        self.paint_toolbar = QToolBar('Параметры рисования')
        self.addToolBar(self.paint_toolbar)
        
        # отображение текущего цвета
        self.current_color_button = QPushButton(self)
        self.current_color_button.setStyleSheet('background-color: black;')
        self.current_color_button.setMinimumSize(QSize(20, 20))
        self.current_color_button.clicked.connect(self.choose_color)

        # создание палитры
        white_color_button = QPushButton(self)
        white_color_button.clicked.connect(lambda: self.change_color('white'))
        white_color_button.setStyleSheet('background-color: white;')
        black_color_button = QPushButton(self)
        black_color_button.clicked.connect(lambda: self.change_color('black'))
        black_color_button.setStyleSheet('background-color: black;')
        red_color_button = QPushButton(self)
        red_color_button.clicked.connect(lambda: self.change_color('red'))
        red_color_button.setStyleSheet('background-color: red;')
        blue_color_button = QPushButton(self)
        blue_color_button.clicked.connect(lambda: self.change_color('blue'))
        blue_color_button.setStyleSheet('background-color: blue;')
        green_color_button = QPushButton(self)
        green_color_button.clicked.connect(lambda: self.change_color('green'))
        green_color_button.setStyleSheet('background-color: green;')
        
        # кнопка выбора цвета
        choose_color_button = QPushButton(self)
        choose_color_button.setText('Другой цвет')
        choose_color_button.setMinimumSize(QSize(20, 20))
        choose_color_button.clicked.connect(self.choose_color)

        # отображение текущей толщины
        self.current_width_button = QPushButton(self)
        self.current_width_button.setMinimumSize(QSize(20, 20))
        self.current_width_button.setText('◯3')

        # толщина кисти
        width_3_button = QPushButton(self)
        width_3_button.setText('3')
        width_3_button.clicked.connect(lambda: self.change_width(3))
        width_5_button = QPushButton(self)
        width_5_button.setText('5')
        width_5_button.clicked.connect(lambda: self.change_width(5))
        width_7_button = QPushButton(self)
        width_7_button.setText('7')
        width_7_button.clicked.connect(lambda: self.change_width(7))
        width_10_button = QPushButton(self)
        width_10_button.setText('10')
        width_10_button.clicked.connect(lambda: self.change_width(10))
        
        # поле для выбора толжины
        self.choose_width_button = QSpinBox(self)
        self.choose_width_button.valueChanged.connect(self.change_width)

        # кнопка режима ластика
        erase_mode_button = QToolButton(self)
        erase_mode_button.setText('Ластик')
        erase_mode_button.setDefaultAction(self.erase_mode_action)

        # кнопка режима ручки
        pen_mode_button = QToolButton(self)
        pen_mode_button.setText('Ручка')
        pen_mode_button.setDefaultAction(self.pen_mode_action)
        
        # добавление виджетов на тулбар
        self.paint_toolbar.addWidget(self.current_color_button)
        self.paint_toolbar.addWidget(self.current_width_button)
        self.paint_toolbar.addSeparator()
        
        for color_button in (white_color_button, black_color_button, red_color_button,
                             blue_color_button, green_color_button):
            color_button.setMinimumSize(QSize(20, 20))
            self.paint_toolbar.addWidget(color_button)
            
        self.paint_toolbar.addWidget(choose_color_button)
        self.paint_toolbar.addSeparator()
    
        for width_button in (width_3_button, width_5_button, width_7_button, width_10_button):
            width_button.setMinimumSize(QSize(20, 20))
            self.paint_toolbar.addWidget(width_button)
        self.paint_toolbar.addWidget(self.choose_width_button)
        self.paint_toolbar.addSeparator()
        self.paint_toolbar.addWidget(erase_mode_button)
        self.paint_toolbar.addWidget(pen_mode_button)
        
        # Создание и настройка рабочей зоны ###
        scroll_area = QScrollArea(self)
        self.canvas = Canvas(self, objectName='main')
        scroll_area.setWidget(self.canvas)
    
        self.setCentralWidget(scroll_area)

    def update_style(self):
        '''load style from file and apply it'''
        with open('./editorLightStyle.qss') as style:
            style_file = style.read()
            font, current_style, colors_name, *styles, style = style_file.split('\n', 5)
            _font = QFont()
            _font.fromString(font)
            QApplication.instance().setFont(_font)
            self.setStyleSheet(format_style(dict(zip(colors_name.split(), 
                               styles[int(current_style) - 1].split())), style))

    def keyPressEvent(self, e):
        self.canvas.keyPressEvent(e)

    def toggle_drawing_mode(self, state):
        """Переключение режима рисования. Действие self.drawing_mode_action"""
        self.canvas.paint_canvas.set_drawing_mode(state)
        if state:
            self.create_text_action.setChecked(False)
            self.create_file_action.setChecked(False)
            self.create_code_action.setChecked(False)

    def toggle_create_text(self, state):
        """Создание текстового поля. Дейстие create_text_action"""
        self.canvas.set_add_notes_mode(state)
        if state:
            self.drawing_mode_action.setChecked(False)
            self.create_file_action.setChecked(False)
            self.create_code_action.setChecked(False)

    def add_file(self, state):
        """Добавление файла. Действие create_file_action"""
        self.canvas.set_add_files_mode(state)
        if state:
            self.drawing_mode_action.setChecked(False)
            self.create_text_action.setChecked(False)
            self.create_code_action.setChecked(False)

    def add_code(self, state):
        """Добавление блока кода. Действие create_code_action"""
        self.canvas.set_add_codes_mode(state)
        if state:
            self.drawing_mode_action.setChecked(False)
            self.create_text_action.setChecked(False)
            self.create_file_action.setChecked(False)

    def set_cursor(self):
        self.drawing_mode_action.setChecked(False)
        self.create_text_action.setChecked(False)
        self.create_file_action.setChecked(False)
        self.create_code_action.setChecked(False)
            
    def open_setting(self):
        """Открытие окна настроек редактора"""
        style_setting = StyleSettingWindow(self, 'editorLightStyle.qss')
        if style_setting.exec():
            pass

    def open_help(self):
        '''Окно справки'''
        with open('helps/editor.txt', encoding='utf-8') as file:
            help_text = file.read()
        help_window = HelpWindow(help_text, self)
        if help_window.exec():
            pass

    def choose_color(self):
        """Окно для выбора цвета"""
        color_choose_dialog = QColorDialog(self)
        if color_choose_dialog.exec():
            return self.change_color(color_choose_dialog.currentColor().name())

    def change_width(self, value: int):
        """Изменение толщины кисти"""
        self.choose_width_button.setValue(value)
        self.current_width_button.setText(f'◯ {value}')
        self.canvas.paint_canvas.set_width(value)

    def change_color(self, color: str):
        """Изменение толщины кисти"""
        self.current_color_button.setStyleSheet(f'background-color: {color};')
        self.canvas.paint_canvas.set_color(color)

    def change_canvas_fone(self):
        """Изменение фона холста"""
        setting_background = SettingBackground()
        if setting_background.exec():
            if setting_background.has_gradient():
                self.canvas.setStyleSheet("Canvas#main {" + setting_background.get_gradient() + ';}')
            elif setting_background.has_image():
                self.canvas.setStyleSheet("Canvas#main {" + setting_background.get_image() + ';}')
            else:
                self.canvas.setStyleSheet('Canvas#main {' +
                                          f'background-color: {setting_background.get_color().name()}' + ';}')               

    def change_canvas_size(self):
        """Изменение размера холста"""
        size_dialog = SettingSize(self.size())
        if size_dialog.exec():
            size = size_dialog.get_size()
            self.canvas.resize(size)
            self.canvas.paint_canvas.resize(size)

    def set_erase_mode(self, state: bool):
        """Изменение режима ластика"""
        if state:
            self.pen_mode_action.setChecked(False)
        self.canvas.paint_canvas.set_erase_mode(state)

    def set_pen_mode(self, state: bool):
        """Изменение режима ручки"""
        if state:
            self.erase_mode_action.setChecked(False)
        self.canvas.paint_canvas.set_pen_mode(state)

    def save(self):
        """Сохранение заметки"""
        self.viewer.database.clear_note_content(self.note_id)
        for data in self.canvas.layout:
            self.viewer.save_note(type=type(data).__name__, **data.info(), note_id=self.note_id)

    def load_note(self, note_content: list | tuple):
        """Загрузка информации из базы данных"""
        for info in note_content:
            note_id, data_id, type, coords, content, size, args = info
            if type == 'PaintCanvas':
                self.canvas.set_paint_canvas(content)
                self.canvas.set_args(**eval(args))
            elif type == 'NoteLabel':
                note = self.canvas.add_note(QPoint(*eval(coords)), text=content.decode('utf-8'))
                note.resize(QSize(*eval(size)))
            elif type == 'ImageLabel':
                image = self.canvas.add_image(QPoint(*eval(coords)), image=content)
                image.resize(QSize(*eval(size)))
            elif type == 'CodeLabel':
                note = self.canvas.add_code(QPoint(*eval(coords)), text=content.decode('utf-8'))
                note.resize(QSize(*eval(size)))
            elif type == 'File':
                note = self.canvas.add_file(QPoint(*eval(coords)), file='')
                note.set_file(content)
                note.set_args(**eval(args))
        self.canvas.do_layout()
                

def main():
    app = QApplication(argv)
    window = NoteEditor()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
