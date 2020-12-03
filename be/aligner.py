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

import pdgraphs as pg
import pandas as pd
import re


def calculate_graphs(lines_from, processing_from_to, res_img, res_path, lang_name_from, lang_name_to, threshold=config.DEFAULT_TRESHOLD, batch_size=config.DEFAULT_BATCHSIZE, window_size=config.DEFAULT_WINDOW):
    
    print("calculating...")
    # print(lines_from)

    graph = txtfile2pgr(lines_from)
    df_edges = graph.edges()
    conn_html = df_edges[df_edges['from'] != df_edges['to']].sort_values(by = 'weight', ascending=False).iloc[:10].to_html()

    # print("html:")
    # print(html)

    res = {"items": {"conn_html": conn_html}}

    print("saving result to", res_path)
    pickle.dump(res, open(res_path, "wb"))

    return

def txtfile2pgr(text):
    lWords = text2words(text)
    dfAdj = lol2adj(lWords)
    return pg.pdGraph(dfAdj)

def lol2adj(lol): # list of lists (tuples, sets, words) of elements to adj matrix
    # slow
    dfEls, dfElsNorm = pd.DataFrame(), pd.DataFrame()
    for i, els in enumerate(lol):
        for el in els: # prepare for sum
            dfEls.at[i, el] = 0
            dfElsNorm.at[i, el] = 0
    for i, els in enumerate(lol):
        weight = 1/len(els)
        for el in els:
            dfEls.at[i, el] += 1
            dfElsNorm.at[i, el] += weight
    return (dfElsNorm.fillna(0).T @ dfEls.fillna(0)).sort_index(axis=0).sort_index(axis=1)

def text2words(txt):
    lWords = re.split('[^а-яё]+', txt.lower(), flags=re.IGNORECASE) #'[^a-zа-яё]+'
    return [word for word in lWords if len(word) > 1]


def serialize_docs(lines_from, lines_to, processing_from_to, res_img, res_img_best, lang_name_from, lang_name_to, threshold=config.DEFAULT_TRESHOLD, batch_size=config.DEFAULT_BATCHSIZE, window_size=config.DEFAULT_WINDOW):
    batch_number = 0
    docs = {
        "items":[],
        "sim_grades":{}
        }   
    zero_treshold = 0
    sims = []

    logging.debug(f"Aligning started.")
    try:
        for lines_from_batch, lines_to_batch, line_ids_from, line_ids_to in helper.get_batch_intersected(lines_from, lines_to, batch_size, window_size):
            batch_number += 1
            
            #test version restriction
            if batch_number > config.TEST_RESTRICTION_MAX_BATCHES or not state.processing_state_exist(processing_from_to):
                logging.debug(f"[Test restriction]. Finishing and removing state. {processing_from_to}")
                state.destroy_processing_state(processing_from_to)
                break
            
            state.set_processing_state(processing_from_to, (con.PROC_IN_PROGRESS, config.TEST_RESTRICTION_MAX_BATCHES, batch_number))

            print("batch:", batch_number)
            logging.debug(f"Batch {batch_number}. Calculating vectors.")

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

            # Actual work
            logging.debug(f"Processing lines.")            
            doc = get_processed(lines_from_batch, lines_to_batch, line_ids_from, line_ids_to, sim_matrix, sim_matrix_best, best_sim_ind, zero_treshold, batch_number, batch_size)
            docs["items"].append(doc)

        sim_grades = calc_sim_grades(sims)
        docs["sim_grades"] = sim_grades

        logging.debug(f"Dumping to file {processing_from_to}.")
        pickle.dump(docs, open(processing_from_to, "wb"))

        logging.debug(f"Alignment is finished. Removing state. {processing_from_to}")
        state.destroy_processing_state(processing_from_to)
    except Exception as e:
        logging.error(e, exc_info=True)
        state.set_processing_state(processing_from_to, (con.PROC_ERROR, config.TEST_RESTRICTION_MAX_BATCHES, batch_number))

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

def get_processed(lines_from, lines_to, line_ids_from, line_ids_to, sim_matrix, sim_matrix_best, best_sim_ind, threshold, batch_number, batch_size, candidates_count=50):
    doc = {}
    for line_from_id in range(sim_matrix.shape[0]):
        line_id_from_abs = line_ids_from[line_from_id]
        line = DocLine(line_id_from_abs, lines_from[line_from_id])
        doc[line] = {}

        candidates = [(line_to_id, sim_matrix[line_from_id, line_to_id]) for line_to_id in range(sim_matrix.shape[1]) if sim_matrix[line_from_id, line_to_id] > threshold]
        doc[line]["from"] = (line, False) #("line", "isEdited")
        doc[line]["to"] = (DocLine(line_ids_to[best_sim_ind[line_from_id]], lines_to[best_sim_ind[line_from_id]]), sim_matrix[line_from_id, best_sim_ind[line_from_id]], False)
        doc[line]["cnd"] = [
                    #text with line_id
                    (DocLine(
                        line_id = line_ids_to[c[0]],
                        text = lines_to[c[0]]),
                    #text similarity
                    sim_matrix[line_from_id, c[0]])
                    for c in candidates]
    return doc

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
    def __init__(self, line_id:int, text=None):
        self.line_id:int = line_id
        self.text = text
    def __hash__(self):
        return hash(self.line_id)
    def __eq__(self, other):
        return self.line_id == other
