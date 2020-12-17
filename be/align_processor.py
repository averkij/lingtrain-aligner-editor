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
import time
import queue

from multiprocessing import Queue, Process

FINISH_PROCESS = "finish_process"

class processor:
    def __init__(self, proc_count, db_path, res_img, res_img_best, lang_name_from, lang_name_to):
        self.proc_count = proc_count
        self.queue_in = Queue()
        self.queue_out = Queue()
        self.db_path = db_path
        self.res_img = res_img
        self.res_img_best = res_img_best
        # self.lines_proxy_to = lines_proxy_to
        self.lang_name_from = lang_name_from
        self.lang_name_to = lang_name_to

    def add_tasks(self, task_list):
        for i, task in enumerate(task_list):
            self.queue_in.put((i, task))
        for i in range(self.proc_count):
            self.queue_in.put((-1, FINISH_PROCESS))     
        self.tasks_count = len(task_list)   

    def work(self, queue_in, queue_out):
        while True:
            try:
                task_index, task = queue_in.get_nowait()
            except queue.Empty:
                print('found an empty queue. Sleeping for a while before checking again...')
                time.sleep(0.01)
            else:
                try:
                    if task == FINISH_PROCESS:
                        print('No more work left to be done. Exiting...')
                        break
                    
                    print("task_index", task_index)
                    
                    self.process_batch(task_index, *task)

                except Exception as e:
                    print('task failed. ' + str(e))
                    queue_out.put("error")

    def handle_result(self, queue_out):
        counter = 0
        error_occured = False
        result = []

        while counter < self.tasks_count:
            result_code, batch_number, texts_from, texts_to = queue_out.get()

            if result_code == con.PROC_DONE:
                print("RESULT:", result_code)
                result.append((batch_number, texts_from, texts_to))
                state.set_processing_state(self.db_path, (con.PROC_IN_PROGRESS, self.tasks_count, counter+1))

            elif result_code==con.PROC_ERROR:                
                error_occured = True
                state.set_processing_state(self.db_path, (con.PROC_ERROR, self.tasks_count, counter+1))
                break

            counter += 1

        #sort by batch_id
        result.sort()
        with sqlite3.connect(self.db_path) as db:
            logging.info(f"writing {len(result)} batches to {self.db_path}")
            for i, texts_from, texts_to in result:
                db.executemany(f"insert into processing_from(text_ids, initial_id, text) values (?,?,?)", texts_from)
                db.executemany(f"insert into processing_to(text_ids, initial_id, text) values (?,?,?)", texts_to)

            logging.info(f"creating index for {self.db_path}")
            helper.create_doc_index(db)
            
        logging.info(f"Alignment is finished. Removing state. {self.db_path}")

        if not error_occured:
            print("finishing. no error occured")
            state.destroy_processing_state(self.db_path)
        else:
            print("finishing with error")
        
    def start(self):
        result_handler = Process(target=self.handle_result, args=(self.queue_out,), daemon=True)
        result_handler.start()

        workers = [Process(target=self.work, args=(self.queue_in, self.queue_out), daemon=True) for _ in range(self.proc_count)]
        for w in workers:
            w.start()

    def process_batch(self, batch_number, lines_from_batch, lines_to_batch, line_ids_from, line_ids_to):
        zero_treshold = 0
        sims = []

        # use_proxy_to = False
        # use_proxy_to = self.lines_proxy_to != None #and len(self.lines_proxy_to)>=len(lines_to)
        #print("use_proxy_to", use_proxy_to, len(lines_proxy_to), len(lines_to)) 

        logging.info(f"Aligning started for {self.db_path}.")
        try:
            #test version restriction
            # if (config.TEST_RESTRICTION_MAX_BATCHES > 0 and batch_number > config.TEST_RESTRICTION_MAX_BATCHES) \
            #         or not state.processing_state_exist(self.db_path):
            #     logging.info(f"[Test restriction]. Finishing and removing state. {self.db_path}")
            #     state.destroy_processing_state(self.db_path)
            #     break
            
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
        
            res_img_batch = "{0}_{1:04d}{2}".format(os.path.splitext(self.res_img)[0], batch_number, os.path.splitext(self.res_img)[1])
            res_img_batch_best = "{0}_{1:04d}{2}".format(os.path.splitext(self.res_img_best)[0], batch_number, os.path.splitext(self.res_img_best)[1])

            # Visualization
            plt.figure(figsize=(12,6))
            sns.heatmap(sim_matrix, cmap="Greens", vmin=zero_treshold, cbar=False)
            plt.savefig(res_img_batch, bbox_inches="tight")

            plt.figure(figsize=(12,6))
            sns.heatmap(sim_matrix_best, cmap="Greens", vmin=zero_treshold, cbar=False)
            plt.xlabel(self.lang_name_to, fontsize=30, labelpad=-40)
            plt.ylabel(self.lang_name_from, fontsize=30, labelpad=-40)
            plt.tick_params(axis='both', which='both', bottom=False, top=False, labelbottom=False, right=False, left=False, labelleft=False)
            plt.savefig(res_img_batch_best, bbox_inches="tight")

            # Aggregating similarities for grade calculation
            best_sim_ind = sim_matrix_best.argmax(1)
            sims.extend(sim_matrix_best[range(best_sim_ind.shape[0]), best_sim_ind])            

            # lines_proxy_to_batch = [''] * len(lines_to_batch)
            # if use_proxy_to:
            #     lines_proxy_to_batch = self.lines_proxy_to[line_ids_to[0]:line_ids_to[-1]+1]
            
            # Actual work
            logging.debug(f"Processing lines.")
            # get_processed(lines_from_batch, lines_to_batch, lines_proxy_to_batch, line_ids_from, line_ids_to, \
            #     sim_matrix, sim_matrix_best, best_sim_ind, zero_treshold, batch_number, batch_size, self.db_path)

            texts_from = []
            texts_to = []

            for line_from_id in range(sim_matrix.shape[0]):
                id_from = line_ids_from[line_from_id]
                text_from = lines_from_batch[line_from_id]
                id_to = line_ids_to[best_sim_ind[line_from_id]]
                text_to = lines_to_batch[best_sim_ind[line_from_id]]

                texts_from.append((f'[{id_from+1}]', id_from+1, text_from.strip()))
                texts_to.append((f'[{id_to+1}]', id_to+1, text_to.strip()))

            self.queue_out.put((con.PROC_DONE, batch_number, texts_from, texts_to))

            #sim_grades = calc_sim_grades(sims)
            # docs["sim_grades"] = sim_grades

        except Exception as e:
            logging.error(e, exc_info=True)
            self.queue_out.put((con.PROC_ERROR, [], []))

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

def get_sim_matrix(vec1, vec2, window=config.DEFAULT_WINDOW):
    sim_matrix = np.zeros((len(vec1), len(vec2)))
    k = len(vec1)/len(vec2)
    for i in range(len(vec1)):
        for j in range(len(vec2)):
            if (j*k > i-window) & (j*k < i+window):
                sim = 1 - spatial.distance.cosine(vec1[i], vec2[j])
                sim_matrix[i,j] = max(sim, 0.01)
    return sim_matrix
