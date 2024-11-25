# Pack Cycle Analysis

This repository contains battery pack cycling data, and tools/scripts to analyze and parse the data.

## Repository Layout

Each project or test run is contained in its own folder under `projects/`.

## Setup Instructions

1. Ensure you have [uv](https://docs.astral.sh/uv/) installed.
2. Clone this repository: `git clone https://github.com/starcopter/pack-cycle-analysis.git`
3. Navigate to the project directory: `cd pack-cycle-analysis`
4. Install the project dependencies: `uv sync`
5. Open the project in VSCode, and start working!

Larger data files are versioned with [DVC](https://dvc.org/) and reside in the `dlake` S3 bucket on Scaleway.
Contact [Finwood](https://github.com/Finwood) if you need access.
