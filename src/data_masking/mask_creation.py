from skimage import filters, segmentation
from skimage.restoration import denoise_nl_means
import numpy as np
import dask
import dask.bag


def denoising(sample: dict[np.ndarray, str], noisy_channels=[]):
    img = sample.get('pixels')
    denoised = np.empty(img.shape, dtype=float)
    channels = img.shape[0]
    # TODO add list parameter with noisy channels + denoising parameter
    for i in range(channels):
        if i not in noisy_channels:
            denoised[i] = denoise_nl_means(
                img[i], multichannel=False, patch_size=4,
                patch_distance=17, fast_mode=True)
        else:
            denoised[i] = img[i]

    return {**sample, **dict(denoised=denoised)}


def felzenszwalb_segmentation(sample: dict):
    segmented = np.empty(sample["denoised"].shape, dtype=float)
    channels = sample["denoised"].shape[0]
    # TODO add list parameter with felzenszwalb parameters
    for i in range(channels):
        segmented[i] = segmentation.felzenszwalb(sample["denoised"][i], sigma=0.90, scale=80)

    return {**sample, **dict(segmented=segmented)}


def otsu_thresholding(sample: dict):
    thresholded_masks = np.empty(sample["segmented"].shape, dtype=bool)
    channels = sample["segmented"].shape[0]
    for i in range(channels):
        # Calculation of Otsu threshold
        threshold = filters.threshold_otsu(sample["segmented"][i])

        # Convertion to Boolean mask with Otsu threshold
        thresholded_masks[i] = sample["segmented"][i] > threshold

    return {**sample, **dict(mask=thresholded_masks)}


def create_masks_on_bag(images: dask.bag.Bag, noisy_channels):

    # we define the different steps as named functions
    # so that Dask can differentiate between them in
    # the dashboard

    def denoise_partition(part):
        return [denoising(p, noisy_channels) for p in part]

    def felzenswalb_segment_partition(part):
        return [felzenszwalb_segmentation(p) for p in part]

    def otsu_threshold_partition(part):
        return [otsu_thresholding(p) for p in part]

    return (
        images
        .map_partitions(denoise_partition)
        .map_partitions(felzenswalb_segment_partition)
        .map_partitions(otsu_threshold_partition)
    )
