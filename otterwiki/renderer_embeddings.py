#!/usr/bin/env pyton
# vim: set et ts=8 sts=4 sw=4 ai:

from otterwiki.plugins import hookimpl, plugin_manager, EmbeddingArgs
from bs4 import BeautifulSoup
from otterwiki.util import sha256sum

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
    def help(self, plugin):
        if plugin.lower() != "datatable":
            return None

        return """
<div class="row mb-10">
<div class="col-md-8 col-sm-12">

```
{{DataTable}
|caption=Months
...
}}
```

</div><div class="col-md-4 col-sm-12">
...
</div></div>
"""

    # FIXME: abusing renderer_markdown_preprocess, we might need another hook
    @hookimpl
    def renderer_markdown_preprocess(self, md: str) -> str:
        self.table_ids = []
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
        # find all tables
        soup = BeautifulSoup(body, 'html.parser')

        for table in soup.find_all('table'):
            id = sha256sum(str(table))[:10]
            self.table_ids.append(id)
            # add the id to the table
            table['id'] = f"s-dt-{id}"
            pass
        # after modifying the table, turn back into html
        return str(soup)

    @hookimpl
    def renderer_javascript(self) -> str | None:
        print(f"renderer_javascript: {self.table_ids=}")
        if not self.table_ids or not len(self.table_ids):
            return None

        # add js block
        script = "<script type=\"text/javascript\"><!--DatatableEmbedding-->\n"
        for id in self.table_ids:
            script += f"""
let datatable_{id} = new simpleDatatables.DataTable("#s-dt-{id}");
"""
        script += "</script>"
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
<div class="col-md-8 col-sm-12">

```
{{ImageFrame
|caption=An Otter Wiki Logo
|width=30%
|position=right/left/center
[![](/static/img/otter.png)](/static/img/otter.png)
}}
```

</div><div class="col-md-4 col-sm-12">

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
        userstyle = args.options_raw.get("style", "")
        width = args.options.get("width", "30%")
        content += "\n".join(args.args)

        styles = [
            "border-width: 1px",
            "border-style: solid",
            "border-color: rgba(255, 255, 255, 0.5)",
            "padding: .5rem",
            "margin: .5rem 0 .5rem .5rem",
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
            f"<div style=\"text-align:center;width:100%;font-weight:bold;\">{caption}</div>"
            if caption
            else ""
        )
        return f"<div style=\"{style};{userstyle}\">{content}{caption}</div>"


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

```
{{Video
|muted=0
|controls=true
|autoplay=off
https://otterwiki.com/examples/Video%20Attachment/example.mp4
/Example/video.ogg
}}
```
</div>
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
<div class="col-md-8 col-sm-12">

````
{{InfoBox
|caption=Some Caption
|Random Key=Value
|Answer=42
|text-align=justify
|Homepage=[otterwiki.com](https://otterwiki.com)
Lorem _ipsum_ dolor sit **amet**, consectetur adipiscing elit.
}}
````

</div><div class="col-md-4 col-sm-12">

{{InfoBox
|caption=Some Caption
|Random Key=Value
|Answer=42
|width=80%
|text-align=justify
|Homepage=[otterwiki.com](https://otterwiki.com)
Lorem _ipsum_ dolor sit **amet**, consectetur adipiscing elit.
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
        userstyle = args.options_raw.get("style", "")

        styles = [
            "border-width: 1px",
            "border-style: solid",
            "border-color: rgba(128, 128, 128, 0.3)",
            "padding: .5rem",
            "margin: .5rem 0 .5rem .5rem",
            "background-color: rgba(0, 0, 0, 0.2)",
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
            f"<div style=\"text-align:center;width:100%;font-weight:bold;\">{caption}</div>"
            if caption
            else ""
        )

        table_html = (
            "<table style=\"width:100%;border: none;background:none;\">"
        )
        if content:
            table_html += f"<tr><td style=\"border:none;text-align:{text_align}\" colspan=\"2\">{content}</td><tr>"
        for key, value in args.options.items():
            if key in ["caption", "width", "float", "text-align"]:
                continue
            if key.startswith("_"):
                key = key[1:]
            table_html += f"<tr style=\"border:none;\"><td style=\"border: none;padding: .5rem;\"><strong>{key}</strong></td><td style=\"border: none;padding: .5rem;\">{value}</td></tr>"
        table_html += "</table>"

        return f"<div style=\"{style};\">{caption}{table_html}</div>"


plugin_manager.register(ImageFrameEmbedding())
plugin_manager.register(InfoBoxEmbedding())
plugin_manager.register(VideoEmbedding())
plugin_manager.register(DatatableEmbedding())
