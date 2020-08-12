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
from typing import Tuple, Optional, List, Dict, Set, Iterable


class Concept:
    def __init__(self, name: str, token_ids: List[int] = None, attribute: bool = False):
        """
        :param name: the name of this concept.
        :param token_ids: the list of token IDs representing this concept.
        :param attribute: if True, this concept is an attribute.
        """
        self.name = name
        self.token_ids = token_ids if token_ids is not None else []
        self.attribute = attribute

    @classmethod
    def factory(cls, d: Dict) -> 'Concept':
        """
        :param d: the dictionary to initialize member fields.
        :return: the concept object initialized by the dictionary.
        """
        return Concept(d['name'], d['token_ids'], d['attribute'])


class Relation:
    def __init__(self, parent_id: str, child_id: str, label: str, referent: bool = False):
        """
        :param parent_id: the ID of the parent concept.
        :param child_id: the ID of the child concept.
        :param label: the label of this relation.
        :param referent: if True, the child concept is referential.
        """
        self.parent_id = parent_id
        self.child_id = child_id
        self.label = label
        self.referent = referent

    @classmethod
    def factory(cls, d: Dict) -> 'Relation':
        """
        :param d: the dictionary to initialize member fields.
        :return: the relation object initialized by the dictionary.
        """
        return Relation(d['parent_id'], d['child_id'], d['label'], d['referent'])


class Offset:
    def __init__(self, begin, end):
        """
        :param begin: the offset of the beginning character (inclusive).
        :param end: the offset of the ending character (exclusive).
        """
        self.begin = begin
        self.end = end


class OffsetMap:
    def __init__(self, tokens: List[str]):
        """
        :param tokens: the input tokens.
        """
        self.tokens = tokens
        self.text = ' '.join(tokens)
        self.begin_offset_to_id = dict()
        self.end_offset_to_id = dict()
        self.id_to_offset = []

        prev = 0
        for i, token in enumerate(tokens):
            begin = prev
            end = begin + len(token)
            prev = end + 1
            self.begin_offset_to_id[begin] = i
            self.end_offset_to_id[end] = i
            self.id_to_offset.append(Offset(begin, end))

    def adjust_begin(self, offset: int) -> int:
        """
        :param offset: the offset of the beginning character (inclusive).
        :return: the adjusted offset (inclusive).
        """
        if offset == 0 or self.text[offset - 1] == ' ': return offset
        if self.text[offset] == ' ': return offset + 1
        return next(i for i in range(offset - 1, -2, -1) if i < 0 or self.text[i] == ' ') + 1

    def adjust_end(self, offset: int) -> int:
        """
        :param offset: the offset of the ending character (exclusive).
        :return: the adjusted offset (exclusive).
        """
        if offset == len(self.text) or self.text[offset] == ' ': return offset
        if self.text[offset - 1] == ' ': return offset - 1
        return next(i for i in range(offset + 1, len(self.text) + 1) if i == len(self.text) or self.text[i] == ' ')

    def token_ids(self, offset: Offset) -> Set[int]:
        """
        :param offset: the offset to retrieve tokens for.
        :return: the list of token IDs representing the offsets if valid; otherwise, None.
        """
        if 0 <= offset.begin < len(self.text) and 0 < offset.end <= len(self.text):
            begin = self.adjust_begin(offset.begin)
            end = self.adjust_end(offset.end)
            if begin < end:
                begin = self.begin_offset_to_id[begin]
                end = self.end_offset_to_id[end]
                return {i for i in range(begin, end + 1)}
        return set()

    def get_offset(self, token_id: int) -> Optional[Offset]:
        """
        :param token_id: the ID of the token to retrieve the offset for.
        :return: the offset representing the token if exists; otherwise, None.
        """
        return self.id_to_offset[token_id] if 0 <= token_id < len(self.tokens) else None


