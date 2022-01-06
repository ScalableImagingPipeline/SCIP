# Copyright (C) 2022 Maxim Lippeveld
#
# This file is part of SCIP.
#
# SCIP is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SCIP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SCIP.  If not, see <http://www.gnu.org/licenses/>.

from typing import Any, Mapping, List

import numpy
from skimage.feature import graycomatrix, graycoprops
from skimage.filters import sobel
import skimage


distances = [3, 5]
graycoprop_names = ['contrast', 'dissimilarity', 'homogeneity', 'energy', 'correlation', 'ASM']


def _texture_features_meta(channel_names: List[str]) -> Mapping[str, Any]:

    out = {}
    for i in channel_names:
        for n in distances:
            out.update({f"glcm_mean_{p}_{n}_{i}": float for p in graycoprop_names})
        for n in distances:
            out.update({f"glcm_std_{p}_{n}_{i}": float for p in graycoprop_names})
        out[f"sobel_mean_{i}"] = float
        out[f"sobel_std_{i}"] = float
        out[f"sobel_max_{i}"] = float
        out[f"sobel_min_{i}"] = float
        for n in distances:
            out.update({f"combined_glcm_mean_{p}_{n}_{i}": float for p in graycoprop_names})
        for n in distances:
            out.update({f"combined_glcm_std_{p}_{n}_{i}": float for p in graycoprop_names})
        out[f"combined_sobel_mean_{i}"] = float
        out[f"combined_sobel_std_{i}"] = float
        out[f"combined_sobel_max_{i}"] = float
        out[f"combined_sobel_min_{i}"] = float
    return out


def _row(pixels, maximum_pixel_value, num_features):
    angles = [
        numpy.pi / 4,  # 45 degrees
        3 * numpy.pi / 4,  # 135 degrees
        5 * numpy.pi / 4,  # 225 degrees
        7 * numpy.pi / 4  # 315 degrees
    ]

    int_img = skimage.img_as_int(pixels / maximum_pixel_value)
    bin_edges = numpy.histogram_bin_edges(int_img, bins=9)
    int_img = numpy.digitize(int_img, bins=bin_edges, right=True)
    glcm = graycomatrix(
        int_img,
        distances=distances,
        angles=angles,
        levels=10,
        symmetric=True
    )

    out = numpy.empty(shape=(num_features,), dtype=float)
    for i, prop in enumerate(graycoprop_names):
        v = graycoprops(glcm, prop=prop)
        out[i:i + len(distances)] = v.mean(axis=1)
        i += len(distances)
        out[i:i + len(distances)] = v.std(axis=1)
        i += len(distances)

    s = sobel(pixels)
    out[-4] = s.mean()
    out[-3] = s.std()
    out[-2] = s.max()
    out[-1] = s.min()

    return out


def texture_features(
    sample: Mapping[str, Any],
    maximum_pixel_value: int
):
    """Extracts texture features from image.

    Texture features are computed based on the gray co-occurence level matrix and sobel map.
    From the former, a contrast, dissimilarity, homogeneity, energy, correlation and ASM metric
    is computed. From the latter, mean, standard deviation, maximum and minimum values are computed.

    Features are not computed on background-substracted values (as in
    :func:scip.features.intensity.intensity_features), because all features are computed on
    relative changes of neighbouring pixels; a substraction does not influence these values.

    Args:
        sample (Mapping[str, Any]): mapping with pixels, mask and combined mask keys.

    Returns:
        Mapping[str, Any]: extacted features.

    """
    num_features = len(graycoprop_names)*2*len(distances)+4

    out = numpy.empty(shape=(len(sample["pixels"]), 2, num_features), dtype=float)

    mask_pixels = sample["pixels"] * sample["mask"]
    combined_mask_pixels = sample["pixels"] * sample["combined_mask"][numpy.newaxis, ...]
    for i in range(len(sample["pixels"])):

        # compute features on channel specific mask
        if numpy.any(sample["mask"][i]):
            out[i, 0] = _row(mask_pixels[i], maximum_pixel_value, num_features)

        # always compute features on combined mask (it can never be empty)
        out[i, 1] = _row(combined_mask_pixels[i], maximum_pixel_value, num_features)

    return out.flatten()
