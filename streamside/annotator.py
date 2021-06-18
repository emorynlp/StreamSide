#  Copyright 2020, 2021 Emory University
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

import sys
from datetime import datetime

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

from streamside.resources import wiser, amr

import argparse
import json
import os
import re
from typing import List, Dict, Optional, Tuple, Callable, Set, Union

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QTextCursor, QTextCharFormat, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow, QAction, qApp, QFileDialog, QHBoxLayout, \
    QMessageBox, QGridLayout, QTextEdit, QCompleter, QLineEdit, QDialog, QPushButton, QCheckBox, QPlainTextEdit, QShortcut, QStatusBar, QInputDialog, QVBoxLayout

from streamside.struct import Graph, OffsetMap, Offset, penman_reader


class InputDialog(QDialog):
    def __init__(self, parent, title: str, width: int, completer_list: List[str], completer_max: int):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(width)

        # completer
        completer = QCompleter(completer_list)
        completer.setMaxVisibleItems(completer_max)
        self.ledit = QLineEdit()
        self.ledit.setCompleter(completer)
        self.ledit.editingFinished.connect(self.edit_finished)

        self.ok = False
        self.btn_ok = QPushButton("OK", self)
        self.btn_ok.clicked.connect(self.button_ok)
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.clicked.connect(self.button_cancel)

    def edit_finished(self):
        pass

    def button_ok(self):
        self.ok = self.sender() == self.btn_ok
        self.close()

    def button_cancel(self):
        self.close()


class ConceptDialog(InputDialog):
    def __init__(self, parent, title: str, concept_name: str, attribute: bool):
        ctype = 'an attribute' if attribute else 'a concept'
        super().__init__(parent, '{} {}'.format(title, ctype), 350, parent.concept_list, 50)
        self.concept_dict = parent.concept_dict
        layout = QVBoxLayout()
        self.setLayout(layout)

        # components
        self.ledit.setText(concept_name)
        self.lb_desc = QPlainTextEdit('Description')
        self.lb_desc.setReadOnly(True)

        wg_concept = QWidget()
        l = QHBoxLayout()
        l.setContentsMargins(0, 0, 0, 0)
        wg_concept.setLayout(l)
        l.addWidget(self.ledit)

        # self.ck_attr = QCheckBox()
        # l.addWidget(self.ck_attr)
        # l.addWidget(QLabel('Attribute'))

        # buttons
        wg_button = QWidget()
        l = QHBoxLayout()
        l.setContentsMargins(50, 0, 50, 0)
        wg_button.setLayout(l)
        l.addWidget(self.btn_ok)
        l.addWidget(self.btn_cancel)

        # layout
        layout.addWidget(QLabel('Enter the name:'))
        layout.addWidget(wg_concept)
        layout.addWidget(self.lb_desc)
        layout.addWidget(wg_button)

        # shortcut
        self.sct_attribute = QShortcut(QKeySequence('Ctrl+R'), self)
        self.sct_attribute.activated.connect(self.check_attribute)

    def edit_finished(self):
        v = self.concept_dict.get(self.ledit.text().strip(), None)
        text = v['description'] if v else 'No description available'
        self.lb_desc.setPlainText(text)
        self.lb_desc.repaint()

    def check_attribute(self):
        self.ck_attr.setChecked(not self.ck_attr.isChecked())

    def exec_(self) -> Optional[str]:
        super().exec_()
        return self.ledit.text().strip() if self.ok else None


