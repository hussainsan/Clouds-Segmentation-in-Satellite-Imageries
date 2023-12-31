import torch
import torch.nn.functional as F
from tqdm import tqdm
from utils.metrics import intersection_over_union, f1_score_fun


def train_fun(
    model,
    criterion,
    optimizer,
    grad_scaler,
    train_loader,
    device,
    amp,
    gradient_clipping,
    epoch,
    epochs,
    experiment,
    global_step,
):
    epoch_loss = 0
    total_step = global_step

    model.train()
    with tqdm(
        total=len(train_loader), desc=f"Epoch {epoch}/{epochs}", unit="img"
    ) as trainbar:
        for _, (images, true_masks) in enumerate(train_loader):
            images = images.type(torch.FloatTensor).to(device=device)
            true_masks = true_masks.type(torch.FloatTensor).to(device=device).squeeze()

            with torch.autocast(
                device.type if device.type != "mps" else "cpu", enabled=amp
            ):
                masks_pred = model(images)
                loss = criterion(masks_pred, true_masks)

            optimizer.zero_grad(set_to_none=True)
            grad_scaler.scale(loss).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clipping)
            grad_scaler.step(optimizer)
            grad_scaler.update()

            trainbar.update(images.shape[0])
            total_step += 1
            epoch_loss += loss.item()
            experiment.log(
                {"train loss": loss.item(), "step": total_step, "epoch": epoch}
            )
            trainbar.set_postfix(**{"loss (batch)": loss.item()})

        average_epoch_loss = epoch_loss / total_step

        experiment.log({"average_epoch_loss": average_epoch_loss, "epoch": epoch})
    return average_epoch_loss, total_step


@torch.inference_mode()
def eval_fun(model, val_loader, device, amp):
    iou_list = []
    f1_list = []
    val_loader = tqdm(val_loader, desc="Validation round", unit="batch", leave=False)
    with torch.no_grad():
        model.eval()
        for data, targets in val_loader:
            input_image = data.type(torch.FloatTensor).to(device)
            true_mask = targets.type(torch.FloatTensor).to(device).squeeze()
            with torch.autocast(
                device.type if device.type != "mps" else "cpu", enabled=amp
            ):
                predicted_mask = model(input_image)
                probas = F.sigmoid(predicted_mask)

            predicted_mask = (probas > 0.5).float().squeeze()

            batch_iou = intersection_over_union(predicted_mask, true_mask)
            batch_f1 = f1_score_fun(predicted_mask, true_mask)
            iou_list.append(batch_iou)
            f1_list.append(batch_f1)

            mean_iou = (torch.sum(torch.stack(iou_list)) / len(iou_list)).item()
            mean_f1 = torch.mean(torch.tensor(f1_list, dtype=torch.float64)).item()

            val_loader.set_postfix(iou=mean_iou, f1=mean_f1)

    model.train()
    return sum(iou_list) / len(iou_list), sum(f1_list) / len(f1_list)
