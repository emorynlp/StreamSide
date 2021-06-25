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

import copy
import json
import re
from typing import Tuple, Optional, List, Dict, Set, Iterable

PENMAN_TEXT = 'snt'
PENMAN_TID = 'id'
PENMAN_ANNOTATOR = 'annotator'
PENMAN_LAST_SAVED = 'save-date'
PENMAN_ALIGNMENTS = 'align'


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
    def __init__(self, text: str, tid: str = None, annotator: str = None, last_saved: str = None):
        """
        This class consists of a text, an AMR graph for the text, and related meta data.
        :param text: the raw text.
        :param tid: the text Iadd_conD.
        :param annotator: the annotator ID.
        """
        # meta
        self.tid = tid
        self.annotator = annotator
        self.last_saved = last_saved
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
        cids = [cid for cid in self.concepts if not self.parent_relations(cid, True)]
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

    def add_token_ids(self, concept_id: str, token_ids: Set[int]) -> Optional[Set[int]]:
        c = self.concepts.get(concept_id, None)
        if c is None: return None

        s = token_ids - self.covered_token_ids
        if not s: return None

        self.covered_token_ids.update(s)
        c.token_ids.extend(s)
        c.token_ids.sort()
        return s

    def remove_token_ids(self, concept_id: str, token_ids: Set[int]) -> Optional[Set[int]]:
        c = self.concepts.get(concept_id, None)
        if c is None: return None

        s = set(c.token_ids).intersection(token_ids)
        if not s: return None

        self.covered_token_ids -= s
        c.token_ids = [t for t in c.token_ids if t not in s]
        return s

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

    def remove_concept(self, concept_id: str, remove_relations: bool = True) -> Optional[Concept]:
        """
        Removes the concept and all relations as well as attributes associated with it.
        :param concept_id: the ID of the concept to be removed.
        :param remove_relations: if True, remove all relations associated with the concept.
        :return: the removed concept if exists; otherwise, None.
        """
        if concept_id not in self.concepts: return None

        if remove_relations:
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

    def child_relations(self, parent_id: str, ignore_referent: bool = False) -> List[Tuple[str, Relation]]:
        """
        :param parent_id: the parent ID.
        :return: list of (relation ID, Relation) with the specific parent.
        """
        if parent_id not in self.concepts: return []
        return [(rid, r) for rid, r in self.relations.items() if r.parent_id == parent_id and not (ignore_referent and r.referent)]

    def parent_relations(self, child_id: str, ignore_referent: bool = False) -> List[Tuple[str, Relation]]:
        """
        :param child_id: the child ID.
        :return: list of (relation ID, Relation) with the specific child.
        """
        if child_id not in self.concepts: return []
        return [(rid, r) for rid, r in self.relations.items() if r.child_id == child_id and not (ignore_referent and r.referent)]

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

    def get_child_ids(self, parent_id, ignore_referent: bool) -> Set[str]:
        """
        :param parent_id: the ID of the parent concept.
        :param ignore_referent: if True, ignore relations where the child concept is a referent.
        :return: the set of child IDs
        """
        return {r.child_id for _, r in self.child_relations(parent_id, ignore_referent)}

    def get_parent_ids(self, child_id, ignore_referent: bool) -> Set[str]:
        """
        :param child_id: the ID of the child concept.
        :param ignore_referent: if True, ignore relations where the child concept is a referent.
        :return: the set of parent IDs
        """
        return {r.parent_id for _, r in self.parent_relations(child_id, ignore_referent)}

    def is_ancestor(self, concept_id1: str, concept_id2: str, ignore_referent: bool = False) -> bool:
        """
        :param concept_id1: the ID of the first concept.
        :param concept_id2: the ID of the second concept.
        :param ignore_referent: if True, ignore relations where the child concept is a referent.
        :return: True if the first concept is an ancestor of the second concept.
        """
        parent_ids = self.get_parent_ids(concept_id2, ignore_referent)
        if concept_id1 in parent_ids: return True
        for parent_id in parent_ids:
            if self.is_ancestor(concept_id1, parent_id, ignore_referent):
                return True
        return False

    def _update_first_token_ids(self, concept_id: str, first_token_id: int):
        for parent_id in self.get_parent_ids(concept_id, True):
            parent = self.get_concept(parent_id)
            if not parent.token_ids and first_token_id < parent.first_token_id:
                parent.first_token_id = first_token_id
                self._update_first_token_ids(parent_id, first_token_id)

    def _assign_first_token_ids(self):
        MAX, count = 1000000, 0
        for cid, concept in self.concepts.items():
            if concept.token_ids:
                concept.first_token_id = concept.token_ids[0]
            else:
                concept.first_token_id = MAX
                count += 1

        while count > 0:
            prev_count = count
            for cid, concept in self.concepts.items():
                first_token_id = concept.first_token_id
                if first_token_id < MAX:
                    for parent_id in self.get_parent_ids(cid, True):
                        parent = self.get_concept(parent_id)
                        if not parent.token_ids and first_token_id < parent.first_token_id:
                            if parent.first_token_id == MAX: count -= 1
                            parent.first_token_id = first_token_id
            if prev_count == count: break

    def penman(self, concept_id: str, amr: bool) -> str:
        """
        :param concept_id: the ID of the root concept.
        :param amr: if True, the return notation is compatible to AMR.
        :return: the Penman notation of the concept's subtree.
        """

        def repr_concept(rel: Relation) -> str:
            if rel.referent: return rel.child_id
            c = self.concepts[rel.child_id]
            if amr and c.attribute and self.parent_relations(rel.child_id): return c.name
            return '({} / {}'.format(rel.child_id, c.name)

        def aux(rel: Relation, r: List[str], indent: str):
            cname = repr_concept(rel)
            r.append(cname)
            if not rel.referent:
                indent += ' ' * (len(rel.child_id) + 2)
                for rid, relation in sorted(self.child_relations(rel.child_id), key=lambda x: self.get_concept(x[1].child_id).first_token_id):
                    r.append('\n{}:{} '.format(indent, relation.label))
                    aux(relation, r, indent + ' ' * (len(relation.label) + 2))
                if cname.startswith('('): r.append(')')

        def alignments():
            ts = [(concept.token_ids[0], '{}/{}'.format(cid, ','.join(map(str, concept.token_ids)))) for cid, concept in self.concepts.items() if concept.token_ids]
            return ' '.join([v for k, v in sorted(ts)])

        rep = []
        aux(Relation('', concept_id, ''), rep, '')
        if amr:
            meta = '# ::{} {} ::{} {} ::{} {}\n# ::{} {}\n'.format(
                PENMAN_TID, self.tid,
                PENMAN_LAST_SAVED, self.last_saved,
                PENMAN_ANNOTATOR, self.annotator,
                PENMAN_TEXT, ' '.join(self.tokens))
            align = alignments()
            if align: meta = '{}# ::{} {}\n'.format(meta, PENMAN_ALIGNMENTS, align)
            return meta + ''.join(rep)
        else:
            return ''.join(rep)

    def penman_graphs(self, amr: bool = False) -> List[str]:
        """
        :param amr: if True, the return notation is compatible to AMR.
        :return: list of graphs in the Penman notation.
        """
        self._assign_first_token_ids()
        return [self.penman(root_id, amr) for root_id in self.root_ids]

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


