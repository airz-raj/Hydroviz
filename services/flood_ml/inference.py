import os
import gc
import numpy as np
import onnxruntime as ort

class FloodInferenceONNX:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.getenv("MODEL_PATH", "/data/models/flood_seg_v1_int8.onnx")
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at {self.model_path}. Did you run download_weights.py and quantize.py on the host?")
            
        # Optimization for ONNX runtime
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        print(f"Loading ONNX model {self.model_path}...")
        self.session = ort.InferenceSession(self.model_path, sess_options, providers=['CPUExecutionProvider'])
        
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
    def _sliding_window_inference(self, tile_data: np.ndarray, window_size=256, step=128):
        """
        Runs sliding window inference over a chunk (e.g. 512x512) loaded into memory.
        Uses Gaussian weighting to blend overlapping predictions.
        """
        c, h, w = tile_data.shape
        out_probs = np.zeros((3, h, w), dtype=np.float32)
        weight_sum = np.zeros((1, h, w), dtype=np.float32)
        
        # Create 2D gaussian window
        y, x = np.ogrid[-window_size//2 : window_size//2, -window_size//2 : window_size//2]
        sigma = window_size / 4.0
        gaussian_weight = np.exp(-(x*x + y*y) / (2.*sigma*sigma))
        
        # Pad tile_data if smaller than window_size
        pad_h = max(0, window_size - h)
        pad_w = max(0, window_size - w)
        if pad_h > 0 or pad_w > 0:
            tile_data = np.pad(tile_data, ((0, 0), (0, pad_h), (0, pad_w)), mode='reflect')
            
        new_h, new_w = tile_data.shape[1], tile_data.shape[2]
        
        for i in range(0, new_h - window_size + 1, step):
            for j in range(0, new_w - window_size + 1, step):
                patch = tile_data[:, i:i+window_size, j:j+window_size]
                patch = np.expand_dims(patch, axis=0).astype(np.float32)
                
                logits = self.session.run([self.output_name], {self.input_name: patch})[0][0]
                
                # Convert logits to probabilities
                probs = np.exp(logits) / np.sum(np.exp(logits), axis=0)
                
                out_probs[:, i:i+window_size, j:j+window_size] += probs * gaussian_weight
                weight_sum[:, i:i+window_size, j:j+window_size] += gaussian_weight
                
        # Normalize
        out_probs /= np.clip(weight_sum, 1e-8, None)
        # Crop back to original size if padded
        out_probs = out_probs[:, :h, :w]
        
        return np.argmax(out_probs, axis=0)
        
    def process_large_scene(self, datasets: dict, chunk_size=512):
        """
        Processes a large scene chunk by chunk to avoid exceeding the 2GB memory limit.
        `datasets` is a dict of rasterio DatasetReaders:
        {'pre_vv': src, 'pre_vh': src, 'post_vv': src, 'post_vh': src, 'slope': src, 'hand': src, 'shadow': src}
        (Assuming pre1 and pre2 are already averaged into 'pre_vv'/'pre_vh' by preprocessing)
        """
        from rasterio.windows import Window
        
        # We assume all datasets have identical dimensions (co-registered)
        width = datasets['post_vv'].width
        height = datasets['post_vv'].height
        
        final_mask = np.zeros((height, width), dtype=np.uint8)
        
        for row_offset in range(0, height, chunk_size):
            for col_offset in range(0, width, chunk_size):
                window = Window(col_offset, row_offset, 
                                min(chunk_size, width - col_offset), 
                                min(chunk_size, height - row_offset))
                
                # Stack 9 channels for the ONNX model (matching training features)
                # 0: pre2_VV, 1: pre2_VH, 2: pre1_VV, 3: pre1_VH, 4: post_VV, 5: post_VH, 6: slope, 7: HAND, 8: shadow
                # We duplicate 'pre' into pre1/pre2 slots if we only have one pre composite
                pre_vv = datasets['pre_vv'].read(1, window=window)
                pre_vh = datasets['pre_vh'].read(1, window=window)
                post_vv = datasets['post_vv'].read(1, window=window)
                post_vh = datasets['post_vh'].read(1, window=window)
                slope = datasets['slope'].read(1, window=window)
                hand = datasets['hand'].read(1, window=window)
                shadow = datasets['shadow'].read(1, window=window)
                
                chunk_data = np.stack([
                    pre_vv, pre_vh, pre_vv, pre_vh, 
                    post_vv, post_vh, 
                    slope, hand, shadow
                ], axis=0)
                
                chunk_mask = self._sliding_window_inference(chunk_data)
                
                final_mask[row_offset:row_offset+window.height, col_offset:col_offset+window.width] = chunk_mask[:window.height, :window.width]
                
                # Crucial for 8GB RAM host / 2GB Container Limit: Garbage Collect
                del chunk_data
                del chunk_mask
                gc.collect()
                
        return final_mask
