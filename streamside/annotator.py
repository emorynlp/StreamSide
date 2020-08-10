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
from typing import List, Dict, Optional, Tuple, Callable, Set

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QTextCursor
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QAction, qApp, QFileDialog, QHBoxLayout, \
    QMessageBox, QGridLayout, QTextEdit, QCompleter, QLineEdit, QDialog, QPushButton, QComboBox, QCheckBox, QPlainTextEdit, QShortcut, QStatusBar

from streamside.struct import Graph, OffsetMap, Offset


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
    def __init__(self, parent, name: str):
        super().__init__(parent)
        self.setWindowTitle('Create a concept')
        self.setMinimumWidth(350)
        layout = QGridLayout()
        self.setLayout(layout)
        self.concept_desc = parent.concept_desc

        # input
        completer = QCompleter(parent.concept_list)
        completer.setMaxVisibleItems(50)
        self.le_name = QLineEdit()
        self.le_name.setText(name)
        self.le_name.setCompleter(completer)

        layout.addWidget(QLabel('Enter the concept name:'), 0, 0, 1, 3)
        layout.addWidget(self.le_name, 1, 0, 1, 3)

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
        args = self.frames.get(self.le_name.text().strip(), 'No description available')
        self.lb_desc.setPlainText(args)
        self.lb_desc.repaint()

    def exec_(self) -> Optional[str]:
        super().exec_()
        return self.le_name.text().strip() if self.ok else None


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


