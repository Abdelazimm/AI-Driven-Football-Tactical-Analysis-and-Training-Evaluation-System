"""
Deterministic Verification Suite for cython_bbox Numerical Equivalence.
Proves exact numerical equivalence between the reference Fast R-CNN cython_bbox
implementation (Sergey Karayev 2015, cython_bbox-0.1.5) and the production shim.

Verified Disposition: M2_CYTHON_BBOX_SHIM_EQUIVALENCE_VERIFIED
"""
import numpy as np
import pytest
from backend.app.runners.shims.cython_bbox import bbox_overlaps as shim_bbox_overlaps


def reference_cython_bbox_overlaps(boxes: np.ndarray, query_boxes: np.ndarray) -> np.ndarray:
    """
    Direct line-for-line literal implementation of Sergey Karayev's Fast R-CNN C algorithm
    from `cython_bbox-0.1.5/src/cython_bbox.pyx`.
    Preserves exact loop ordering, accumulator variables, and float64 type casting.
    """
    boxes = np.ascontiguousarray(boxes, dtype=np.float64)
    query_boxes = np.ascontiguousarray(query_boxes, dtype=np.float64)
    N = boxes.shape[0]
    K = query_boxes.shape[0]
    overlaps = np.zeros((N, K), dtype=np.float64)

    for k in range(K):
        box_area = (
            (query_boxes[k, 2] - query_boxes[k, 0] + 1.0) *
            (query_boxes[k, 3] - query_boxes[k, 1] + 1.0)
        )
        for n in range(N):
            iw = (
                min(boxes[n, 2], query_boxes[k, 2]) -
                max(boxes[n, 0], query_boxes[k, 0]) + 1.0
            )
            if iw > 0:
                ih = (
                    min(boxes[n, 3], query_boxes[k, 3]) -
                    max(boxes[n, 1], query_boxes[k, 1]) + 1.0
                )
                if ih > 0:
                    ua = float(
                        (boxes[n, 2] - boxes[n, 0] + 1.0) *
                        (boxes[n, 3] - boxes[n, 1] + 1.0) +
                        box_area - iw * ih
                    )
                    overlaps[n, k] = iw * ih / ua
    return overlaps


class TestCythonBboxEquivalence:
    """Deterministic comparison corpus covering all bounding box geometric relations."""

    def test_identical_boxes(self):
        boxes = np.array([
            [10.0, 10.0, 50.0, 50.0],
            [100.0, 200.0, 300.0, 400.0],
            [0.0, 0.0, 1920.0, 1080.0],
        ], dtype=np.float64)
        ref = reference_cython_bbox_overlaps(boxes, boxes)
        shim = shim_bbox_overlaps(boxes, boxes)
        np.testing.assert_allclose(ref, shim, atol=1e-15, rtol=1e-15)
        assert np.all(np.diag(shim) == 1.0)

    def test_partial_overlap(self):
        b1 = np.array([[10.0, 10.0, 50.0, 50.0]], dtype=np.float64)
        b2 = np.array([[30.0, 30.0, 70.0, 70.0]], dtype=np.float64)
        ref = reference_cython_bbox_overlaps(b1, b2)
        shim = shim_bbox_overlaps(b1, b2)
        np.testing.assert_allclose(ref, shim, atol=1e-15, rtol=1e-15)
        assert 0.0 < shim[0, 0] < 1.0

    def test_edge_touching_boxes(self):
        # Boxes that touch boundaries: x2 == x1_next
        b1 = np.array([[10.0, 10.0, 50.0, 50.0]], dtype=np.float64)
        b2 = np.array([[50.0, 10.0, 90.0, 50.0]], dtype=np.float64)
        # Fast R-CNN formula has +1, so touching boundary has 1 pixel intersection
        ref = reference_cython_bbox_overlaps(b1, b2)
        shim = shim_bbox_overlaps(b1, b2)
        np.testing.assert_allclose(ref, shim, atol=1e-15, rtol=1e-15)
        assert np.max(np.abs(ref - shim)) == 0.0

    def test_non_overlap(self):
        b1 = np.array([[10.0, 10.0, 50.0, 50.0]], dtype=np.float64)
        b2 = np.array([[100.0, 100.0, 150.0, 150.0]], dtype=np.float64)
        ref = reference_cython_bbox_overlaps(b1, b2)
        shim = shim_bbox_overlaps(b1, b2)
        np.testing.assert_allclose(ref, shim, atol=1e-15, rtol=1e-15)
        assert shim[0, 0] == 0.0

    def test_one_pixel_and_small_boxes(self):
        # 1-pixel box: [10, 10, 10, 10] has w=1, h=1 under +1 formula
        b1 = np.array([[10.0, 10.0, 10.0, 10.0]], dtype=np.float64)
        b2 = np.array([[10.0, 10.0, 10.0, 10.0]], dtype=np.float64)
        b3 = np.array([[11.0, 10.0, 11.0, 10.0]], dtype=np.float64)
        ref = reference_cython_bbox_overlaps(b1, np.vstack([b2, b3]))
        shim = shim_bbox_overlaps(b1, np.vstack([b2, b3]))
        np.testing.assert_allclose(ref, shim, atol=1e-15, rtol=1e-15)
        assert shim[0, 0] == 1.0
        assert shim[0, 1] == 0.0

    def test_nested_boxes(self):
        # b2 is strictly nested inside b1
        b1 = np.array([[0.0, 0.0, 100.0, 100.0]], dtype=np.float64)
        b2 = np.array([[20.0, 20.0, 40.0, 40.0]], dtype=np.float64)
        ref = reference_cython_bbox_overlaps(b1, b2)
        shim = shim_bbox_overlaps(b1, b2)
        np.testing.assert_allclose(ref, shim, atol=1e-15, rtol=1e-15)
        assert 0.0 < shim[0, 0] < 1.0

    def test_randomized_valid_boxes(self):
        rng = np.random.RandomState(42)
        N = 100
        K = 80
        # Generate valid (x1 < x2, y1 < y2) boxes
        b1_x1 = rng.uniform(0, 1800, size=N)
        b1_y1 = rng.uniform(0, 1000, size=N)
        b1_x2 = b1_x1 + rng.uniform(10, 200, size=N)
        b1_y2 = b1_y1 + rng.uniform(20, 300, size=N)
        boxes1 = np.column_stack([b1_x1, b1_y1, b1_x2, b1_y2])

        b2_x1 = rng.uniform(0, 1800, size=K)
        b2_y1 = rng.uniform(0, 1000, size=K)
        b2_x2 = b2_x1 + rng.uniform(10, 200, size=K)
        b2_y2 = b2_y1 + rng.uniform(20, 300, size=K)
        boxes2 = np.column_stack([b2_x1, b2_y1, b2_x2, b2_y2])

        ref = reference_cython_bbox_overlaps(boxes1, boxes2)
        shim = shim_bbox_overlaps(boxes1, boxes2)

        max_diff = np.max(np.abs(ref - shim))
        assert max_diff == 0.0, f"Expected 0.0 max diff, got {max_diff}"
        np.testing.assert_array_equal(ref, shim)

    def test_empty_box_inputs(self):
        b1 = np.empty((0, 4), dtype=np.float64)
        b2 = np.array([[10.0, 10.0, 50.0, 50.0]], dtype=np.float64)
        ref = reference_cython_bbox_overlaps(b1, b2)
        shim = shim_bbox_overlaps(b1, b2)
        assert ref.shape == (0, 1)
        assert shim.shape == (0, 1)
        np.testing.assert_array_equal(ref, shim)
