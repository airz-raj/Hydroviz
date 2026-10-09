"""
IMPORTANT:
Run this script locally on your HOST machine before running `docker compose up`.
Do NOT run this script inside the `flood_ml` Docker container.

Why?
To meet the 8GB RAM local testing constraint, we explicitly DO NOT install 
PyTorch in the `flood_ml` container. PyTorch has a massive memory footprint.
This script downloads the .pt weights, converts them to ONNX, and (optionally)
quantizes them. The lightweight ONNX runtime is what the container will use.

Make sure you have `torch` and `onnx` installed locally:
pip install torch onnx onnxruntime
"""

import os
import urllib.request
import sys

URL = "https://www.dropbox.com/scl/fi/3vlsveoobqe1wc71s5z2d/best_segmentation.pt?rlkey=xpy2thmozzxfzymr8b13m7n51&dl=1"
PT_OUTPUT = "kurosiwo_snunet.pt"
ONNX_OUTPUT = "flood_seg_v1.onnx"

def download_file(url: str, dest: str):
    print(f"Downloading weights from {url}...")
    urllib.request.urlretrieve(url, dest)
    print(f"Downloaded successfully to {dest}.")

def convert_to_onnx():
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        print("PyTorch is not installed. Skipping ONNX conversion.")
        print("Please run this script in an environment with PyTorch and ONNX installed.")
        return

    # Embed the KuroSiwo SNUNet architecture for loading weights
    class ConvBlockNested(nn.Module):
        def __init__(self, in_ch, mid_ch, out_ch):
            super().__init__()
            self.activation = nn.ReLU(inplace=True)
            self.conv1 = nn.Conv2d(in_ch, mid_ch, kernel_size=3, padding=1, bias=True)
            self.bn1 = nn.BatchNorm2d(mid_ch)
            self.conv2 = nn.Conv2d(mid_ch, out_ch, kernel_size=3, padding=1, bias=True)
            self.bn2 = nn.BatchNorm2d(out_ch)

        def forward(self, x):
            x_conv = self.conv1(x)
            identity = x_conv
            x_conv = self.bn1(x_conv)
            x_conv = self.activation(x_conv)
            x_conv = self.conv2(x_conv)
            x_conv = self.bn2(x_conv)
            return self.activation(x_conv + identity)

    class Up(nn.Module):
        def __init__(self, in_ch, bilinear=False):
            super().__init__()
            if bilinear:
                self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
            else:
                self.up = nn.ConvTranspose2d(in_ch, in_ch, kernel_size=2, stride=2)

        def forward(self, x):
            return self.up(x)

    class ChannelAttention(nn.Module):
        def __init__(self, in_channels, ratio=16):
            super().__init__()
            self.avg_pool = nn.AdaptiveAvgPool2d(1)
            self.max_pool = nn.AdaptiveMaxPool2d(1)
            reduced_channels = max(1, in_channels // ratio)
            self.fc1 = nn.Conv2d(in_channels, reduced_channels, kernel_size=1, bias=False)
            self.relu1 = nn.ReLU()
            self.fc2 = nn.Conv2d(reduced_channels, in_channels, kernel_size=1, bias=False)
            self.sigmoid = nn.Sigmoid()

        def forward(self, x):
            avg_out = self.fc2(self.relu1(self.fc1(self.avg_pool(x))))
            max_out = self.fc2(self.relu1(self.fc1(self.max_pool(x))))
            out = avg_out + max_out
            return self.sigmoid(out)

    class SNUNet_ECAM(nn.Module):
        def __init__(self, in_channels=2, out_ch=2, base_channel=32):
            super().__init__()
            n1 = base_channel
            filters = [n1, n1 * 2, n1 * 4, n1 * 8, n1 * 16]

            self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

            self.conv0_0 = ConvBlockNested(in_channels, filters[0], filters[0])
            self.conv1_0 = ConvBlockNested(filters[0], filters[1], filters[1])
            self.Up1_0 = Up(filters[1])
            self.conv2_0 = ConvBlockNested(filters[1], filters[2], filters[2])
            self.Up2_0 = Up(filters[2])
            self.conv3_0 = ConvBlockNested(filters[2], filters[3], filters[3])
            self.Up3_0 = Up(filters[3])
            self.conv4_0 = ConvBlockNested(filters[3], filters[4], filters[4])
            self.Up4_0 = Up(filters[4])

            self.conv0_1 = ConvBlockNested(filters[0] * 2 + filters[1], filters[0], filters[0])
            self.conv1_1 = ConvBlockNested(filters[1] * 2 + filters[2], filters[1], filters[1])
            self.Up1_1 = Up(filters[1])
            self.conv2_1 = ConvBlockNested(filters[2] * 2 + filters[3], filters[2], filters[2])
            self.Up2_1 = Up(filters[2])
            self.conv3_1 = ConvBlockNested(filters[3] * 2 + filters[4], filters[3], filters[3])
            self.Up3_1 = Up(filters[3])

            self.conv0_2 = ConvBlockNested(filters[0] * 3 + filters[1], filters[0], filters[0])
            self.conv1_2 = ConvBlockNested(filters[1] * 3 + filters[2], filters[1], filters[1])
            self.Up1_2 = Up(filters[1])
            self.conv2_2 = ConvBlockNested(filters[2] * 3 + filters[3], filters[2], filters[2])
            self.Up2_2 = Up(filters[2])

            self.conv0_3 = ConvBlockNested(filters[0] * 4 + filters[1], filters[0], filters[0])
            self.conv1_3 = ConvBlockNested(filters[1] * 4 + filters[2], filters[1], filters[1])
            self.Up1_3 = Up(filters[1])

            self.conv0_4 = ConvBlockNested(filters[0] * 5 + filters[1], filters[0], filters[0])

            self.ca = ChannelAttention(filters[0] * 4, ratio=16)
            self.ca1 = ChannelAttention(filters[0], ratio=max(1, 16 // 4))

            self.conv_final = nn.Conv2d(filters[0] * 4, out_ch, kernel_size=1)

        def forward(self, xA, xB):
            x0_0A = self.conv0_0(xA)
            x1_0A = self.conv1_0(self.pool(x0_0A))
            x2_0A = self.conv2_0(self.pool(x1_0A))
            x3_0A = self.conv3_0(self.pool(x2_0A))

            x0_0B = self.conv0_0(xB)
            x1_0B = self.conv1_0(self.pool(x0_0B))
            x2_0B = self.conv2_0(self.pool(x1_0B))
            x3_0B = self.conv3_0(self.pool(x2_0B))
            x4_0B = self.conv4_0(self.pool(x3_0B))

            x0_1 = self.conv0_1(torch.cat([x0_0A, x0_0B, self.Up1_0(x1_0B)], 1))
            x1_1 = self.conv1_1(torch.cat([x1_0A, x1_0B, self.Up2_0(x2_0B)], 1))
            x0_2 = self.conv0_2(torch.cat([x0_0A, x0_0B, x0_1, self.Up1_1(x1_1)], 1))

            x2_1 = self.conv2_1(torch.cat([x2_0A, x2_0B, self.Up3_0(x3_0B)], 1))
            x1_2 = self.conv1_2(torch.cat([x1_0A, x1_0B, x1_1, self.Up2_1(x2_1)], 1))
            x0_3 = self.conv0_3(torch.cat([x0_0A, x0_0B, x0_1, x0_2, self.Up1_2(x1_2)], 1))

            x3_1 = self.conv3_1(torch.cat([x3_0A, x3_0B, self.Up4_0(x4_0B)], 1))
            x2_2 = self.conv2_2(torch.cat([x2_0A, x2_0B, x2_1, self.Up3_1(x3_1)], 1))
            x1_3 = self.conv1_3(torch.cat([x1_0A, x1_0B, x1_1, x1_2, self.Up2_2(x2_2)], 1))
            x0_4 = self.conv0_4(torch.cat([x0_0A, x0_0B, x0_1, x0_2, x0_3, self.Up1_3(x1_3)], 1))

            out = torch.cat([x0_1, x0_2, x0_3, x0_4], 1)
            intra = torch.sum(torch.stack((x0_1, x0_2, x0_3, x0_4)), dim=0)
            ca1 = self.ca1(intra)
            out = self.ca(out) * (out + ca1.repeat(1, 4, 1, 1))
            out = self.conv_final(out)
            return out

    class HydroVizSNUNetAdapter(nn.Module):
        def __init__(self, base_snunet, num_classes=3):
            super().__init__()
            self.base_snunet = base_snunet
            self.num_classes = num_classes
            in_final = base_snunet.conv_final.in_channels
            self.base_snunet.conv_final = nn.Conv2d(in_final, num_classes, kernel_size=1)

        def forward(self, x_9ch):
            # 0: pre2_VV, 1: pre2_VH, 2: pre1_VV, 3: pre1_VH, 4: post_VV, 5: post_VH, 6: slope, 7: HAND, 8: shadow_mask
            pre_vv = (x_9ch[:, 0:1] + x_9ch[:, 2:3]) * 0.5
            pre_vh = (x_9ch[:, 1:2] + x_9ch[:, 3:4]) * 0.5
            post_vv = x_9ch[:, 4:5]
            post_vh = x_9ch[:, 5:6]
            xA = torch.cat([pre_vv, pre_vh], dim=1)
            xB = torch.cat([post_vv, post_vh], dim=1)
            return self.base_snunet(xA, xB)

    print("Instantiating base SNUNet...")
    base_model = SNUNet_ECAM(in_channels=2, out_ch=2)
    print("Loading pretrained weights...")
    state_dict = torch.load(PT_OUTPUT, map_location="cpu")
    # if it's wrapped in a dict with 'model'
    if 'model' in state_dict:
        state_dict = state_dict['model']
    # remove 'module.' prefix if trained with DataParallel
    state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
    base_model.load_state_dict(state_dict, strict=False)

    print("Wrapping with HydroViz adapter...")
    model = HydroVizSNUNetAdapter(base_model, num_classes=3)
    model.eval()

    print("Exporting to ONNX...")
    dummy_input = torch.randn(1, 9, 256, 256)
    torch.onnx.export(
        model,
        dummy_input,
        ONNX_OUTPUT,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=['input_tensor_9ch'],
        output_names=['class_logits_3ch'],
        dynamic_axes={
            'input_tensor_9ch': {0: 'batch_size', 2: 'height', 3: 'width'},
            'class_logits_3ch': {0: 'batch_size', 2: 'height', 3: 'width'}
        }
    )
    print(f"ONNX model saved successfully to {ONNX_OUTPUT}")

if __name__ == "__main__":
    if not os.path.exists(PT_OUTPUT):
        download_file(URL, PT_OUTPUT)
    else:
        print(f"{PT_OUTPUT} already exists.")
    
    if not os.path.exists(ONNX_OUTPUT):
        convert_to_onnx()
    else:
        print(f"{ONNX_OUTPUT} already exists.")
