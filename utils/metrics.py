import torch
import torch.nn as nn
import numpy as np

class XEDiceLoss(torch.nn.Module):
    """
    Computes (0.5 * CrossEntropyLoss) + (0.5 * DiceLoss).
    """

    def __init__(self):
        super().__init__()
        self.xe = torch.nn.BCEWithLogitsLoss(reduction="none")

    def forward(self, pred, true):
        
        pred = pred.squeeze(1)
        valid_pixel_mask = true.ne(255)  # valid pixel mask

        # Cross-entropy loss
        temp_true = torch.where((true == 255), 0, true) 
        xe_loss = self.xe(pred, temp_true.float())
        xe_loss = xe_loss.masked_select(valid_pixel_mask).mean()

        # Dice loss
        
        pred = pred.sigmoid()
        
        pred = pred.masked_select(valid_pixel_mask)
        true = true.masked_select(valid_pixel_mask)
        
        dice_loss = 1 - (2.0 * torch.sum(pred * true) + 1e-7) / (torch.sum(pred + true) + 1e-7)
        
        return (0.5 * xe_loss) + (0.5 * dice_loss)



def intersection_over_union(pred, true):
    """
    Calculates intersection and union for a batch of images.

    Args:
        pred (torch.Tensor): a tensor of predictions
        true (torc.Tensor): a tensor of labels

    Returns:
        intersection (int): total intersection of pixels
        union (int): total union of pixels
    """
    valid_pixel_mask = true.ne(255)  # valid pixel mask
    true = true.masked_select(valid_pixel_mask).to("cpu")
    pred = pred.masked_select(valid_pixel_mask).to("cpu")

    # # Intersection and union totals
    intersection = np.logical_and(true, pred)
    union = np.logical_or(true, pred)
    return intersection.sum() / union.sum()

    