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
from PyQt5.QtGui import QKeySequence, QTextCursor, QTextCharFormat
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QAction, qApp, QFileDialog, QHBoxLayout, \
    QMessageBox, QGridLayout, QTextEdit, QCompleter, QLineEdit, QDialog, QPushButton, QCheckBox, QPlainTextEdit, QShortcut, QStatusBar

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
        self.concept_dict = parent.concept_dict

        # input name
        completer = QCompleter(parent.concept_list)
        completer.setMaxVisibleItems(50)
        self.le_name = QLineEdit()
        self.le_name.setText(name)
        self.le_name.setCompleter(completer)

        layout.addWidget(QLabel('Enter the concept name:'), 0, 0, 1, 3)
        layout.addWidget(self.le_name, 1, 0, 1, 2)

        # check attribute
        w = QWidget()
        l = QHBoxLayout()
        w.setLayout(l)
        self.attribute = QCheckBox()
        l.addWidget(self.attribute)
        l.addWidget(QLabel('Attribute'))
        layout.addWidget(w, 1, 2)

        # buttons
        self.btn_describe = QPushButton("Describe", self)
        self.btn_describe.clicked.connect(self.button_describe)
        layout.addWidget(self.btn_ok, 2, 0)
        layout.addWidget(self.btn_describe, 2, 1)
        layout.addWidget(self.btn_cancel, 2, 2)

        # shortcut
        self.sct_describe = QShortcut(QKeySequence('Ctrl+D'), self)
        self.sct_describe.activated.connect(self.button_describe)

        self.sct_attribute = QShortcut(QKeySequence('Ctrl+R'), self)
        self.sct_attribute.activated.connect(self.check_attribute)

        # description
        self.lb_desc = QPlainTextEdit('Description')
        self.lb_desc.setReadOnly(True)
        layout.addWidget(self.lb_desc, 3, 0, 1, 3)

    def button_describe(self):
        v = self.concept_dict.get(self.le_name.text().strip(), None)
        text = v['description'] if v else 'No description available'
        self.lb_desc.setPlainText(text)
        self.lb_desc.repaint()

    def check_attribute(self):
        self.attribute.setChecked(not self.attribute.isChecked())

    def exec_(self) -> Optional[Tuple[str, bool]]:
        super().exec_()
        return (self.le_name.text().strip(), self.attribute.isChecked()) if self.ok else None


class RelationDialog(InputDialog):
    def __init__(self, parent, parent_desc: str, child_desc: str):
        super().__init__(parent)
        self.setWindowTitle('Create a relation')
        self.setMinimumWidth(350)
        layout = QGridLayout()
        self.setLayout(layout)
        self.relation_dict = parent.relation_dict

        # parent/child descriptions
        layout.addWidget(QLabel('Parent: {}'.format(parent_desc)), 0, 0, 1, 3)
        layout.addWidget(QLabel('Child: {}'.format(child_desc)), 1, 0, 1, 2)

        # input role
        completer = QCompleter(parent.relation_list)
        completer.setMaxVisibleItems(50)
        self.le_role = QLineEdit()
        self.le_role.setCompleter(completer)
        layout.addWidget(self.le_role, 2, 0, 1, 2)

        # check referent/inverse
        w = QWidget()
        l = QGridLayout()
        l.setContentsMargins(0, 0, 0, 0)
        w.setLayout(l)

        self.referent = QCheckBox()
        l.addWidget(self.referent, 0, 0)
        l.addWidget(QLabel('Referent'), 0, 1)

        self.inverse = QCheckBox()
        l.addWidget(self.inverse, 1, 0)
        l.addWidget(QLabel('Inverse'), 1, 1)
        layout.addWidget(w, 1, 2, 2, 1)

        # buttons
        self.btn_describe = QPushButton("Describe", self)
        self.btn_describe.clicked.connect(self.button_describe)
        layout.addWidget(self.btn_ok, 3, 0)
        layout.addWidget(self.btn_describe, 3, 1)
        layout.addWidget(self.btn_cancel, 3, 2)

        # shortcut
        self.sct_describe = QShortcut(QKeySequence('Ctrl+D'), self)
        self.sct_describe.activated.connect(self.button_describe)
        self.sct_referent = QShortcut(QKeySequence('Ctrl+R'), self)
        self.sct_referent.activated.connect(self.check_referent)
        self.sct_inverse = QShortcut(QKeySequence('Ctrl+F'), self)
        self.sct_inverse.activated.connect(self.check_inverse)

        # description
        self.lb_desc = QPlainTextEdit('Description')
        self.lb_desc.setReadOnly(True)
        layout.addWidget(self.lb_desc, 4, 0, 1, 3)

    def button_describe(self):
        v = self.relation_dict.get(self.le_role.text().strip(), None)
        text = v['description'] if v else 'No description available'
        self.lb_desc.setPlainText(text)
        self.lb_desc.repaint()

    def check_referent(self):
        self.referent.setChecked(not self.referent.isChecked())

    def check_inverse(self):
        self.inverse.setChecked(not self.inverse.isChecked())

    def exec_(self) -> Optional[Tuple[str, bool]]:
        super().exec_()
        if self.ok:
            label = self.le_role.text().strip()
            if self.inverse.isChecked(): label += '-of'
            return label, self.referent.isChecked()
        else:
            return None


