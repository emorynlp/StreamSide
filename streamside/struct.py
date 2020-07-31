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

import copy
import json
from typing import Tuple, Optional, List, Dict


class Concept:
    def __init__(self, name: str, begin: int = -1, end: int = -1):
        """
        :param name: the name of this concept
        :param begin: the offset of the first character in the original text (inclusive)
        :param end: the offset of the last character in the original text (exclusive)
        """
        self.name = name
        self.begin = begin
        self.end = end

    @classmethod
    def factory(cls, d: Dict) -> 'Concept':
        """
        :param d: the dictionary to initialize member fields.
        :return: the concept object initialized by the dictionary.
        """
        return Concept(d['name'], d['begin'], d['end'])


class Relation:
    def __init__(self, pid: str, cid: str, label: str, ref: bool = False):
        """
        :param pid: the ID of the parent concept.
        :param cid: the ID of the child concept.
        :param label: the label of this relation.
        :param ref: if True, the child concept is referential.
        """
        self.pid = pid
        self.cid = cid
        self.label = label
        self.ref = ref

    @classmethod
    def factory(cls, d: Dict) -> 'Relation':
        """
        :param d: the dictionary to initialize member fields.
        :return: the relation object initialized by the dictionary.
        """
        return Relation(d['pid'], d['cid'], d['label'], d['ref'])


class Attribute:
    def __init__(self, pid: str, name: str, label: str):
        """
        :param pid: the ID of the parent concept.
        :param name: the name of this attribute.
        :param label: the label of this attribute.
        """
        self.pid = pid
        self.name = name
        self.label = label

    @classmethod
    def factory(cls, d: Dict) -> 'Attribute':
        """
        :param d: the dictionary to initialize member fields.
        :return: the attribute object initialized by the dictionary.
        """
        return Attribute(d['pid'], d['name'], d['label'])


