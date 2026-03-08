#!/usr/bin/env pyton
# vim: set et ts=8 sts=4 sw=4 ai:

from otterwiki.plugins import hookimpl, plugin_manager, EmbeddingArgs
from bs4 import BeautifulSoup
from otterwiki.util import sha256sum
import mistune

"""
The default Embeddings are implemented as Plugins via pluggy despite of
being part of An Otter Wikis core.
"""


class DatatableEmbedding:
    @hookimpl
    def info(self):
        return (
            "DataTable",
            "Embedding for displaying tables.",
            "Syntax/Embeddings",
        )

    @hookimpl
    def help_category_prelude(self, category):
        if category != self.info()[2]:
            return None
        return "Embeddings are additions to the standard markdown syntax in An Otter Wiki. They provide capabilities beyond basic markdown, such as special layout elements, enhanced features, and entirely new functionality. <br/><span class=\"text-secondary-dm bg-secondary-lm\">Embeddings are an experimental feature and subject to change.</span>"

    @hookimpl
    def help(self, plugin):
        if plugin.lower() != "datatable":
            return None

        return """
<div class="row mb-10">
The DataTable Embedding is for turning markdown tables into datatables that can be paginated, search and sorted.
<div class="col-md-8 col-sm-12">

```
{{datatable
|paging=false
|perPage=42
|searchable=false
|fixedHeight=True
|caption=Python Stable
| Version | Released   |
| -------:| ---------- |
|    3.13 | 2024-10-07 |
|    3.12 | 2023-10-02 |
|    3.11 | 2022-10-24 |
|    3.10 | 2021-10-04 |
|     3.9 | 2020-10-05 |
|     3.8 | 2019-10-14 |
|     3.7 | 2018-06-27 |
|     3.0 | 2008-12-03 |
}}
```

</div><div class="col-md-4 col-sm-12 pl-20" style="padding-top:10px;">

{{datatable
|paging=true
|perPage=5
|searchable=false
|fixedHeight=True
|caption=Python Stable
| Version | Released   |
| -------:| ---------- |
|    3.13 | 2024-10-07 |
|    3.12 | 2023-10-02 |
|    3.11 | 2022-10-24 |
|    3.10 | 2021-10-04 |
|     3.9 | 2020-10-05 |
|     3.8 | 2019-10-14 |
|     3.7 | 2018-06-27 |
|     3.0 | 2008-12-03 |
}}

</div></div>
"""

    str_options = ["caption"]
    int_options = ["perPage"]
    bool_options = ["searchable", "fixedHeight", "sortable", "paging"]

    # FIXME: abusing renderer_markdown_preprocess, we might need another hook
    @hookimpl
    def renderer_markdown_preprocess(self, md: str) -> str:
        self.datatables = {}
        return md

    @hookimpl
    def embedding_render(
        self,
        embedding: str,
        args: EmbeddingArgs,
    ):
        if embedding.lower() != "datatable":
            return None
        body = "\n".join(args.args)
        # default options
        options = {
            "perpage": "25",
            "fixedheight": "true",
            "sortable": "true",
        }
        # collect options
        for k, v in args.options.items():
            # all lowercase
            if k.lower() in [
                x.lower()
                for x in self.bool_options
                + self.str_options
                + self.int_options
            ]:
                options[k.lower()] = v

        # find all tables
        soup = BeautifulSoup(body, 'html.parser')
        for table in soup.find_all('table'):
            id = ""
            while id == "" or id in self.datatables:
                id = sha256sum(str(table) + str(id))[:10]
            self.datatables[id] = options
            # add the id to the html table element
            table['id'] = f"s-dt-{id}"
        # after modifying the table, turn back into html
        return str(soup)

    @hookimpl
    def renderer_javascript(self) -> str | None:
        if not self.datatables or len(self.datatables) < 0:
            return None

        script = ""
        # add js block
        for id, options in self.datatables.items():
            # default values
            perPageSelect = {25: "25", 50: "50", 100: "100", 0: "All"}
            # add perPage value to perPageSelect if set
            try:
                add_page = int(options.get("perpage"))
                perPageSelect[add_page] = str(add_page)
            except ValueError:
                pass
            # glue perPageSelect into jsoptions
            jsoptions = [
                f"perPageSelect: ["
                + ",".join(
                    f"[\"{perPageSelect[k]}\", {k}]"
                    for k in sorted(perPageSelect.keys())
                )
                + "]"
            ]
            for bool_option in self.bool_options:
                if options.get(bool_option.lower(), None):
                    value = (
                        "true"
                        if options.get(bool_option.lower(), "").lower()
                        in ["yes", "true", "1", "y"]
                        else "false"
                    )
                    jsoptions.append(f"{bool_option}: {value}")
            for str_option in self.str_options:
                if options.get(str_option.lower(), None):
                    jsoptions.append(
                        f"{str_option}: \"{mistune.escape(options.get(str_option))}\""
                    )
            for int_option in self.int_options:
                if options.get(int_option.lower(), None):
                    try:
                        jsoptions.append(
                            f"{int_option}: {int(options.get(int_option.lower()))}"
                        )
                    except ValueError as e:
                        print(e)
                        pass
            script += f"""
let options_{id} = {{{", ".join(jsoptions)}}};
let datatable_{id} = new simpleDatatables.DataTable("#s-dt-{id}", options_{id});
"""
        return script


