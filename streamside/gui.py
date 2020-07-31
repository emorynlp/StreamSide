#  Copyright 2020 Emory University
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

__author__ = 'Jinho D. Choi'

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QAction, qApp, QFileDialog, QHBoxLayout, \
    QMessageBox, QGridLayout, QTextEdit, QScrollArea


class StreamSide(QMainWindow):
    def __init__(self, annotator: str = 'unknown'):
        super().__init__()
        layout = self._init_central_layout('StreamSide: {}'.format(annotator), 600, 600)

        # annotation
        self.annoator = annotator
        self.filename = None
        self.tid = -1
        self.amrs = []
        self.lb_tid = QLabel('?:')
        self.lb_text = QLabel('Open a text file to start annotating')
        self.te_amrs = QTextEdit()
        self._init_annotation(layout)

        # "<span style=\"color:#ff0000;\" >Red Text</span> Black <span style=\"color:#ffff00;\" >Blue Text</span>"

        # menu
        self._init_menubar()

        # # shortcuts
        # self.sct_predictate = QShortcut(QKeySequence('p'), self)
        # self.sct_predictate.activated.connect(self.handle_sct_start)

        # # auto complete options
        # names = ["Apple", "Alps", "Berry", "Cherry"]
        # completer = QCompleter(names)
        #
        # # create line edit and add auto complete
        # self.lineedit = QLineEdit()
        # self.lineedit.setCompleter(completer)
        # layout.addWidget(self.lineedit)

    ########################################  Initializers  ########################################

    def _init_central_layout(self, title: str, width: int, height: int) -> QGridLayout:
        widget = QWidget()
        layout = QGridLayout()
        widget.setLayout(layout)

        self.setWindowTitle(title)
        self.setCentralWidget(widget)
        self.setMinimumSize(width, height)

        return layout

    def _init_annotation(self, layout: QGridLayout):
        # text
        self.lb_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lb_text.setWordWrap(True)

        s = QScrollArea()
        s.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        s.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        s.setFixedHeight(100)
        s.setWidget(self.lb_text)
        s.setContentsMargins(0, 0, 0, 0)

        w = QWidget()
        l = QHBoxLayout()
        w.setLayout(l)
        w.setContentsMargins(0, 0, 0, 0)
        l.setContentsMargins(0, 0, 0, 0)

        l.addWidget(self.lb_tid, 2)
        l.addWidget(self.lb_text, 98)
        layout.addWidget(w)

        # graph
        self.te_amrs.setReadOnly(True)
        layout.addWidget(self.te_amrs)

    ########################################  Menubar  ########################################

    def _init_menubar(self):
        def action(name, shortcut, handler):
            act = QAction(name, self)
            act.setShortcut(shortcut)
            act.triggered.connect(handler)
            return act

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        # file
        menu = menubar.addMenu('&File')
        menu.addAction(action('&Open', 'Ctrl+O', self._menu_file_open))
        menu.addAction(action('&Save', 'Ctrl+S', self._menu_file_save))
        menu.addSeparator()
        menu.addAction(action('&Quit', 'Ctrl+Q', qApp.quit))

        # navigate
        menu = menubar.addMenu('&Navigate')
        menu.addAction(action('&Previous', 'Ctrl+,', self._menu_navigate_previous))
        menu.addAction(action('&Next', 'Ctrl+.', self._menu_navigate_next))

    def _menu_file_open(self):
        def open_txt(txt_file: str):
            amr_file = '{}{}.amr'.format(txt_file[:-3], self.annoator)

            if os.path.exists(amr_file):
                msg = 'Annotation exists for the selected text file. Opening the annotation file instead.'
                message_box(msg, QMessageBox.Ok)
            else:
                fin = open(txt_file)
                self.amrs = [line for line in fin]

        def open_amr(amr_file: str):
            # TODO
            self.setWindowTitle(filename)
            self.filename = filename

            self.te_amrs.setPlainText("")
            self.set_text(0)

        # get filename
        filename = QFileDialog.getOpenFileName(self, 'Open File')[0]
        if not filename: return
        self._menu_file_save()

        # check extension
        # TODO: only extensions in lowercase are supported
        if filename.endswith('.txt'):
            open_txt(filename)
        elif filename.endswith('.json'):
            open_amr(filename)
        else:
            text = 'Unsupported file type:\n{}'.format(os.path.basename(filename))
            message_box(text, QMessageBox.Ok)

    def _menu_file_save(self):
        if not self.filename: return
        # TODO:
        print(self.getWindowTitle())

    def _menu_navigate_previous(self):
        print('Previous')

    def _menu_navigate_next(self):
        print('Next')

    ########################################  SETTERS  ########################################

    def set_text(self, gid):
        if 0 <= gid < len(self.amrs):
            self.tid = gid
            self.lb_tid.setText('{}:'.format(gid))
            self.lb_text.setText(self.amrs[gid])

    def get_selected_text(self):
        # TODO: strip white spaces and segmented characters
        return self.lb_text.selectedText()

    def get_frameset_id(self):
        # TODO: suggest the frameset ID
        return self.get_selected_text()

    def handle_sct_start(self):
        s = '(x{} / {}'.format(self.var_id, self.get_frameset_id())
        self.var_id += 1
        self.te_amrs.setPlainText(s)

    def handle_btn_click(self):
        print(self.lb_text.selectedText())


def message_box(text: str, icon: int, default_button: int = -1) -> int:
    msg = QMessageBox()
    msg.setText(text)
    msg.setIcon(QMessageBox.Critical)
    msg.setStandardButtons(icon)
    if default_button != -1: msg.setDefaultButton(default_button)
    return msg.exec_()


if __name__ == "__main__":
    annotator = sys.argv[1] if len(sys.argv) > 1 else 'unknown'
    app = QApplication([])
    gui = StreamSide(annotator)
    gui.show()
    app.exec_()
