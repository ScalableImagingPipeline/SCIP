# Scalable image processing

## Installation

We recommend using [mamba](https://github.com/mamba-org/mamba) and pip to install SCIP. 

1. Create a new python 3.8 environment: `mamba create -n scip python=3.8`
1. Activate environment: `conda activate scip`
1. Install dask: `mamba install dask`
1. Install CellProfiler:
    1. `pip install cellprofiler`
    1. or, if you get errors: `pip install -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/ cellprofiler`
1. Install SCIP: `pip install .` or `pip install -e .` for development
1. (Optional) Install SCIP development dependencies: `pip install -r requirements.txt`