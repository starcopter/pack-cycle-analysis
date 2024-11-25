from datetime import timedelta
from typing import Callable

import pandas as pd


def find_rising_edges(condition: pd.Series, drop: bool = True) -> pd.Series:
    mask = condition.astype(int).diff().fillna(0).astype(int) == 1
    if drop:
        return condition.loc[mask]
    return mask


def refine_condition(
    data: pd.Series,
    fn: Callable[[pd.DataFrame], bool],
    df: pd.DataFrame,
    dt: timedelta = timedelta(seconds=20),
) -> pd.Series:
    data = data.copy()
    data.index = pd.Index([fn(df.loc[ts - dt : ts + dt]).idxmax() for ts in data.index], name=data.index.name)
    return data
