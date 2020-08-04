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
import re
from typing import List, Dict, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QTextCursor
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QAction, qApp, QFileDialog, QHBoxLayout, \
    QMessageBox, QGridLayout, QTextEdit, QCompleter, QLineEdit, QDialog, QPushButton, QComboBox, QCheckBox, QPlainTextEdit, QShortcut

from streamside.struct import Graph, Concept


class InputDialog(QDialog):
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


class ConceptDialog(InputDialog):
    def __init__(self, parent, name: str, frames: Dict[str, Dict[str, str]]):
        super().__init__(parent)
        self.setWindowTitle('Create a concept')
        self.setMinimumWidth(350)
        layout = QGridLayout()
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


class GraphAnnotator(QMainWindow):
    def __init__(self, resource_dir: str, annotator: str = 'unknown'):
        super().__init__()

        # primary fields



        # graphical user interface
        layout = self._init_central_widget('StreamSide Graph Annotator: {}'.format(annotator), 600, 600)
        self.annotator = annotator
        self.filename = None
        self.tid = -1
        self.graphs: List[Graph] = []
        self.lb_tid = QLabel('Index:')
        self.lb_text = QLabel('Open a text or json file to start annotating')
        self.te_graph = QTextEdit()
        self._init_annotation(layout)
        self._init_menubar()

        # resources
        self.frames = None
        self.init_resources(resource_dir)

        # constants
        self.COLOR_COVERED_TEXT = 'lightgray'
        self.COLOR_SELECTED_PARENT = 'lightpink'
        self.COLOR_SELECTED_CHILD = 'lightsteelblue'

        # fields
        self.re_concept_id = re.compile(r'^c\d+$')
        self.selected_parent = None
        self.selected_child = None

    ########################################  Init  ########################################

    def _init_central_widget(self, title: str, width: int, height: int) -> QGridLayout:
        widget = QWidget()
        layout = QGridLayout()
        widget.setLayout(layout)

        self.setWindowTitle(title)
        self.setCentralWidget(widget)
        self.setMinimumSize(width, height)

        return layout

    def init_resources(self, resource_dir: str):
        # frames
        frames = json.load(open(os.path.join(resource_dir, 'frames-arg_descriptions.json')))
        for k, v in frames.items(): frames[k] = '\n'.join(['{}: {}'.format(label, desc) for label, desc in sorted(v.items())])
        self.frames = frames
        # TODO: initialize more resources



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

        # edit
        menu = menubar.addMenu('Edit')
        menu.addAction(action('Concept', 'C', self.menu_create_concept))
        menu.addAction(action('Relation', 'R', self.menu_create_relation))
        menu.addAction(action('Attribute', 'A', self.menu_create_attribute))
        menu.addSeparator()
        menu.addAction(action('Update', 'U', self.menu_update))
        menu.addAction(action('Delete', 'D', self.menu_delete))

        # select
        menu = menubar.addMenu('Select')
        menu.addAction(action('Select Parent', '[', self.menu_select_parent))
        menu.addAction(action('Select Child', "]", self.menu_select_child))
        menu.addSeparator()
        menu.addAction(action('Deselect Parent', 'Shift+[', self.menu_deselect_parent))
        menu.addAction(action('Deselect Child', 'Shift+]', self.menu_deselect_child))
        menu.addAction(action('Deselect All', 'Shift+\\', self.menu_deselect_all))

        # navigate
        menu = menubar.addMenu('Navigate')
        menu.addAction(action('Previous', 'Ctrl+,', self.menu_navigate_previous))
        menu.addAction(action('Next', 'Ctrl+.', self.menu_navigate_next))
        menu.addAction(action('Jump to', 'Ctrl+/', self.menu_navigate_goto))

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
                self.graphs = [Graph(text, '{}.{}'.format(tid, i), self.annotator) for i, text in enumerate(fin)]

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
        self.select_graph(self.tid - 1)
        # TODO: init

    def menu_navigate_next(self):
        self.select_graph(self.tid + 1)
        # TODO: init

    def menu_navigate_goto(self):
        print('Jump to')
        # TODO: init

    def menu_create_concept(self):
        text = self.lb_text.selectedText().lower()
        begin = self.lb_text.selectionStart()
        end = begin + len(text)
        name = ConceptDialog(self, text, self.frames).exec_()
        if name:
            self.graphs[self.tid].add_concept(name, begin, end)
            self.refresh_graph()

    # TODO: non-recursive selection
    def menu_create_relation(self):
        c = self.te_graph.textCursor()

        cids = ['c0', 'c1', 'c2', 'c3']
        labels = ['ARG0', 'ARG1', 'ARG2', 'ARG3', 'ARG4']

        parent_id = c.selectedText()
        t = RelationDialog(self, parent_id, cids, labels).exec_()
        if t:
            self.graphs[self.tid].add_relation(parent_id, *t)
            self.refresh_graph()

    def menu_create_attribute(self):
        print('Attribute')

    def menu_update(self):
        print('Update')

    def menu_delete(self):
        print('Delete')

    def menu_select_parent(self):
        con = self.selected_concept()
        if con is not None:
            self.selected_parent = con
            self.refresh_graph()

    def menu_select_child(self):
        con = self.selected_concept()
        if con is not None:
            self.selected_child = con
            self.refresh_graph()

    def menu_deselect_parent(self):
        self.selected_parent = None
        self.refresh_graph()

    def menu_deselect_child(self):
        self.selected_child = None
        self.refresh_graph()

    def menu_deselect_all(self):
        self.menu_deselect_parent()
        self.menu_deselect_child()

    ########################################  SETTERS  ########################################

    def display_text(self, graph: Graph):
        def color(cid):
            if self.selected_parent and cid == self.selected_parent.name:
                return self.COLOR_SELECTED_PARENT
            if self.selected_child and cid == self.selected_child.name:
                return self.COLOR_SELECTED_CHILD
            return self.COLOR_COVERED_TEXT

        begin = 0
        tt = []

        for cid, con in sorted(graph.concepts.items(), key=lambda t: t[1].begin):
            if con.begin < 0 or con.end < 0: continue
            tt.append(graph.text[begin:con.begin])
            tt.append('<span style="background-color:{};">'.format(color(cid)))
            tt.append(graph.text[con.begin:con.end])
            tt.append('</span>')
            begin = con.end

        tt.append(graph.text[begin:len(graph.text)])
        self.lb_text.setText(''.join(tt))

    def display_graph(self, graph: Graph):
        def set_color(c, color):
            if c is None: return
            cursor = self.te_graph.textCursor()
            cursor.setPosition(c.begin, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(c.name))
            cursor.insertHtml('<span style="background-color:{};">{}</span>'.format(color, c.name))

        self.te_graph.setText('\n'.join(graph.penman_graphs()))
        set_color(self.selected_parent, self.COLOR_SELECTED_PARENT)
        set_color(self.selected_child, self.COLOR_SELECTED_CHILD)

    def select_graph(self, tid: int):
        if 0 <= tid < len(self.graphs):
            self.tid = tid
            graph = self.graphs[tid]
            self.lb_tid.setText('{}:'.format(tid))
            self.display_text(graph)
            self.display_graph(graph)
            self.te_graph.repaint()

    def refresh_graph(self):
        self.select_graph(self.tid)

    def selected_concept(self) -> Optional[Concept]:
        cursor = self.te_graph.textCursor()
        cid = cursor.selectedText()
        if self.re_concept_id.match(cid):
            begin = cursor.selectionStart()
            end = begin + len(cid)
            return Concept(cid, begin, end)
        return None

    def get_selected_text(self):
        # TODO: strip white spaces and segmented characters
        return self.lb_text.selectedText()

    def get_frameset_id(self):
        # TODO: suggest the frameset ID
        return self.get_selected_text()


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
    parser.add_argument('-r', '--resources', type=str, default='resources/amr', help='path to the directory containing resource files')
    args = parser.parse_args()

    app = QApplication([])
    gui = GraphAnnotator(args.resources, args.annotator)
    gui.show()
    app.exec_()


if __name__ == "__main__":
    main()
