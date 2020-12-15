import logging
import os
import pickle
import sys
from typing import List

import matplotlib
import numpy as np
import seaborn as sns
#https://stackoverflow.com/questions/49921721/runtimeerror-main-thread-is-not-in-main-loop-with-matplotlib-and-flask
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy import spatial

import config
import constants as con
import helper
import model_dispatcher
import sim_helper
import state_manager as state

import sqlite3



def serialize_docs(lines_from, lines_to, lines_proxy_to, res_img, res_img_best, lang_name_from, lang_name_to, db_path, total_batches, \
                    threshold=config.DEFAULT_TRESHOLD, batch_size=config.DEFAULT_BATCHSIZE, window_size=config.DEFAULT_WINDOW):
    batch_number = 0
    zero_treshold = 0
    sims = []

    use_proxy_to = lines_proxy_to != None and len(lines_proxy_to)>=len(lines_to)
    print("use_proxy_to", use_proxy_to, len(lines_proxy_to), len(lines_to)) 

    logging.info(f"Aligning started for {db_path}.")
    try:
        for lines_from_batch, lines_to_batch, line_ids_from, line_ids_to in helper.get_batch_intersected(lines_from, lines_to, batch_size, window_size):
            batch_number += 1
            
            #test version restriction
            if (config.TEST_RESTRICTION_MAX_BATCHES > 0 and batch_number > config.TEST_RESTRICTION_MAX_BATCHES) \
                    or not state.processing_state_exist(db_path):
                logging.info(f"[Test restriction]. Finishing and removing state. {db_path}")
                state.destroy_processing_state(db_path)
                break
            
            state.set_processing_state(db_path, (con.PROC_IN_PROGRESS, total_batches, batch_number))

            print("batch:", batch_number)
            logging.info(f"Batch {batch_number}. Calculating vectors.")
            
            vectors1 = [*get_line_vectors(lines_from_batch)]
            vectors2 = [*get_line_vectors(lines_to_batch)]
            logging.debug(f"Batch {batch_number}. Vectors calculated. len(vectors1)={len(vectors1)}. len(vectors2)={len(vectors2)}.")

            # Similarity matrix
            logging.debug(f"Calculating similarity matrix.")
            sim_matrix = get_sim_matrix(vectors1, vectors2)
            sim_matrix_best = sim_helper.best_per_row(sim_matrix)

            # Heuristics
            sim_matrix_best = sim_helper.fix_inside_window(sim_matrix, sim_matrix_best, fixed_window_size=2)
        
            res_img_batch = "{0}_{1:04d}{2}".format(os.path.splitext(res_img)[0], batch_number, os.path.splitext(res_img)[1])
            res_img_batch_best = "{0}_{1:04d}{2}".format(os.path.splitext(res_img_best)[0], batch_number, os.path.splitext(res_img_best)[1])

            # Visualization
            plt.figure(figsize=(12,6))
            sns.heatmap(sim_matrix, cmap="Greens", vmin=zero_treshold, cbar=False)
            plt.savefig(res_img_batch, bbox_inches="tight")

            plt.figure(figsize=(12,6))
            sns.heatmap(sim_matrix_best, cmap="Greens", vmin=zero_treshold, cbar=False)
            plt.xlabel(lang_name_to, fontsize=30, labelpad=-40)
            plt.ylabel(lang_name_from, fontsize=30, labelpad=-40)
            plt.tick_params(axis='both', which='both', bottom=False, top=False, labelbottom=False, right=False, left=False, labelleft=False)
            plt.savefig(res_img_batch_best, bbox_inches="tight")

            # Aggregating similarities for grade calculation
            best_sim_ind = sim_matrix_best.argmax(1)
            sims.extend(sim_matrix_best[range(best_sim_ind.shape[0]), best_sim_ind])            

            lines_proxy_to_batch = [''] * len(lines_to_batch)
            if use_proxy_to:
                lines_proxy_to_batch = lines_proxy_to[line_ids_to[0]:line_ids_to[-1]+1]
            
            # Actual work
            logging.debug(f"Processing lines.")
            get_processed(lines_from_batch, lines_to_batch, lines_proxy_to_batch, line_ids_from, line_ids_to, \
                sim_matrix, sim_matrix_best, best_sim_ind, zero_treshold, batch_number, batch_size, db_path)

        helper.create_doc_index(db_path)

        sim_grades = calc_sim_grades(sims)
        # docs["sim_grades"] = sim_grades

        logging.info(f"Alignment is finished. Removing state. {db_path}")
        state.destroy_processing_state(db_path)
    except Exception as e:
        logging.error(e, exc_info=True)
        state.set_processing_state(db_path, (con.PROC_ERROR, config.TEST_RESTRICTION_MAX_BATCHES, batch_number))

def calc_sim_grades(sims):
    key, res = 0, {}
    for i, s in enumerate(sorted(sims)):
        while key < s:
            res[round(key*100)] = len(sims) - i
            key += 0.01
    while len(res) <= 100:
        res[round(key*100)] = 0
        key += 0.01
    return res

def get_line_vectors(lines):
    return model_dispatcher.models[config.MODEL].embed(lines)

def get_processed(lines_from, lines_to, lines_proxy_to, line_ids_from, line_ids_to, sim_matrix, sim_matrix_best, best_sim_ind, \
                    threshold, batch_number, batch_size, db_path, candidates_count=50):
    #saving to db
    texts_from = []
    texts_to = []

    for line_from_id in range(sim_matrix.shape[0]):
        id_from = line_ids_from[line_from_id]
        text_from = lines_from[line_from_id]
        id_to = line_ids_to[best_sim_ind[line_from_id]]
        text_to = lines_to[best_sim_ind[line_from_id]]

        texts_from.append((f'[{id_from+1}]', id_from+1, text_from.strip()))
        texts_to.append((f'[{id_to+1}]', id_to+1, text_to.strip()))
    
    with sqlite3.connect(db_path) as db:
        db.executemany(f"insert into processing_from(text_ids, initial_id, text) values (?,?,?)", texts_from)
        db.executemany(f"insert into processing_to(text_ids, initial_id, text) values (?,?,?)", texts_to)
    return

def get_pairs(lines_from, lines_to, ru_proxy_lines, sim_matrix, threshold):
    res_from = []
    res_to = []
    proxy_from = []
    sims = []
    for i in range(sim_matrix.shape[0]):
        for j in range(sim_matrix.shape[1]):
            if sim_matrix[i,j] >= threshold:
                res_from.append(lines_from[j])
                res_to.append(lines_to[i])
                proxy_from.append(ru_proxy_lines[i])
                sims.append(sim_matrix[i,j])
                
    return res_from,res_to,proxy_from,sims

def get_sim_matrix(vec1, vec2, window=config.DEFAULT_WINDOW):
    sim_matrix = np.zeros((len(vec1), len(vec2)))
    k = len(vec1)/len(vec2)
    for i in range(len(vec1)):
        for j in range(len(vec2)):
            if (j*k > i-window) & (j*k < i+window):
                sim = 1 - spatial.distance.cosine(vec1[i], vec2[j])
                sim_matrix[i,j] = max(sim, 0.01)
    return sim_matrix

class DocLine:
    def __init__(self, line_id:int, text=None, proxy=None):
        self.line_id:int = line_id
        self.text = text
        self.proxy = proxy
    def __hash__(self):
        return hash(self.line_id)
    def __eq__(self, other):
        return self.line_id == other
