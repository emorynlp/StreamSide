# Getting Started

Upgrade the pip version of Python 3 if needed:

```bash
$ python3 -m pip install --upgrade pip
$ python3 -m pip --version
```

Install a virtual environment using Python 3 if needed:

```bash
$ python3 -m pip install --user virtualenv
```

Create a virtual environment:

```bash
$ python3 -m venv venv
```

Activate the virtual environment:

```bash
$ source venv/bin/activate
```

Under the virtual environment, install StreamSide:

```bash
(venv) $ pip install streamside
```

Launch the [Graph Annotator](graph_annotator.md) using the following command (replace `ANNOTATOR_ID` with your ID):

```bash
(venv) $ python streamside.annotator -a ANNOTATOR_ID &
```
