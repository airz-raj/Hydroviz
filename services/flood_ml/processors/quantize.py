import os
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

def quantize_model(input_onnx="flood_seg_v1.onnx", output_onnx="flood_seg_v1_int8.onnx"):
    """
    Applies INT8 dynamic quantization to the exported ONNX model.
    This reduces the model size and memory footprint for the 8GB RAM constraint.
    """
    if not os.path.exists(input_onnx):
        print(f"Input model {input_onnx} not found. Please run download_weights.py first.")
        return
        
    print(f"Quantizing {input_onnx} to {output_onnx} using INT8 dynamic quantization...")
    try:
        quantize_dynamic(
            model_input=input_onnx,
            model_output=output_onnx,
            weight_type=QuantType.QUInt8,
        )
        print("Quantization complete!")
        print(f"Original size: {os.path.getsize(input_onnx) / 1024 / 1024:.2f} MB")
        print(f"Quantized size: {os.path.getsize(output_onnx) / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"Failed to quantize: {e}")

if __name__ == "__main__":
    quantize_model()
