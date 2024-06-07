from functools import partial
from io import TextIOWrapper
from os import environ as env
from os.path import exists, join
from sys import stderr
from typing import Union, Literal

from IPython.display import Image

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from plotly.validators.scatter.marker import SymbolValidator
symbols = SymbolValidator().values[2::12]

from utz import err


# Env vars to fall back to, for various plot kwargs
PLOT_SHOW_VAR = 'UTZ_PLOT_SHOW'
PLOT_DIR_VAR = 'UTZ_PLOT_DIR'
PLOT_MARGIN_VAR = 'UTZ_PLOT_MARGIN'
PLOT_BG_VAR = 'UTZ_PLOT_BG'
PLOT_GRID_VAR = 'UTZ_PLOT_GRID'
PLOT_SUBTITLE_SIZE_VAR = 'UTZ_PLOT_SUBTITLE_SIZE'

DEFAULT_BG = 'white'
DEFAULT_SHOW = 'html'
DEFAULT_GRID = '#ccc'
DEFAULT_SUBTITLE_SIZE = '0.8em'


class Unset:
    pass


_Unset = type(Unset)


Title = str | list[str] | None


def title(s: Title, subtitle_size: str | None = None) -> str | None:
    if isinstance(s, list):
        if subtitle_size is None:
            subtitle_size = env.get(PLOT_SUBTITLE_SIZE_VAR, DEFAULT_SUBTITLE_SIZE)

        title, *subtitles = s
        prefix = f'<br><span style="font-size:{subtitle_size}">'
        suffix = '</span>'
        title = prefix.join([title] + [ f'{subtitle}{suffix}' for subtitle in subtitles ])
        return title
    else:
        return s


make_title = title


def save(fig, title, name, **kwargs):
    return plot(fig, title, name=name, **kwargs)


def plot(
        fig: Figure,
        title: Title,
        name: str | None = None,
        bg: str | None | _Unset = Unset,
        subtitle_size: str | None = None,
        hoverx: bool = False,
        hovertemplate: Title = None,
        png_title: bool = True,
        yrange: str | None = 'tozero',
        legend: Union[bool, dict, None] = None,
        bottom_legend: Union[bool, Literal['all']] = False,
        pretty: bool = False,
        margin: Union[None, int, dict, _Unset] = Unset,
        dir: str | None = None,
        w: int | None = None,
        h: int | None = None,
        xtitle: Title = None,
        ytitle: Title = None,
        ltitle: Title = None,
        grid: str | None | _Unset = Unset,
        xgrid: str | None = None,
        ygrid: str | None = None,
        x: dict | str | None = None,
        y: dict | str | None = None,
        log: TextIOWrapper | bool | None = stderr,
        show: Literal['png', 'file', 'html'] | bool | None = None,
        zerolines: bool | Literal['x', 'y'] | None = True,
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
    """
    mk_title = partial(make_title, subtitle_size=subtitle_size)
    xtitle = mk_title(xtitle)
    if xtitle:
        fig.update_xaxes(title=dict(text=xtitle))

    ytitle = mk_title(ytitle)
    if ytitle:
        fig.update_yaxes(title=dict(text=ytitle))

    ltitle = mk_title(ltitle)
    layout['legend_title'] = layout.get('legend_title', ltitle or '')

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

    if legend is False:
        layout['showlegend'] = False
    elif isinstance(legend, dict):
        layout['legend'] = legend

    if grid is Unset:
        grid = env.get(PLOT_GRID_VAR)
        if grid is None:
            grid = DEFAULT_GRID

    if xgrid:
        fig.update_xaxes(gridcolor=xgrid)
    elif grid:
        fig.update_xaxes(gridcolor=grid)

    if ygrid:
        fig.update_yaxes(gridcolor=ygrid)
    elif grid:
        fig.update_yaxes(gridcolor=grid)

    if zerolines == 'x' or zerolines is True:
        fig.update_xaxes(
            zeroline=True,
            zerolinecolor=xgrid or grid,
            zerolinewidth=1,
        )

    if zerolines == 'y' or zerolines is True:
        fig.update_yaxes(
            zeroline=True,
            zerolinecolor=ygrid or grid,
            zerolinewidth=1,
        )

    if isinstance(x, str):
        fig.update_xaxes(title_text=x)
    elif isinstance(x, dict):
        fig.update_xaxes(**x)

    if isinstance(y, str):
        fig.update_yaxes(title_text=y)
    elif isinstance(y, dict):
        fig.update_yaxes(**y)

    title = mk_title(title)
    title_layout = dict(title_text=title, title_x=0.5) if title else {}
    if png_title:
        layout.update(title_layout)
    fig.update_layout(**layout)

    saved = go.Figure(fig)
    if not png_title:
        # only need to do this if it wasn't already done above
        fig.update_layout(**title_layout)

    if bottom_legend is True:
        saved.update_layout(
            legend=bottom_legend_kwargs,
        )

    if margin is Unset:
        margin = env.get(PLOT_MARGIN_VAR)
        if margin:
            margin = json.loads(margin)
    if isinstance(margin, int):
        margin = { k: margin for k in 'trbl' }
    if margin:
        saved.update_layout(margin=margin)

    if log is True:
        log = err
    elif log:
        log = partial(print, file=log)
    else:
        log = lambda: ()

    if name:
        if dir is None:
            dir = env.get(PLOT_DIR_VAR)
        if dir:
            if not exists(dir):
                makedirs(dir, exist_ok=True)
        else:
            dir = '.'
        json_path = join(dir, f'{name}.json')
        saved.write_json(json_path, pretty=pretty)
        png_path = join(dir, f'{name}.png')
        log(f"Wrote plot JSON to {png_path}")
        saved.write_image(png_path)
        log(f"Wrote plot image to {png_path}")

    if show is None:
        show = env.get(PLOT_SHOW_VAR)
        if show is None:
            show = DEFAULT_SHOW
    if show == 'file':
        return Image(filename=png_path)
    elif show == 'png':
        return Image(fig.to_image())
    elif show is None or show is False:
        return
    else:
        return fig
