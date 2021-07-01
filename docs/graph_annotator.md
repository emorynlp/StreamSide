# Graph Annotator

## Launch

The following describes the command to launch the graph annotator:

```bash
python -m streamside.annotator -a ANNOTATOR_ID [-s wiser|amr -r RESOURCE_DIR] &
```
* `-a` or `--annotator`: the ID of the annotator (required).
* `-s` or `--scheme`: choose the representation `wisen` (default) or `amr`.
* `-r` or `--resources`: the path to a custom resource directory; if not specified, it uses the default [resources](../streamside/resources/).

> For the following sections, replace the `Ctrl` key with the `Cmd` key if you are using a mac.


## File Menu

### Open

Press `Ctrl+o` to prompt a file dialog:

* For the initial annotation, choose a text file comprising a sentence per line (e.g., [sample-amr.txt](../samples/sample-amr.txt)).
* For a returning annotation, choose a JSON file that is previously saved (e.g., [sample-amr.jdchoi.json](../samples/sample-amr.jdchoi.json)).
* If you have an existing annotation in the Penman notation, choose a Penman file (e.g., [sample-amr.penman](../samples/sample-amr.penman)).

> StreamSide supports only the following file extensions: `txt`, `json`, `penman`. 

### Save

Press `Ctrl+s` to save the current annotation to the JSON file whose name includes the annotator ID.

### Quit

Press `Ctrl+q` to quit the annotator.


## Edit Menu

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

> The `Referent` box gets automatically checked if (1) the child concept already has another parent concept or (2) if the child concept is an ancestor of the parent concept.   

### Update

To update the name of a concept or an attribute:

* Highlight the ID of the concept/attribute and press `Ctrl+f`.

To update the label of a relation:

* Highlight the label of the relation and press `Ctrl+f`.

### Delete

To delete a concept or an attribute:

* Highlight the ID of the concept/attribute and press `Ctrl+d`.

To delete a relation:

* Highlight the label of the relation and press `Ctrl+d`.

### Add/Remove Text Span

To add/remove certain text spans to an existing concept (or attribute):

* Highlight the ID of the concept and press `z` that shows it as well as text spans associated with the concept in a <span style="background-color:burlywood;">burlywood</span> background.
* Highlight text spans you want to add/remove to/from the concept and press `v`.
* To deselect the concept/attribute, press `Shift+z`.

### Navigate

* To move to the previous sentence, press `,`.
* To move to the next sentence, press `.`.
* To move to the first sentence, press `Ctrl+,`.
* To move to the last sentence, press `Ctrl+.`.
* To jump to a certain sentence, press `Ctrl+/` and choose the sentence ID.
