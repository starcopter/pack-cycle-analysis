# %%
import duckdb
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["savefig.dpi"] = 240


# %%
def reset_datetime_index(df: pd.DataFrame, normalize: pd.Timedelta | None = pd.Timedelta(seconds=1)) -> pd.DataFrame:
    new_index = df.index - df.index[0]
    if normalize:
        new_index = new_index / normalize
    return df.set_index(new_index)


# %%
duckdb.sql("""
create table dsg_current as

with pack_current as (
    select time, node_id, current
    from read_parquet('data/packs.parquet')
),
cycles as (
    select
        cycle,
        dsg_start::timestamptz as dsg_start,
        dsg_end::timestamptz as dsg_end,
        chg_start::timestamptz as chg_start,
        chg_end::timestamptz as chg_end,
    from read_parquet('data/cycles.parquet')
)

select dsg.cycle as cycle, p.*
from pack_current p
join cycles dsg on p.time between dsg.dsg_start + interval '2 seconds' and dsg.dsg_end - interval '2 seconds'
order by time, node_id;
""")

# %%
c6 = (
    duckdb.sql("select time, node_id, current from dsg_current where cycle = 6")
    .df()
    .set_index("time")
    .pivot(columns="node_id", values="current")
    .pipe(reset_datetime_index, normalize=pd.Timedelta(minutes=1))
)
c105 = (
    duckdb.sql("select time, node_id, current from dsg_current where cycle = 105")
    .df()
    .set_index("time")
    .pivot(columns="node_id", values="current")
    .pipe(reset_datetime_index, normalize=pd.Timedelta(minutes=1))
)
std = (
    duckdb.sql("select cycle, node_id, stddev(current) as std from dsg_current group by all")
    .df()
    .set_index("cycle")
    .pivot(columns="node_id", values="std")
)


# %%
fig = plt.figure(figsize=(12, 7))
gs = fig.add_gridspec(2, 2)

# Bottom plot spanning both columns
ax0 = fig.add_subplot(gs[1, :])
std.plot(ax=ax0, xlabel="Cycle", title="Standard Deviation")
ax0.set_ylim(0, None)
ax0.legend(bbox_to_anchor=(0.5, 0.02), loc="lower center", ncols=6)

# Top left plot
ax1 = fig.add_subplot(gs[0, 0])
c6.plot(ax=ax1, legend=False, xlabel="Time (minutes)", title="Cycle 6")
ax1.set_yticks([-11, -12, -13, -14, -15])

# Top right plot
ax2 = fig.add_subplot(gs[0, 1], sharey=ax1)
c105.plot(ax=ax2, legend=False, xlabel="Time (minutes)", title="Cycle 105")

# Common styling
for ax in [ax0, ax1, ax2]:
    ax.set_ylabel("Current (A)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

fig.suptitle("Current in Discharge Phase")
fig.tight_layout()
fig.savefig("img/current-in-discharge.png")
