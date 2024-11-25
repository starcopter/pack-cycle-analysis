# %%
from enum import IntEnum

import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["savefig.dpi"] = 240


# %%
class Phase(IntEnum):
    NONE = 0
    DSG = 1
    DSG_REST = 2
    CHG = 3
    CHG_REST = 4


def map_cycles(df: pd.DataFrame | pd.DatetimeIndex, cycles: pd.DataFrame, cycle_offset: int = 0) -> pd.DataFrame:
    if isinstance(df, pd.DatetimeIndex):
        df = pd.DataFrame(index=df)
    else:
        df = df.copy()

    df["cycle"] = -1
    df["phase"] = Phase.NONE

    for cycle in cycles.index:
        dsg_start, dsg_end = cycles.loc[cycle, ["dsg_start", "dsg_end"]]
        chg_start, chg_end = cycles.loc[cycle, ["chg_start", "chg_end"]]

        try:
            next_dsg_start = cycles.loc[cycle + 1, "dsg_start"]
        except KeyError:
            next_dsg_start = df.index[-1]

        df.loc[dsg_start:next_dsg_start, "cycle"] = cycle + cycle_offset
        df.loc[dsg_start:dsg_end, "phase"] = Phase.DSG
        df.loc[dsg_end:chg_start, "phase"] = Phase.DSG_REST
        df.loc[chg_start:chg_end, "phase"] = Phase.CHG
        df.loc[chg_end:next_dsg_start, "phase"] = Phase.CHG_REST

    return df


# %%
c3 = (
    pd.read_parquet("data/sm15k.parquet", columns=["time", "voltage", "current"])
    .set_index("time")
    # .resample("1s")
    # .mean()
    # .interpolate()
    .pipe(
        map_cycles,
        pd.read_parquet("data/cycles.parquet"),
        cycle_offset=45,
    )
    .query("cycle > -1")
)
c3["current"] /= 6


# %%
un38_3 = (
    pd.read_parquet("../UN38.3/source.parquet", columns=["_time", "voltage", "current"])
    .rename(columns={"_time": "time"})
    .set_index("time")
    # .resample("1s")
    # .mean()
    # .interpolate()
    .pipe(
        map_cycles,
        (
            pd.read_csv(
                "../UN38.3/cycles.csv",
                index_col="cycle",
                parse_dates=["chg_start", "chg_end", "dsg_start", "dsg_end"],
            )
            .loc[:, ["chg_start", "chg_end", "dsg_start", "dsg_end"]]
            .apply(lambda series: series.dt.tz_convert("UTC"))
        ),
    )
    .query("cycle > -1")
)
un38_3["current"] /= 4


# %%
df = pd.concat([un38_3, c3], axis=0)
df


# %%
duration = (
    df.groupby(["cycle", "phase"])["voltage"]
    .apply(lambda df: pd.Series(df.index - df.index[0], index=df.index))
    .rename("duration")
)

# %%
new_df = (
    df.set_index(["cycle", "phase"], append=True)
    .join(duration / pd.Timedelta(1, "m"))
    .set_index("duration", append=True)
    .reset_index("time", drop=True)
)
new_df

# %%
dsg = new_df.xs(Phase.DSG, level="phase")


# %%
fig, ax = plt.subplots(1, 1, figsize=(10, 4))

dsg.loc[1, "voltage"].where(lambda v: v >= 18).plot(ax=ax, lw=1.0, label="Cycle 1")
dsg.loc[25, "voltage"].where(lambda v: v >= 18).plot(ax=ax, lw=1.0, label="Cycle 25")
dsg.loc[51, "voltage"].plot(ax=ax, lw=1.0, label="Cycle 50")
dsg.loc[100, "voltage"].plot(ax=ax, lw=1.0, label="Cycle 100")
dsg.loc[150, "voltage"].plot(ax=ax, lw=1.0, label="Cycle 150")

dsg.loc[1, "voltage"].where(lambda v: v < 18).plot(ax=ax, lw=1.0, c="C0", label="", ls="--")
dsg.loc[25, "voltage"].where(lambda v: v < 18).plot(ax=ax, lw=1.0, c="C1", label="", ls="--")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlabel("Duration in minutes")
ax.set_ylabel("Voltage in V")
ax.legend()

fig.suptitle("12A Constant Current Discharge Curves")
fig.tight_layout()
fig.savefig("img/discharge-curves.png")
