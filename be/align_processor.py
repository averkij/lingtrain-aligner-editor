"""Alignment processor"""

import logging
import os
import queue
import sqlite3
import time
from multiprocessing import Process, Queue

import config
import constants as con
import helper
import matplotlib
import model_dispatcher
import numpy as np
import seaborn as sns
import sim_helper
import vis_helper
from matplotlib import pyplot as plt
from scipy import spatial

# https://stackoverflow.com/questions/49921721/runtimeerror-main-thread-is-not-in-main-loop-with-matplotlib-and-flask
matplotlib.use('Agg')


FINISH_PROCESS = "finish_process"


class AlignmentProcessor:
    """Processor with parallel texts alignment logic"""

    def __init__(self, proc_count, db_path, user_db_path, res_img, res_img_best, lang_name_from, lang_name_to, guid_from, guid_to):
        self.proc_count = proc_count
        self.queue_in = Queue()
        self.queue_out = Queue()
        self.db_path = db_path
        self.user_db_path = user_db_path
        self.res_img = res_img
        self.res_img_best = res_img_best
        # self.lines_proxy_to = lines_proxy_to
        self.lang_name_from = lang_name_from
        self.lang_name_to = lang_name_to
        self.tasks_count = 0
        self.guid_from = guid_from
        self.guid_to = guid_to

    def add_tasks(self, task_list):
        """Add batches with string arrays for the further processing"""
        for i, task in enumerate(task_list):
            self.queue_in.put((i, task))
        for i in range(self.proc_count):
            self.queue_in.put((-1, FINISH_PROCESS))
        self.tasks_count = len(task_list)

    def work(self, queue_in, queue_out):
        """Create separate alignment processes"""
        while True:
            try:
                task_index, task = queue_in.get_nowait()
            except queue.Empty:
                print(
                    'found an empty queue. Sleeping for a while before checking again...')
                time.sleep(0.01)
            else:
                try:
                    if task == FINISH_PROCESS:
                        print('No more work left to be done. Exiting...')
                        break

                    print("task_index", task_index)

                    self.process_batch(*task)

                except Exception as e:
                    print('task failed. ' + str(e))
                    queue_out.put("error")

    def handle_result(self, queue_out):
        """Handle the result of a single finished process"""
        counter = 0
        error_occured = False
        result = []

        while counter < self.tasks_count:
            result_code, batch_number, texts_from, texts_to = queue_out.get()

            if result_code == con.PROC_DONE:
                result.append((batch_number, texts_from, texts_to))
                helper.update_batch_progress(self.db_path, batch_number)
                helper.increment_alignment_state(
                    self.db_path, self.user_db_path, self.guid_from, self.guid_to, con.PROC_IN_PROGRESS)

            elif result_code == con.PROC_ERROR:
                error_occured = True
                helper.increment_alignment_state(
                    self.db_path, self.user_db_path, self.guid_from, self.guid_to, con.PROC_ERROR)
                break

            counter += 1

        # sort by batch_id
        result.sort()
        with sqlite3.connect(self.db_path) as db:
            logging.info(f"writing {len(result)} batches to {self.db_path}")
            helper.rewrite_processing_batches(db, result)

            logging.info(f"creating index for {self.db_path}")
            helper.create_doc_index(db, result)

        if not error_occured:
            print("finishing. no error occured")
            helper.update_alignment_state(
                self.user_db_path, self.guid_from, self.guid_to, con.PROC_IN_PROGRESS_DONE)
        else:
            print("finishing with error")

    def start(self):
        """Start workers"""
        result_handler = Process(
            target=self.handle_result, args=(self.queue_out,), daemon=True)
        result_handler.start()

        workers = [Process(target=self.work, args=(self.queue_in, self.queue_out), daemon=True) for _ in range(
            min(self.proc_count, self.tasks_count))]  # do not run more processes than necessary
        for w in workers:
            w.start()

    def process_batch(self, lines_from_batch, lines_to_batch, line_ids_from, line_ids_to, batch_number):
        """Do the actual alignment process logic"""
        zero_treshold = 0
        sims = []

        # use_proxy_to = False
        # use_proxy_to = self.lines_proxy_to != None #and len(self.lines_proxy_to)>=len(lines_to)
        #print("use_proxy_to", use_proxy_to, len(lines_proxy_to), len(lines_to))

        logging.info(f"Alignment started for {self.db_path}.")
        try:
            print("batch:", batch_number)
            logging.info(f"Batch {batch_number}. Calculating vectors.")

            vectors1 = [*get_line_vectors(lines_from_batch)]
            vectors2 = [*get_line_vectors(lines_to_batch)]
            logging.debug(
                f"Batch {batch_number}. Vectors calculated. len(vectors1)={len(vectors1)}. len(vectors2)={len(vectors2)}.")

            # Similarity matrix
            logging.debug(f"Calculating similarity matrix.")
            sim_matrix = get_sim_matrix(vectors1, vectors2)
            sim_matrix_best = sim_helper.best_per_row_with_ones(sim_matrix)

            vis_helper.save_pic(sim_matrix_best, self.lang_name_to, self.lang_name_from, self.res_img_best, batch_number)

            best_sim_ind = sim_matrix_best.argmax(1)
            texts_from = []
            texts_to = []

            for line_from_id in range(sim_matrix.shape[0]):
                id_from = line_ids_from[line_from_id]
                text_from = lines_from_batch[line_from_id]
                id_to = line_ids_to[best_sim_ind[line_from_id]]
                text_to = lines_to_batch[best_sim_ind[line_from_id]]

                texts_from.append(
                    (f'[{id_from+1}]', id_from+1, text_from.strip()))
                texts_to.append((f'[{id_to+1}]', id_to+1, text_to.strip()))

            self.queue_out.put(
                (con.PROC_DONE, batch_number, texts_from, texts_to))
        except Exception as e:
            logging.error(e, exc_info=True)
            self.queue_out.put((con.PROC_ERROR, [], []))


def calc_sim_grades(sims):
    """Calculate similarity gradations"""
    key, res = 0, {}
    for i, sim in enumerate(sorted(sims)):
        while key < sim:
            res[round(key*100)] = len(sims) - i
            key += 0.01
    while len(res) <= 100:
        res[round(key*100)] = 0
        key += 0.01
    return res


def get_line_vectors(lines):
    """Calculate embedding of the string"""
    return model_dispatcher.models[config.MODEL].embed(lines)


def get_sim_matrix(vec1, vec2, window=config.DEFAULT_WINDOW):
    """Calculate similarity matrix"""
    sim_matrix = np.zeros((len(vec1), len(vec2)))
    k = len(vec1)/len(vec2)
    for i, vector1 in enumerate(vec1):
        for j, vector2 in enumerate(vec2):
            if (j*k > i-window) & (j*k < i+window):
                sim = 1 - spatial.distance.cosine(vector1, vector2)
                sim_matrix[i, j] = max(sim, 0.01)
    return sim_matrix
