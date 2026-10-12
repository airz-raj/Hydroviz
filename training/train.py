import os
import argparse
import yaml
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from dataset import HimalayanSARFloodDataset
from models import FloodSegmentationUNet

def dice_loss(pred_logits: torch.Tensor, target: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    probs = torch.softmax(pred_logits, dim=1)[:, 1]
    target_f = target.float()
    intersection = (probs * target_f).sum()
    dice = (2.0 * intersection + eps) / (probs.sum() + target_f.sum() + eps)
    return 1.0 - dice

def compute_iou(pred_mask: torch.Tensor, target: torch.Tensor) -> float:
    intersection = (pred_mask & (target == 1)).sum().item()
    union = (pred_mask | (target == 1)).sum().item()
    return (intersection / union) if union > 0 else 1.0

def train_one_epoch(model, loader, optimizer, criterion_ce, device):
    model.train()
    total_loss = 0.0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        out = model(x)
        loss = 0.4 * criterion_ce(out, y) + 0.6 * dice_loss(out, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / max(1, len(loader))

def main():
    parser = argparse.ArgumentParser(description="Train HydroViz Flood Delineation Model")
    parser.add_argument("--config", default="./training/configs/default_config.yaml", help="Path to config yaml")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu"))
    print(f"Initializing HydroViz training on device: {device}")

    dataset = HimalayanSARFloodDataset("./training/datasets", patch_size=256)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    model = FloodSegmentationUNet(in_channels=9, num_classes=2, base_channels=16).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    criterion_ce = nn.CrossEntropyLoss()

    checkpoint_dir = "./training/checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        loss = train_one_epoch(model, loader, optimizer, criterion_ce, device)
        print(f"Epoch [{epoch}/{args.epochs}] — Train Loss: {loss:.4f}")

    ckpt_path = os.path.join(checkpoint_dir, "best_model.pth")
    torch.save(model.state_dict(), ckpt_path)
    print(f"Training complete. Checkpoint saved to: {ckpt_path}")

if __name__ == "__main__":
    main()
