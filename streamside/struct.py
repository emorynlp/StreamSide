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
from enum import IntEnum
from typing import Tuple, Optional, NewType, List, Dict


class ChildType(IntEnum):
    CONCEPT = 0
    REFERENCE = 1


Concept = NewType('Concept', Tuple[str, int, int])  # (concept, begin_offset, end_offset)
Relation = NewType('Relation', Tuple[str, str, str, bool])  # (label, parent ID, child ID, child type)
Attribute = NewType('Attribute', Tuple[str, str, str])  # (label, parent ID, attribute)


class AMR:
    def __init__(self, text: str = None, tid: str = None, annotator: str = None, date: str = None):
        """
        This class consists of a text, an AMR graph for the text, and related meta data.
        :param text: the raw text.
        :param tid: the text ID.
        :param date: the last annotation date.
        :param annotator: the annotator ID.
        """
        # meta
        self.text = '' if text is None else ' '.join(text.split())  # strip unnecessary spaces
        self.tid = tid
        self.date = date
        self.annotator = annotator

        # graph
        self.concepts = dict()
        self.relations = dict()
        self.attributes = dict()

        # to be assigned
        self._concept_id = 0
        self._relation_id = 0
        self._attribute_id = 0

    @property
    def root_ids(self):
        """
        :return: the list of root concept IDs sorted by begin_offset in ascending order.
        """
        cids = [cid for cid in self.concepts if not self.parent_relations(cid)]
        return sorted(cids, key=lambda cid: self.concepts[cid][1])

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """
        :param concept_id: the ID of the concept to be retrieved.
        :return: Concept if exists; otherwise, None
        """
        return self.concepts.get(concept_id, None)

    # TODO: check if the same concept already exists
    def add_concept(self, concept: str, begin_offset: int = -1, end_offset: int = -1) -> str:
        """
        :param concept: the concept to be added (e.g., believe-01, boy)
        :param begin_offset: the offset of the beginning character in self.text
        :param end_offset: the offset of the ending character in self.text
        :return: the ID of the added concept
        """

        def adjust_begin_offset(offset: int) -> int:
            if offset == 0 or self.text[offset - 1] == ' ': return offset
            if self.text[offset] == ' ': return offset + 1
            return next(i for i in range(offset - 1, -2, -1) if i < 0 or self.text[i] == ' ') + 1

        def adjust_end_offset(offset: int) -> int:
            if offset == len(self.text) or self.text[offset] == ' ': return offset
            if self.text[offset - 1] == ' ': return offset - 1
            return next(i for i in range(offset + 1, len(self.text) + 1) if i == len(self.text) or self.text[i] == ' ')

        # generate ID
        cid = 'c{}'.format(self._concept_id)
        self._concept_id += 1

        # adjust offsets
        if 0 <= begin_offset < len(self.text) and 0 < end_offset <= len(self.text):
            t = [concept, adjust_begin_offset(begin_offset), adjust_end_offset(end_offset)]
        else:
            t = [concept, -1, -1]

        # add concept
        self.concepts[cid] = t
        return cid

    def update_concept(self, concept_id: str, concept: str) -> Optional[Concept]:
        """
        :param concept_id: the ID of the concept to be updated
        :param concept: the concept to be updated
        :return: Concept if exists; otherwise, None
        """
        c = self.concepts.get(concept_id, None)
        if c is None: return None
        c[0] = concept
        return c

    def remove_concept(self, concept_id: str) -> Optional[Concept]:
        """
        Removes the concept and all relations and attributes associated with it.
        :param concept_id: the ID of the concept to be removed.
        :return: the removed concept if exists; otherwise, None.
        """
        if concept_id not in self.concepts: return None

        for rid, r in list(self.relations.items()):
            if r[1] == concept_id or r[2] == concept_id:
                del self.relations[rid]

        for aid, a in list(self.attributes.items()):
            if a[1] == concept_id:
                del self.attributes[aid]

        return self.concepts.pop(concept_id)

    def get_relation(self, relation_id: str) -> Optional[Relation]:
        """
        :param relation_id: the relation ID.
        :return: Relation if exists; otherwise, None
        """
        return self.relations.get(relation_id, None)

    def child_relations(self, parent_id: str) -> List[Tuple[str, Relation]]:
        """
        :param parent_id: the parent ID.
        :return: list of (relation ID, Relation) with the specific parent.
        """
        if parent_id not in self.concepts: return []
        return [(rid, r) for rid, r in self.relations.items() if r[1] == parent_id]

    def parent_relations(self, child_id: str) -> List[Tuple[str, Relation]]:
        """
        :param child_id: the child ID.
        :return: list of (relation ID, Relation) with the specific child.
        """
        if child_id not in self.concepts: return []
        return [(rid, r) for rid, r in self.relations.items() if r[2] == child_id]

    # TODO: check if the same relation already exists
    def add_relation(self, label: str, parent_id: str, child_id: str, child_type: ChildType = ChildType.CONCEPT) -> str:
        """
        :param label: the label of the relation to be added.
        :param parent_id: the ID of the parent concept.
        :param child_id: the ID or the constant value of the child.
        :param child_type: the type of the child.
        :return: the ID of the added relation.
        """
        # generate ID
        rid = 'r{}'.format(self._relation_id)
        self._relation_id += 1

        # add relation
        t = [label, parent_id, child_id, child_type]
        self.relations[rid] = t
        return rid

    def update_relation(self, relation_id: str, label: str) -> Optional[Relation]:
        """
        :param relation_id: the ID of the relation to be updated.
        :param label: the label to be updated.
        :return: Relation if exists; otherwise, None.
        """
        r = self.relations.get(relation_id, None)
        if r is None: return None
        r[0] = label
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
        :param attribute_id:
        :return: Relation if exists; otherwise, None
        """
        return self.attributes.get(attribute_id, None)

    def get_attributes(self, parent_id: str) -> List[Tuple[str, Attribute]]:
        """
        :param parent_id: the parent ID.
        :return: list of (attribute ID, Attribute) with the specific parent.
        """
        if parent_id not in self.concepts: return []
        return [(aid, a) for aid, a in self.attributes.items() if a[1] == parent_id]

    def add_attribute(self, label: str, parent_id: str, attribute: str) -> str:
        """
        :param label: the label of the attribute to be added.
        :param parent_id: the ID of the parent concept.
        :param attribute: the attribute.
        :return: the ID of the added attribute.
        """
        # generate ID
        aid = 'a{}'.format(self._attribute_id)
        self._attribute_id += 1

        # add attribute
        t = [label, parent_id, attribute]
        self.attributes[aid] = t
        return aid

    def update_attribute(self, attribute_id: str, attribute: str) -> Optional[Attribute]:
        """
        :param attribute_id: the ID of the attribute to be updated.
        :param label: the attribute to be updated.
        :return: Attribute if exists; otherwise, None.
        """
        a = self.attributes.get(attribute_id, None)
        if a is None: return None
        a[2] = attribute
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

        def repr_concept(cid: str, ctype: ChildType) -> str:
            if ctype == ChildType.CONCEPT:
                c = self.concepts[cid]
                return '({} / {}'.format(cid, c[0])
            else:
                return cid

        def aux(cid: str, ctype: ChildType, r: List[str], indent: str):
            r.append(repr_concept(cid, ctype))
            if ctype == ChildType.CONCEPT:
                indent += ' ' * (len(cid) + 2)
                for aid, attribute in self.get_attributes(cid):
                    r.append('\n{}:{} {}'.format(indent, attribute[0], attribute[2]))
                for rid, relation in self.child_relations(cid):
                    r.append('\n{}:{} '.format(indent, relation[0]))
                    aux(relation[2], relation[3], r, indent + ' ' * (len(relation[0]) + 2))
                r.append(')')

        rep = []
        aux(concept_id, ChildType.CONCEPT, rep, '')
        return ''.join(rep)

    def penman_graphs(self) -> List[str]:
        """
        :return: list of graphs in the Penman notation.
        """
        return [self.penman(root_id) for root_id in self.root_ids]

    def to_dict(self) -> Dict:
        """
        :return: the dictionary representation of this AMR object.
        """
        return copy.deepcopy(self.__dict__)

    def clone(self) -> 'AMR':
        """
        :return: a clone of this AMR object.
        """
        return self.factory(self.to_dict())

    @classmethod
    def factory(cls, params: Dict) -> 'AMR':
        """
        :param params: the return value of to_dict().
        :return: an AMR object initialized by the parameters.
        """
        amr = AMR()
        amr.__dict__ = params
        return amr


# class Concept:
#     def __init__(self, name: str, begin: int = -1, end: int = -1):
#         self.name = name
#         self.begin = begin
#         self.end = end
#
#