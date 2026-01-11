from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PyQt6.QtCore import Qt
import pygments
from pygments import lexers, styles
from pygments.formatter import Formatter

class PygmentsHighlighter(QSyntaxHighlighter):
    def __init__(self, document, lexer_name='python', style_name='default'):
        super().__init__(document)
        self._lexer = lexers.get_lexer_by_name(lexer_name)
        self._style = styles.get_style_by_name(style_name)
        self._formatter = QFormatter(style=self._style)

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        # This is a simplified approach. Pygments tokenizes the whole string usually.
        # For huge files, we should use a more incremental approach or QScintilla.
        # But for QSyntaxHighlighter, we iterate over tokens in the block.
        # Note: highlighting line by line with pygments lexers might lose state (like multiline strings),
        # but it's the standard way to integrate with QSyntaxHighlighter for simple use cases.
        
        try:
            tokens = pygments.lex(text, self._lexer)
            index = 0
            for token, value in tokens:
                length = len(value)
                format = self._formatter.get_format(token)
                if format:
                    self.setFormat(index, length, format)
                index += length
        except Exception:
            pass # Fail gracefully

class QFormatter(Formatter):
    def __init__(self, style):
        super().__init__(style=style)
        self.data = {}
        self._cache = {}
        for token, style in self.style:
            format = QTextCharFormat()
            if style['color']:
                format.setForeground(QColor(f"#{style['color']}"))
            if style['bgcolor']:
                format.setBackground(QColor(f"#{style['bgcolor']}"))
            if style['bold']:
                format.setFontWeight(QFont.Weight.Bold)
            if style['italic']:
                format.setFontItalic(True)
            if style['underline']:
                format.setFontUnderline(True)
            self.data[token] = format

    def get_format(self, token):
        if token in self._cache:
            return self._cache[token]
            
        # Pygments returns specific token types, we need to walk up the hierarchy
        # to find a matching style if exact match fails
        orig_token = token
        while token.parent:
            if token in self.data:
                res = self.data[token]
                self._cache[orig_token] = res
                return res
            token = token.parent
        
        res = self.data.get(token, None)
        self._cache[orig_token] = res
        return res

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Consolas", 10))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._highlighter = PygmentsHighlighter(self.document())

    def set_language(self, lang):
        # Update highlighter lexer
        try:
            self._highlighter = PygmentsHighlighter(self.document(), lexer_name=lang)
            self.rehighlight()
        except:
            pass # Fallback to default/previous

    def rehighlight(self):
        self._highlighter.rehighlight()

    def goto_line(self, lineno):
        if lineno < 1: return
        block = self.document().findBlockByNumber(lineno - 1)
        cursor = self.textCursor()
        cursor.setPosition(block.position())
        self.setTextCursor(cursor)
        self.centerCursor()