class AMRGraph:
    def __init__(self, text: str, tid: str = None, annotator: str = None, date: str = None):
        """
        This class consists of a text, an AMR graph for the text, and related meta data.
        :param text: the raw text.
        :param tid: the text ID.
        :param date: the last annotation date.
        :param annotator: the annotator ID.
        """
        # meta
        self.text = ' '.join(text.split())  # strip unnecessary spaces
        self.tid = tid
        self.date = date
        self.annotator = annotator

        # graph
        self.concepts: Dict[str, Concept] = {}
        self.relations: Dict[str, Relation] = {}
        self.attributes: Dict[str, Attribute] = {}

        # to be assigned
        self._concept_id = 0
        self._relation_id = 0
        self._attribute_id = 0

    @property
    def root_ids(self) -> List[str]:
        """
        :return: list of root concept IDs sorted by begin offsets in ascending order.
        """
        cids = [cid for cid in self.concepts if not self.parent_relations(cid)]
        return sorted(cids, key=lambda cid: self.concepts[cid].begin)

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """
        :param concept_id: the ID of the concept to be retrieved.
        :return: the concept object if exists; otherwise, None
        """
        return self.concepts.get(concept_id, None)

    # TODO: check if the same concept already exists
    def add_concept(self, name: str, begin: int = -1, end: int = -1) -> str:
        """
        :param name: the name of the concept to be added (e.g., believe-01, boy).
        :param begin: the offset of the beginning character in self.text.
        :param end: the offset of the ending character in self.text.
        :return: the ID of the added concept.
        """

        def adjust_begin(offset: int) -> int:
            if offset == 0 or self.text[offset - 1] == ' ': return offset
            if self.text[offset] == ' ': return offset + 1
            return next(i for i in range(offset - 1, -2, -1) if i < 0 or self.text[i] == ' ') + 1

        def adjust_end(offset: int) -> int:
            if offset == len(self.text) or self.text[offset] == ' ': return offset
            if self.text[offset - 1] == ' ': return offset - 1
            return next(i for i in range(offset + 1, len(self.text) + 1) if i == len(self.text) or self.text[i] == ' ')

        # generate ID
        cid = 'c{}'.format(self._concept_id)
        self._concept_id += 1

        # adjust offsets
        if 0 <= begin < len(self.text) and 0 < end <= len(self.text):
            begin, end = adjust_begin(begin), adjust_end(end)
        else:
            begin, end = -1, -1

        # add concept
        self.concepts[cid] = Concept(name, begin, end)
        return cid

    def update_concept(self, concept_id: str, name: str) -> Optional[Concept]:
        """
        :param concept_id: the ID of the concept.
        :param name: the name of the concept to be updated.
        :return: the updated concept if exists; otherwise, None.
        """
        c = self.concepts.get(concept_id, None)
        if c is None: return None
        c.name = name
        return c

    def remove_concept(self, concept_id: str) -> Optional[Concept]:
        """
        Removes the concept and all relations as well as attributes associated with it.
        :param concept_id: the ID of the concept to be removed.
        :return: the removed concept if exists; otherwise, None.
        """
        if concept_id not in self.concepts: return None

        for rid, r in list(self.relations.items()):
            if r.pid == concept_id or r.cid == concept_id:
                del self.relations[rid]

        for aid, a in list(self.attributes.items()):
            if a.pid == concept_id:
                del self.attributes[aid]

        return self.concepts.pop(concept_id)

    def get_relation(self, relation_id: str) -> Optional[Relation]:
        """
        :param relation_id: the relation ID.
        :return: the relation object if exists; otherwise, None
        """
        return self.relations.get(relation_id, None)

    def child_relations(self, parent_id: str) -> List[Tuple[str, Relation]]:
        """
        :param parent_id: the parent ID.
        :return: list of (relation ID, Relation) with the specific parent.
        """
        if parent_id not in self.concepts: return []
        return [(rid, r) for rid, r in self.relations.items() if r.pid == parent_id]

    def parent_relations(self, child_id: str) -> List[Tuple[str, Relation]]:
        """
        :param child_id: the child ID.
        :return: list of (relation ID, Relation) with the specific child.
        """
        if child_id not in self.concepts: return []
        return [(rid, r) for rid, r in self.relations.items() if r.cid == child_id]

    # TODO: check if the same relation already exists
    def add_relation(self, parent_id: str, child_id: str, label: str, ref: bool = False) -> str:
        """
        :param label: the label of the relation to be added.
        :param parent_id: the ID of the parent concept.
        :param child_id: the ID or the constant value of the child.
        :param ref: if True, the child concept is referential.
        :return: the ID of the added relation.
        """
        # generate ID
        rid = 'r{}'.format(self._relation_id)
        self._relation_id += 1

        # add relation
        self.relations[rid] = Relation(parent_id, child_id, label, ref)
        return rid

    def update_relation(self, relation_id: str, label: str) -> Optional[Relation]:
        """
        :param relation_id: the ID of the relation.
        :param label: the label to be updated.
        :return: Relation if exists; otherwise, None.
        """
        r = self.relations.get(relation_id, None)
        if r is None: return None
        r.label = label
        return r

    def remove_relation(self, relation_id: str) -> Optional[Relation]:
        """
        Removes the relation.
        :param relation_id: the ID of the relation to be removed.
        :return: the removed relation if exists; otherwise, None.
        """
        return self.relations.pop(relation_id) if relation_id in self.relations else None

    def get_attribute(self, attribute_id: str) -> Optional[Attribute]:
        """
        :param attribute_id: the attribute ID.
        :return: the attribute object if exists; otherwise, None
        """
        return self.attributes.get(attribute_id, None)

    def get_attributes(self, parent_id: str) -> List[Tuple[str, Attribute]]:
        """
        :param parent_id: the parent ID.
        :return: list of (attribute ID, Attribute) with the specific parent.
        """
        if parent_id not in self.concepts: return []
        return [(aid, a) for aid, a in self.attributes.items() if a.pid == parent_id]

    def add_attribute(self, parent_id: str, name: str, label: str) -> str:
        """
        :param parent_id: the ID of the parent concept.
        :param label: the label of the attribute to be added.
        :param name: the name of the attribute.
        :return: the ID of the added attribute.
        """
        # generate ID
        aid = 'a{}'.format(self._attribute_id)
        self._attribute_id += 1

        # add attribute
        self.attributes[aid] = Attribute(parent_id, name, label)
        return aid

    def update_attribute(self, attribute_id: str, name: Optional[str] = None, label: Optional[str] = None) -> Optional[Attribute]:
        """
        :param attribute_id: the ID of the attribute.
        :param name: the name of the attribute to be updated (if not None).
        :param label: the label of the attribute to be updated (if not None).
        :return: Attribute if exists; otherwise, None.
        """
        a = self.attributes.get(attribute_id, None)
        if a is None: return None
        if name: a.name = name
        if label: a.label = label
        return a

    def remove_attribute(self, attribute_id: str) -> Optional[Attribute]:
        """
        :param attribute_id: the ID of the attribute to be removed.
        :return: Attribute if exists; otherwise, None.
        """
        return self.attributes.pop(attribute_id) if attribute_id in self.attributes else None

    def penman(self, concept_id: str) -> str:
        """
        :param concept_id: the ID of the root concept.
        :return: the Penman notation of the concept's subtree.
        """

        def repr_concept(cid: str, ref: bool) -> str:
            if ref: return cid
            c = self.concepts[cid]
            return '({} / {}'.format(cid, c.name)

        def aux(cid: str, ref: bool, r: List[str], indent: str):
            r.append(repr_concept(cid, ref))
            if not ref:
                indent += ' ' * (len(cid) + 2)
                for aid, attribute in self.get_attributes(cid):
                    r.append('\n{}:{} {}'.format(indent, attribute.label, attribute.name))
                for rid, relation in self.child_relations(cid):
                    r.append('\n{}:{} '.format(indent, relation.label))
                    aux(relation.cid, relation.ref, r, indent + ' ' * (len(relation.label) + 2))
                r.append(')')

        rep = []
        aux(concept_id, False, rep, '')
        return ''.join(rep)

    def penman_graphs(self) -> List[str]:
        """
        :return: list of graphs in the Penman notation.
        """
        return [self.penman(root_id) for root_id in self.root_ids]

    def json_dumps(self, **kwargs) -> str:
        """
        :return: the JSON representation of this AMR object.
        """
        return json.dumps(self, default=lambda x: x.__dict__, **kwargs)

    def clone(self) -> 'AMRGraph':
        """
        :return: a clone of this AMR object.
        """
        amr = AMRGraph('')
        amr.__dict__ = copy.deepcopy(self.__dict__)
        return amr

    @classmethod
    def factory(cls, params: Dict) -> 'AMRGraph':
        """
        :param params: the return value of json.loads(#json_dumps()).
        :return: an AMR object initialized by the parameters.
        """
        graph = AMRGraph('')

        for k, v in params.items():
            if k == 'concepts':
                v = {cid: Concept.factory(c) for cid, c in v.items()}
            elif k == 'relations':
                v = {rid: Relation.factory(r) for rid, r in v.items()}
            elif k == 'attributes':
                v = {aid: Attribute.factory(a) for aid, a in v.items()}

            graph.__dict__[k] = v

        return graph