class ImageFrameEmbedding:
    @hookimpl
    def info(self):
        return (
            "ImageFrame",
            "Embedding for displaying images in frames in pages.",
            "Syntax/Embeddings",
        )

    @hookimpl
    def help(self, plugin):
        if plugin.lower() != "imageframe":
            return None

        return """
<div class="row mb-10">
Display images in frames on the wiki page.
<div class="col-md-8 col-sm-12">

```
{{ImageFrame
|caption=An Otter Wiki Logo
|width=30%
|position=right/left/center
[![](/static/img/otter.png)](/static/img/otter.png)
}}
```

</div><div class="col-md-4 col-sm-12" style="padding-top:5px;">

{{ImageFrame
|caption=An Otter Wiki Logo
|width=80%
|position=right
[![](/static/img/otter.png)](/static/img/otter.png)
}}
</div></div>
"""

    @hookimpl
    def embedding_render(
        self,
        embedding: str,
        args: EmbeddingArgs,
    ):
        if (
            embedding.lower() != "imageframe"
            and embedding.lower() != "image frame"
        ):
            return None
        caption = args.options.get("caption", "")
        content = args.options.get("content", "")
        text_align = args.options.get("text-align", None) or args.options.get(
            "align", ""
        )
        position = args.options.get("position", None) or args.options.get(
            "pos", "right"
        )
        floating = args.options.get("float", position)

        if floating.lower() == "left":
            margin = "margin: .5rem .5rem 0 .5rem"
        else:
            floating = "right"
            margin = "margin: .5rem 0 .5rem .5rem"

        userstyle = args.options_raw.get("style", "")
        width = args.options.get("width", "30%")
        content += "\n".join(args.args)

        styles = [
            "border-width: 1px",
            "border-style: solid",
            "border-color: rgba(128, 128, 128, 0.3)",
            "padding: .5rem",
            margin,
        ]

        if floating.lower() in ["left", "right"]:
            styles.append(f"float:{floating.lower()}")
            styles.append(f"clear:{floating.lower()}")

        if width:
            styles.append(f"width:{width}")

        if text_align:
            styles.append(f"text-align:{text_align}")

        style = ";".join(styles)
        caption = (
            f"<div class=\"imageframe\" style=\"text-align:center;width:100%;font-weight:bold;\">{caption}</div>"
            if caption
            else ""
        )
        return f"<div class=\"imageframe-caption\" style=\"{style};{userstyle}\">{content}{caption}</div>"


class VideoEmbedding:
    @hookimpl
    def info(self):
        return (
            "Video",
            "Embedding for displaying video attachments.",
            "Syntax/Embeddings",
        )

    @hookimpl
    def help(self, plugin):
        if plugin.lower() != "video":
            return None

        return """<div class="row mb-10">
Embed a video player that supports video and audio playback in your document.
<div class="col-md-8 col-sm-12">

```
{{Video
|width=80%
|muted=true
|controls=true
|autoplay=on
/static/img/otter.mp4
}}
```

</div><div class="col-md-4 col-sm-12" style="text-align:right; padding-top:10px;">

{{Video
|width=80%
|muted=true
|controls=true
|autoplay=on
/static/img/otter.mp4
}}

</div></div>
"""

    @hookimpl
    def embedding_render(
        self,
        embedding: str,
        args: EmbeddingArgs,
    ):
        if embedding.lower() != "video":
            return None
        width = args.options_raw.get("width", "100%")
        flags = []
        if args.get_flag("controls", True):
            flags.append("controls")
        if args.get_flag("autoplay", False):
            flags.append("autoplay")
        if args.get_flag("muted", True):
            flags.append("muted")
        if args.get_flag("loop", True):
            flags.append("loop")
        src = args.options_raw.get("src", [])
        if type(src) is str:
            src = [src] + args.args_raw
        elif type(src) is list:
            src += args.args_raw

        if len(src) < 1:
            raise ValueError("No src given.")
        sources = ""
        for s in src:
            t = ""
            if s.endswith(".mp4"):
                t = " type=\"video/mp4\""
            if s.endswith(".ogg"):
                t = "type=\"video/ogg\""
            sources += f"""<source src="{s}"{t}>\n"""

        return f"<video width=\"{width}\" {' '.join(flags)}>\n{sources}\nYour browser does not support the video tag.\n</video>"


