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


if __name__ == "__main__":
    frames_to_json('resources/propbank-amr-frames-arg-descr.txt')
