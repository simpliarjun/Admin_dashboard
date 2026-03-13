import plotly.express as px
import pandas as pd

def plot_pie(series, title):
    series = series.dropna()
    fig = px.pie(
        values=series.values,
        names=series.index,
        title=title,
        hole=0.3
    )
    fig.update_layout(
        legend_title="",
        title_x=0.5,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def plot_bar(series, title, xlabel="", ylabel=""):
    series = series.dropna()
    df = series.sort_values().reset_index()
    df.columns = [xlabel or "Category", ylabel or "Value"]
    fig = px.bar(
        df,
        x=ylabel or "Value",
        y=xlabel or "Category",
        orientation="h",
        title=title
    )
    fig.update_layout(
        title_x=0.5,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def plot_line(series, title, xlabel="", ylabel=""):
    series = series.dropna()
    df = pd.DataFrame({
        xlabel or "X": series.index.astype(str),
        ylabel or "Y": series.values
    })
    fig = px.area(
        df,
        x=xlabel or "X",
        y=ylabel or "Y",
        title=title
    )
    fig.update_traces(line=dict(width=3))
    fig.update_layout(
        title_x=0.5,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig
