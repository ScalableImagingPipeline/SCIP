import dask
from PIL import Image
import dask.bag
import numpy
from pathlib import Path


@dask.delayed
def load_image(p: str) -> dict[numpy.ndarray, str]:
    im = Image.open(p)
    arr = numpy.empty(shape=(im.n_frames, im.height, im.width), dtype=float)
    for i in range(im.n_frames):
        im.seek(i)
        arr[i] = numpy.array(im)
    return dict(pixels=arr, path=p)


def bag_from_directory(path: str) -> dask.bag.Bag:
    """
    Construct delayed ops for all tiffs in a directory

    path (str): Directory to find tiffs

    """

    image_paths = []
    for p in Path(path).glob("**/*.tiff"):
        image_paths.append(load_image(str(p)))

    return dask.bag.from_sequence(image_paths, partition_size=100).map(load_image)
