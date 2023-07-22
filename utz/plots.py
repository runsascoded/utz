from os import environ as env
from os.path import exists
from typing import Optional

import plotly.graph_objects as go
from IPython.display import Image


DEFAULT_PLOTS_DIR = 'www/public/plots'
DEFAULT_MARGIN = { 't': 0, 'r': 25, 'b': 0, 'l': 0, }

# set this env var to a truthy string to return a static Image (instead of an interactive plot)
PLOT_DISPLAY_IMG = 'PLOT_DISPLAY_IMG'


def save(
        fig, title, name,
        bg=None, hoverx=False, hovertemplate=None, png_title=False,
        yrange='tozero', bottom_legend='all',
        pretty=False, margin=None,
        dir=None, w=None, h=None,
        xtitle=None, ytitle=None, ltitle=None,
        grid=None, xgrid=None, ygrid=None,
        return_img: Optional[bool] = None,
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
    layout['xaxis_title'] = layout.get('xaxis_title', xtitle or '')
    layout['yaxis_title'] = layout.get('yaxis_title', ytitle or '')
    layout['legend_title'] = layout.get('legend_title', ltitle or '')
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
    if xgrid:
        fig.update_xaxes(gridcolor=xgrid,)
    elif grid:
        fig.update_xaxes(gridcolor=grid,)
    if ygrid:
        fig.update_yaxes(gridcolor=ygrid,)
    elif grid:
        fig.update_yaxes(gridcolor=grid,)
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
    saved.update_layout(margin=margin or DEFAULT_MARGIN)
    saved.write_json(f'{dir}/{name}.json', pretty=pretty)
    png_path = f'{dir}/{name}.png'
    saved.write_image(png_path, width=w, height=h)

    if return_img is None:
        return_img = bool(env.get(PLOT_DISPLAY_IMG))
    if return_img:
        return Image(filename=png_path)
    else:
        return fig
