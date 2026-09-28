"""
Exact Pure-Python / NumPy Drop-in Shim for cython_bbox (version 0.1.5).
Derived directly from reference source `cython_bbox.pyx` (Fast R-CNN, Sergey Karayev 2015).
Provides exact bitwise/numerical float64 equivalence for `bbox_overlaps(boxes, query_boxes)`.
Used when MSVC C compilation is unavailable on target Windows environments.
"""
import numpy as np

__version__ = "0.1.5"


def bbox_overlaps(boxes, query_boxes):
    """
    Parameters
    ----------
    boxes: (N, 4) ndarray of float
    query_boxes: (K, 4) ndarray of float
    Returns
    -------
    overlaps: (N, K) ndarray of overlap between boxes and query_boxes
    """
    boxes = np.ascontiguousarray(boxes, dtype=np.float64)
    query_boxes = np.ascontiguousarray(query_boxes, dtype=np.float64)
    n = boxes.shape[0]
    k = query_boxes.shape[0]
    if n == 0 or k == 0:
        return np.zeros((n, k), dtype=np.float64)

    # Vectorized exact implementation of cython_bbox.pyx formula:
    box_area = (query_boxes[:, 2] - query_boxes[:, 0] + 1.0) * (
        query_boxes[:, 3] - query_boxes[:, 1] + 1.0
    )
    boxes_area = (boxes[:, 2] - boxes[:, 0] + 1.0) * (
        boxes[:, 3] - boxes[:, 1] + 1.0
    )

    # Intersections: (N, K)
    iw = (
        np.minimum(boxes[:, None, 2], query_boxes[None, :, 2])
        - np.maximum(boxes[:, None, 0], query_boxes[None, :, 0])
        + 1.0
    )
    ih = (
        np.minimum(boxes[:, None, 3], query_boxes[None, :, 3])
        - np.maximum(boxes[:, None, 1], query_boxes[None, :, 1])
        + 1.0
    )

    valid = (iw > 0.0) & (ih > 0.0)
    inter = np.where(valid, iw * ih, 0.0)
    ua = boxes_area[:, None] + box_area[None, :] - inter

    return np.where(valid & (ua > 0.0), inter / ua, 0.0)
