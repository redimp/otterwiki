#!/usr/bin/env pyton
# vim: set et ts=8 sts=4 sw=4 ai:

import csv
import fnmatch
import io
import urllib.parse

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
            "Renders sort-, search and pageable tables.",
            "Syntax/Embeddings",
        )

    @hookimpl
    def help_category_prelude(self, category):
        if category != self.info()[2]:
            return None
        return (
            "Embeddings are additions to the standard markdown syntax"
            " in An Otter Wiki. They provide capabilities beyond basic"
            " markdown, such as special layout elements, enhanced"
            " features, and entirely new functionality."
            " <br/><span class=\"text-secondary-dm bg-secondary-lm\">"
            "Embeddings are an experimental feature and subject to"
            " change.</span>\n\n"
            "<h4>Usage</h4>\n\n"
            "An embedding starts with <code>{{"
            "<em>EmbeddingName</em></code> and ends with"
            " <code>}}</code>. Between the opening and closing"
            " braces you can pass **options** and **args**.\n\n"
            "**Options** are key-value pairs separated by"
            " `|` in the form"
            " `|key=value`. "
            "Each option starts with a `|` followed by"
            " the key, an `=` and the value.\n\n"
            "**Args** are any remaining lines that are not options."
            " They form the body content of the embedding and can"
            " contain regular markdown.\n\n"
            "```\n"
            "{{EmbeddingName\n"
            "|option1=value1\n"
            "|option2=value2\n"
            "args content (markdown)\n"
            "}}\n"
            "```\n"
            "**Escaping:** Use <code>\\\\|</code> to include a"
            " literal <code>|</code> in a key, value, or args."
            " Use <code>\\\\=</code> to include a literal"
            " <code>=</code> in a key.\n\n"
        )

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
|sortable=true
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

<div class="row mb-10">
CSV attachments can also be rendered as datatables:
<div class="col-md-8 col-sm-12">

```
{{datatable
|src=data.csv
|delimiter=;
|quotechar="
|header=true
|columns=1,3
|headers=Name,Score
|caption=My Data
}}
```

</div><div class="col-md-4 col-sm-12 pl-20">

