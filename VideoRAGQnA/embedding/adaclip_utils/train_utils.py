import torch
from utils.logger import LOGGER


def verbose(metrics, metric_name, epoch=0, name="EVAL"):
    if "Acc" in metrics:
        msg = f"[{metric_name}]{name:s} epoch {epoch}, Acc: {metrics['Acc']:.2f}"
    else:
        r1, r5, r10, r50 = metrics["R1"], metrics["R5"], metrics["R10"], metrics["R50"]
        msg = f"[{metric_name}]{name:s} epoch {epoch}, R@1: {r1:.1f}"
        msg += f", R@5: {r5:.1f}, R@10 {r10:.1f}, R@50 {r50:.1f}"
        msg += f", MedR: {metrics['MedR']:g}, MeanR: {metrics['MeanR']:.1f}"
    LOGGER.info(msg)


def log_metrics(metrics, metric_name, epoch, writer):
    for key, value in metrics.items():
        writer.add_scalar(f"{metric_name}/{key}", value, epoch)


def progress(batch_idx, len_epoch):
    base = '[{}/{} ({:.0f}%)]'
    current = batch_idx
    total = len_epoch
    return base.format(current, total, 100.0 * current / total)


def save_checkpoint(ckpt, cfg, optimizer, ckpt_path):
    """Saving checkpoints

    :param epoch: current epoch number
    """
    model = ckpt['model'].module if hasattr(ckpt['model'], 'module') else ckpt['model']
    epoch = ckpt['epoch']
    arch = type(model).__name__
    state = {
        'arch': arch,
        'epoch': epoch,
        'state_dict': model.state_dict(),
        'config': cfg,
        'optimizer': optimizer.state_dict()
    }

    torch.save(state, ckpt_path)