def penman_reader(input_file: str) -> Optional[List[Graph]]:
    class DynamicStack:
        def __init__(self):
            self.concept_stack: List[str] = list()
            self.cid_map: Dict[str, str] = dict()
            self.relation: Optional[str] = None

        def push_concept(self, org_cid: str, new_cid: str):
            self.concept_stack.append(new_cid)
            self.cid_map[org_cid] = new_cid

        def pop_concept(self) -> str:
            return self.concept_stack.pop()

    def trim_line(ln):
        ln = ln.strip()
        ln = RE_LRB.sub('(', ln)
        ln = RE_RRB.sub(')', ln)
        return ln

    def parse_comments(cdict: Dict[str, str], ln: str):
        key, values = None, []

        for t in ln.split():
            if t.startswith('::'):
                if key: cdict[key] = ' '.join(values) if values else True
                key, values = t[2:], []
            else:
                values.append(t)

        if key: cdict[key] = ' '.join(values) if values else True

    def create_graph(cdict: Dict[str, str]) -> Graph:
        text = cdict.get(PENMAN_TEXT, '')
        tid = cdict.get(PENMAN_TID, None)
        annotator = cdict.get(PENMAN_ANNOTATOR, cdict.get('amr-annotator', None))
        last_saved = cdict.get(PENMAN_LAST_SAVED, None)
        return Graph(text, tid, annotator, last_saved)

    def get_concept_name(cname: str):
        for j in range(len(cname), 0, -1):
            if cname[j - 1] != ')':
                return cname[:j], len(cname) - j
        return None, -1

    def handle_relation(cid: str, referent: bool = False) -> bool:
        if dstack.relation:
            if not dstack.concept_stack:
                print('Line {}: missing parent concept'.format(lid))
                return False
            pid = dstack.concept_stack[-1]
            graph.add_relation(pid, cid, dstack.relation, referent)
            dstack.relation = None
        return True

    def populate_graph(graph: Graph, dstack: DynamicStack, lid: int, line: str) -> bool:
        ts = line.split()
        i, n, skip = 0, len(ts), False

        while i < n:
            t = ts[i]
            if t.startswith('('):
                if not (i + 2 < n and ts[i + 1] == '/'):
                    print('Line {}: invalid concept definition'.format(lid))
                    return False

                org_cid = t[1:]
                i += 2
                cname, nrrb = get_concept_name(ts[i])
                if cname is None:
                    print('Line {}: invalid concept definition'.format(lid))
                    return False

                new_cid = graph.add_concept(cname)
                if not handle_relation(new_cid): return False
                dstack.push_concept(org_cid, new_cid)
                for _ in range(nrrb): dstack.pop_concept()
            elif t.startswith(':'):
                dstack.relation = t[1:]
            else:
                cname, nrrb = get_concept_name(t)
                if cname is None:
                    print('Line {}: invalid concept definition'.format(lid))
                    return False

                new_cid = dstack.cid_map.get(cname, None)
                if new_cid:
                    if not handle_relation(new_cid, True): return False
                else:
                    new_aid = graph.add_concept(cname, attribute=True)
                    if not handle_relation(new_aid): return False
                for _ in range(nrrb): dstack.pop_concept()
            i += 1
        return True

    def to_alignments(comments: Dict[str, str]):
        v = comments.get(PENMAN_ALIGNMENTS, None)
        if v is None: return dict()
        d = dict()
        for t in v.split():
            idx = t.find('/')
            if idx < 0: return None
            cid = t[:idx]
            tids = list(map(int, t[idx + 1:].split(',')))
            d[cid] = tids
        return d

    def finalize_graph(g: Graph, dstack: DynamicStack, comments: Dict[str, str]) -> Graph:
        for cid, concept in list(g.concepts.items()):
            if concept.attribute:
                new_cid = dstack.cid_map.get(concept.name, None)
                if new_cid:
                    for rid, relation in g.parent_relations(cid):
                        relation.child_id = new_cid
                        relation.referent = True
                    g.remove_concept(cid, False)

        for org_cid, tids in to_alignments(comments).items():
            new_cid = dstack.cid_map.get(org_cid, '')
            c = g.get_concept(new_cid)
            if c:
                g.covered_token_ids.update(tids)
                c.token_ids = tids

        return g

    RE_LRB = re.compile(r'\(\s+')
    RE_RRB = re.compile(r'\s+\)')
    graph, comments, dstack = None, dict(), DynamicStack()
    fin = open(input_file)
    graphs = []

    for lid, line in enumerate(fin, 1):
        line = trim_line(line)
        if not line: continue

        if line.startswith('#'):
            parse_comments(comments, line)
            continue

        if graph is None:
            if not line.startswith('('):
                print('Line {}: missing concept definition'.format(lid))
                return None
            graph = create_graph(comments)

        if not populate_graph(graph, dstack, lid, line):
            return None

        if not dstack.concept_stack:
            graphs.append(finalize_graph(graph, dstack, comments))
            graph, comments, dstack = None, dict(), DynamicStack()

    return graphs
