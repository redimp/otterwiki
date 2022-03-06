# Home

_Lorem_ ipsum ~~dolor~~ sit amet, **consectetur** adipiscing elit.
Maecenas sapien *urna*, aliquam sed euismod quis, iaculis et eros.
Mauris et ante lectus. Vestibulum sem leo, tristique sit amet ultricies
eu, mattis a augue. Sed sodales gravida erat, a vestibulum ligula. Morbi
orci nibh, auctor in blandit et, lacinia finibus nunc. Vestibulum sed
interdum mauris. Curabitur interdum porta massa, eu tempor urna
facilisis sit amet. Suspendisse in tellus maximus, laoreet neque vitae,
venenatis magna. Sed quam elit, ultrices a massa sed, porta auctor
libero.  Maecenas mollis tempus porta. 

[Cras fermentum](https://github.com/redimp/otterwiki) ullamcorper
tellus, et fermentum sapien dictum laoreet. Pellentesque varius cursus
eros, sed eleifend augue sollicitudin vitae. Proin suscipit nisi at
posuere rutrum.

## Codeblock

`code`

```python
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static/img"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )

class SomeClass:
    pass

>>> message = '''interpreter
... prompt'''
```
## Table

| Syntax      | Description |
| ----------- | ----------- |
| Header      | Title       |
| Paragraph   | Text        |


## Lists

Unordered

- Create a list by starting a line with `+`, `-`, or `*`
- Sub-lists are made by indenting 2 spaces:
- Very easy!

Ordered

1. Lorem ipsum dolor sit amet
2. Consectetur adipiscing elit
3. Integer molestie lorem at massa

## Blockquotes

> Blockquotes can also be nested...
>> ...by using additional greater-than signs right next to each other...
> > > ...or with spaces between arrows.

