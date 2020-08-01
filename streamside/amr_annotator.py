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

import argparse
import json
import os
from collections import OrderedDict
from typing import List, Dict, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QAction, qApp, QFileDialog, QHBoxLayout, \
    QMessageBox, QGridLayout, QTextEdit, QCompleter, QLineEdit, QDialog, QPushButton, QComboBox, QCheckBox, QPlainTextEdit, QShortcut

from streamside.struct import AMRGraph


class CreateDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.ok = False
        self.btn_ok = QPushButton("OK", self)
        self.btn_ok.clicked.connect(self.button_ok)
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.clicked.connect(self.button_cancel)

    def button_ok(self):
        self.ok = self.sender() == self.btn_ok
        self.close()

    def button_cancel(self):
        self.close()


class ConceptDialog(CreateDialog):
    def __init__(self, parent, name: str, frames: Dict[str, Dict[str, str]]):
        super().__init__(parent)
        layout = QGridLayout()
        self.setMinimumWidth(350)
        self.setWindowTitle('Create a concept')
        self.setLayout(layout)
        self.frames = frames

        # input
        completer = QCompleter(frames.keys())
        completer.setMaxVisibleItems(50)
        self.ledit = QLineEdit()
        self.ledit.setText(name)
        self.ledit.setCompleter(completer)

        layout.addWidget(QLabel('Enter the concept name:'), 0, 0, 1, 3)
        layout.addWidget(self.ledit, 1, 0, 1, 3)

        # buttons
        self.btn_describe = QPushButton("Describe", self)
        self.btn_describe.clicked.connect(self.button_describe)

        # shortcut
        self.sct_describe = QShortcut(QKeySequence('Ctrl+D'), self)
        self.sct_describe.activated.connect(self.button_describe)

        layout.addWidget(self.btn_ok, 2, 0)
        layout.addWidget(self.btn_describe, 2, 1)
        layout.addWidget(self.btn_cancel, 2, 2)

        # description
        self.lb_desc = QPlainTextEdit('Description')
        self.lb_desc.setReadOnly(True)
        layout.addWidget(self.lb_desc, 3, 0, 1, 3)

    def button_describe(self):
        args = self.frames.get(self.ledit.text().strip(), 'No description available')
        self.lb_desc.setPlainText(args)
        self.lb_desc.repaint()

    def exec_(self) -> Optional[str]:
        super().exec_()
        return self.ledit.text().strip() if self.ok else None


class RelationDialog(QDialog):
    def __init__(self, parent, parent_id, concept_ids, labels):
        super().__init__(parent)
        self.setWindowTitle('Create a relation')
        layout = QGridLayout()
        self.setLayout(layout)
        # layout.setAlignment(Qt.AlignLeft)

        # parent
        l = QLabel('Parent: {}'.format(parent_id))
        layout.addWidget(l, 0, 0)

        # children
        w = QWidget()
        l = QHBoxLayout()
        w.setLayout(l)
        self.children = QComboBox()
        self.children.addItems(concept_ids)
        l.addWidget(QLabel('Child:'))
        l.addWidget(self.children)
        layout.addWidget(w, 0, 1)

        # labels
        w = QWidget()
        l = QHBoxLayout()
        w.setLayout(l)
        self.labels = QComboBox()
        self.labels.addItems(labels)
        l.addWidget(QLabel('Label:'))
        l.addWidget(self.labels)
        layout.addWidget(w, 0, 2)

        # referential
        w = QWidget()
        l = QHBoxLayout()
        w.setLayout(l)
        self.ref = QCheckBox()
        l.addWidget(QLabel('Ref:'))
        l.addWidget(self.ref)
        layout.addWidget(w, 0, 3)

        self.ok = False
        self.btn_ok = QPushButton("Ok", self)
        self.btn_ok.clicked.connect(self.button_press)
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.clicked.connect(self.button_press)

        layout.addWidget(self.btn_ok, 1, 0, 1, 2)
        layout.addWidget(self.btn_cancel, 1, 2, 1, 2)

    def button_press(self):
        self.ok = self.sender() == self.btn_ok
        self.close()

    def exec_(self) -> Optional[Tuple[str, str]]:
        super().exec_()
        t = self.children.currentText(), self.labels.currentText(), self.ref.isChecked()
        return t if self.ok else None


