from __future__ import annotations

import json
from functools import partial
from io import TextIOWrapper
from os import environ as env, makedirs
from os.path import exists, join, relpath
from sys import stderr
from typing import Callable, Literal, Union

import plotly.graph_objects as go
from IPython.display import Image
from plotly.graph_objs import Figure
from plotly.validators.scatter.marker import SymbolValidator

from utz import err

# Plotly marker names
symbols = SymbolValidator().values[2::12]


# Env vars to fall back to, for various plot kwargs
PLOT_SHOW_VAR = 'UTZ_PLOT_SHOW'
PLOT_DIR_VAR = 'UTZ_PLOT_DIR'
PLOT_MARGIN_VAR = 'UTZ_PLOT_MARGIN'
PLOT_BG_VAR = 'UTZ_PLOT_BG'
PLOT_GRID_VAR = 'UTZ_PLOT_GRID'
PLOT_SUBTITLE_SIZE_VAR = 'UTZ_PLOT_SUBTITLE_SIZE'
PLOT_HTML_VAR = 'UTZ_PLOT_HTML'

DEFAULT_BG = 'white'
DEFAULT_SHOW = 'html'
DEFAULT_GRID = '#ccc'
DEFAULT_SUBTITLE_SIZE = '0.8em'


class Unset:
    pass


_Unset = type(Unset)


Title = Union[str, list[str], None]


def title(s: Title, subtitle_size: Title = None) -> str | None:
    """Convert a list of strings into a `<br>`-joined plot title, with optional font-size styling.

    If `subtitle_size` is a `str`, all elements of `s` after the first (subtitles) will be given that size.
    If it's a `list[str]`, the sizes will be applied to each element of `s`, with the last "size" repeated out to the
    length of the `s` list."""
    if isinstance(s, list):
        if subtitle_size is None:
            subtitle_size = env.get(PLOT_SUBTITLE_SIZE_VAR, DEFAULT_SUBTITLE_SIZE)

        title0, *subtitles = s
        if isinstance(subtitle_size, list) and subtitle_size:
            sizes = [
                subtitle_size[i] if i < len(subtitle_size) else subtitle_size[-1]
                for i in range(len(s))
            ]
            title_size, *subtitle_sizes = sizes
            title0 = f'<span style="font-size:{title_size}">{title0}</span>'
            subtitles = [
                f'<span style="font-size:{subtitle_size}">{subtitle}</span>'
                for subtitle_size, subtitle in zip(subtitle_sizes, subtitles)
            ]
        elif isinstance(subtitle_size, str):
            subtitles = [
                f'<span style="font-size:{subtitle_size}">{subtitle}</span>'
                for subtitle in subtitles
            ]
        return '<br>'.join([title0, *subtitles ])
    else:
        return s


make_title = title


def save(
    fig: Figure,
    name: str,
    title: Title = None,
    **kwargs
):
    """Wrap `plot`, enforce non-``None`` ``name``, allow passing ``name`` then ``title`` as positional args."""
    if not name:
        raise ValueError("`name` must be nonempty")
    return plot(fig, name=name, title=title, **kwargs)


