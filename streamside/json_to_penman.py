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

import argparse
import glob
import json
import os

from streamside.struct import Graph


def convert(input_file: str, output_dir: str):
    output_file = os.path.join(output_dir, os.path.basename(input_file)[:-4] + 'penman')
    fout = open(output_file, 'w')
    d = json.load(open(input_file))

    for g in d['graphs']:
        graph = Graph.factory(g)
        if graph.concepts:
            fout.write('\n'.join(graph.penman_graphs(True)) + '\n\n')


def main():
    parser = argparse.ArgumentParser(description='JSON to Penman Converter')
    parser.add_argument('-i', '--input', type=str, help='the path to a JSON file or a directory containing JSON files')
    parser.add_argument('-o', '--output', type=str, default=None, help='the path to the output file(s)')
    args = parser.parse_args()

    output_dir = args.output if args.output else os.path.dirname(args.input)
    if os.path.isdir(args.input):
        for input_file in glob.glob(os.path.join(args.input, '*.json')):
            convert(input_file, output_dir)
    else:
        convert(args.input, output_dir)


if __name__ == "__main__":
    main()
