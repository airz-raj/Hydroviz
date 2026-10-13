import os
import gc
from typing import Optional, Dict, Any
import numpy as np
import onnxruntime as ort

class FloodInferenceONNX:
    """
    ONNX Runtime inference engine for 9-channel multi-temporal SAR and DEM
    flood inundation segmentation.
    
    Model Contract:
    - Input: 'input_tensor_9ch', shape (B, 9, H, W), float32.
      Channels:
        0: pre2_VV (dB normalized to [-1, 1])
        1: pre2_VH (dB normalized to [-1, 1])
        2: pre1_VV (dB normalized to [-1, 1])
        3: pre1_VH (dB normalized to [-1, 1])
        4: post_VV (dB normalized to [-1, 1])
        5: post_VH (dB normalized to [-1, 1])
        6: Slope (degrees, normalized by /60.0 to [0, 1])
        7: HAND (meters, normalized by /100.0 to [0, 1])
        8: Shadow/Layover mask (binary float [0, 1])
    - Output: 'class_logits_3ch', shape (B, 3, H, W), float32 logits.
      Classes:
        0: no water / dry land
        1: permanent water
        2: flood inundation
    """
    def __init__(self, model_path: Optional[str] = None):
        if model_path and os.path.exists(model_path):
            self.model_path = os.path.abspath(model_path)
        else:
            candidates = []
            if model_path:
                candidates.append(model_path)
            env_path = os.getenv("MODEL_PATH")
            if env_path:
                candidates.append(env_path)
            candidates.extend([
                "/data/models/flood_seg_v1_int8.onnx",
                "/data/models/flood_seg_v1.onnx",
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "flood_seg_v1_int8.onnx")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "flood_seg_v1.onnx")),
                os.path.abspath("flood_seg_v1_int8.onnx"),
                os.path.abspath("flood_seg_v1.onnx")
            ])
            self.model_path = None
            for cand in candidates:
                if cand and os.path.exists(cand):
                    self.model_path = os.path.abspath(cand)
                    break

        if not self.model_path or not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model not found at {self.model_path}. Checked candidate paths for flood_seg_v1_int8.onnx and flood_seg_v1.onnx."
            )

        self.model_name = os.path.basename(self.model_path)

        # Optimization for ONNX runtime
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        print(f"Loading ONNX model {self.model_path}...")
        self.session = ort.InferenceSession(self.model_path, sess_options, providers=['CPUExecutionProvider'])

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        out_shape = self.session.get_outputs()[0].shape
        if len(out_shape) >= 2 and isinstance(out_shape[1], int):
            self.num_classes = out_shape[1]
        else:
            self.num_classes = 3

    @staticmethod
    def preprocess_inputs(
        pre1_vv: np.ndarray,
        pre1_vh: Optional[np.ndarray],
        post_vv: np.ndarray,
        post_vh: Optional[np.ndarray],
        slope_deg: np.ndarray,
        hand_m: np.ndarray,
        shadow_mask: np.ndarray,
        pre2_vv: Optional[np.ndarray] = None,
        pre2_vh: Optional[np.ndarray] = None,
        valid_mask: Optional[np.ndarray] = None,
        **kwargs
    ) -> np.ndarray:
        """
        Preprocesses multi-temporal SAR and terrain rasters into the 9-channel normalized tensor
        matching HimalayanSARFloodDataset training conventions:
        - Channels 0-1: pre2_VV, pre2_VH (normalized via clip((dB + 15) / 15, -1, 1))
        - Channels 2-3: pre1_VV, pre1_VH (normalized via clip((dB + 15) / 15, -1, 1))
        - Channels 4-5: post_VV, post_VH (normalized via clip((dB + 15) / 15, -1, 1))
        - Channel 6: Slope deg (normalized via clip(slope / 60, 0, 1))
        - Channel 7: HAND m (normalized via clip(hand / 100, 0, 1))
        - Channel 8: Shadow (binary float in [0, 1])

        Rejects unverified synthetic fallbacks:
        - Does NOT synthesize missing VH via VV - 6.5 dB.
        - Does NOT duplicate pre1 into pre2 to impersonate distinct temporal scenes.
        """
        if pre1_vv is None and "pre_vv" in kwargs:
            pre1_vv = kwargs["pre_vv"]
        if pre1_vh is None and "pre_vh" in kwargs:
            pre1_vh = kwargs["pre_vh"]

        # Validate that all required channels are present without unverified synthetic fallbacks
        missing = []
        if pre1_vv is None:
            missing.append("pre1_VV")
        if pre1_vh is None:
            missing.append("pre1_VH (cross-polarization)")
        if post_vv is None:
            missing.append("post_VV")
        if post_vh is None:
            missing.append("post_VH (cross-polarization)")
        if pre2_vv is None or pre2_vh is None:
            missing.append("pre2_VV / pre2_VH (second distinct pre-event acquisition)")

        if missing:
            raise ValueError(
                f"Missing required 9-channel SAR inputs: {', '.join(missing)}. "
                "Synthetic VH approximation (e.g. VV - 6.5 dB) and scene duplication (pre1 -> pre2) "
                "are rejected because they are not supported by the Kuro Siwo training contract."
            )

        def to_db(arr: np.ndarray, channel_name: str) -> np.ndarray:
            with np.errstate(divide='ignore', invalid='ignore'):
                clipped = np.clip(arr, 1e-4, 50.0)
                db = 10.0 * np.log10(clipped)
                db = np.nan_to_num(db, nan=-15.0, posinf=10.0, neginf=-35.0)
            return db.astype(np.float32)

        pre2_vv_db = to_db(pre2_vv, "pre2_vv")
        pre2_vh_db = to_db(pre2_vh, "pre2_vh")
        pre1_vv_db = to_db(pre1_vv, "pre1_vv")
        pre1_vh_db = to_db(pre1_vh, "pre1_vh")
        post_vv_db = to_db(post_vv, "post_vv")
        post_vh_db = to_db(post_vh, "post_vh")

        # Normalize SAR dB [-25, -5] -> [-1, 1] matching training/dataset.py
        norm_pre2_vv = np.clip((pre2_vv_db + 15.0) / 15.0, -1.0, 1.0)
        norm_pre2_vh = np.clip((pre2_vh_db + 15.0) / 15.0, -1.0, 1.0)
        norm_pre1_vv = np.clip((pre1_vv_db + 15.0) / 15.0, -1.0, 1.0)
        norm_pre1_vh = np.clip((pre1_vh_db + 15.0) / 15.0, -1.0, 1.0)
        norm_post_vv = np.clip((post_vv_db + 15.0) / 15.0, -1.0, 1.0)
        norm_post_vh = np.clip((post_vh_db + 15.0) / 15.0, -1.0, 1.0)

        # Normalize Terrain matching training/dataset.py
        norm_slope = np.clip(np.nan_to_num(slope_deg, nan=0.0) / 60.0, 0.0, 1.0).astype(np.float32)
        norm_hand = np.clip(np.nan_to_num(hand_m, nan=100.0) / 100.0, 0.0, 1.0).astype(np.float32)
        norm_shadow = np.clip(np.nan_to_num(shadow_mask, nan=0.0).astype(np.float32), 0.0, 1.0)

        if valid_mask is not None:
            # Map nodata/invalid pixels to neutral non-water values
            invalid = ~valid_mask
            norm_pre2_vv[invalid] = 0.0
            norm_pre2_vh[invalid] = 0.0
            norm_pre1_vv[invalid] = 0.0
            norm_pre1_vh[invalid] = 0.0
            norm_post_vv[invalid] = 0.0
            norm_post_vh[invalid] = 0.0
            norm_slope[invalid] = 0.0
            norm_hand[invalid] = 1.0
            norm_shadow[invalid] = 1.0

        tensor_9ch = np.stack([
            norm_pre2_vv, norm_pre2_vh,
            norm_pre1_vv, norm_pre1_vh,
            norm_post_vv, norm_post_vh,
            norm_slope, norm_hand, norm_shadow
        ], axis=0).astype(np.float32)

        return tensor_9ch

    def _sliding_window_inference(self, tile_data: np.ndarray, window_size: int = 256, step: int = 128, return_probs: bool = False) -> np.ndarray:
        """
        Runs sliding window inference over a multi-channel tensor.
        Uses Gaussian weighting to blend overlapping predictions.
        If return_probs is True, returns out_probs array of shape (num_classes, H, W).
        If return_probs is False (default), returns argmax class prediction array of shape (H, W).
        """
        c, h, w = tile_data.shape

        # Pad tile_data if smaller than window_size
        pad_h = max(0, window_size - h)
        pad_w = max(0, window_size - w)
        if pad_h > 0 or pad_w > 0:
            padded_data = np.pad(tile_data, ((0, 0), (0, pad_h), (0, pad_w)), mode='reflect')
        else:
            padded_data = tile_data

        new_h, new_w = padded_data.shape[1], padded_data.shape[2]

        out_probs = np.zeros((self.num_classes, new_h, new_w), dtype=np.float32)
        weight_sum = np.zeros((1, new_h, new_w), dtype=np.float32)

        # Create 2D gaussian window
        y, x = np.ogrid[-window_size // 2 : window_size // 2, -window_size // 2 : window_size // 2]
        sigma = window_size / 4.0
        gaussian_weight = np.exp(-(x * x + y * y) / (2.0 * sigma * sigma)).astype(np.float32)

        # Generate row and col offsets ensuring complete coverage
        row_steps = list(range(0, new_h - window_size + 1, step))
        if not row_steps or row_steps[-1] < new_h - window_size:
            row_steps.append(new_h - window_size)
        row_steps = sorted(list(set(row_steps)))

        col_steps = list(range(0, new_w - window_size + 1, step))
        if not col_steps or col_steps[-1] < new_w - window_size:
            col_steps.append(new_w - window_size)
        col_steps = sorted(list(set(col_steps)))

        for i in row_steps:
            for j in col_steps:
                patch = padded_data[:, i : i + window_size, j : j + window_size]
                patch = np.expand_dims(patch, axis=0).astype(np.float32)

                logits = self.session.run([self.output_name], {self.input_name: patch})[0][0]

                # Convert logits to probabilities via softmax
                exp_logits = np.exp(logits - np.max(logits, axis=0, keepdims=True))
                probs = exp_logits / np.sum(exp_logits, axis=0, keepdims=True)

                out_probs[:, i : i + window_size, j : j + window_size] += probs * gaussian_weight
                weight_sum[:, i : i + window_size, j : j + window_size] += gaussian_weight

        # Normalize by accumulated weights
        out_probs /= np.clip(weight_sum, 1e-8, None)
        # Crop back to original unpadded size
        out_probs = out_probs[:, :h, :w]

        if return_probs:
            return out_probs
        return np.argmax(out_probs, axis=0)

    def predict(
        self,
        pre1_vv: np.ndarray,
        pre1_vh: Optional[np.ndarray],
        post_vv: np.ndarray,
        post_vh: Optional[np.ndarray],
        slope_deg: np.ndarray,
        hand_m: np.ndarray,
        shadow_mask: np.ndarray,
        pre2_vv: Optional[np.ndarray] = None,
        pre2_vh: Optional[np.ndarray] = None,
        valid_mask: Optional[np.ndarray] = None,
        window_size: int = 256,
        step: int = 128,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes end-to-end flood segmentation:
        1. Preprocesses 9-channel tensor with verified multi-temporal normalization.
        2. Executes sliding-window ONNX inference.
        3. Extracts flood mask and permanent water mask (no debris class in model contract).
        4. Applies spatial valid_mask and shadow/layover exclusion.
        """
        if pre1_vv is None and "pre_vv" in kwargs:
            pre1_vv = kwargs["pre_vv"]
        if pre1_vh is None and "pre_vh" in kwargs:
            pre1_vh = kwargs["pre_vh"]

        tensor_9ch = self.preprocess_inputs(
            pre1_vv=pre1_vv,
            pre1_vh=pre1_vh,
            post_vv=post_vv,
            post_vh=post_vh,
            slope_deg=slope_deg,
            hand_m=hand_m,
            shadow_mask=shadow_mask,
            pre2_vv=pre2_vv,
            pre2_vh=pre2_vh,
            valid_mask=valid_mask
        )

        probs = self._sliding_window_inference(tensor_9ch, window_size=window_size, step=step, return_probs=True)
        pred_classes = np.argmax(probs, axis=0)

        if self.num_classes == 3:
            # 0: dry terrain, 1: permanent water, 2: flood water
            flood_mask = (pred_classes == 2)
            perm_water_mask = (pred_classes == 1)
        else:
            # 2-class model (0: dry, 1: flood)
            flood_mask = (pred_classes == 1)
            perm_water_mask = None

        # Apply spatial validity mask & shadow mask to eliminate radar blind spots
        if valid_mask is not None:
            flood_mask = flood_mask & valid_mask
            if perm_water_mask is not None:
                perm_water_mask = perm_water_mask & valid_mask

        shadow_bool = (shadow_mask > 0)
        flood_mask = flood_mask & (~shadow_bool)
        if perm_water_mask is not None:
            perm_water_mask = perm_water_mask & (~shadow_bool)

        return {
            "flood_mask": flood_mask.astype(np.uint8),
            "perm_water_mask": perm_water_mask.astype(np.uint8) if perm_water_mask is not None else None,
            "raw_class_probabilities": probs,
            "pred_classes": pred_classes,
            "num_classes": self.num_classes,
            "model_path": self.model_path,
            "model_name": self.model_name
        }

    def process_large_scene(self, datasets: dict, chunk_size=512):
        """
        Processes a large scene chunk by chunk. Retained for backwards compatibility.
        """
        from rasterio.windows import Window

        width = datasets['post_vv'].width
        height = datasets['post_vv'].height

        final_mask = np.zeros((height, width), dtype=np.uint8)

        for row_offset in range(0, height, chunk_size):
            for col_offset in range(0, width, chunk_size):
                window = Window(
                    col_offset, row_offset,
                    min(chunk_size, width - col_offset),
                    min(chunk_size, height - row_offset)
                )

                pre_vv = datasets['pre_vv'].read(1, window=window)
                pre_vh = datasets['pre_vh'].read(1, window=window) if 'pre_vh' in datasets else None
                post_vv = datasets['post_vv'].read(1, window=window)
                post_vh = datasets['post_vh'].read(1, window=window) if 'post_vh' in datasets else None
                slope = datasets['slope'].read(1, window=window)
                hand = datasets['hand'].read(1, window=window)
                shadow = datasets['shadow'].read(1, window=window)

                chunk_tensor = self.preprocess_inputs(
                    pre_vv=pre_vv, pre_vh=pre_vh,
                    post_vv=post_vv, post_vh=post_vh,
                    slope_deg=slope, hand_m=hand, shadow_mask=shadow
                )

                chunk_probs = self._sliding_window_inference(chunk_tensor)
                chunk_classes = np.argmax(chunk_probs, axis=0)
                chunk_mask = (chunk_classes == 2) if self.num_classes == 3 else (chunk_classes == 1)

                final_mask[row_offset : row_offset + window.height, col_offset : col_offset + window.width] = chunk_mask[:window.height, :window.width].astype(np.uint8)

                del chunk_tensor
                del chunk_probs
                del chunk_classes
                gc.collect()

        return final_mask
