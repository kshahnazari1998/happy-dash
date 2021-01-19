# Author: Kevin Shahnazari
# Date created: Jan 18 2021

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly_express as px


###********************************* Define constants *******************************************
summary_df = pd.read_csv("data/processed/summary_df.csv").sort_values(by="country")

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "14rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    # "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# Define relationship between dataset columns and display names
feature_dict = {
    "GDP Per Capita": "gdp_per_capita",
    "Family": "family",
    "Life Expectancy": "health_life_expectancy",
    "Freedom": "freedom",
    "Corruption": "perceptions_of_corruption",
    "Generosity": "generosity",
    "Dystopia baseline + residual": "dystopia_residual",
}


###***************************************Layout building************************************

mirco_tab_leftbar_countries = dcc.Dropdown(
    id="country-select-1",
    multi=True,
    options=[{"label": x, "value": x} for x in summary_df.country.unique()],
    value=["Canada", "Switzerland", "China"],
)

sidebar = dbc.Col(
    children=[
        html.H2("Features", className="display-6"),
        html.Hr(),
        dbc.Checklist(
            id="feature-select-1",
            options=[{"label": k, "value": v} for k, v in feature_dict.items()],
            value=[v for k, v in feature_dict.items()],
        ),
        html.Hr(),
        html.H3("Year Range", className="display-6"),
        dcc.RangeSlider(
            id="year-select-1",
            min=min(summary_df.year),
            max=max(summary_df.year),
            step=1,
            marks={
                int(x): {"label": str(x), "style": {"transform": "rotate(45deg)"}}
                for x in list(summary_df.year.unique())
            },
            value=[2015, 2019],
            pushable=1,
        ),
        html.Hr(),
        html.H3("Countries", className="display-6"),
        dbc.Col(
            dcc.Dropdown(
                id="country-select-1",
                multi=True,
                options=[{"label": x, "value": x} for x in summary_df.country.unique()],
                value=["Canada", "Switzerland", "China"],
            ),
            width=12,
            style={
                # "width": "100%",
                # "height": "300px",
                # "overflow": "scroll",
                "padding": "10px 10px 10px 0px",
            },
        ),
    ],
    style={"background-color": "#f8f9fa"},
    # style=SIDEBAR_STYLE,
    md=3,
)


### CODE TO SETUP SIDEBAR WITHIN TABS:
# micro_tab_leftbar = [
#     mirco_tab_leftbar_features,
#     dbc.Label("Countries"),
# ]

# micro_tab = dbc.Row(
#     [dbc.Col(micro_tab_leftbar, lg=2, md=2), dbc.Col(html.Div(), md=4, lg=4)]
# )

content = dbc.Col(
    id="micro-content",
    # style=CONTENT_STYLE,
    md=9,
    children=[
        dcc.Graph(id="happiness-over-time", style={"height": "25%", "margin": "0"}),
        dcc.Graph(id="features-over-time", style={"height": "75%"}),
    ],
)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container(
    children=[
        dbc.Row(
            children=[
                # dbc.Tabs([
                #     dbc.Tab(micro_tab, label='Micro', style={'background-color': 'red'}),
                #     dbc.Tab('overall tab', label='Overall')
                # ])
                sidebar,
                content,
            ],
            className="h-100",
        )
    ],
    fluid=True,
    style={"height": "100vh"},
)

####*******************************************Callback definition***************************
def filter_df(summary_df, country_list, feat_list, year_range):
    """
    Helper func to filter summary_df to countries, columns (feat_list), and list of years.
    Keep "country", "happiness_score", "year" for downstream tasks
    """
    year_list = list(range(min(year_range), max(year_range) + 1))

    return summary_df.loc[
        ((summary_df.country.isin(country_list)) & (summary_df.year.isin(year_list))),
        feat_list + ["country", "happiness_score", "year"],
    ]


@app.callback(
    [Output("happiness-over-time", "figure"), Output("features-over-time", "figure")],
    [
        Input("country-select-1", "value"),
        Input("feature-select-1", "value"),
        Input("year-select-1", "value"),
    ],
)
def build_detail_plots(country_list, feat_list, year_range):
    """Builds a list of bar charts summarizing certain countries, feature names (columns in the df)
    and a time frame.

    Parameters
    ----------
    summary_df : Pandas.DataFrame
        Dataframe with columns
    country_list : list
        List of country names to filter `summary_df` on
    feat_list : list
        List of features (column names in `summary_df`). If `None` use all 7 contributing features to happiness score
    year_list : list
        List of years to filter on

    Returns
    -------
    list : List[plotly.express.Figure]
        First chart: Happiness score over time by country
        Second - Eigth chart: Contributing factor trend over time by country.
        Empty charts appended at end if all features aren't specified.
    """
    # ALl features to consider
    all_feats = [v for v in feature_dict.values()]

    if feat_list is None:
        feat_list = all_feats

    # Filter to specified data
    # Improve year formatting for datetime x-axis
    filtered_df = filter_df(summary_df, country_list, feat_list, year_range).assign(
        year=lambda x: pd.to_datetime(x.year, format="%Y")
    )
    cols = list(set(all_feats).intersection(filtered_df.columns))

    fig_list = []
    # Build first plot - happiness scores over time
    happiness_plot = (
        px.line(
            filtered_df,
            x="year",
            y="happiness_score",
            color="country",
            title="Happiness Score Over Time by Country",
        )
        .update_traces(mode="lines+markers")
        .update_layout(
            {
                "xaxis": {
                    # "tickformat": "%Y",
                    "tickmode": "array",
                    "tickvals": filtered_df.year.dt.year.unique(),
                    "ticktext": [str(x) for x in filtered_df.year.dt.year.unique()],
                }
            }
        )
    )
    fig_list.append(happiness_plot)

    # Facetted plot for features
    fig_list.append(
        px.line(
            filtered_df.melt(
                id_vars=["country", "year"], value_vars=cols, value_name="Contribution"
            ),
            x="year",
            y="Contribution",
            color="country",
            facet_col="variable",
            facet_col_wrap=2,
            facet_col_spacing=0.04,
            facet_row_spacing=0.07,
            title="Impact Of Features Over Time On Happiness Score",
        )
        .update_yaxes(matches=None)
        .update_xaxes(showticklabels=True)
        .update_traces(mode="lines+markers")
    )

    return fig_list


if __name__ == "__main__":
    app.run_server(debug=True)
