# StreamSide Guidelines

## Text Alignment

In the simple case, align a concept with the corresponding span.

> The boy wanted the apple

		(w / want-01
			:ARG0 (b / boy)
			:ARG1 (a / apple))

Align 'boy' with `b`, 'want' with `w`, and 'apple' with `a`

The quickest way to do this is to highlight 'boy' and press c on the keyboard, this will open the *Create a concept* box with the string 'boy' already present in the search bar, hit enter. Do the same thing for predicates like 'want' but make sure you pick the correct predicate sense `want-01`. Do not include function words such as the determiner 'the' in the span aligned with `b`.

Verb-particle constructions such as 'pick up' often feature alignment between a concept and two disjoint spans of text.

> The boy picked the apple up

		(p / pick-up-11
			:ARG0 (b / boy)
			:ARG1 (a / apple))

Highlight the verb 'picked' and press x, this will leave the span selected. Next highlight the particle 'up' and press c. This will open the *Create a concept* box with the string 'picked-up' in the search bar. Delete this until you get to just 'pick', then choose the correct sense `pick-up-11` from the search results.

For instances of coreference, align every coreferential term with the same node.

> The boy wanted the girl to believe him

		(w / want-01
			:ARG0 (b / boy)
			:ARG1 (b2 / believe-01
				:ARG0 (g / girl)
				:ARG1 b))

Here align both 'boy' and 'him' with node `b`. You can do this in two ways:

1. Highlight 'boy' and press x, then highlight 'him' and press c. This will open the *Create a concept* box with the string 'boy-him' already present. Delete 'him' create an instance of the concept `boy`.
2. Alternatively, you can highlight 'boy' and press c, creating an instance of the concept `boy`. Then highlight the variable ID `b` associated with that concept and press z to keep it selected, next highlight the span 'him' and press v.

Option 1 is generally easier, but option 2 is useful if you missed one or more coreferential terms when you first created the concept.

If a complex concept is aligned with a single word, align the span with the concept or attribute which carries the most relevant information. Align name 'California', with the name attribute `"Califonia"` not with `s` or `n`.

> California

		(s / state
			:name (n / name
				:op "California"))

To do this, highlight the span 'California' and press a, this will open the *Create an attribute* box with the string 'California' entered in the search bar. Surround the string with double quotation marks and press enter.

Similarly for agentive and relational nouns.

> dancer

		(p / person
			:ARG0-of (d / dance-01))

Align 'dancer' with `d`, the instance of the concept `dance-01`.

> my uncle

		(p / person
			:ARG0-of (h / have-rel-role-91
				:ARG1 (i / i)
				:ARG2 (u / uncle)))

Align 'uncle' with `u` and 'my' with `i`.

Even though an uncle or a dancer is a person, align 'dancer' with `dance-01` and 'uncle' with `uncle` since these are the single concepts most closely related to the resepective words.


## Attributes

The following constants are all attributes:

* `-` for `:polarity`
* `+` for `:polite`
* `expressive` and `imperative` for `:mode`
* integers e.g., `23` for `:value` etc.
* strings e.g., `"California"` for name enitities

These should be created using either *Create Attribute* from the *Edit* menu, or by using the keyboard shortcut a.


## Reentrancies

When reusing a variabe ID for a new relation, StreamSide will automatically check the *referent* box in the *Create a relation* pop up.

Inverse relations can be created by either checking the *-of* box, or by pressing ctl+f when creating a new relation. You can also add '-of' to the end of the relation label.
