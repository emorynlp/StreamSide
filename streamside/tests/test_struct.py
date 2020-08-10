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

import json
import unittest

from streamside.struct import Graph, OffsetMap, Offset


class TestGraph(unittest.TestCase):
    # The boy want the girl not to believe him
    # 0123456789012345678901234567890123456789
    #           1         2         3
    text = 'The boy want the girl not to believe him'
    amr = Graph(text)

    def test_add_concept(self):
        offmap = OffsetMap(self.amr.tokens)

        # ' boy '
        cid = self.amr.add_concept('boy', offmap.token_ids(Offset(3, 8)))
        self.assertEqual('c0', cid)
        c = self.amr.get_concept(cid)
        self.assertEqual(('boy', [1]), (c.name, c.token_ids))

        # 'want'
        cid = self.amr.add_concept('want', offmap.token_ids(Offset(8, 12)))
        self.assertEqual('c1', cid)
        c = self.amr.get_concept(cid)
        self.assertEqual(('want', [2]), (c.name, c.token_ids))

        # `ir'
        cid = self.amr.add_concept('girl', offmap.token_ids(Offset(18, 20)))
        self.assertEqual('c2', cid)
        c = self.amr.get_concept(cid)
        self.assertEqual(('girl', [4]), (c.name, c.token_ids))

        # 'believe'
        cid = self.amr.add_concept('believe', offmap.token_ids(Offset(29, 36)))
        self.assertEqual('c3', cid)
        c = self.amr.get_concept(cid)
        self.assertEqual(('believe', [7]), (c.name, c.token_ids))

        # 'not'
        cid = self.amr.add_concept('-', offmap.token_ids(Offset(22, 25)), True)
        c = self.amr.get_concept(cid)
        self.assertEqual(('-', [5], True), (c.name, c.token_ids, c.attribute))

        # 'want' again
        cid = self.amr.add_concept('want', offmap.token_ids(Offset(8, 12)))
        self.assertIsNone(cid)

    def test_add_relation(self):
        # ARG0(want, boy)
        rid = self.amr.add_relation('c1', 'c0', 'ARG0')
        self.assertEqual('r0', rid)
        r = self.amr.get_relation(rid)
        self.assertEqual(('c1', 'c0', 'ARG0', False), (r.parent_id, r.child_id, r.label, r.referent))

        # ARG1(want, believe)
        self.amr.add_relation('c1', 'c3', 'ARG1')

        # ARG0(believe, girl)
        self.amr.add_relation('c3', 'c2', 'ARG0')

        # ARG1(believe, boy)
        rid = self.amr.add_relation('c3', 'c0', 'ARG1', True)
        self.assertEqual('r3', rid)
        r = self.amr.get_relation(rid)
        self.assertEqual(('c3', 'c0', 'ARG1', True), (r.parent_id, r.child_id, r.label, r.referent))

        # polarity(believe, -)
        self.amr.add_relation('c3', 'c4', 'polarity')

    def test_child_relations(self):
        self.assertEqual([], self.amr.child_relations('c0'))
        self.assertEqual([('r0', self.amr.relations['r0']), ('r1', self.amr.relations['r1'])], self.amr.child_relations('c1'))
        self.assertEqual([], self.amr.child_relations('c2'))
        self.assertEqual([('r2', self.amr.relations['r2']), ('r3', self.amr.relations['r3']), ('r4', self.amr.relations['r4'])], self.amr.child_relations('c3'))

    def test_parent_relations(self):
        self.assertEqual([('r0', self.amr.relations['r0']), ('r3', self.amr.relations['r3'])], self.amr.parent_relations('c0'))
        self.assertEqual([], self.amr.parent_relations('c1'))
        self.assertEqual([('r2', self.amr.relations['r2'])], self.amr.parent_relations('c2'))
        self.assertEqual([('r1', self.amr.relations['r1'])], self.amr.parent_relations('c3'))
        self.assertEqual([('r4', self.amr.relations['r4'])], self.amr.parent_relations('c4'))

    def test_json(self):
        s = self.amr.json_dumps()
        d = json.loads(s)
        amr = Graph.factory(d)
        self.assertEqual(s, amr.json_dumps())

    def test_remove_concept(self):
        amr = self.amr.clone()
        self.assertEqual(['c1'], amr.root_ids)

        c3 = amr.remove_concept('c3')
        self.assertEqual(['c1', 'c2', 'c4'], amr.root_ids)

        amr.add_concept(c3.name, set())
        self.assertEqual(['c1', 'c2', 'c4', 'c5'], amr.root_ids)

    def test_remove_relation(self):
        amr = self.amr.clone()
        s = '\n'.join(amr.penman_graphs())

        r1 = amr.remove_relation('r1')
        self.assertEqual(['c1', 'c3'], amr.root_ids)

        amr.add_relation(r1.parent_id, r1.child_id, r1.label, r1.referent)
        self.assertEqual(s, '\n'.join(amr.penman_graphs()))


if __name__ == '__main__':
    unittest.main()
