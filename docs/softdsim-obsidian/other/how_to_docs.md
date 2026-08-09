# Writing Documentation

Our documentation is hosted on [Read The Docs](https://readthedocs.org/). All source files related to the documentation are located in the `docs/` directory.


## Example: Creating a New Documentation Page

Suppose you want to create a new documentation page (such as this one) explaining how to write documentation. You would start by creating a new directory `docs/documentation` and then add a new file named `how_to.md`. This file uses Markdown, a lightweight markup language for writing formatted text. For guidance, you can refer to the existing file `docs/documentation/how_to.md`.


## Adding to the Table of Contents

Next, include your new file in the table of contents by editing `docs/index.rst`. Add the relative path of your file like so:

```rst
.. toctree::
   api/endpoints.md
   api/endpoints/test_endpoint.md
   api/reference.md
   documentation/how_to.md
```


## Deployment

Once your changes are complete, push your code to GitHub. Shortly after the code is merged into the `develop` branch, the new documentation will automatically appear on Read The Docs.


## Markdown Overview

Refer to the [Basic Markdown Syntax Guide](https://www.markdownguide.org/basic-syntax/) for more detailed information.

### Key Markdown Elements

### Headings

```markdown
# Main Title
## Subheading
### Sub-subheading
```

```markdown
This is **bold**, this is *italic*, and this is `inline code`.
```
Becomes:

This is **bold**, this is *italic*, and this is `inline code`.

### Links

```markdown
[MySt](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html) provides even more useful features.
```

[MySt](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html) provides even more useful features.

### Notes and Warnings


```{note}
For example, this is a *note box*.
```

```{warning}
This is a warning box.
```

### Auto-Referencing Classes

```{eval-rst}
.. autoclass:: app.src.scenario.Scenario
    :members: json, add, tasks_total
```

This allows automatic referencing of Python classes and their members in your documentation.