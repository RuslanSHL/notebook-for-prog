from PyQt6.QtWidgets import QTextEdit, QApplication
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor, QBrush
import sys
import re


def text_format(bc=None, fc=None, bold=False, italic=False):
    '''Создание стиля'''
    format = QTextCharFormat()
    if fc is not None:
        format.setForeground(QBrush(QColor(fc)))
    if bc is not None:
        format.setBackground(QBrush(QColor(bc)))
    if bold:
        format.setFontWeight(QFont.Weight.Bold)
    format.setFontItalic(italic)
    return format


syntax_formats = {
    r'#+.*': text_format(fc='red'),
    r"'.*?'": text_format(fc='green'),
    r'".*?"': text_format(fc='green'),
    r'\b((?<=class)|(?<=def)).*?(?=:|\()': text_format(fc='blue')}

keywords = ['class', 'def', 'if', 'elif', 'else', 'match', 'and', 'or',
            'not', 'in', 'for', 'while', 'try', 'except', 'finally',
            'from', 'import', 'as', 'None', 'True', 'False', 'return']
keywords_syntax = {}
for i in keywords:
    keywords_syntax[r'\b' + i + r'\b'] = text_format(fc='dark orange')

syntax_formats = keywords_syntax | syntax_formats
 

class PythonSyntaxHighlighterInBlockCode(QSyntaxHighlighter):
    def highlightBlock(self, text):
        try:
            for code_text in re.finditer('`.*`', text):
                self.setFormat(code_text.start(), code_text.end() - code_text.start(), text_format(bold=True))
                for pattern, format in syntax_formats.items():
                    format.setFontWeight(QFont.Weight.Bold)
                    for match_ in re.finditer(pattern, text[code_text.start():code_text.end()]):
                        start, end = match_.span()
                        self.setFormat(start, end - start, format)

            self.setCurrentBlockState(0)
            start_index = 0
            end_index = len(text)
            if self.previousBlockState() != 1:
                for block_code in re.finditer(r'```.*', text):
                    self.setFormat(block_code.start(), block_code.end() - block_code.start(), text_format(bold=True))
                    start_index = block_code.start()
                    end_index_ = re.search(r'.*```', text[start_index + 3:])
                    self.setCurrentBlockState(1)
                    if end_index_ is not None:
                        end_index = end_index_.end() + start_index
                        self.setCurrentBlockState(0)
                    for pattern, format in syntax_formats.items():
                        format.setFontWeight(QFont.Weight.Bold)
                        for match_ in re.finditer(pattern, text[start_index + 3:end_index]):
                            start, end = match_.span()
                            self.setFormat(start + start_index + 3, end - start + start_index, format)
            else:
                self.setCurrentBlockState(1)
                end_index_ = re.search(r'.*```', text)
                if end_index_ is not None:
                    end_index = end_index_.end()
                    self.setCurrentBlockState(0)
                self.setFormat(0, end_index, text_format(bold=True))
                for pattern, format in syntax_formats.items():
                    format.setFontWeight(QFont.Weight.Bold)
                    for match_ in re.finditer(pattern, text[start_index:end_index]):
                        start, end = match_.span()
                        self.setFormat(start + start_index, end - start + start_index, format)
        except Exception as e:
            print(e)


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        try:
            for pattern, format in syntax_formats.items():
                for match_ in re.finditer(pattern, text):
                    start, end = match_.span()
                    self.setFormat(start, end - start, format)     
        except Exception as e:
            print(e)


if __name__ == '__main__':          
    app = QApplication(sys.argv)

    window = QTextEdit()
    test = PythonSyntaxHighlighterInBlockCode(window.document())
    window.show()

    app.exec()
