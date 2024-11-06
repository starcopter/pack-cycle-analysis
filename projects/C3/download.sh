#!/usr/bin/env bash

base=$PWD

pushd ~/src/parflux
source .envrc

nice parflux -vv --start "2024-10-25 18:31:00" --stop "2024-11-06 14:59:00" get \
	--dest $base/data \
	sm15k/supply

nice parflux -vv --start "2024-10-25 18:31:00" --stop "2024-11-06 14:59:00" get \
	--dest $base/data \
	--filter 'r.logger == "pyric-t420-lasse"' \
	pyric/reg.udral.physics.electricity.SourceTs.0.1 \
	pyric/reg.udral.service.battery.Status.0.2 \
	pyric/starcopter.aeric.bms.SystemStatus.0.4 \
	pyric/starcopter.aeric.bms.Temperatures.0.1

popd

nice duckdb < convert.sql
