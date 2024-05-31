"""Module for computing performance metrics
"""
import torch
import numpy as np


def t2v_metrics(sims, break_pts=None):
    """Compute retrieval metrics from a similiarity matrix.
    Args:
        sims (th.Tensor): N x M matrix of similarities between embeddings, where
             x_{i,j} = <text_embd[i], vid_embed[j]>
    Returns:
        (dict[str:float]): retrieval metrics
    """
    orders = torch.argsort(sims, descending=True)
    inds = torch.argsort(orders)
    if break_pts is None:
        return ranks_to_recall(inds.diag().cpu().numpy())
    ranks = []
    for i in range(min(inds.shape[0], inds.shape[1])):
        # inds = (num_caps, num_imgs) return best image for each caption
        ranks.append(inds[break_pts[i]:break_pts[i+1], i])
    ranks = torch.cat(ranks).cpu().numpy()
    return ranks_to_recall(ranks)


def v2t_metrics(sims, break_pts=None):
    # switch axes of text and video
    sims = torch.transpose(sims, 0, 1)
    orders = torch.argsort(sims, descending=True)
    inds = torch.argsort(orders)
    if break_pts is None:
        return ranks_to_recall(inds.diag().cpu().numpy())
    ranks = []
    for i in range(min(inds.shape[0], inds.shape[1])):
        # inds = (num_imgs, num_caps) return minimum rank of all the captions
        ranks.append(min(inds[i, break_pts[i]:break_pts[i+1]]).unsqueeze(0))
    ranks = torch.cat(ranks).cpu().numpy()
    return ranks_to_recall(ranks)


def ranks_to_recall(ranks):
    metrics = {}
    metrics["R1"] = 100 * float(np.sum(ranks == 0)) / len(ranks)
    metrics["R5"] = 100 * float(np.sum(ranks < 5)) / len(ranks)
    metrics["R10"] = 100 * float(np.sum(ranks < 10)) / len(ranks)
    metrics["R50"] = 100 * float(np.sum(ranks < 50)) / len(ranks)
    metrics["MedR"] = np.median(ranks) + 1
    metrics["MeanR"] = np.mean(ranks) + 1
    return metrics 
