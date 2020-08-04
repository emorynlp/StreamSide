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

from streamside.struct import Graph


class TestGraph(unittest.TestCase):
    # The boy want the girl not to believe him
    # 0123456789012345678901234567890123456789
    #           1         2         3
    amr = Graph('The boy want the girl not to believe him')

    def test_add_concept(self):
        # ' boy '
        cid = self.amr.add_concept('boy', 3, 8)
        self.assertEqual('c0', cid)
        c = self.amr.get_concept(cid)
        self.assertEqual(('boy', 4, 7), (c.name, c.begin, c.end))

        # 'want'
        cid = self.amr.add_concept('want-01', 8, 12)
        self.assertEqual('c1', cid)
        c = self.amr.get_concept(cid)
        self.assertEqual(('want-01', 8, 12), (c.name, c.begin, c.end))

        # `ir'
        cid = self.amr.add_concept('girl', 18, 20)
        self.assertEqual('c2', cid)
        c = self.amr.get_concept(cid)
        self.assertEqual(('girl', 17, 21), (c.name, c.begin, c.end))

        # 'believe'
        self.amr.add_concept('believe-01', 29, 36)

        # 'not'
        cid = self.amr.add_concept('-', 22, 25, True)
        c = self.amr.get_concept(cid)
        self.assertEqual(('-', True), (c.name, c.attr))

        # Donald Trump is the president of the United States
        # 01234567890123456789012345678901234567890123456789
        amr = Graph('Donald Trump is the president of the United States')

        # 'Donald T'
        cid = amr.add_concept('Trump', 0, 8)
        c = amr.get_concept(cid)
        self.assertEqual(('Trump', 0, 12), (c.name, c.begin, c.end))

        # 'ed States'
        cid = amr.add_concept('Trump', 41, 50)
        c = amr.get_concept(cid)
        self.assertEqual(('Trump', 37, 50), (c.name, c.begin, c.end))

    def test_add_relation(self):
        # ARG0(want, boy)
        rid = self.amr.add_relation('c1', 'c0', 'ARG0')
        self.assertEqual('r0', rid)
        r = self.amr.get_relation(rid)
        self.assertEqual(('c1', 'c0', 'ARG0', False), (r.pid, r.cid, r.label, r.ref))

        # ARG1(want, believe)
        self.amr.add_relation('c1', 'c3', 'ARG1')

        # ARG0(believe, girl)
        self.amr.add_relation('c3', 'c2', 'ARG0')

        # ARG1(believe, boy)
        rid = self.amr.add_relation('c3', 'c0', 'ARG1', True)
        self.assertEqual('r3', rid)
        r = self.amr.get_relation(rid)
        self.assertEqual(('c3', 'c0', 'ARG1', True), (r.pid, r.cid, r.label, r.ref))

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
        self.assertEqual(s, json.dumps(amr, default=lambda x: x.__dict__))

    def test_remove_concept(self):
        amr = self.amr.clone()
        self.assertEqual(['c1'], amr.root_ids)

        c3 = amr.remove_concept('c3')
        self.assertEqual(['c1', 'c2', 'c4'], amr.root_ids)

        amr.add_concept(c3.name, c3.begin, c3.end)
        self.assertEqual(['c1', 'c2', 'c4', 'c5'], amr.root_ids)

    def test_remove_relation(self):
        amr = self.amr.clone()
        s = '\n'.join(amr.penman_graphs())

        r1 = amr.remove_relation('r1')
        self.assertEqual(['c1', 'c3'], amr.root_ids)

        amr.add_relation(r1.pid, r1.cid, r1.label, r1.ref)
        self.assertEqual(s, '\n'.join(amr.penman_graphs()))


if __name__ == '__main__':
    unittest.main()