Options specific to CSV:
- `src`: filename of a CSV attachment on the page
- `delimiter` field delimiter, default `;`
- `quotechar` character used to quote fields, default `"`
- `header` use first row as column headers (default `true`)
- `columns` comma-separated list of 1-based column indices or header names to include
- `headers` comma-separated list of column header labels (overrides CSV headers)

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
    def page_render_context(self, page, preview: bool):
        self.page = page

    def _csv_to_html_table(self, args: EmbeddingArgs) -> str:
        """Build an HTML table string from a CSV page attachment."""
        from otterwiki.wiki import Attachment

        src = args.options.get('src', None)
        if not src:
            return ''

        delimiter = args.options.get(
            'delimiter',
            args.options.get('sep', args.options.get('separator', ';')),
        )
        quotechar = args.options_raw.get('quotechar', '"')
        use_header = args.get_flag('header', True)
        columns_opt = args.options.get('columns', None)
        headers_opt = args.options.get('headers', None)
        if delimiter == "\\t":
            delimiter = "\t"

        page = getattr(self, 'page', None)
        if page is None:
            raise ValueError('no page context available.')

        attachment = Attachment(page.pagepath, src)
        if not attachment.exists():
            raise ValueError(f'csv attachment "{src}" not found.')
        with open(attachment.abspath, 'r', encoding='utf-8', newline='') as f:
            content = f.read()

        reader = csv.reader(
            io.StringIO(content), delimiter=delimiter, quotechar=quotechar
        )
        rows = list(reader)

        if not rows:
            return '<table></table>'

        if use_header:
            header_row = rows[0]
            data_rows = rows[1:]
        else:
            header_row = None
            data_rows = rows

        # Determine which columns to include
        n_cols = len(
            header_row
            if header_row is not None
            else (data_rows[0] if data_rows else [])
        )
        all_indices = list(range(n_cols))

        if columns_opt:
            col_specs = [c.strip() for c in columns_opt.split(',')]
            try:
                # 1-based integer indices
                col_indices = [int(c) - 1 for c in col_specs]
            except ValueError:
                # column names — requires a header row
                if header_row is not None:
                    col_indices = [
                        header_row.index(name)
                        for name in col_specs
                        if name in header_row
                    ]
                else:
                    col_indices = all_indices
        else:
            col_indices = all_indices

        # Override display headers
        if headers_opt:
            override_headers = [h.strip() for h in headers_opt.split(',')]
        else:
            override_headers = None

        html = '<table>\n'

        if use_header or override_headers:
            html += '<thead><tr>'
            if override_headers:
                for h in override_headers:
                    html += f'<th>{mistune.escape(h)}</th>'
            elif header_row is not None:
                for i in col_indices:
                    cell = header_row[i] if 0 <= i < len(header_row) else ''
                    html += f'<th>{mistune.escape(cell)}</th>'
            html += '</tr></thead>\n'

        html += '<tbody>\n'
        for row in data_rows:
            html += '<tr>'
            for i in col_indices:
                cell = row[i] if 0 <= i < len(row) else ''
                html += f'<td>{mistune.escape(cell)}</td>'
            html += '</tr>\n'
        html += '</tbody>\n</table>\n'

        return html

    @hookimpl
    def embedding_render(
        self,
        embedding: str,
        args: EmbeddingArgs,
    ):
        if embedding.lower() != "datatable":
            return None

        src = args.options.get('src', None)
        if src:
            body = self._csv_to_html_table(args)
        else:
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
            "Render an image/images in a framed box next to the main content.",
            "Syntax/Embeddings",
        )

    @hookimpl
    def help(self, plugin):
        if plugin.lower() != "imageframe":
            return None

        return """
<div class="row mb-10">
Display images in frames on the wiki page.
</div><div class="row mb-10">

<div class="col-md-8 col-sm-12">

```
{{ImageFrame
|caption=An Otter Wiki Logo
|width=30%
|position=right/left
|float=right/left
|text-align=center/left/right/justify
|style=custom css
[![](/static/img/otter.png)](/static/img/otter.png)
}}
```

Use `|src=` to embed an attachment directly, with an optional `|alt=` text:

```
{{ImageFrame
|caption=An Otter Wiki Logo
|src=otter.png
|alt=The Otter Wiki logo
}}
```

Use an absolute path to embed an attachment from another page:

```
{{ImageFrame
|src=/OtherPage/otter.png
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
    def page_render_context(self, page, preview: bool):
        self.page = page

    @hookimpl
    def static_css(self):
        return """
div.imageframe-caption {
    border: 1px solid rgba(128, 128, 128, 0.3);
    padding: .5rem;
}
div.imageframe-caption.imageframe-float-right {
    float: right;
    clear: right;
    margin: .5rem 0 .5rem .5rem;
}
div.imageframe-caption.imageframe-float-left {
    float: left;
    clear: left;
    margin: .5rem .5rem 0 .5rem;
}
div.imageframe {
    text-align: center;
    width: 100%;
    font-weight: bold;
}
@media (max-width: 576px) {
    div.imageframe-caption.imageframe-float-right,
    div.imageframe-caption.imageframe-float-left {
        float: none;
        clear: both;
        margin: .5rem 0;
        width: 100% !important;
    }
}
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
        if floating.lower() != "left":
            floating = "right"

        userstyle = args.options_raw.get("style", "")
        width = args.options.get("width", "30%")

        src = args.options.get("src", None)
        if src:
            from otterwiki.wiki import Attachment

            if src.startswith("/"):
                # absolute: /pagepath/filename — attachment from another page
                parts = src.lstrip("/").rsplit("/", 1)
                if len(parts) != 2:
                    raise ValueError(
                        f'ImageFrame: invalid absolute src "{src}",'
                        f' expected /pagepath/filename.'
                    )
                att_pagepath, att_filename = parts
            else:
                # relative: attachment on the current page
                page = getattr(self, 'page', None)
                if page is None:
                    raise ValueError(
                        "ImageFrame |src= requires a page context."
                    )
                att_pagepath = page.pagepath
                att_filename = src
            attachment = Attachment(att_pagepath, att_filename)
            if not attachment.exists():
                raise ValueError(f'ImageFrame: attachment "{src}" not found.')
            alt = mistune.escape(args.options.get("alt", att_filename))
            img_url = attachment.get_url()
            content += f'<img src="{img_url}" alt="{alt}" style="width:100%">'
        else:
            content += "\n".join(args.args)

        # dynamic per-instance styles only; fixed styles live in static_css()
        inline_styles = []
        if width:
            inline_styles.append(f"width:{width}")
        if text_align:
            inline_styles.append(f"text-align:{text_align}")
        if userstyle:
            inline_styles.append(userstyle)
        style_attr = (
            f' style="{";".join(inline_styles)}"' if inline_styles else ""
        )

        caption_html = (
            f'<div class="imageframe">{caption}</div>' if caption else ""
        )
        return f'<div class="imageframe-caption imageframe-float-{floating}"{style_attr}>{content}{caption_html}</div>'


