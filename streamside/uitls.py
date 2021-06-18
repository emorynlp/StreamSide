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


def create_concept_json():
    resource_dir = 'resources/wiser'
    cson = dict()

    d = json.load(open(os.path.join(resource_dir, 'concept-predicate.json')))
    for k in d: cson[k.lower()] = 'Predicate'

    for l in open(os.path.join(resource_dir, 'concept-date.txt')):
        cson[l.strip().lower()] = 'Date entity'

    for l in open(os.path.join(resource_dir, 'concept-name.txt')):
        cson[l.strip().lower()] = 'Named entity'

    for l in open(os.path.join(resource_dir, 'concept-quantity.txt')):
        cson[l.strip().lower()] = 'Quantity entity'

    for l in open(os.path.join(resource_dir, 'concept-misc.txt')):
        cson[l.strip().lower()] = 'Miscellaneous entity'

    json.dump(cson, open(os.path.join(resource_dir, 'concept-desc.json'), 'w'), indent=2)


def map_concept():
    resource_dir = 'resources/wiser'
    pred = json.load(open(os.path.join(resource_dir, 'concept-predicate.json')))
    cson = json.load(open(os.path.join(resource_dir, 'concept-desc.json')))

    for k, v in cson.items():
        d = {'description': v}
        e = pred.get(k, None)
        if e: d['aliases'] = e['aliases']
        cson[k] = d

    json.dump(cson, open(os.path.join(resource_dir, 'concepts.json'), 'w'), indent=2)


def create_relation_json():
    resource_dir = 'resources/wiser'
    cson = dict()

    for l in open(os.path.join(resource_dir, 'relation-core.txt')):
        cson[l.strip()] = {'description': 'Central relation'}

    for l in open(os.path.join(resource_dir, 'relation-non_core.txt')):
        cson[l.strip().lower()] = {'description': 'Peripheral relation'}

    for l in open(os.path.join(resource_dir, 'relation-date.txt')):
        cson[l.strip().lower()] = {'description': 'Date relation'}

    json.dump(cson, open(os.path.join(resource_dir, 'relations.json'), 'w'), indent=2)


def add_field_to_concept(concept_file):
    ds = json.load(open(concept_file))

    for k, v in ds.items():
        desc = v['description']
        if desc.startswith('Predicate'):
            vtype = 'pred'
        elif desc.startswith('Named'):
            vtype = 'name'
        elif desc.startswith('Quant'):
            vtype = 'quant'
        elif desc.startswith('Date'):
            vtype = 'date'
        elif desc.startswith('Misc'):
            vtype = 'misc'
        elif desc.startswith('Attribute'):
            vtype = 'attr'
        else:
            print(desc)

        v['type'] = vtype

    json.dump(ds, open(concept_file + '.json', 'w'), indent=2)


def amr_concept_json():
    cson = dict()

    d = json.load(open('resources/amr/frames-arg_descriptions.json'))
    for k, v in d.items():
        cson[k] = dict(description='\n'.join(['{}: {}'.format(a, b) for a, b in sorted(v.items())]), type='pred')

    for line in open('resources/amr/concept-name.txt'):
        cson[line.strip()] = dict(description='Named entity', type='name')

    for line in open('resources/amr/concept-quantity.txt'):
        cson[line.strip()] = dict(description='Quantity entity', type='quant')

    for line in open('resources/amr/concept-date.txt'):
        cson[line.strip()] = dict(description='Date entity', type='date')

    for line in open('resources/amr/concept-misc.txt'):
        cson[line.strip()] = dict(description='Miscellaneous entity', type='misc')

    for line in open('resources/amr/attributes.txt'):
        cson[line.strip()] = dict(description='Attribute', type='attr')

    json.dump(cson, open('resources/amr/concepts.json', 'w'), indent=2)


def add_field_to_relation(relation_file):
    ds = json.load(open(relation_file))

    for k, v in ds.items():
        desc = v['description']
        if desc.startswith('Central'):
            vtype = 'core'
        elif desc.startswith('Peripheral'):
            vtype = 'non_core'
        elif desc.startswith('Date'):
            vtype = 'date'
        else:
            print(desc)

        v['type'] = vtype

    json.dump(ds, open(relation_file + '.json', 'w'), indent=2)


def amr_concept_json():
    cson = dict()

    for line in open('resources/amr/relation-core.txt'):
        cson[line.strip()] = dict(description='Central relation', type='core')

    for line in open('resources/amr/relation-non_core.txt'):
        cson[line.strip()] = dict(description='Peripheral relation', type='oblique')

    for line in open('resources/amr/relation-date.txt'):
        cson[line.strip()] = dict(description='Date relation', type='date')

    json.dump(cson, open('resources/amr/relations.json', 'w'), indent=2)



if __name__ == "__main__":
    # frames_to_json('resources/propbank-amr-frames-arg-descr.txt')
    # propbank_frames_to_json('resources/amr/propbank-frames-xml/', 'resources/wiser/concept-predicate.json', 'resources/amr/propbank-amr-frames-arg-descr.txt')
    # create_concept_json()
    # map_concept()
    # create_relation_json()
    # add_field_to_concept('resources/wiser/concepts.json')
    # amr_concept_json()
    # add_field_to_relation('resources/wiser/relations.json')
    # amr_concept_json()
    pass