class Graph:
    def __init__(self, text: str, tid: str = None, annotator: str = None):
        """
        This class consists of a text, an AMR graph for the text, and related meta data.
        :param text: the raw text.
        :param tid: the text Iadd_conD.
        :param annotator: the annotator ID.
        """
        # meta
        self.tid = tid
        self.annotator = annotator
        self.tokens = text.split()

        # graph
        self.concepts: Dict[str, Concept] = dict()
        self.relations: Dict[str, Relation] = dict()
        self.covered_token_ids = set()

        # to be assigned
        self._concept_id = 0
        self._relation_id = 0

    @property
    def root_ids(self) -> List[str]:
        """
        :return: list of root concept IDs sorted by begin offsets in ascending order.
        """
        cids = [cid for cid in self.concepts if not self.parent_relations(cid)]
        cids.sort(key=lambda x: int(x[1:]))
        return cids

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """
        :param concept_id: the ID of the concept to be retrieved.
        :return: the concept object if exists; otherwise, None
        """
        return self.concepts.get(concept_id, None)

    def add_concept(self, name: str, token_ids: Optional[Set[int]] = None, attribute: bool = False) -> Optional[str]:
        """
        :param name: the name of the concept to be added (e.g., believe-01, boy).
        :param token_ids: the set of token IDs representing this concept.
        :param attribute: if True, the added concept is an attribute.
        :return: the ID of the added concept if added successfully; otherwise, None.
        """
        if token_ids:
            # check if the tokens are already covered by existing concepts
            for tid in token_ids:
                if tid in self.covered_token_ids: return None

            # convert the set to an ordered list
            self.covered_token_ids.update(token_ids)
            token_ids = sorted(token_ids)
        else:
            token_ids = []

        # add concept
        cid = '{}{}'.format('a' if attribute else 'c', self._concept_id)
        self._concept_id += 1
        self.concepts[cid] = Concept(name, token_ids, attribute)
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
            if r.parent_id == concept_id or r.child_id == concept_id:
                del self.relations[rid]

        con = self.concepts.pop(concept_id)
        self.covered_token_ids -= set(con.token_ids)
        return con

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
        return [(rid, r) for rid, r in self.relations.items() if r.parent_id == parent_id]

    def parent_relations(self, child_id: str) -> List[Tuple[str, Relation]]:
        """
        :param child_id: the child ID.
        :return: list of (relation ID, Relation) with the specific child.
        """
        if child_id not in self.concepts: return []
        return [(rid, r) for rid, r in self.relations.items() if r.child_id == child_id]

    # TODO: check if the relation already exists
    def add_relation(self, parent_id: str, child_id: str, label: str, referent: bool = False) -> str:
        """
        :param label: the label of the relation to be added.
        :param parent_id: the ID of the parent concept.
        :param child_id: the ID or the constant value of the child.
        :param referent: if True, the child concept is referential.
        :return: the ID of the added relation.
        """
        # generate ID
        rid = 'r{}'.format(self._relation_id)
        self._relation_id += 1

        # add relation
        self.relations[rid] = Relation(parent_id, child_id, label, referent)
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

    def penman(self, concept_id: str) -> str:
        """
        :param concept_id: the ID of the root concept.
        :return: the Penman notation of the concept's subtree.
        """

        def repr_concept(cid: str, ref: bool) -> str:
            if ref: return cid
            c = self.concepts[cid]
            # if c.attribute and self.parent_relations(cid): return c.name
            return '({} / {}'.format(cid, c.name)

        # TODO: sort the relation labels per node
        def aux(cid: str, ref: bool, r: List[str], indent: str):
            cname = repr_concept(cid, ref)
            r.append(cname)
            if not ref:
                indent += ' ' * (len(cid) + 2)
                for rid, relation in sorted(self.child_relations(cid), key=lambda x: x[1].label):
                    r.append('\n{}:{} '.format(indent, relation.label))
                    aux(relation.child_id, relation.referent, r, indent + ' ' * (len(relation.label) + 2))
                if cname.startswith('('): r.append(')')

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
        self.covered_token_ids = list(self.covered_token_ids)
        s = json.dumps(self, default=lambda x: x.__dict__, **kwargs)
        self.covered_token_ids = set(self.covered_token_ids)
        return s

    def clone(self) -> 'Graph':
        """
        :return: a clone of this AMR object.
        """
        amr = Graph('')
        amr.__dict__ = copy.deepcopy(self.__dict__)
        return amr

    @classmethod
    def factory(cls, params: Dict) -> 'Graph':
        """
        :param params: the return value of json.loads(#json_dumps()).
        :return: an AMR object initialized by the parameters.
        """
        graph = Graph('')

        for k, v in params.items():
            if k == 'concepts':
                v = {cid: Concept.factory(c) for cid, c in v.items()}
            elif k == 'relations':
                v = {rid: Relation.factory(r) for rid, r in v.items()}
            elif k == 'covered_token_ids':
                v = set(v)

            graph.__dict__[k] = v

        return graph

    def get_tokens(self, token_ids: Iterable[int]) -> List[str]:
        """
        :param token_ids: a iterable collection of token IDs.
        :return: the ordered list of tokens from the IDs.
        """
        token_ids = sorted(token_ids)
        return [self.tokens[i] for i in token_ids]
