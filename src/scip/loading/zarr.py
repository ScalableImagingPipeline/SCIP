import dask
import dask.bag
import dask.dataframe
import pandas
import zarr
import numpy
from pathlib import Path


def load_image(event, z, channels, clip):
    """
    Load an image from a certain path

    Args:
        path (str): path of image,
        z (zarr): zarr object
        channels (list, optional): image channels to load. Defaults to None.

    Returns:
        dict: dictionary containing pixel values (ndarray) and path for each image
    """

    i = event["zarr_idx"]
    if clip is not None:
        event["pixels"] = numpy.clip(z[i].reshape(z.attrs["shape"][i])[channels], 0, clip)
    else:
        event["pixels"] = z[i].reshape(z.attrs["shape"][i])[channels]
    event["pixels"] = event["pixels"].astype(numpy.float32)
    return event


def load_image_partition(partition, z,  channels, clip):
    return [load_image(event, z, channels, clip) for event in partition]


def bag_from_directory(path, idx, channels, partition_size, clip):
    """
    Construct delayed ops for all tiffs in a directory

    Args:
        path (str): Directory to find tiffs

    Returns:
        dask.bag: bag containing dictionaries with image data
    """

    z = zarr.open(path)
    path = Path(path)
    events = []
    for i, obj in enumerate(z.attrs["object_number"]):
        events.append(dict(
            path=str(path),
            zarr_idx=i,
            idx=f"{idx}_{obj}",
            group=str(path.stem)
        ))

    meta = pandas.DataFrame.from_records(data=events, index="idx")
    meta.columns = [f"meta_{c}" for c in meta.columns]
    meta = dask.dataframe.from_pandas(meta, chunksize=10*partition_size)

    bag = dask.bag.from_sequence(events, partition_size=partition_size)
    bag = bag.map_partitions(load_image_partition, z, channels, clip)

    return bag, meta, clip