class RelationDialog(InputDialog):
    def __init__(self, parent, title: str, parent_desc: str, child_desc: str, label: str = '', update: bool = False):
        super().__init__(parent, title, 550, parent.relation_list, 50)
        self.relation_dict = parent.relation_dict
        layout = QVBoxLayout()
        self.setLayout(layout)

        # components
        self.ledit.setText(label)
        self.referent = QCheckBox()
        self.inverse = QCheckBox()
        self.lb_desc = QPlainTextEdit('Description')
        self.lb_desc.setReadOnly(True)

        # AMR only
        self.concept_desc = None
        if parent.mode == 'amr':
            parent_id = parent_desc.split()[0][1:]
            con = parent.current_graph.get_concept(parent_id)
            d = parent.concept_dict.get(con.name, None)
            if d and d['type'] == 'pred':
                self.concept_desc = d['description']
                self.lb_desc.setPlainText(self.concept_desc)

        # child + referent
        wg_child = QWidget()
        l = QHBoxLayout()
        l.setContentsMargins(0, 0, 0, 0)
        wg_child.setLayout(l)
        l.addWidget(QLabel('Child: {}'.format(child_desc)), 80)
        if not update:
            l.addWidget(self.referent)
            l.addWidget(QLabel('Referent'))

        # ledit + inverse
        wg_ledit = QWidget()
        l = QHBoxLayout()
        l.setContentsMargins(0, 0, 0, 0)
        wg_ledit.setLayout(l)
        l.addWidget(self.ledit)
        if not update:
            l.addWidget(self.inverse)
            l.addWidget(QLabel('-of'))

        # buttons
        wg_button = QWidget()
        l = QHBoxLayout()
        l.setContentsMargins(50, 0, 50, 0)
        wg_button.setLayout(l)
        l.addWidget(self.btn_ok)
        l.addWidget(self.btn_cancel)

        # layout
        layout.addWidget(QLabel('Parent: {}'.format(parent_desc)))
        layout.addWidget(wg_child)
        layout.addWidget(wg_ledit)
        layout.addWidget(self.lb_desc)
        layout.addWidget(wg_button)

        # shortcuts
        self.sct_referent = QShortcut(QKeySequence('Ctrl+R'), self)
        self.sct_referent.activated.connect(self.check_referent)
        self.sct_inverse = QShortcut(QKeySequence('Ctrl+F'), self)
        self.sct_inverse.activated.connect(self.check_inverse)

    def edit_finished(self):
        if self.concept_desc is None:
            v = self.relation_dict.get(self.ledit.text().strip(), None)
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
            label = self.ledit.text().strip()
            if self.inverse.isChecked(): label += '-of'
            return label, self.referent.isChecked()
        else:
            return None