class VideoEmbedding:
    @hookimpl
    def info(self):
        return (
            "Video",
            "Embed a video from an url or an attachment",
            "Syntax/Embeddings",
        )

    @hookimpl
    def help(self, plugin):
        if plugin.lower() != "video":
            return None

        return """<div class="row mb-10">
Embed a video player that supports video and audio playback in your document,
or embed a YouTube video by providing a YouTube URL.
<div class="col-md-8 col-sm-12">

```
{{Video
|width=10%
|muted=false/true
|controls=true/false
|autoplay=false/true
|loop=false/true
|src=/full/path/to/video.mp4
/alternative/full/path/to/video.mp4
}}
```

YouTube URLs (`youtube.com/watch?v=…` or `youtu.be/…`) are rendered as embedded iframes:

```
{{Video
|width=100%
|muted=false/true
|controls=true/false
|autoplay=false/true
|loop=false/true
https://www.youtube.com/watch?v=dQw4w9WgXcQ
}}
```

</div><div class="col-md-4 col-sm-12" style="text-align:right; padding-top:10px;">

{{Video
|width=100%
|muted=true
|controls=true
|autoplay=on
/static/img/otter.mp4
}}

</div></div>
"""

    @staticmethod
    def _get_youtube_id(url: str):
        """Extract YouTube video ID from various URL formats, or return None."""
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower().lstrip('www.')
        if host == 'youtube.com' or host == 'youtube-nocookie.com':
            if parsed.path.startswith('/embed/'):
                return parsed.path.split('/')[2]
            qs = urllib.parse.parse_qs(parsed.query)
            ids = qs.get('v', [])
            return ids[0] if ids else None
        if host == 'youtu.be':
            return parsed.path.lstrip('/')
        return None

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
        # first join all args blocks with new lines and split again
        args_list = "\n".join(args.args_raw).splitlines()
        if type(src) is str:
            src = [src] + args_list
        elif type(src) is list:
            src += args_list
        # filter out blank entries (e.g. from empty body)
        src = [s.strip() for s in src if s.strip()]

        if len(src) < 1:
            raise ValueError("No src given.")

        yt_sources = [s for s in src if self._get_youtube_id(s)]
        file_sources = [s for s in src if not self._get_youtube_id(s)]
        if yt_sources and file_sources:
            raise ValueError(
                "Cannot mix YouTube links and file sources in the same Video embedding."
            )

        # Build YouTube embed query params from options
        yt_params = {}
        if not args.get_flag("controls", True):
            yt_params['controls'] = '0'
        if args.get_flag("autoplay", False):
            yt_params['autoplay'] = '1'
        if args.get_flag("muted", True):
            yt_params['mute'] = '1'
        # loop requires playlist=VIDEO_ID; added per-video below

        html_parts = []
        video_sources = ""
        for s in src:
            yt_id = self._get_youtube_id(s)
            if yt_id:
                params = dict(yt_params)
                if args.get_flag("loop", True):
                    params['loop'] = '1'
                    params['playlist'] = yt_id
                qs = ('?' + urllib.parse.urlencode(params)) if params else ''
                html_parts.append(
                    f'<iframe width="{width}" height="315"'
                    f' src="https://www.youtube.com/embed/{yt_id}{qs}"'
                    f' title="YouTube video player" frameborder="0"'
                    f' allow="accelerometer; autoplay; clipboard-write;'
                    f' encrypted-media; gyroscope; picture-in-picture; web-share"'
                    f' referrerpolicy="strict-origin-when-cross-origin"'
                    f' allowfullscreen></iframe>'
                )
            else:
                t = ""
                if s.endswith(".mp4"):
                    t = " type=\"video/mp4\""
                elif s.endswith(".ogg"):
                    t = " type=\"video/ogg\""
                video_sources += f'<source src="{s}"{t}>\n'

        if video_sources:
            html_parts.append(
                f'<video width="{width}" {" ".join(flags)}>\n'
                f'{video_sources}\n'
                f'Your browser does not support the video tag.\n'
                f'</video>'
            )

        return "\n".join(html_parts)


