import torch


def gumbel_softmax_top_k(logits, top_k, tau, hard=False, reduce_sum=True, maskvector=True, logit_tau=1):
    """
    Adapted from: https://uvadlc-notebooks.readthedocs.io/en/latest/tutorial_notebooks/DL2/sampling/subsets.html#Subset-Sampler-Class
    and https://pytorch.org/docs/stable/_modules/torch/nn/functional.html#gumbel_softmax
    """
    dim = -1
    m = torch.distributions.gumbel.Gumbel(torch.zeros_like(logits, memory_format=torch.legacy_contiguous_format), torch.ones_like(logits, memory_format=torch.legacy_contiguous_format))
    gumbels = m.sample()
    y = (logits / logit_tau) + gumbels

    _EPS = torch.tensor(1e-40).to(logits.device)
    khot = torch.zeros_like(logits, memory_format=torch.legacy_contiguous_format)
    onehot_approx = torch.zeros_like(logits, memory_format=torch.legacy_contiguous_format)

    if maskvector:
        mask_vector = torch.zeros_like(logits, memory_format=torch.legacy_contiguous_format)

    if not reduce_sum:
        khot_list = []
        indmax_list = []
    for i in range(top_k):
        khot_mask = torch.maximum(1.0 - onehot_approx, _EPS)
        y += khot_mask.log()

        if not maskvector:
            if i != 0 and not reduce_sum and hard:
                y[torch.arange(y.shape[0]),ind_max] += torch.log(_EPS)

        onehot_approx = (y / tau).softmax(dim)  # B,N
        if reduce_sum:
            khot = torch.add(khot, onehot_approx)
        else:
            khot_list.append(onehot_approx)

        if not reduce_sum and hard:
            if maskvector:
                masked_onehot_approx = onehot_approx + mask_vector
                ind_max = torch.argmax(masked_onehot_approx, dim=-1)
                mask_vector[torch.arange(mask_vector.shape[0]),ind_max] += torch.log(_EPS)
            else:
                ind_max = torch.argmax(onehot_approx, dim=-1)
            indmax_list.append(ind_max)

    if reduce_sum:
        if hard:
            index = khot.topk(top_k, dim)[1]
            y_hard = torch.zeros_like(logits, memory_format=torch.legacy_contiguous_format).scatter_(dim, index, 1.0)
            ret = y_hard - khot.detach() + khot
        else:
            ret = khot
    else:
        khot_matrix = torch.stack(khot_list, dim=1)  #B,K,N
        if hard:
            indmax_matrix = torch.stack(indmax_list, dim=-1)
            for ind in indmax_matrix:
                assert torch.unique(ind).shape[0] == top_k, "found duplicate token proposal during gumbel top-k sampling!"
            y_hard = torch.zeros_like(khot_matrix, memory_format=torch.legacy_contiguous_format).scatter_(dim, indmax_matrix[:,:,None], 1.0)
            ret = y_hard - khot_matrix.detach() + khot_matrix
        else:
            ret = khot_matrix
    return ret
