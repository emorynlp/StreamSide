# Graph Annotator

## Launch

The following describes the command to launch the graph annotator:

```bash
python -m streamside.annotator -a ANNOTATOR_ID [-m wisen|amr -r RESOURCE_DIR] &
```
* `-a` or `--annotator`: the ID of the annotator (required).
* `-m` or `--mode`: choose the representation `wisen` (default) or `amr`.
* `-r` or `--resources`: the path to a custom resource directory; if not specified, it uses the default [resources](../streamside/resources/).


## Annotate

> If you are using a mac, replace the `Ctrl` key with the `Cmd` key .

### Open File

Press `Ctrl+o` to prompt a file dialog:

* For the initial annotation, choose a text file comprising a sentence per line (e.g., [training-examples.txt](training-examples.txt)).
* For a returning annotation, choose a JSON file that is previously saved (e.g., [training-examples.jdchoi.json](training-examples.jdchoi.json)).

### Save File

Press `Ctrl+s` to save the current annotation to the JSON file whose name includes the annotator ID.

### Create Concept

Any of the following actions will prompt the input dialog to create a concept:

* For a concept aligned to no word span, simply press `c`.
* For a concept aligned to a consecutive word span, highlight the span and press `c`.
* For a concept aligned to disjoint word spans, highlight each span and press `x` that selects the span and shows it in a <span style="background-color:khaki;">yellow</span> background. When all spans are selected, press `c`.

> Spans that are already aligned to previously created concepts cannot be selected.

To deselect spans:

* Highlight spans to deselect and press `Shift+x`. The highlighted span could include words that were not selected; any selected word within the highlight will be deselected.
* To deselect all selected spans, press `Shift+x` without highlighting any word.


Once the input dialog is prompted:

* Type the concept name; predefined concepts will be auto-completed by the input textbox.
* Press `Enter` or the `OK` button to create the concept.

Once the concept is created, its spans are displayed in <span style="background-color:lightgray;">gray</span> on the text.

### Create Attribute

Attribute can be created in the exact same way as the concept by pressing `a` instead of `c`.

### Create Relation

The following actions will prompt the input dialog to create a relation:

* Highlight the ID of the parent concept in the graph and press `w` that selects and shows the parent in <span style="background-color:lightpink;">pink</span>.
* Highlight the ID of the child concept in the graph and press `e` that selects and shows the child in <span style="background-color:lightgreen;">green</span>.
* Once the parent and the child concepts are selected, press `r` to create a relation.

> The parent and child IDs must be selected to create a relation.

To deselect the IDs:

* Press `Shift+w` to deselect the parent concept.
* Press `Shift+e` to deselect the parent concept.

Once the input dialog is prompted:

* Type the relation label; predefined labels will be auto-completed by the input textbox.
* To make the child concept as a referent argument, press `Ctrl+r` or check the `Referent` box.
* To make an inverse relation (`*-of`), press `Ctrl+f` or check the `Inverse` box.
* Press `Enter` or the `OK` button to create the concept.

### Delete

To delete a concept or an attribute:

* Highlight the ID of the concept/attribute and press `Ctrl+d`.

To delete a relation:

* Highlight the label of the relation and press `Ctrl+d`.

### Update

To update the name of a concept or an attribute:

* Highlight the ID of the concept/attribute and press `Ctrl+f`.

To update the label of a relation:

* Highlight the label of the relation and press `Ctrl+f`.


### Navigate

* To move to the previous sentence, press `,`.
* To move to the next sentence, press `.`.
* To move to the first sentence, press `Ctrl+,`.
* To move to the last sentence, press `Ctrl+.`.
* To jump to a certain sentence, press `Ctrl+/` and choose the sentence ID.
