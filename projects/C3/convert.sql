create or replace table sm15k as

select
    time_bucket('100ms', _time) as time,
    avg("voltage") as voltage,
    avg("current") as current,
from read_parquet('data/sm15k/supply.parquet')
group by time
order by time;

--------------------------------------------------------------------------------

create or replace table packs as

with energy_source as (
    select
        time_bucket('1s', _time) as time,
        node_id::int as node_id,
        avg("value.power.voltage") as voltage,
        avg("value.power.current") as current,
    from read_parquet('data/pyric/reg.udral.physics.electricity.SourceTs.0.1.parquet')
    group by time, node_id
    order by time, node_id
),
battery_status as (
    select
        time_bucket('1s', _time) as time,
        node_id::int as node_id,
        avg("cell_voltages[0]") as vc1,
        avg("cell_voltages[1]") as vc2,
        avg("cell_voltages[2]") as vc3,
        avg("cell_voltages[3]") as vc4,
        avg("cell_voltages[4]") as vc5,
        avg("cell_voltages[5]") as vc6,
    from read_parquet('data/pyric/reg.udral.service.battery.Status.0.2.parquet')
    group by time, node_id
    order by time, node_id
),
system_status as (
    select
        time_bucket('1s', _time) as time,
        node_id::int as node_id,
        avg("cell_balancing[0]") as cb1,
        avg("cell_balancing[1]") as cb2,
        avg("cell_balancing[2]") as cb3,
        avg("cell_balancing[3]") as cb4,
        avg("cell_balancing[4]") as cb5,
        avg("cell_balancing[5]") as cb6,
    from read_parquet('data/pyric/starcopter.aeric.bms.SystemStatus.0.4.parquet')
    group by time, node_id
    order by time, node_id
),
temperatures as (
    select
        time_bucket('1s', _time) as time,
        node_id::int as node_id,
        avg("bq76925_int_temp") - 273.15 as bq76925_temp,
        avg("stm32_core_temp") - 273.15 as stm32_temp,
        avg("bat_t3") - 273.15 as pack_temp,
    from read_parquet('data/pyric/starcopter.aeric.bms.Temperatures.0.1.parquet')
    group by time, node_id
    order by time, node_id
)

select
    es.time, es.node_id,
    es.voltage, es.current,
    bs.vc1, bs.vc2, bs.vc3, bs.vc4, bs.vc5, bs.vc6,
    ts.bq76925_temp, ts.stm32_temp, ts.pack_temp,
from energy_source es
join battery_status bs on es.time = bs.time and es.node_id = bs.node_id
join temperatures ts on es.time = ts.time and es.node_id = ts.node_id
order by es.time, es.node_id;

--------------------------------------------------------------------------------

copy sm15k to 'data/sm15k.parquet';
copy packs to 'data/packs.parquet';