class InfoBoxEmbedding:
    @hookimpl
    def info(self):
        return (
            "InfoBox",
            "Embedding for displaying information on a page in a standardized way.",
            "Syntax/Embeddings",
        )

    @hookimpl
    def help(self, plugin):
        if plugin.lower() != "infobox":
            return None

        return """
<div class="row mb-10">
An element for displaying structured data in a document.
<div class="col-md-8 col-sm-12">

````
{{InfoBox
|caption=Some Caption
|Random Key=Value
|Answer=42
|text-align=justify
|Homepage=[otterwiki.com](https://otterwiki.com)
Lorem _ipsum_ dolor sit **amet**, consectetur
adipiscing elit.
```python
#!/usr/bin/env python
markdown=True
```
}}
````

</div><div class="col-md-4 col-sm-12" style="padding-top:5px;">

{{InfoBox
|caption=Some Caption
|Random Key=Value
|Answer=42
|width=80%
|text-align=justify
|Homepage=[otterwiki.com](https://otterwiki.com)
Lorem _ipsum_ dolor sit **amet**, consectetur
adipiscing elit.
```python
#!/usr/bin/env python
markdown=True
```
}}
</div></div>
"""

    @hookimpl
    def embedding_render(
        self,
        embedding: str,
        args: EmbeddingArgs,
    ):
        if embedding.lower() != "infobox" and embedding.lower() != "info box":
            return None

        content = "\n".join(args.args)
        caption = args.options.get("caption", "")
        text_align = args.options.get("text-align", None) or args.options.get(
            "align", ""
        )
        width = args.options.get("width", "30%")

        position = args.options.get("position", None) or args.options.get(
            "pos", "right"
        )
        floating = args.options.get("float", position)

        if floating.lower() == "left":
            margin = "margin: .5rem .5rem 0 .5rem"
        else:
            floating = "right"
            margin = "margin: .5rem 0 .5rem .5rem"
        userstyle = args.options_raw.get("style", "")

        styles = [
            "border-width: 1px",
            "border-style: solid",
            "border-color: rgba(128, 128, 128, 0.3)",
            "padding: .5rem",
            "background-color: rgba(0, 0, 0, 0.2)",
            margin,
        ]

        if width:
            styles.append(f"width:{width}")

        if floating.lower() in ["left", "right"]:
            styles.append(f"float:{floating.lower()}")
            styles.append(f"clear:{floating.lower()}")

        style = ";".join(styles)
        # append custom style
        style += userstyle

        caption = (
            f"<div class=\"infobox-caption\" style=\"text-align:center;width:100%;font-weight:bold;\">{caption}</div>"
            if caption
            else ""
        )

        table_html = "<table class=\"infobox\" style=\"width:100%;border: none;background:none;\">"
        if content:
            table_html += f"<tr class=\"infobox-args\"><td style=\"border:none;text-align:{text_align}\" colspan=\"2\">{content}</td><tr>"
        for key, value in args.options.items():
            if key in ["caption", "width", "float", "text-align"]:
                continue
            if key.startswith("_"):
                key = key[1:]
            table_html += f"<tr class=\"infobox-key-value\" style=\"border:none;\"><td style=\"border: none;padding: .5rem;\"><strong>{key}</strong></td><td style=\"border: none;padding: .5rem;\">{value}</td></tr>"
        table_html += "</table>"

        return f"<div class=\"infobox\" style=\"{style};\">{caption}{table_html}</div>"


plugin_manager.register(ImageFrameEmbedding())
plugin_manager.register(InfoBoxEmbedding())
plugin_manager.register(VideoEmbedding())
plugin_manager.register(DatatableEmbedding())
