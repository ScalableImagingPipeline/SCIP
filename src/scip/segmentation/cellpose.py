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

from typing import Optional, List, Any, Mapping
import numpy
from cellpose import models
from skimage.measure import regionprops
from dask.distributed import get_worker
import torch
from scip.utils.util import copy_without


def segment_block(
    events: List[Mapping[str, Any]],
    *,
    parent_channel_index: int,
    dapi_channel_index: int,
    gpu_accelerated: Optional[bool] = False,
    cell_diameter: Optional[int] = None,
    **kwargs
) -> List[dict]:

    if len(events) == 0:
        return events

    w = get_worker()
    if hasattr(w, "cellpose"):
        model = w.cellpose
    else:
        if gpu_accelerated:
            device = torch.device(w.name - 2)
            model = models.Cellpose(gpu=True, device=device, model_type='cyto2')
        else:
            model = models.Cellpose(gpu=False, model_type='cyto2')
        w.cellpose = model

    parents, _, _, _ = model.eval(
        x=[e["pixels"][[parent_channel_index, dapi_channel_index]] for e in events],
        channels=[1, 2],
        diameter=cell_diameter,
        batch_size=128
    )

    children = []
    for channel_index in range(len(events[0]["pixels"])):
        if channel_index == parent_channel_index:
            continue

        o, _, _, _ = model.eval(
            x=[e["pixels"][[channel_index, dapi_channel_index]] for e in events],
            channels=[1, 2],
            diameter=cell_diameter,
            batch_size=128
        )
        children.append(o)

    for e_i, event in enumerate(events):

        labeled_mask = numpy.repeat(parents[e_i][numpy.newaxis], event["pixels"].shape[0], axis=0)

        for channel_index in range(len(event["pixels"])):
            if channel_index == parent_channel_index:
                continue

            # assign over-segmented children to parent objects
            mask = numpy.zeros_like(parents[e_i])
            for i in numpy.unique(parents[e_i])[1:]:
                idx, counts = numpy.unique(
                    children[channel_index][e_i][parents[e_i] == i], return_counts=True)
                idx, counts = idx[1:], counts[1:]  # skip zero (= background)

                idx = idx[(counts / (parents[e_i] == i).sum()) > 0.1]
                mask[numpy.isin(children[channel_index][e_i], idx) & (parents[e_i] == i)] = i

            labeled_mask[channel_index] = mask

        event["mask"] = labeled_mask

    return events


def to_events(
    events: List[Mapping[str, Any]],
    *,
    group_keys: Optional[List[str]] = None,
    parent_channel_index: int,
    **kwargs
):
    """Converts the segmented objects into a list of dictionaries that can be converted
    to a dask.bag.Bag. The dictionaries contain the pixel information for one detected cell,
    or event, and the meta data of that event.
    """

    newevents = []
    for event in events:

        labeled_mask = event["mask"]
        cells = labeled_mask[parent_channel_index]
        cell_regions = regionprops(cells)

        if group_keys is not None:
            group = "_".join([str(event[k]) for k in group_keys])
        else:
            group = None

        for props in cell_regions:

            bbox = props.bbox

            mask = labeled_mask[:, bbox[0]:bbox[2], bbox[1]:bbox[3]] == props.label
            combined_mask = cells[bbox[0]:bbox[2], bbox[1]:bbox[3]] == props.label

            regions = []
            for m in mask:
                regions.append(int(m.any()))

            newevent = copy_without(event=event, without=["mask", "pixels"])
            newevent["pixels"] = event["pixels"][:, bbox[0]: bbox[2], bbox[1]:bbox[3]]
            newevent["combined_mask"] = combined_mask
            newevent["mask"] = mask
            newevent["group"] = group
            newevent["bbox"] = tuple(bbox)
            newevent["regions"] = regions
            newevent["background"] = numpy.zeros(
                shape=(event["pixels"].shape[0],), dtype=float)
            newevent["combined_background"] = numpy.zeros(
                shape=(event["pixels"].shape[0],), dtype=float)
            newevent["id"] = props.label

            newevents.append(newevent)

    return newevents
