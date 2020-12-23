"""Similarity calculations helper"""

import numpy as np


def best_per_row(sim_matrix):
    """Transfor matrix by leaving only best match"""
    sim_matrix_best = np.zeros_like(sim_matrix)
    max_sim = sim_matrix.argmax(1)
    sim_matrix_best[range(sim_matrix.shape[0]), max_sim] = sim_matrix[range(
        sim_matrix.shape[0]), max_sim]
    return sim_matrix_best


def fix_inside_window(sim_matrix, sim_matrix_best, fixed_window_size=1):
    """Fix matrix"""
    window = fixed_window_size + 1
    if sim_matrix_best.shape[0] <= window or window < 1:
        return sim_matrix_best
    for i in range(sim_matrix_best.shape[0] - window):
        first = sim_matrix_best[i].argmax()
        last = sim_matrix_best[i+window].argmax()
        if last-first == window:
            for j in range(1, window+1):
                k = i+j
                middle = sim_matrix_best[k].argmax()
                if middle != first+j:
                    sim_matrix_best[k, middle] = 0
                    sim_matrix_best[k, first+j] = sim_matrix[k, first+j]
    return sim_matrix_best