def plot(
    fig: Figure,
    title: Title = None,
    name: str | None = None,
    *,
    bg: str | None | _Unset = Unset,
    subtitle_size: str | None = None,
    hoverx: bool = False,
    hovertemplate: Title = None,
    png_title: bool = True,
    yrange: str | None = 'tozero',
    legend: bool | dict | Literal['reversed'] | None = None,
    bottom_legend: bool | Literal['all'] = False,
    pretty: bool = False,
    margin: None | int | dict | _Unset = Unset,
    dir: str | None = None,
    w: int | None = None,
    h: int | None = None,
    png: dict | int | tuple[int] | tuple[int, int] | None = None,
    xtitle: Title = None,
    ytitle: Title = None,
    ltitle: Title = None,
    grid: str | None | _Unset = Unset,
    xgrid: str | None | _Unset = Unset,
    ygrid: str | None | _Unset = Unset,
    x: dict | str | None = None,
    y: dict | str | None = None,
    log: TextIOWrapper | bool | None = stderr,
    show: Literal['png', 'file', 'html'] | bool | None = None,
    zerolines: bool | Literal['x', 'y'] | None = True,
    html: dict | bool | None | _Unset = Unset,
    title_suffix: str | None = None,
    png_name: str | None = None,
    **layout,
):
    """Plotly wrapper with convenience kwargs for common configurations.

    Args:
        fig: Plotly figure
        title: Title string or list of strings (tail will be converted to "subtitle" lines)
        name: "Stem" for output file paths
        bg: Background color, falls back to $UTZ_PLOT_BG, defaults to `DEFAULT_BG` ("white")
        subtitle_size: Subtitle font size; falls back to $UTZ_PLOT_SUBTITLE_SIZE, defaults to "0.8em"
        hoverx: Alias for `hovermode="x"`
        hovertemplate: Hover template; `list[str]` will be `<br>.join()`'d.
        png_title: Whether to include the title in PNG (sometimes nice to disable this, e.g. for PNGs that will be embedded in Markdown that includes the title).
        yrange: Y-axis range mode
        legend: Legend configuration
        bottom_legend: Orient the legend horizontally along the bottom; True ⇒ JSON/PNG outputs only, 'all' ⇒ also in returned Figure
        pretty: Pretty-print JSON output
        margin: Margin size or dict of sizes (falls back to $UTZ_PLOT_MARGIN)
        dir: Output directory (falls back to $UTZ_PLOT_DIR)
        w: Width; applied to Figure and any resulting PNG output
        h: Height; applied to Figure and any resulting PNG output
        png: layout options specific to saved/static representations of the plot (omitted from JSON, included in PNG/HTML); "w" and "h" are short-hands for "width" and "height", a pair of ints will be interpreted as (w, h), and a single int or (int,) tuple will be interpreted as width.
        xtitle: X-axis title; string or list of strings (tail will be converted to "subtitle" lines)
        ytitle: Y-axis title; string or list of strings (tail will be converted to "subtitle" lines)
        ltitle: Legend title; string or list of strings (tail will be converted to "subtitle" lines)
        grid: Grid color (x- and y-axes)
        xgrid: X-axis grid color
        ygrid: Y-axis grid color
        x: X-axis configuration (passed to `update_xaxes`)
        y: Y-axis configuration (passed to `update_yaxes`)
        log: Whether/where to print log info (e.g. about files written); defaults to stderr
        show: Format to return the Figure in: 'png' ⇒ return PNG `Image`, 'file' ⇒ return `Image(filename=…)` pointing to output `.png`, 'html' ⇒ return default Plotly Figure HTML, False ⇒ None (don't show figure, if `plot(…)` call is last expression in a notebook cell). Falls back to $UTZ_PLOT_SHOW, defaults to 'html'.
        zerolines: Whether to show zero lines; 'x' ⇒ only on x-axis, 'y' ⇒ only on y-axis, True (default) ⇒ on both axes
        title_suffix: When saving static plots (e.g. PNG), and this is set, two versions will be saved: one including the title, and one not. This string will be appended to the filename stem of the former. Assumes the default is the "untitled" version. Useful when embedding in contexts where it looks nicer to render the title in surrounding Markdown/HTML.
        png_name: Customize PNG save-path stem name
        html: When truthy, save plot as HTML. Value is interpreted as kwargs for Figure.to_html; falls back to json.loads($UTZ_PLOT_HTML).
    """
    mk_title = partial(make_title, subtitle_size=subtitle_size)
    ltitle = mk_title(ltitle)
    layout['legend_title'] = layout.get('legend_title', ltitle or '')

    save_json = layout.pop('json') if 'json' in layout else True

    if w is not None:
        layout['width'] = w
    if h is not None:
        layout['height'] = h

    if bg is Unset:
        bg = env.get(PLOT_BG_VAR)
        if bg is None:
            bg = DEFAULT_BG

    if bg:
        layout['plot_bgcolor'] = bg
        layout['paper_bgcolor'] = bg

    if isinstance(hovertemplate, list):
        hovertemplate = '<br>'.join(hovertemplate)
    if hoverx:
        layout['hovermode'] = 'x'
        fig.update_traces(hovertemplate=hovertemplate)
    elif hovertemplate:
        fig.update_traces(hovertemplate=hovertemplate)

    if yrange:
        layout['yaxis_rangemode'] = yrange

    if legend is False:
        layout['showlegend'] = False
    elif legend == 'reversed':
        layout['legend'] = dict(traceorder='reversed')
    elif isinstance(legend, dict):
        layout['legend'] = legend

    bottom_legend_kwargs = dict(
        orientation='h',
        x=0.5,
        xanchor='center',
        yanchor='top',
    ) if bottom_legend else {}
    if bottom_legend == 'all':
        if 'legend' not in layout:
            layout['legend'] = {}
        layout['legend'].update(**bottom_legend_kwargs)

    if grid is Unset:
        grid = env.get(PLOT_GRID_VAR)
        if grid is None:
            grid = DEFAULT_GRID

    def update_axis(
        xy: str | dict | None,
        xy_name: str,
        update_axes: Callable,
        xy_title: Title,
        xy_grid: str | None | Unset,
    ):
        if isinstance(xy, str):
            update_axes(title_text=xy)
        elif isinstance(xy, dict):
            if 'title' in xy:
                xy['title_text'] = xy['title']
                del xy['title']
            update_axes(**xy)

        if xy_grid is not Unset:
            update_axes(gridcolor=xy_grid)
        elif grid:
            update_axes(gridcolor=grid)

        if zerolines == xy_name or zerolines is True:
            zerolinecolor = xy_grid or grid
            if zerolinecolor is not Unset:
                update_axes(
                    zeroline=True,
                    zerolinecolor=zerolinecolor,
                    zerolinewidth=1,
                )

        xy_title = mk_title(xy_title)
        if xy_title:
            update_axes(title=dict(text=xy_title))

    update_axis(x, 'x', fig.update_xaxes, xtitle, xgrid)
    update_axis(y, 'y', fig.update_yaxes, ytitle, ygrid)

    title = mk_title(title)
    title_layout = dict(title_text=title, title_x=0.5) if title else {}
    if png_title:
        layout.update(title_layout)

    if bottom_legend is True:
        fig.update_layout(
            legend=bottom_legend_kwargs,
        )

    if margin is Unset:
        margin = env.get(PLOT_MARGIN_VAR)
        if margin:
            margin = json.loads(margin)
    if isinstance(margin, int):
        margin = { k: margin for k in 'trbl' }
    if margin:
        fig.update_layout(margin=margin)

    fig.update_layout(**layout)

    saved = go.Figure(fig)
    if not png_title:
        # Only need to do this if it wasn't already done above
        fig.update_layout(**title_layout)

    if log is True:
        log = err
    elif log:
        log = partial(print, file=log)
    else:
        log = lambda _: ()

    png_path = None
    if name or png_name:
        if dir is None:
            dir = env.get(PLOT_DIR_VAR)
        if dir:
            if not exists(dir):
                makedirs(dir, exist_ok=True)
        else:
            dir = '.'
        if name and save_json:
            json_path = join(dir, f'{name}.json')
            saved.write_json(json_path, pretty=pretty)
            log(f"Wrote plot JSON to {relpath(json_path)}")
        png_path = join(dir, f'{png_name or name}.png')
        if png:
            # Convert `int | tuple[int] | tuple[int, int]` to `dict`
            if isinstance(png, tuple):
                if len(png) == 1:
                    png = dict(w=png[0])
                elif len(png) == 2:
                    w, h = png
                    png = dict(w=w, h=h)
                else:
                    raise ValueError(f"Invalid PNG tuple: {png}")
            elif isinstance(png, int):
                png = dict(w=png)

            # `png` is a `dict`
            if 'w' in png:
                saved.update_layout(width=png['w'])
                del png['w']
            if 'h' in png:
                saved.update_layout(height=png['h'])
                del png['h']
            if 'title' in png and isinstance(png['title'], str):
                saved.update_layout(title_text=png['title'])
                del png['title']

            saved.update_layout(**png)

        if title_suffix:
            no_title = go.Figure(saved)
            no_title.update_layout(title_text='')
            title_path = join(dir, f'{name}{title_suffix}.png')
            no_title.write_image(png_path)
            log(f"Wrote plot image to {relpath(png_path)}")
            saved.write_image(title_path)
            log(f"Wrote plot image to {relpath(title_path)}")
        else:
            saved.write_image(png_path)
            log(f"Wrote plot image to {relpath(png_path)}")

        if html is Unset:
            html = env.get(PLOT_HTML_VAR)
            if html:
                html = json.loads(html)
        if html:
            html_path = join(dir, f'{name}.html')
            html_kwargs = dict(include_plotlyjs='cdn')
            if isinstance(html, dict):
                html_kwargs.update(html)
            saved.write_html(html_path, **html_kwargs)
            log(f"Wrote HTML to {relpath(html_path)}: {html}")

    if show is None:
        show = env.get(PLOT_SHOW_VAR)
        if show is None:
            show = DEFAULT_SHOW
    if show == 'file':
        if png_path:
            return Image(filename=png_path)
        else:
            raise ValueError("No `name` passed, for `show='file'`")
    elif show == 'png':
        return Image(fig.to_image())
    elif show is None or show is False:
        return
    else:
        return fig
