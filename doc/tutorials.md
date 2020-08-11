# Tutorials

> If you are using a mac, use the `Cmd` key instead of the `Ctrl` key.

## Open File

Press `Ctrl+o` to prompt a file dialog:

* For the initial annotation, choose a text file that consists of a sentence per line.
* For a returning annotation, choose a JSON file that is previously saved.

## Save File

Press `Ctrl+s` to save the current annotation to the JSON file whose name indicates the annotator ID.

## Create Concept

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
* To see the description of a predefined concept, press `Ctrl+d` or the `Describe` button.
* To make this concept as an attribute, press `Ctrl+r` or check the `Attribute` box.
* Press `Enter` or the `OK` button to create the concept.

Once the concept is created, its spans are displayed in <span style="background-color:lightgray;">gray</span> on the text.

## Create Relation

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
* To see the description of a predefined concept, press `Ctrl+d` or the `Describe` button.
* To make the child concept as a referent argument, press `Ctrl+r` or check the `Referent` box.
* To make an inverse relation (`*-of`), press `Ctrl+f` or check the `Inverse` box.
* Press `Enter` or the `OK` button to create the concept.

## Navigate

* To move to the previous sentence, press `,`.
* To move to the next sentence, press `.`.
* To move to the first sentence, press `Ctrl+,`.
* To move to the last sentence, press `Ctrl+.`.
* To jump to a certain sentence, press `Ctrl+/` and choose the sentence ID.
