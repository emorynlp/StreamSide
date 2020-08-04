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

import glob
import json
import os
from collections import OrderedDict
from xml.etree import ElementTree


def frames_to_json(text_file: str):
    def aux(ts, bidx, eidx, args):
        label = ts[bidx]
        if label.endswith(':'): label = label[:-1]
        args[label] = ' '.join(ts[bidx + 1:eidx])

    fin = open(text_file)
    d = dict()

    for line in fin:
        tokens = line.split()
        frame_id = tokens[0]
        arguments = dict()
        tokens = tokens[1:]
        begin = 0

        for i, token in enumerate(tokens):
            if token.startswith('ARG'):
                if begin < i: aux(tokens, begin, i, arguments)
                begin = i
        if begin < len(tokens):
            aux(tokens, begin, len(tokens), arguments)

        d[frame_id] = arguments

    json_file = text_file[:-3] + 'json'
    json.dump(d, open(json_file, 'w'), indent=2)


def propbank_frames_to_json(frame_dir: str, json_file: str, arg_file: str):
    frames = dict()

    for filename in sorted(glob.glob(os.path.join(frame_dir, '*.xml'))):
        tree = ElementTree.parse(filename)
        source = os.path.basename(filename)
        for predicate in tree.findall('predicate'):
            lemma = predicate.attrib['lemma'].replace('-', '_')
            d = frames.setdefault(lemma, {'sources': [], 'aliases': {lemma}})
            sources = d['sources']
            aliases = d['aliases']
            sources.append(source)
            for alias in predicate.iter('alias'): aliases.add(alias.text.replace('-', '_'))
            if len(sources) > 1: print('{}: {}'.format(lemma, str(sources)))

    for lemma, d in frames.items(): d['aliases'] = sorted(list(d['aliases']))
    print("Predicates from frameset files: {}".format(len(frames)))

    source = os.path.basename(arg_file)
    for line in open(arg_file):
        lemma = line.split()[0]
        lemma = lemma[:lemma.rfind('-')]
        lemma = lemma.replace('-', '_')
        if lemma not in frames:
            frames[lemma] = {'sources': [source], 'aliases': [lemma]}

    print("+ AMR: {}".format(len(frames)))
    frames = OrderedDict({k: v for k, v in sorted(frames.items())})
    json.dump(frames, open(json_file, 'w'), indent=2)
    return frames


if __name__ == "__main__":
    # frames_to_json('resources/propbank-amr-frames-arg-descr.txt')
    propbank_frames_to_json('resources/amr/propbank-frames-xml/', 'resources/lexica/concept-predicate.json', 'resources/amr/propbank-amr-frames-arg-descr.txt')
    pass