class InfoBoxEmbedding:
    @hookimpl
    def info(self):
        return (
            "InfoBox",
            "Render structured information next to the main content in a standardized way",
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
|position=right/left
|float=right/left
|width=35%
|text-align=justify
|style=additional inline css
|Random Key=Value
|Answer=42
|Homepage=[otterwiki.com](https://otterwiki.com)
Lorem _ipsum_ dolor sit **amet**, consectetur
adipiscing elit.
```python
#!/usr/bin/env python
markdown=True
```
}}
````

Note: On small screens the box automatically expands to full width regardless of the `width` option.
The optional `|style=` allows additional inline CSS overrides.

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
    def static_css(self):
        return """
div.infobox {
    border: 1px solid rgba(128, 128, 128, 0.3);
    padding: .5rem;
    background-color: rgba(0, 0, 0, 0.2);
}
div.infobox.infobox-float-right {
    float: right;
    clear: right;
    margin: .5rem 0 .5rem .5rem;
}
div.infobox.infobox-float-left {
    float: left;
    clear: left;
    margin: .5rem .5rem 0 .5rem;
}
div.infobox-caption {
    text-align: center;
    width: 100%;
    font-weight: bold;
}
table.infobox {
    width: 100%;
    border: none;
    background: none;
}
table.infobox tr {
    border: none;
}
table.infobox td {
    border: none;
    padding: .5rem;
}
@media (max-width: 576px) {
    div.infobox.infobox-float-right,
    div.infobox.infobox-float-left {
        float: none;
        clear: both;
        margin: .5rem 0;
        width: 100% !important;
    }
}
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
        width = args.options.get("width", "35%")

        position = args.options.get("position", None) or args.options.get(
            "pos", "right"
        )
        floating = args.options.get("float", position)
        if floating.lower() != "left":
            floating = "right"

        userstyle = args.options_raw.get("style", "")

        # dynamic per-instance styles only; fixed styles live in static_css()
        inline_styles = []
        if width:
            inline_styles.append(f"width:{width}")
        if userstyle:
            inline_styles.append(userstyle)
        style_attr = (
            f' style="{";".join(inline_styles)}"' if inline_styles else ""
        )

        caption_html = (
            f'<div class="infobox-caption">{caption}</div>' if caption else ""
        )

        table_html = '<table class="infobox">'
        if content:
            align_attr = (
                f' style="text-align:{text_align}"' if text_align else ""
            )
            table_html += f'<tr class="infobox-args"><td{align_attr} colspan="2">{content}</td></tr>'
        skip_keys = {
            "caption",
            "width",
            "float",
            "position",
            "pos",
            "text-align",
            "align",
            "style",
        }
        for key, value in args.options.items():
            if key in skip_keys:
                continue
            if key.startswith("_"):
                key = key[1:]
            table_html += f'<tr class="infobox-key-value"><td><strong>{key}</strong></td><td>{value}</td></tr>'
        table_html += "</table>"

        return f'<div class="infobox infobox-float-{floating}"{style_attr}>{caption_html}{table_html}</div>'


class AttachmentListEmbedding:
    @hookimpl
    def info(self):
        return (
            "AttachmentList",
            "Render the attachments to the current page as table.",
            "Syntax/Embeddings",
        )

    @hookimpl
    def page_render_context(
        self,
        page,
        preview: bool,
    ):
        self.page = page
        self.attachments = page._attachments_list()
        self.preview = preview

    @hookimpl
    def embedding_render(
        self,
        embedding: str,
        args: EmbeddingArgs,
    ):
        if embedding.lower() not in (
            'attachmentlist',
            'attachment list',
            'attachments',
        ):
            return None

        attachments = getattr(self, 'attachments', [])
        filter_pattern = args.options.get('filter', '*')
        fmt = args.options.get(
            'fmt', args.options.get('format', 'full')
        ).lower()
        show_icons = args.get_flag(
            'icons', False if fmt == "minimal" else True
        )

        if filter_pattern and filter_pattern != '*':
            attachments = [
                f
                for f in attachments
                if fnmatch.fnmatch(f['filename'], filter_pattern)
            ]

        caption = mistune.escape(args.options.get('caption', ''))
        caption_html = f'<caption>{caption}</caption>' if caption else ''

        if not attachments:
            return (
                f'<div class="attachmentlist-embedding">'
                f'<table class="table">{caption_html}</table>'
                f'</div>'
            )

        # build header and rows depending on format
        if fmt == 'minimal':
            header = f'<th>Attachment</th>'
        elif fmt == 'details':
            header = f'<th>Filename</th><th>Size</th><th>Date</th>'
        else:  # full
            header = (
                f'<th>Attachment</th>'
                f'<th>Size</th>'
                f'<th>Date</th>'
                f'<th>Author</th>'
                f'<th>Comment</th>'
            )

        if show_icons:
            header = f'<th></th>' + header

        rows = ''
        for f in attachments:
            filename = mistune.escape(f['filename'])
            url = f['url'] or ''

            if show_icons:
                thumb = (
                    f'<img src="{f["thumbnail_url"]}"/>'
                    if f.get('thumbnail_url')
                    else f.get('thumbnail_icon', '')
                )
                icon_cell = f'<td width="1"><a href="{url}">{thumb}</a></td>'
            else:
                icon_cell = ''

            if fmt == 'minimal':
                cells = f'<td><a href="{url}">{filename}</a></td>'
            elif fmt == 'details':
                dt = f['datetime']
                dt_str = (
                    dt.strftime('%Y-%m-%d %H:%M')
                    if hasattr(dt, 'strftime')
                    else mistune.escape(str(dt))
                )
                filesize = mistune.escape(f['filesize'])
                cells = (
                    f'<td><a href="{url}">{filename}</a></td>'
                    f'<td>{filesize}</td>'
                    f'<td>{dt_str}</td>'
                )
            else:  # full
                dt = f['datetime']
                dt_str = (
                    dt.strftime('%Y-%m-%d %H:%M')
                    if hasattr(dt, 'strftime')
                    else mistune.escape(str(dt))
                )
                filesize = mistune.escape(f['filesize'])
                author = mistune.escape(f['author_name'] or '')
                message = mistune.escape(f['message'] or '')
                cells = (
                    f'<td><a href="{url}">{filename}</a></td>'
                    f'<td>{filesize}</td>'
                    f'<td>{dt_str}</td>'
                    f'<td>{author}</td>'
                    f'<td class="text-wrap">{message}</td>'
                )

            rows += f'<tr>{icon_cell}{cells}</tr>\n'

        return (
            f'<div class="attachmentlist-embedding">'
            f'<table class="table">'
            f'{caption_html}'
            f'<thead><tr>{header}</tr></thead>'
            f'<tbody>{rows}</tbody>'
            f'</table>'
            f'</div>'
        )

    @hookimpl
    def help(self, plugin):
        if plugin.lower() != "attachmentlist":
            return None

        return """
