from skimage.filters import threshold_otsu
from skimage.segmentation import watershed, expand_labels
from skimage.restoration import denoise_nl_means
from skimage import feature, measure
import skimage
from scipy.ndimage import distance_transform_edt
from skimage.measure import regionprops

from typing import List
import dask
import numpy


@dask.delayed
def segment_block(
    block: numpy.ndarray,
    *,
    group: str,
    idx: int,
    cell_diameter: int,
    dapi_channel: int
) -> List[dict]:

    plane = block[0, dapi_channel]
    plane = skimage.img_as_float32(plane)

    plane = denoise_nl_means(plane, patch_size=3, patch_distance=2, multichannel=False)

    t = threshold_otsu(plane)
    cells = plane > t
    distance = distance_transform_edt(cells)

    local_max_coords = feature.peak_local_max(distance, min_distance=cell_diameter)
    local_max_mask = numpy.zeros(distance.shape, dtype=bool)
    local_max_mask[tuple(local_max_coords.T)] = True
    markers = measure.label(local_max_mask)

    segmented_cells = watershed(-distance, markers, mask=cells)
    segmented_cells = expand_labels(segmented_cells, distance=cell_diameter * 0.25)

    events = []
    props = regionprops(segmented_cells)
    for i, prop in enumerate(props):
        bbox = prop.bbox
        events.append(dict(
            pixels=block[0, :, bbox[0]: bbox[2], bbox[1]:bbox[3]],
            mask=numpy.repeat(prop.image[numpy.newaxis] > 0, block.shape[1], axis=0),
            combined_mask=prop.image > 0,
            idx=idx+i,
            group=group,
            bbox=tuple(bbox),
            regions=[1] * block.shape[1],
            background=numpy.zeros(shape=(block.shape[1],), dtype=float),
            combined_background=numpy.zeros(shape=(block.shape[1],), dtype=float)
        ))

    return events