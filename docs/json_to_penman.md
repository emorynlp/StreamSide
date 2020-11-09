# JSON to Penman Converter

The following command converts the JSON files generated by StreamSide to the Penman notation:

```bash
python -m streamside.json_to_penman -i INPUT_PATH [-o OUTPUT_PATH]
```
* `-i` or `--input`: the path to a JSON file or a directory containing JSON files (required).
* `-o` or `--output`: the path to the output file(s) (default: the input directory).