<div class="row mb-10">
Display attachments to the current page as list.
</div><div class="row mb-10">
<div class="col">

```
{{AttachmentList
|caption=Attachments
|filter=*
|format=full/details/minimal
|icons=true/false
}}
```

With format you can decide what is displayed in the table: `minimal` shows only the filenames, `details` shows filename, date and size, `full` shows all information.
</div>

</div><div class="row mb-10">

<table class="table"><thead><tr><th></th><th>Attachment</th><th>Size</th><th>Date</th><th>Author</th><th>Comment</th></tr></thead><tbody><tr><td width="1"><a href="#"><i class="far fa-file-pdf" style="font-size:48px;"></i></a></td><td><a href="#">example.pdf</a></td><td>110.0KiB</td><td>2026-03-08 11:26</td><td>Anonymous</td><td class="text-wrap">Added AttachmentList documentation.</td></tr>
</tbody></table>

</div>
"""


class PageIndexEmbedding:
    @hookimpl
    def info(self):
        return (
            "PageIndex",
            "Render a page index listing all pages below the" " current page.",
            "Syntax/Embeddings",
        )

    @hookimpl
    def page_render_context(self, page, preview: bool):
        self.page = page

    @hookimpl
    def help(self, plugin):
        if plugin.lower() != "pageindex":
            return None

        return """
