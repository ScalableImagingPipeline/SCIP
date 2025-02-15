![SCIP logo](docs/source/logo.png)

# SCIP: Scalable Cytometry Image Processing

![main workflow badge](https://github.com/ScalableImagingPipeline/dask-pipeline/actions/workflows/main.yml/badge.svg) [![Documentation Status](https://readthedocs.org/projects/scalable-cytometry-image-processing/badge/?version=latest)](https://scalable-cytometry-image-processing.readthedocs.io/en/latest/?badge=latest) [![codecov](https://codecov.io/gh/ScalableCytometryImageProcessing/SCIP/branch/main/graph/badge.svg?token=6RYKJ8CLU0)](https://codecov.io/gh/ScalableCytometryImageProcessing/SCIP)

Scalable Cytometry Image Processing (SCIP) is an open-source tool that implements
an image processing pipeline on top of Dask, a distributed computing framework written in Python.
SCIP performs normalization, image segmentation and masking, and feature extraction.

Check the [docs](https://scalable-cytometry-image-processing.readthedocs.io/en/latest/) for
installation and usage instructions, and API documentation.

## Development

### Generating documentation

For publishing online:
```
cd docs
make clean
make html
```

For development with live reloading:
```
cd docs
make livehtml
```

### Generate release changelog
```
git log v{previous version tag}..HEAD --oneline | xclip -sel clip
```