class Annotator(QMainWindow):
    def __init__(self, resource_dir: str, annotator: str = 'unknown'):
        super().__init__()

        # resources
        self.concept_desc: Dict[str, str] = dict()
        self.concept_list: List[str] = []
        self.relation_list: List[str] = []
        self.init_resources(resource_dir)

        # fields
        self.annotator: str = annotator
        self.filename: str = ''
        self.tid: int = -1
        self.graphs: List[Graph] = []
        self.offset_maps: List[OffsetMap] = []
        self.selected_parent: Optional[Tuple[Set[int], Offset]] = None
        self.selected_child: Optional[Tuple[Set[int], Offset]] = None
        self.selected_text_spans: Set[int] = set()

        # constants
        self.RE_CONCEPT_ID = re.compile(r'^c\d+$')
        self.COLOR_COVERED_TOKEN = 'lightgray'
        self.COLOR_SELECTED_PARENT = 'lightpink'
        self.COLOR_SELECTED_CHILD = 'lightsteelblue'
        self.COLOR_COVERED_TEXT_SPAN = 'khaki'

        # graphical user interface
        layout = self._init_central_widget('StreamSide Graph Annotator: {}'.format(annotator), 600, 600)
        self.lb_tid = QLabel('Index:')
        self.lb_text = QLabel('Open a text or json file to start annotating')
        self.te_graph = QTextEdit()
        self.statusbar = self._init_statusbar()
        self._init_annotation(layout)
        self._init_menubar()

    ########################################  Properties  ########################################

    @property
    def current_graph(self) -> Optional[Graph]:
        return self.graphs[self.tid] if 0 <= self.tid < len(self.graphs) else None

    @property
    def current_offset_map(self) -> Optional[OffsetMap]:
        return self.offset_maps[self.tid] if 0 <= self.tid < len(self.offset_maps) else None

    ########################################  Init  ########################################

    def init_resources(self, resource_dir: str):
        # concepts
        self.concept_desc = json.load(open(os.path.join(resource_dir, 'concept-desc.json')))
        self.concept_list = sorted(self.concept_desc.keys())

        # TODO: initialize relations

    def _init_central_widget(self, title: str, width: int, height: int) -> QGridLayout:
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

    def _init_statusbar(self) -> QStatusBar:
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        return statusbar

    def _init_menubar(self):
        def action(name: str, shortcut: str, handler: Callable[[], None]):
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
        menu.addAction(action('Create Concept', 'C', self.menu_create_concept))
        menu.addAction(action('Create Relation', 'R', self.menu_create_relation))
        menu.addAction(action('Create Attribute', 'A', self.menu_create_attribute))
        menu.addSeparator()
        menu.addAction(action('Update', 'U', self.menu_update))
        menu.addAction(action('Delete', 'D', self.menu_delete))

        # select
        menu = menubar.addMenu('&Select')
        menu.addAction(action('Select Parent', '[', self.menu_select_parent))
        menu.addAction(action('Select Child', "]", self.menu_select_child))
        menu.addAction(action('Select Span', 'v', self.menu_select_span))
        menu.addSeparator()
        menu.addAction(action('Deselect Parent', 'Shift+[', self.menu_deselect_parent))
        menu.addAction(action('Deselect Child', 'Shift+]', self.menu_deselect_child))
        menu.addAction(action('Deselect Span', 'Shift+v', self.menu_deselect_span))

        # navigate
        menu = menubar.addMenu('Navigate')
        menu.addAction(action('Previous', 'Ctrl+,', self.menu_navigate_previous))
        menu.addAction(action('Next', 'Ctrl+.', self.menu_navigate_next))
        menu.addAction(action('Jump to', 'Ctrl+/', self.menu_navigate_goto))

    ####################  Menubar: File  ####################

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
                self.filename = json_file

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
            self.statusbar.showMessage('Create {}'.format(self.filename))
        elif filename[-5:].lower() == '.json':
            open_json(filename)
            self.statusbar.showMessage('Open {}'.format(self.filename))
        else:
            self.statusbar.showMessage('Cannot open "{}" - unsupported file type'.format(os.path.basename(filename)))
            # message_box(text, QMessageBox.Ok)
            return

        # initialize
        self.offset_maps = [OffsetMap(graph.tokens) for i, graph in enumerate(self.graphs)]
        self.setWindowTitle(os.path.basename(self.filename))
        self.select_annotation(0)

    def menu_file_save(self):
        if not self.filename: return
        # TODO:
        print(self.getWindowTitle())

    ####################  Menubar: Edit  ####################

    def menu_create_concept(self):
        self.menu_select_span()
        if not self.selected_text_spans: return

        graph = self.current_graph
        tokens = graph.get_tokens(self.selected_text_spans)
        text = ' '.join(tokens).lower()
        name = ConceptDialog(self, text).exec_()

        if name:
            graph.add_concept(name, self.selected_text_spans)
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

    ####################  Menubar: Select  ####################

    def menu_select_parent(self):
        # TODO:
        con = self.concept_selected_in_graph()
        if con:
            self.selected_parent = con
            self.refresh_graph()

    def menu_deselect_parent(self):
        # TODO:
        self.selected_parent = None
        self.refresh_graph()

    def menu_select_child(self):
        # TODO:
        con = self.concept_selected_in_graph()
        if con:
            self.selected_child = con
            self.refresh_graph()

    def menu_deselect_parent_child(self):
        # TODO:
        self.menu_deselect_parent()
        self.menu_deselect_child()

    def menu_deselect_child(self):
        # TODO:
        self.selected_child = None
        self.refresh_graph()

    def menu_select_span(self):
        offset = self.selected_text_offset()
        if offset is None:
            self.statusbar.showMessage('No text span is highlighted')
            return None

        token_ids = self.current_offset_map.token_ids(offset) - self.current_graph.covered_token_ids
        if not token_ids:
            self.statusbar.showMessage('Cannot select text spans that are already concepts')
            return None

        self.selected_text_spans.update(token_ids)
        self.refresh_text()

        tokens = self.current_graph.get_tokens(token_ids)
        self.statusbar.showMessage('Select "{}"'.format(' '.join(tokens)))

    def menu_deselect_span(self):
        offset = self.selected_text_offset()
        if offset is None:
            self.statusbar.showMessage('No text span is highlighted')
            return

        token_ids = self.current_offset_map.token_ids(offset)
        inter = self.selected_text_spans.intersection(token_ids)
        if inter:
            self.selected_text_spans -= inter
            self.refresh_text()
            tokens = self.current_graph.get_tokens(inter)
            self.statusbar.showMessage('Deselect {}'.format(str(tokens)))
        else:
            self.statusbar.showMessage('No selected text span is i highlighted')

    ####################  Menubar: Navigate  ####################

    def menu_navigate_previous(self):
        self.select_annotation(self.tid - 1)
        # TODO: init

    def menu_navigate_next(self):
        self.select_annotation(self.tid + 1)
        # TODO: init

    def menu_navigate_goto(self):
        print('Jump to')
        # TODO: init

    ########################################  Text & Graph  ########################################

    def select_annotation(self, tid: int):
        if 0 <= tid < len(self.graphs):
            self.tid = tid
            self.lb_tid.setText('{}:'.format(tid))
            self.refresh_text()
            self.refresh_graph()

    def refresh_text(self):
        def color(token_id: int):
            if self.selected_parent and token_id in self.selected_parent[0]:
                return self.COLOR_SELECTED_PARENT
            if self.selected_child and token_id in self.selected_child[0]:
                return self.COLOR_SELECTED_CHILD
            if token_id in self.selected_text_spans:
                return self.COLOR_COVERED_TEXT_SPAN
            if token_id in graph.covered_token_ids:
                return self.COLOR_COVERED_TOKEN
            return None

        graph = self.current_graph
        tt = []

        for i, token in enumerate(graph.tokens):
            c = color(i)
            if c:
                tt.append('<span style="background-color:{};">'.format(c))
                tt.append(token)
                tt.append('</span>')
            else:
                tt.append(token)
            if i + 1 < len(graph.tokens):
                tt.append(' ')

        self.lb_text.setText(''.join(tt))

    def refresh_graph(self):
        graph = self.current_graph

        def set_color(c, color):
            if c is None: return
            cursor = self.te_graph.textCursor()
            cursor.setPosition(c.begin, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(c.name))
            cursor.insertHtml('<span style="background-color:{};">{}</span>'.format(color, c.name))

        self.te_graph.setText('\n'.join(graph.penman_graphs()))
        set_color(self.selected_parent, self.COLOR_SELECTED_PARENT)
        set_color(self.selected_child, self.COLOR_SELECTED_CHILD)
        self.te_graph.repaint()

    def concept_selected_in_graph(self) -> Optional[Tuple[str, int, int]]:
        cursor = self.te_graph.textCursor()
        cid = cursor.selectedText()
        if self.RE_CONCEPT_ID.match(cid):
            begin = cursor.selectionStart()
            end = begin + len(cid)
            return cid, begin, end
        return None

    def selected_text_offset(self) -> Optional[Offset]:
        """
        :return: the offset if valid; otherwise, None.
        """
        text = self.lb_text.selectedText()
        begin = self.lb_text.selectionStart()
        end = begin + len(text)
        return Offset(begin, end) if text else None


def message_box(text: str, icon: int, default_button: int = -1) -> int:
    msg = QMessageBox()
    msg.setText(text)
    msg.setIcon(QMessageBox.Critical)
    msg.setStandardButtons(icon)
    if default_button != -1: msg.setDefaultButton(default_button)
    return msg.exec_()


def overlap(offset1: List[int], offset2: List[int]):
    # TODO: check if overlaps
    pass


def main():
    parser = argparse.ArgumentParser(description='StreamSide: AMR Annotator')
    parser.add_argument('-a', '--annotator', type=str, help='annotator ID')
    parser.add_argument('-r', '--resources', type=str, default='resources/lexica', help='path to the directory containing resource files')
    args = parser.parse_args()

    app = QApplication([])
    gui = Annotator(args.resources, args.annotator)
    gui.show()
    app.exec_()


if __name__ == "__main__":
    main()
