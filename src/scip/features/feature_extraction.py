import dask
import dask.bag
import dask.dataframe
import pandas

from .shape import shape_features, shape_features_meta
from .intensity import intensity_features, intensity_features_meta
from .texture import texture_features, texture_features_meta

from scip.utils.util import check


def bbox_features_meta(channel_names):
    d = {
        "bbox_minr": float,
        "bbox_minc": float,
        "bbox_maxr": float,
        "bbox_maxc": float
    }
    d.update({f"regions_{i}": float for i in channel_names})
    return d


def bbox_features(p, channel_names):
    d = {
        "bbox_minr": p["bbox"][0],
        "bbox_minc": p["bbox"][1],
        "bbox_maxr": p["bbox"][2],
        "bbox_maxc": p["bbox"][3],
    }
    d.update({f"regions_{i}": c for i, c in zip(channel_names, p["regions"])})
    return d


def extract_features(  # noqa: C901
    *,
    images: dask.bag.Bag,
    channel_names: list,
    types: list,
    maximum_pixel_value: int,
    loader_meta: dict = {}
) -> dask.dataframe.DataFrame:
    """
    Extract features from pixel data

    Args:
        images (dask.bag): bag containing dictionaries of image data

    Returns:
        dask.bag: bag containing dictionaries of image features
    """

    def features_partition(part):
        data = []
        for p in part:
            out = {k: p[k] for k in loader_meta.keys()}
            out["idx"] = p["idx"]

            if "pixels" in p:
                if "bbox" in types:
                    out.update(bbox_features(p, channel_names))
                if "shape" in types:
                    out.update(shape_features(p, channel_names))
                if "intensity" in types:
                    out.update(intensity_features(p, channel_names))
                if "texture" in types:
                    out.update(texture_features(p, channel_names, maximum_pixel_value))

            data.append(out)
        return data

    meta = {}
    if "bbox" in types:
        meta.update(bbox_features_meta(channel_names))
    if "shape" in types:
        meta.update(shape_features_meta(channel_names))
    if "intensity" in types:
        meta.update(intensity_features_meta(channel_names))
    if "texture" in types:
        meta.update(texture_features_meta(channel_names))

    full_meta = {**meta, **loader_meta, "idx": int}

    images = images.map_partitions(features_partition)
    images = images.map_partitions(
        lambda p: pandas.DataFrame(p, columns=full_meta.keys()).astype(meta, copy=False))
    images_df = images.to_dataframe(meta=full_meta, optimize_graph=False)

    return images_df
