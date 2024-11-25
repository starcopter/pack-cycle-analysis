#!/usr/bin/env python3

import logging
from pathlib import Path

import pandas as pd
from rich.logging import RichHandler
from scipy import integrate

from pack_cycle_analysis import find_rising_edges, refine_condition

SM15K_DATA_PATH = Path("data/sm15k.parquet")


def parse_cycles() -> pd.DataFrame:
    log = logging.getLogger(__name__)

    log.info(f"Loading data from {SM15K_DATA_PATH}")
    sm15k = pd.read_parquet(SM15K_DATA_PATH, columns=["time", "voltage", "current"]).set_index("time")

    log.info("Resampling current to 10s")
    _current = (
        sm15k.loc["2024-10-25 17:30+00:00":"2024-11-06 11:00:00+00:00", "current"]
        .resample("10s")
        .mean()
        .interpolate(method="linear")
    )

    log.info("Detecting phase transitions")
    discharge_start = (
        find_rising_edges(_current < -24)
        .pipe(refine_condition, fn=lambda df: df.current < -1, df=sm15k)
        .rename("discharge_start")
    )
    discharge_end = (
        find_rising_edges(_current > -24)
        .pipe(refine_condition, fn=lambda df: df.current > -1, df=sm15k)
        .rename("discharge_end")
    )
    charge_start = (
        find_rising_edges(_current > 24)
        .pipe(refine_condition, fn=lambda df: df.current > 1, df=sm15k)
        .rename("charge_start")
    )
    charge_end = (
        find_rising_edges(_current < 600e-3)
        .pipe(refine_condition, fn=lambda df: df.current < -600e-3, df=sm15k)
        .rename("charge_end")
    )

    _df = pd.concat([discharge_start, discharge_end, charge_start, charge_end], axis=1).fillna(0).astype(bool)
    assert all(_df[_df.sum(axis=1) == 1])

    cycles = pd.concat(
        [
            discharge_start.reset_index().time.dt.floor("100ms").rename("dsg_start"),
            discharge_end.reset_index().time.dt.ceil("100ms").rename("dsg_end"),
            charge_start.reset_index().time.dt.floor("100ms").rename("chg_start"),
            charge_end.reset_index().time.dt.ceil("100ms").rename("chg_end"),
        ],
        axis=1,
    )
    cycles.index = pd.RangeIndex(1, len(cycles) + 1, name="cycle")

    log.info("Resampling voltage and current to 100ms")
    df = sm15k.resample("100ms").mean().interpolate()
    df["power"] = df["voltage"] * df["current"]
    df["cycle"] = -1
    df["phase"] = ""

    log.info("Assigning cycles and phases")
    for cycle, cs, ce, ds, de in cycles[["chg_start", "chg_end", "dsg_start", "dsg_end"]].dropna().itertuples():
        df.loc[cs:ce, "cycle"] = cycle
        df.loc[ds:de, "cycle"] = cycle
        df.loc[cs:ce, "phase"] = "charge"
        df.loc[ds:de, "phase"] = "discharge"

    log.info("Calculating charge and energy")
    charge_Ah = (
        df.loc[df["cycle"] != -1]
        .groupby(["cycle", "phase"])["current"]
        .aggregate(integrate.trapezoid, dx=0.1)
        .divide(3600)
        .unstack()
    )
    energy_Wh = (
        df.loc[df["cycle"] != -1]
        .groupby(["cycle", "phase"])["power"]
        .aggregate(integrate.trapezoid, dx=0.1)
        .divide(3600)
        .unstack()
    )

    log.info("Finalizing cycles")
    cycles["dsg_start"] = cycles["dsg_start"].dt.floor("100ms")
    cycles["dsg_end"] = cycles["dsg_end"].dt.ceil("100ms")
    cycles["chg_start"] = cycles["chg_start"].dt.floor("100ms")
    cycles["chg_end"] = cycles["chg_end"].dt.ceil("100ms")

    cycles["dsg_duration"] = cycles["dsg_end"] - cycles["dsg_start"]
    cycles["chg_duration"] = cycles["chg_end"] - cycles["chg_start"]
    cycles["dsg_charge_Ah"] = charge_Ah["discharge"]
    cycles["chg_charge_Ah"] = charge_Ah["charge"]
    cycles["dsg_energy_Wh"] = energy_Wh["discharge"]
    cycles["chg_energy_Wh"] = energy_Wh["charge"]
    cycles["energy_loss_Wh"] = cycles["chg_energy_Wh"] + cycles["dsg_energy_Wh"]

    return cycles


def main():
    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    cycles = parse_cycles()

    cycles.to_csv("data/cycles.csv")
    cycles.to_parquet("data/cycles.parquet")


if __name__ == "__main__":
    main()