class AMRAnnotator(QMainWindow):
    def __init__(self, frames: Dict[str, str], annotator: str = 'unknown'):
        super().__init__()
        layout = self._init_central_layout('AMR Annotator: {}'.format(annotator), 600, 600)

        self.frames = frames
        self.annotator = annotator
        self.filename = None
        self.tid = -1
        self.graphs: List[AMRGraph] = []
        self.lb_tid = QLabel('Index:')
        self.lb_text = QLabel('Open a text or json file to start annotating')
        self.te_graph = QTextEdit()
        self._init_annotation(layout)
        self._init_menubar()

    ########################################  Init  ########################################

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

        w = QWidget()
        l = QHBoxLayout()
        w.setLayout(l)
        w.setContentsMargins(0, 0, 0, 0)
        l.setContentsMargins(0, 0, 0, 0)

        l.addWidget(self.lb_tid, 2)
        l.addWidget(self.lb_text, 98)
        layout.addWidget(w)

        # graph
        self.te_graph.setReadOnly(True)
        layout.addWidget(self.te_graph)

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
        menu = menubar.addMenu('File')
        menu.addAction(action('Open', 'Ctrl+O', self.menu_file_open))
        menu.addAction(action('Save', 'Ctrl+S', self.menu_file_save))
        menu.addSeparator()
        menu.addAction(action('Quit', 'Ctrl+Q', qApp.quit))

        # navigate
        menu = menubar.addMenu('Navigate')
        menu.addAction(action('Previous', 'Ctrl+,', self.menu_navigate_previous))
        menu.addAction(action('Next', 'Ctrl+.', self.menu_navigate_next))
        menu.addAction(action('Goto', 'Ctrl+/', self.menu_navigate_goto))

        # edit
        menu = menubar.addMenu('Edit')
        menu.addAction(action('Concept', 'C', self.menu_create_concept))
        menu.addAction(action('Relation', 'R', self.menu_create_relation))
        menu.addAction(action('Attribute', 'A', self.menu_create_attribute))
        menu.addSeparator()
        menu.addAction(action('Update', 'U', self.menu_update))
        menu.addAction(action('Delete', 'D', self.menu_delete))

    def menu_file_open(self):
        def open_txt(txt_file):
            json_file = '{}{}.json'.format(txt_file[:-3], self.annotator)
            self.filename = json_file

            if os.path.exists(json_file):
                msg = 'Annotation exists for the selected text file. Opening the annotation file instead.'
                message_box(msg, QMessageBox.Ok)
                open_json(json_file)
            else:
                fin = open(txt_file)
                tid = os.path.basename(txt_file)[:-4]
                self.graphs = [AMRGraph(text, '{}.{}'.format(tid, i), self.annotator) for i, text in enumerate(fin)]

        def open_json(json_file):
            # TODO
            self.filename = json_file

        # get filename
        filename = QFileDialog.getOpenFileName(self, 'Open File')[0]
        if not filename: return
        self.menu_file_save()

        # check extension
        if filename[-4:].lower() == '.txt':
            open_txt(filename)
        elif filename[-5:].lower() == '.json':
            open_json(filename)
        else:
            text = 'Unsupported file type:\n{}'.format(os.path.basename(filename))
            message_box(text, QMessageBox.Ok)
            return

        # TODO: check ill-formed file
        # display
        self.setWindowTitle(self.filename)
        self.select_graph(0)

    def menu_file_save(self):
        if not self.filename: return
        # TODO:
        print(self.getWindowTitle())

    def menu_navigate_previous(self):
        print('Previous')

    def menu_navigate_next(self):
        print('Next')

    def menu_navigate_goto(self):
        print('Goto')

    def menu_create_concept(self):
        text = self.lb_text.selectedText().lower()
        begin = self.lb_text.selectionStart()
        end = begin + len(text)
        name = ConceptDialog(self, text, self.frames).exec_()
        if name:
            self.graphs[self.tid].add_concept(name, begin, end)
            self.select_graph(self.tid)

    # TODO: non-recursive selection
    def menu_create_relation(self):
        c = self.te_graph.textCursor()

        # '<span style=\"color:#ff0000;\" >Red Text</span> Black <span style=\"color:#ffff00;\" >Blue Text</span>'

        cids = ['c0', 'c1', 'c2', 'c3']
        labels = ['ARG0', 'ARG1', 'ARG2', 'ARG3', 'ARG4']

        parent_id = c.selectedText()
        t = RelationDialog(self, parent_id, cids, labels).exec_()
        if t:
            self.graphs[self.tid].add_relation(parent_id, *t)
            self.select_graph(self.tid)

    def menu_create_attribute(self):
        print('Attribute')

    def menu_update(self):
        print('Update')

    def menu_delete(self):
        print('Delete')

    ########################################  SETTERS  ########################################

    def select_graph(self, tid: int):
        if 0 <= tid < len(self.graphs):
            self.tid = tid
            graph = self.graphs[tid]
            self.lb_tid.setText('{}:'.format(tid))
            self.lb_text.setText(graph.text)
            self.te_graph.setText('\n'.join(graph.penman_graphs()))

    def get_selected_text(self):
        # TODO: strip white spaces and segmented characters
        return self.lb_text.selectedText()

    def get_frameset_id(self):
        # TODO: suggest the frameset ID
        return self.get_selected_text()

    def handle_sct_start(self):
        s = '(x{} / {}'.format(self.var_id, self.get_frameset_id())
        self.var_id += 1
        self.te_graph.setPlainText(s)

    def handle_btn_click(self):
        print(self.lb_text.selectedText())


def message_box(text: str, icon: int, default_button: int = -1) -> int:
    msg = QMessageBox()
    msg.setText(text)
    msg.setIcon(QMessageBox.Critical)
    msg.setStandardButtons(icon)
    if default_button != -1: msg.setDefaultButton(default_button)
    return msg.exec_()


def main():
    parser = argparse.ArgumentParser(description='StreamSide: AMR Annotator')
    parser.add_argument('-a', '--annotator', type=str, help='annotator ID')
    parser.add_argument('-f', '--frame_file', type=str, default='resources/propbank-amr-frames-arg-descr.json', help='filepath to the JSON file containing frame information')
    args = parser.parse_args()

    frames = json.load(open(args.frame_file), object_pairs_hook=OrderedDict)
    for k, v in frames.items(): frames[k] = '\n'.join(['{}: {}'.format(label, desc) for label, desc in v.items()])
    app = QApplication([])
    gui = AMRAnnotator(frames, args.annotator)
    gui.show()
    app.exec_()


if __name__ == "__main__":
    main()