class GraphAnnotator(QMainWindow):
    def __init__(self, resource_dir: str, mode: str, annotator: str = 'unknown'):
        super().__init__()

        # constants
        font = QFont()
        font.setFamily('Courier New')

        self.VERSION = '0.1'
        self.RE_CONCEPT_ID = re.compile(r'([ca]\d+)')
        self.RE_CONCEPT_ID_PAREN = re.compile(r'(?:^| )\(([ca]\d+) /')
        self.FONT_GRAPH = font
        self.COLOR_COVERED_TOKEN = 'lightgray'
        self.COLOR_SELECTED_PARENT = 'lightpink'
        self.COLOR_SELECTED_CHILD = 'lightgreen'
        self.COLOR_COVERED_TEXT_SPAN = 'khaki'

        # resources
        self.concept_dict: Dict[str, str] = dict()
        self.concept_list: List[str] = []
        self.relation_dict: Dict[str, str] = dict()
        self.relation_list: List[str] = []
        self.init_resources(resource_dir, mode)

        # fields
        self.mode = mode
        self.annotator: str = annotator
        self.filename: str = ''
        self.tid: int = -1
        self.graphs: List[Graph] = []
        self.offset_maps: List[OffsetMap] = []
        self.selected_parent: Optional[Tuple[str, int]] = None
        self.selected_child: Optional[Tuple[str, int]] = None
        self.selected_text_spans: Set[int] = set()

        # graphical user interface
        layout = self._init_central_widget('StreamSide Graph Annotator: {}'.format(annotator), 800, 800)
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

    def init_resources(self, resource_dir: str, mode: str):
        if resource_dir:
            f_concepts = open(os.path.join(resource_dir, 'concepts.json'))
            f_relations = open(os.path.join(resource_dir, 'relations.json'))
        else:
            m = wiser if mode == 'wiser' else amr
            f_concepts = pkg_resources.open_text(m, 'concepts.json')
            f_relations = pkg_resources.open_text(m, 'relations.json')

        # concepts
        self.concept_dict = json.load(f_concepts)
        self.concept_list = sorted(self.concept_dict.keys())
        self.relation_dict = json.load(f_relations)
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
        tb_layout = QHBoxLayout()
        w.setLayout(tb_layout)
        tb_layout.setContentsMargins(0, 0, 0, 0)

        tb_layout.addWidget(self.lb_tid, 2)
        tb_layout.addWidget(self.lb_text, 98)
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
        menu.addAction(action('Open', 'Ctrl+o', self.menu_file_open))
        menu.addAction(action('Save', 'Ctrl+s', self.menu_file_save))
        menu.addSeparator()
        menu.addAction(action('About', 'Ctrl+i', self.menu_file_about))
        menu.addAction(action('Quit', 'Ctrl+q', qApp.quit))

        # edit
        menu = menubar.addMenu('Edit')
        menu.addAction(action('Create Attribute', 'a', self.menu_create_attribute))
        menu.addAction(action('Create Concept', 'c', self.menu_create_concept))
        menu.addAction(action('Create Relation', 'r', self.menu_create_relation))
        menu.addSeparator()
        menu.addAction(action('Delete', 'Ctrl+d', self.menu_delete))
        menu.addAction(action('Update', 'Ctrl+f', self.menu_update))

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
        menu.addAction(action('Previous', ',', self.menu_navigate_previous))
        menu.addAction(action('Next', '.', self.menu_navigate_next))
        menu.addSeparator()
        menu.addAction(action('Jump to First', 'Ctrl+,', self.menu_navigate_jump_first))
        menu.addAction(action('Jump to Last', 'Ctrl+.', self.menu_navigate_jump_last))
        menu.addAction(action('Jump to ...', 'Ctrl+/', self.menu_navigate_jump))

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

        def open_json(json_file):
            self.filename = json_file
            with open(self.filename) as fin:
                d = json.load(fin)
                self.graphs = [Graph.factory(graph) for graph in d['graphs']]

        def open_penman(penman_file):
            json_file = '{}{}.json'.format(penman_file[:-6], self.annotator)
            self.filename = json_file

            if os.path.exists(json_file):
                msg = 'Annotation exists for the selected text file. Opening the annotation file instead.'
                message_box(msg, QMessageBox.Ok)
                open_json(json_file)
            else:
                self.graphs = penman_reader(penman_file)

        # get filename
        filename = QFileDialog.getOpenFileName(self, 'Open File')[0]
        if not filename: return
        self.menu_file_save()

        # check extension
        if filename[-4:].lower() == '.txt':
            open_txt(filename)
        elif filename[-5:].lower() == '.json':
            open_json(filename)
        elif filename[-7:].lower() == '.penman':
            open_penman(filename)
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

        self.current_graph.last_saved = current_time()
        with open(self.filename, 'w') as fout:
            d = ['    ' + graph.json_dumps() for graph in self.graphs]
            fout.write('{{\n  "graphs": [\n{}\n  ]\n}}\n'.format(',\n'.join(d)))

        self.statusbar.showMessage('Save: {}'.format(self.filename))

    def menu_file_about(self):
        msg = QMessageBox()
        text = 'StreamSide v{} developed by Emory NLP\nhttps://github.com/emorynlp/StreamSide\nContact: jinho.choi@emory.edu'.format(self.VERSION)
        msg.setText(text)
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        self.menu_file_save()
        event.accept()

    ####################  Menubar: Edit  ####################

    def _menu_create_concept(self, attribute: bool):
        self.menu_select_text_span()
        graph = self.current_graph
        tokens = graph.get_tokens(self.selected_text_spans)
        text = ' '.join(tokens) if attribute else '_'.join(tokens).lower()
        name = ConceptDialog(self, 'Create', text, attribute).exec_()
        ctype = 'Attribute' if attribute else 'Concept'

        if name:
            cid = graph.add_concept(name, self.selected_text_spans, attribute)
            self.selected_text_spans.clear()
            self.refresh_annotation()
            self.statusbar.showMessage('{} created: ({} / {}) - {}'.format(ctype, cid, name, str(tokens)))
        else:
            self.statusbar.showMessage('{} creation is cancelled.'.format(ctype))

    def menu_create_concept(self):
        self._menu_create_concept(False)

    def menu_create_attribute(self):
        self._menu_create_concept(True)

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

        t = RelationDialog(self, 'Create a relation', parent_desc, child_desc).exec_()
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

    def menu_delete(self):
        sel = self.find_concept_or_relation()
        if sel is None:
            self.statusbar.showMessage('No valid concept or relation is highlighted.')
            return

        graph = self.current_graph
        deleted = False

        if type(sel) is str:
            if graph.remove_concept(sel):
                deleted = True
                self.statusbar.showMessage('Delete concept: {}'.format(sel))
        else:
            label, parent_id, child_id = sel[0], sel[1], sel[2]
            for rid, r in graph.parent_relations(child_id):
                if r.label == label and r.parent_id == parent_id:
                    graph.remove_relation(rid)
                    deleted = True
                    self.statusbar.showMessage('Delete relation: {}({}, {})'.format(label, parent_id, child_id))
                    break

        if deleted:
            self.selected_parent = None
            self.selected_child = None
            self.refresh_annotation()
        else:
            self.statusbar.showMessage('No valid concept or relation is highlighted.')

    def menu_update(self):
        sel = self.find_concept_or_relation()
        if sel is None:
            self.statusbar.showMessage('No valid concept or relation is highlighted.')
            return

        graph = self.current_graph
        updated = False

        if type(sel) is str:
            c = graph.get_concept(sel)
            if c:
                c.attribute
                name = ConceptDialog(self, 'Update', c.name, c.attribute).exec_()
                if name:
                    c.name = name
                    updated = True
                    self.statusbar.showMessage('Update: {}'.format(sel))
        else:
            label, parent_id, child_id = sel[0], sel[1], sel[2]
            for rid, r in graph.parent_relations(child_id):
                if r.label == label and r.parent_id == parent_id:
                    parent_concept = graph.get_concept(parent_id)
                    child_concept = graph.get_concept(child_id)
                    parent_desc = '({} / {})'.format(parent_id, parent_concept.name)
                    child_desc = '({} / {})'.format(child_id, child_concept.name)
                    name = RelationDialog(self, 'Update the relation', parent_desc, child_desc, label, True).exec_()
                    if name:
                        r.label = name[0]
                        self.statusbar.showMessage('Update relation: {}({}, {})'.format(label, parent_id, child_id))
                        updated = True
                    break

        if updated:
            self.selected_parent = None
            self.selected_child = None
            self.refresh_annotation()
        else:
            self.statusbar.showMessage('No valid concept or relation is highlighted.')

    def find_concept_or_relation(self) -> Optional[Union[str, Tuple[str, str, str]]]:
        cursor = self.te_graph.textCursor()
        sel = cursor.selectedText()
        if not sel:
            self.statusbar.showMessage('No concept or relation is highlighted')
            return None

        if self.RE_CONCEPT_ID.match(sel):
            return sel
        else:
            text = self.te_graph.toPlainText()
            begin = cursor.selectionStart()

            # get parent ID
            parent_id = None
            ls = text[:begin].split('\n')
            indent = len(ls[-1]) - 1
            for line in reversed(ls[:-1]):
                idx = len(line) - len(line.lstrip())
                if idx < indent:
                    m = self.RE_CONCEPT_ID_PAREN.search(line)
                    if m: parent_id = m.group(1)
                    break

            m = self.RE_CONCEPT_ID.search(text[begin + len(sel):])
            child_id = m.group(1) if m else None
            if parent_id and child_id: return sel, parent_id, child_id

        return None

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
        tid = self.tid - 1

        if 0 <= tid:
            self.select_annotation(tid)
            self.statusbar.showMessage('Navigate: {}'.format(tid))
        else:
            self.statusbar.showMessage('Already at the first text.')

    def menu_navigate_next(self):
        self.menu_file_save()
        tid = self.tid + 1

        if tid < len(self.graphs):
            self.select_annotation(tid)
            self.statusbar.showMessage('Navigate: {}'.format(tid))
        else:
            self.statusbar.showMessage('Already at the last text.')

    def menu_navigate_jump_first(self):
        self.menu_file_save()
        self.select_annotation(0)
        self.statusbar.showMessage('Navigate: {}'.format(0))

    def menu_navigate_jump_last(self):
        self.menu_file_save()
        tid = len(self.graphs) - 1
        self.select_annotation(tid)
        self.statusbar.showMessage('Navigate: {}'.format(tid))

    def menu_navigate_jump(self):
        self.menu_file_save()
        max = len(self.graphs) - 1

        tid, ok = QInputDialog.getInt(self, 'Jump to', 'Select between 0 and {}'.format(max), value=self.tid, min=0, max=max)
        if ok:
            self.select_annotation(tid)
            self.statusbar.showMessage('Navigate: {}'.format(tid))

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
        self.te_graph.setFont(self.FONT_GRAPH)
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


def current_time():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description='StreamSide Annotator')
    parser.add_argument('-a', '--annotator', type=str, help='annotator ID')
    parser.add_argument('-m', '--mode', type=str, default='wiser', help='wiser|amr')
    parser.add_argument('-r', '--resources', type=str, default='', help='path to the directory containing resource files')
    args = parser.parse_args()

    app = QApplication([])
    gui = GraphAnnotator(args.resources, args.mode, args.annotator)
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
