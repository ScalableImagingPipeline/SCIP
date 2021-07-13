from skimage import img_as_float, img_as_uint, filters, exposure, morphology, segmentation, measure
from skimage.restoration import denoise_nl_means
from dask.delayed import Delayed
from PIL import Image
import numpy as np
import dask


@dask.delayed
def apply_mask(dict_sample: dict[np.ndarray, str, np.ndarray]):
    dict_sample = dict_sample.copy()
    img = dict_sample.get("image")
    mask = dict_sample.get("mask")
    masked_img = np.empty(img.shape, dtype=float)

    for i in range(img.shape[0]):
        masked_img[i] = img[i]*mask[i]

    dict_sample.update(masked_img=masked_img)
    return dict_sample

@dask.delayed
def get_masked_intensities(dict_sample: dict[np.ndarray, str, np.ndarray]):
    dict_sample = dict_sample.copy()

    img = dict_sample.get("image")
    mask = dict_sample.get("mask")

    masked_intensities = list()

    for i in range(img.shape[0]):
        img_flatten = img[i].flatten()
        mask_flatten = mask[i].flatten()
        masked_intensities.append(np.extract(mask_flatten, img_flatten))


    dict_sample.update(masked_intensities=masked_intensities)
    return dict_sample

def create_masks(imageList: list[Delayed]) -> list[Delayed]:
    mask_samples = []

    for img in imageList:
        mask_samples.append(apply_mask(img))

    return mask_samples