import os
import argparse
import torch
from models import FloodSegmentationUNet

def export_to_onnx(checkpoint_path: str = "", output_path: str = "flood_seg_v1.onnx", quantized_output_path: str = "flood_seg_v1_int8.onnx"):
    """
    Exports the PyTorch FloodSegmentationUNet model to ONNX format with dynamic batch and patch sizes,
    and applies ONNX Runtime dynamic INT8 quantization for optimal inference speed.
    """
    model = FloodSegmentationUNet(in_channels=9, num_classes=2, base_channels=16)
    if checkpoint_path and os.path.exists(checkpoint_path):
        model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
        print(f"Loaded weights from {checkpoint_path}")
    model.eval()

    dummy_input = torch.randn(1, 9, 256, 256, dtype=torch.float32)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size", 2: "height", 3: "width"},
            "output": {0: "batch_size", 2: "height", 3: "width"}
        }
    )
    print(f"Successfully exported full-precision ONNX model to {output_path}")

    # Quantize to INT8 via onnxruntime
    try:
        from onnxruntime.quantization import quantize_dynamic, QuantType
        quantize_dynamic(
            output_path,
            quantized_output_path,
            weight_type=QuantType.QInt8
        )
        print(f"Successfully quantized model to INT8: {quantized_output_path}")
    except Exception as e:
        print(f"Quantization note: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="", help="Path to PyTorch checkpoint")
    parser.add_argument("--out", default="flood_seg_v1.onnx", help="Output ONNX filename")
    args = parser.parse_args()
    export_to_onnx(args.checkpoint, args.out)