class Annotator(QMainWindow):
    def __init__(self, resource_dir: str, annotator: str = 'unknown'):
        super().__init__()

        # resources
        self.concept_dict: Dict[str, str] = dict()
        self.concept_list: List[str] = []
        self.relation_dict: Dict[str, str] = dict()
        self.relation_list: List[str] = []
        self.init_resources(resource_dir)

        # fields
        self.annotator: str = annotator
        self.filename: str = ''
        self.tid: int = -1
        self.graphs: List[Graph] = []
        self.offset_maps: List[OffsetMap] = []
        self.selected_parent: Optional[Tuple[str, int]] = None
        self.selected_child: Optional[Tuple[str, int]] = None
        self.selected_text_spans: Set[int] = set()

        # constants
        self.RE_CONCEPT_ID = re.compile(r'^c\d+$')
        self.COLOR_COVERED_TOKEN = 'lightgray'
        self.COLOR_SELECTED_PARENT = 'lightpink'
        self.COLOR_SELECTED_CHILD = 'lightgreen'
        self.COLOR_COVERED_TEXT_SPAN = 'khaki'

        # graphical user interface
        layout = self._init_central_widget('StreamSide WISeN Annotator: {}'.format(annotator), 600, 600)
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
        self.concept_dict = json.load(open(os.path.join(resource_dir, 'concepts.json')))
        self.concept_list = sorted(self.concept_dict.keys())
        self.relation_dict = json.load(open(os.path.join(resource_dir, 'relations.json')))
        self.relation_list = sorted(self.relation_dict.keys())

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
        menu.addSeparator()
        menu.addAction(action('Update', 'U', self.menu_update))
        menu.addAction(action('Delete', 'D', self.menu_delete))

        # select
        menu = menubar.addMenu('&Select')
        menu.addAction(action('Select Text Span', 'x', self.menu_select_text_span))
        menu.addAction(action('Select Parent ID', 'w', self.menu_select_parent))
        menu.addAction(action('Select Child ID', "e", self.menu_select_child))
        menu.addSeparator()
        menu.addAction(action('Deselect Text Span', 'Shift+x', self.menu_deselect_text_span))
        menu.addAction(action('Deselect Parent ID', 'Shift+w', self.menu_deselect_parent))
        menu.addAction(action('Deselect Child ID', 'Shift+e', self.menu_deselect_child))

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
            self.filename = json_file
            with open(self.filename) as fin:
                graphs = json.load(fin)
                self.graphs = [Graph.factory(graph) for graph in graphs]

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
            self.statusbar.showMessage('Unsupported file type: {}'.format(os.path.basename(filename)))
            return

        # initialize
        self.statusbar.showMessage('Open: {}'.format(self.filename))
        self.offset_maps = [OffsetMap(graph.tokens) for i, graph in enumerate(self.graphs)]
        self.setWindowTitle(os.path.basename(self.filename))
        self.select_annotation(0)

    def menu_file_save(self):
        if not self.filename:
            self.statusbar.showMessage('Output file is not specified.')
            return

        with open(self.filename, 'w') as fout:
            d = [graph.json_dumps() for graph in self.graphs]
            fout.write('[\n{}\n]\n'.format(',\n'.join(d)))

        self.statusbar.showMessage('Save: {}'.format(self.filename))

    ####################  Menubar: Edit  ####################

    def menu_create_concept(self):
        self.menu_select_text_span()
        graph = self.current_graph
        tokens = graph.get_tokens(self.selected_text_spans)
        text = '_'.join(tokens).lower()
        t = ConceptDialog(self, text).exec_()

        if t:
            name = t[0]
            attr = t[1]
            cid = graph.add_concept(name, self.selected_text_spans, attr)
            self.selected_text_spans.clear()
            self.refresh_annotation()
            self.statusbar.showMessage('Concept created: ({} / {}) - {}'.format(cid, name, str(tokens)))
        else:
            self.statusbar.showMessage('Concept creation is cancelled.')

    def menu_create_relation(self):
        if self.selected_parent is None:
            self.statusbar.showMessage('Parent ID is not selected.')
            return

        if self.selected_child is None:
            self.statusbar.showMessage('Child ID is not selected.')
            return

        graph = self.current_graph
        parent_id = self.selected_parent[0]
        child_id = self.selected_child[0]
        parent_concept = graph.get_concept(parent_id)
        child_concept = graph.get_concept(child_id)
        parent_desc = '({} / {})'.format(parent_id, parent_concept.name)
        child_desc = '({} / {})'.format(child_id, child_concept.name)

        t = RelationDialog(self, parent_desc, child_desc).exec_()
        if t:
            label = t[0]
            referent = t[1]
            graph.add_relation(parent_id, child_id, label, referent)
            self.selected_parent = self.selected_parent[0], None
            self.selected_child = None
            self.refresh_annotation()
            self.statusbar.showMessage('Relation created: {}({}, {})'.format(label, parent_id, child_id))
        else:
            self.statusbar.showMessage('Relation creation is cancelled.')

    def menu_update(self):
        print('Update')

    def menu_delete(self):
        print('Delete')

    ####################  Menubar: Select  ####################

    def menu_select_concept_in_graph(self, pctype):
        selection = self.selected_concept_in_graph()
        if selection is None:
            self.statusbar.showMessage('No valid concept ID is highlighted')
            return

        cid = selection[0]

        if pctype == 'p':
            if self.selected_parent and cid == self.selected_parent[0]: return
            if self.selected_child and cid == self.selected_child[0]: self.selected_child = None
            self.selected_parent = selection
            pc = 'parent'
        else:
            if self.selected_child and cid == self.selected_child[0]: return
            if self.selected_parent and cid == self.selected_parent[0]: self.selected_parent = None
            self.selected_child = selection
            pc = 'child'

        self.statusbar.showMessage('Select {}: {}'.format(pc, cid))
        self.refresh_annotation()

    def menu_select_parent(self):
        self.menu_select_concept_in_graph('p')

    def menu_select_child(self):
        self.menu_select_concept_in_graph('c')

    def menu_deselect_parent(self):
        if self.selected_parent:
            self.statusbar.showMessage('Deselect parent: {}'.format(self.selected_parent[0]))
            self.selected_parent = None
            self.refresh_annotation()
        else:
            self.statusbar.showMessage('No parent is selected')

    def menu_deselect_child(self):
        if self.selected_child:
            self.statusbar.showMessage('Deselect child: {}'.format(self.selected_child[0]))
            self.selected_child = None
            self.refresh_annotation()
        else:
            self.statusbar.showMessage('No child is selected')

    def menu_select_text_span(self):
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
        self.statusbar.showMessage('Select span: "{}"'.format(' '.join(tokens)))

    def menu_deselect_text_span(self):
        offset = self.selected_text_offset()
        if offset is None:
            inter = set(self.selected_text_spans)
        else:
            token_ids = self.current_offset_map.token_ids(offset)
            inter = self.selected_text_spans.intersection(token_ids)

        if inter:
            self.selected_text_spans -= inter
            self.refresh_text()
            tokens = self.current_graph.get_tokens(inter)
            self.statusbar.showMessage('Deselect span: {}'.format(str(tokens)))
        else:
            self.statusbar.showMessage('No selected text span is highlighted')

    ####################  Menubar: Navigate  ####################

    def menu_navigate_previous(self):
        self.menu_file_save()
        self.select_annotation(self.tid - 1)

    def menu_navigate_next(self):
        self.menu_file_save()
        self.select_annotation(self.tid + 1)

    def menu_navigate_goto(self):
        self.menu_file_save()
        print('Jump to')
        # TODO: init

    ########################################  Text & Graph  ########################################

    def select_annotation(self, tid: int):
        if 0 <= tid < len(self.graphs):
            self.tid = tid
            self.selected_parent = None
            self.selected_child = None
            self.selected_text_spans = set()
            self.lb_tid.setText('{}:'.format(tid))
            self.refresh_text()
            self.refresh_graph()

    def refresh_annotation(self):
        self.refresh_text()
        self.refresh_graph()

    def refresh_text(self):
        def color(token_id: int):
            if token_id in selected_parent:
                return self.COLOR_SELECTED_PARENT
            if token_id in selected_child:
                return self.COLOR_SELECTED_CHILD
            if token_id in self.selected_text_spans:
                return self.COLOR_COVERED_TEXT_SPAN
            if token_id in graph.covered_token_ids:
                return self.COLOR_COVERED_TOKEN
            return None

        graph = self.current_graph
        selected_parent = set(graph.get_concept(self.selected_parent[0]).token_ids) if self.selected_parent else set()
        selected_child = set(graph.get_concept(self.selected_child[0]).token_ids) if self.selected_child else set()
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
        def set_color(c, color):
            if c is None: return
            cid, begin = c
            cursor.setPosition(begin, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(cid))
            cursor.insertHtml('<span style="background-color:{};">{}</span>'.format(color, cid))

        def find_offset_in_graph(cid: str) -> int:
            c = graph.get_concept(cid)
            s = '{} / {}'.format(cid, c.name)
            return text.find(s)

        cursor = self.te_graph.textCursor()
        cursor.setCharFormat(QTextCharFormat())
        cursor.clearSelection()

        graph = self.current_graph
        text = '\n'.join(graph.penman_graphs())
        self.te_graph.setText(text)
        if self.selected_parent and self.selected_parent[1] is None:
            pid = self.selected_parent[0]
            self.selected_parent = pid, find_offset_in_graph(pid)

        set_color(self.selected_parent, self.COLOR_SELECTED_PARENT)
        set_color(self.selected_child, self.COLOR_SELECTED_CHILD)
        self.te_graph.repaint()

    def selected_text_offset(self) -> Optional[Offset]:
        """
        :return: the offset if valid; otherwise, None.
        """
        text = self.lb_text.selectedText()
        begin = self.lb_text.selectionStart()
        end = begin + len(text)
        return Offset(begin, end) if text else None

    def selected_concept_in_graph(self) -> Optional[Tuple[str, int]]:
        cursor = self.te_graph.textCursor()
        cid = cursor.selectedText()
        if self.RE_CONCEPT_ID.match(cid):
            begin = cursor.selectionStart()
            return cid, begin
        return None


def message_box(text: str, icon: int, default_button: int = -1) -> int:
    msg = QMessageBox()
    msg.setText(text)
    msg.setIcon(QMessageBox.Critical)
    msg.setStandardButtons(icon)
    if default_button != -1: msg.setDefaultButton(default_button)
    return msg.exec_()


def main():
    parser = argparse.ArgumentParser(description='StreamSide WiSeN Annotator')
    parser.add_argument('-a', '--annotator', type=str, help='annotator ID')
    parser.add_argument('-r', '--resources', type=str, default='resources/lexica', help='path to the directory containing resource files')
    args = parser.parse_args()

    app = QApplication([])
    gui = Annotator(args.resources, args.annotator)
    gui.show()
    app.exec_()


if __name__ == "__main__":
    main()
