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

from typing import Mapping, List, Any

import numpy
import scipy.stats
from scipy.ndimage import convolve
from numba import njit

props = [
    'mean',
    'median',
    'max',
    'min',
    'std',
    'mad',
    'lower_quartile',
    'upper_quartile',
    'sum',
    'skewness',
    'kurtosis',
]


def _intensity_features_meta(channel_names: List[str]) -> Mapping[str, type]:
    out = {}
    for i in channel_names:
        out.update({f"{p}_{i}": float for p in props})
        out.update({f"bgcorr_{p}_{i}": float for p in props})
        out.update({f"combined_{p}_{i}": float for p in props})
        out.update({f"combined_bgcorr_{p}_{i}": float for p in props})
        out.update({f"edge_{p}_{i}": float for p in props})
        out.update({f"bgcorr_edge_{p}_{i}": float for p in props})
        out.update({f"combined_edge_{p}_{i}": float for p in props})
        out.update({f"combined_bgcorr_edge_{p}_{i}": float for p in props})
    return out


@njit(cache=True)
def _row(pixels: numpy.ndarray) -> list:
    percentiles = numpy.percentile(pixels, q=(0, 25, 50, 75, 100))

    d = [
        numpy.mean(pixels),
        percentiles[2],
        percentiles[4],
        percentiles[0],
        numpy.std(pixels),
        numpy.median(numpy.absolute(pixels - percentiles[2])),
        percentiles[1],
        percentiles[3],
        numpy.sum(pixels)
    ]

    return d


def _row2(pixels: numpy.ndarray) -> list:
    return [
        scipy.stats.skew(pixels),
        scipy.stats.kurtosis(pixels)
    ]


def intensity_features(
    sample: Mapping[str, Any]
) -> numpy.ndarray:
    """Compute intensity features.

    Find following intensity features based on masked pixel values:
        * 'mean',
        * 'max',
        * 'min',
        * 'var',
        * 'mad',
        * 'skewness',
        * 'kurtosis',
        * 'sum',
        * 'modulation'

    The features are computed on 8 different views on the pixel data:
        1. Raw values of channel specific mask
        2. Background substracted values of channel specific mask
        3. Edge values of channel specific mask
        4. Background substracted edge values of channel specific mask
        5. Raw values of union of masks
        6. Background substracted values of union of masks
        7. Edge values of union of masks
        8. Background substracted edge values of union of masks

    Args:
        sample (Mapping): mapping with pixels, mask, combined_mask, background and
          combined background keys.

    Returns:
        Mapping[str, Any]: extracted features
    """

    do_combined = "combined_mask" in sample
    do_background = "background" in sample

    m = 2 if do_background else 1
    n = 2 if do_combined else 1
    out = numpy.full(
        shape=(len(sample["pixels"]), 2, m, n, len(props)),
        fill_value=None,
        dtype=float
    ) # axis dimensions: channels, full / edge, no bgcorr / bgcorr, mask / combined mask, props

    for i in range(len(sample["pixels"])):
        mask = sample["mask"][i]

        # compute features on channel specific mask
        if numpy.any(mask):
            plane = sample["pixels"][i]

            mask_pixels = plane[mask]

            conv = convolve(
                mask.astype(int),
                weights=numpy.ones(shape=[4, 4], dtype=int),
                mode="constant"
            )
            edge = ((conv > 0) & (conv < 15)) * mask
            mask_edge_pixels = plane[edge]

            out[i, 0, 0, 0] = _row(mask_pixels) + _row2(mask_pixels)
            out[i, 1, 0, 0] = _row(mask_edge_pixels) + _row2(mask_edge_pixels)

            if do_background:
                background = sample["background"][i]
                mask_bgcorr_pixels = mask_pixels - background
                mask_bgcorr_edge_pixels = mask_edge_pixels - background

                out[i, 0, 1, 0] = _row(mask_bgcorr_pixels) + _row2(mask_bgcorr_pixels)
                out[i, 1, 1, 0] = _row(mask_bgcorr_edge_pixels) + _row2(mask_bgcorr_edge_pixels)
        else:
            # write default values
            out[i] = 0

        if do_combined:
            combined_mask = sample["combined_mask"]
            mask_pixels = plane[combined_mask]

            conv = convolve(
                combined_mask.astype(int),
                weights=numpy.ones(shape=[4, 4], dtype=int),
                mode="constant"
            )
            combined_edge = ((conv > 0) & (conv < 15)) * combined_mask

            mask_edge_pixels = plane[combined_edge]

            out[i, 0, 0, 1] = _row(mask_pixels) + _row2(mask_pixels)
            out[i, 1, 0, 1] = _row(mask_edge_pixels) + _row2(mask_edge_pixels)

            if do_background:
                combined_background = sample["combined_background"][i]
                mask_bgcorr_pixels = mask_pixels - combined_background
                mask_bgcorr_edge_pixels = mask_edge_pixels - combined_background

                out[i, 0, 1, 1] = _row(mask_bgcorr_pixels) + _row2(mask_bgcorr_pixels)
                out[i, 1, 1, 1] = _row(mask_bgcorr_edge_pixels) + _row2(mask_bgcorr_edge_pixels)

    return out.flatten()
