from os import environ as env
from os.path import exists
from typing import Optional, Union, Literal

import plotly.graph_objects as go
from IPython.display import Image
from plotly.graph_objs import Figure

from utz import err

DEFAULT_PLOTS_DIR = 'www/public/plots'
DEFAULT_MARGIN = { 't': 0, 'r': 25, 'b': 0, 'l': 0, }

# set this env var to a truthy string to return a static Image (instead of an interactive plot)
PLOT_DISPLAY_IMG = 'PLOT_DISPLAY_IMG'

class Unset:
    pass


_Unset = type(Unset)


def save(fig, title, name, **kwargs):
    return plot(fig, title, name=name, **kwargs)


def plot(
        fig: Figure,
        title: str,
        name: str | None = None,
        bg: str | None = None,
        hoverx: bool = False,
        hovertemplate: str | None = None,
        png_title: bool = False,
        yrange: str | None = 'tozero',
        legend: Union[bool, dict, _Unset] = Unset,
        bottom_legend: Union[bool, Literal['all']] = 'all',
        pretty: bool = False,
        margin: Union[None, int, dict] = None,
        dir: str | None = None,
        w: int | None = None,
        h: int | None = None,
        xtitle: str | None = None,
        ytitle: str | None = None,
        ltitle: str | None = None,
        grid: str | None = None,
        xgrid: str | None = None,
        ygrid: str | None = None,
        return_img: bool | None = None,
        x: dict | str | None = None,
        y: dict | str | None = None,
        **layout,
):
    """Plotly wrapper with convenience kwargs for common configurations"""
    if not dir:
        if exists(DEFAULT_PLOTS_DIR):
            dir = DEFAULT_PLOTS_DIR
        elif exists(f'../{DEFAULT_PLOTS_DIR}'):
            dir = f'../{DEFAULT_PLOTS_DIR}'
        else:
            dir = '.'

    bottom_legend_kwargs = dict(
        orientation='h',
        x=0.5,
        xanchor='center',
        yanchor='top',
    )
    if xtitle:
        fig.update_xaxes(title=dict(text=xtitle))
    if ytitle:
        fig.update_yaxes(title=dict(text=ytitle))
    layout['legend_title'] = layout.get('legend_title', ltitle or '')

    if w is not None:
        layout['width'] = w
    if h is not None:
        layout['height'] = h

    if bg:
        layout['plot_bgcolor'] = 'white'
        layout['paper_bgcolor'] = 'white'
    if hoverx:
        layout['hovermode'] = 'x'
        fig.update_traces(hovertemplate=hovertemplate)
    elif hovertemplate:
        fig.update_traces(hovertemplate=hovertemplate)
    if yrange:
        layout['yaxis_rangemode'] = yrange

    if bottom_legend == 'all':
        if 'legend' not in layout:
            layout['legend'] = {}
        layout['legend'].update(**bottom_legend_kwargs)

    if legend is False:
        layout['showlegend'] = False
    elif isinstance(legend, dict):
        layout['legend'] = legend

    if xgrid:
        fig.update_xaxes(gridcolor=xgrid,)
    elif grid:
        fig.update_xaxes(gridcolor=grid,)

    if ygrid:
        fig.update_yaxes(gridcolor=ygrid,)
    elif grid:
        fig.update_yaxes(gridcolor=grid,)

    if isinstance(x, str):
        fig.update_xaxes(title_text=x)
    elif isinstance(x, dict):
        fig.update_xaxes(**x)

    if isinstance(y, str):
        fig.update_yaxes(title_text=y)
    elif isinstance(y, dict):
        fig.update_yaxes(**y)

    title_layout = dict(title=title, title_x=0.5)
    if png_title:
        layout.update(title_layout)
    fig.update_layout(**layout)
    fig.update_yaxes(rangemode='tozero')
    saved = go.Figure(fig)
    if not png_title:
        # only need to do this if it wasn't already done above
        fig.update_layout(**title_layout)

    if bottom_legend is True:
        saved.update_layout(
            legend=bottom_legend_kwargs,
        )

    if isinstance(margin, int):
        margin = { 't': margin, 'r': margin, 'b': margin, 'l': margin }
    saved.update_layout(margin=margin or DEFAULT_MARGIN)
    if name:
        saved.write_json(f'{dir}/{name}.json', pretty=pretty)
        png_path = f'{dir}/{name}.png'
        saved.write_image(png_path)
        err(f"Wrote image to {png_path}")

    if return_img is None:
        return_img = bool(env.get(PLOT_DISPLAY_IMG))
    if return_img:
        return Image(filename=png_path)
    else:
        return fig