<div class="row mb-10">
Display a page index listing pages below the current page,
optionally filtered by a glob pattern.
<div class="col-md-8 col-sm-12">

```
{{PageIndex
|src=*
|toc=true/false
|toggle=true/false
}}
```

Options:
- `src`: glob pattern to filter pages by title (default `*`, matches all pages)
- `toc`: show page headings (default `false`)
- `toggle`: show the toggle for the page headings (default `true`)

</div>
<div class="col-md-4 col-sm-12">

<div class="pageindex-letterblock" style="width:80%; float: right;"><h2 class="content-title font-weight-bolder pageindex-header">E</h2>
<div class="pageindex-pageblock pageindex-depth-0" style="padding-left:0.0rem;">
<a class="global-toc-link pageindex-page pageindex-depth-0" href="$">Example 1</a><br/>
<a class="global-toc-link pageindex-page pageindex-depth-0" href="$">Example 2</a>
</div>
</div>

</div>
</div>
"""

    @hookimpl
    def embedding_render(
        self,
        embedding: str,
        args: EmbeddingArgs,
    ):
        if embedding.lower() not in ('pageindex', 'page index'):
            return None

        from flask import render_template
        from otterwiki.pageindex import PageIndex

        src = args.options.get('src', '*')
        show_toc = args.get_flag('toc', False)
        heading_toggle = args.get_flag('toggle', True)

        page = getattr(self, 'page', None)
        path = page.pagepath if page else None
        page_index = PageIndex(path=path)

        pages = page_index.toc
        if src != '*':
            pages = {}
            for letter, entries in page_index.toc.items():
                filtered = [
                    e
                    for e in entries
                    if fnmatch.fnmatch(e.title.rstrip('/'), src)
                ]
                if filtered:
                    pages[letter] = filtered

        togglediv = f"""<div class="d-inline-block custom-switch font-size-12 mb-10">
    <input type="checkbox" id="switch-headings" {"checked" if show_toc else ""} value="" onchange="otterwiki.toggleClass(event.target.checked,'pagetoc')"><label for="switch-headings">Toggle page headings</label>
</div>"""

        return (
            (togglediv if heading_toggle else '')
            + '<div class="pageindex-embedding">'
            + render_template(
                'snippets/pageindex.html',
                pages=pages,
                hide_toc=not show_toc,
            )
            + '</div>'
        )


plugin_manager.register(ImageFrameEmbedding())
plugin_manager.register(InfoBoxEmbedding())
plugin_manager.register(VideoEmbedding())
plugin_manager.register(DatatableEmbedding())
plugin_manager.register(AttachmentListEmbedding())
plugin_manager.register(PageIndexEmbedding())
