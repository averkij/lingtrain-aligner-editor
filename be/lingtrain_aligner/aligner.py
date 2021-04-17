"""Texts aligner part of the engine"""


import json
import logging
import os
import sqlite3

import numpy as np
from lingtrain_aligner import model_dispatcher, splitter, vis_helper
from scipy import spatial


def get_line_vectors(lines, model_name):
    """Calculate embedding of the string"""
    return model_dispatcher.models[model_name].embed(lines)


def process_batch(lines_from_batch, lines_to_batch, line_ids_from, line_ids_to, batch_number, model_name, window, save_pic=False, lang_name_from="", lang_name_to="", img_path=""):
    """Do the actual alignment process logic"""
    # try:
    logging.info(f"Batch {batch_number}. Calculating vectors.")

    vectors1 = [*get_line_vectors(lines_from_batch, model_name)]
    vectors2 = [*get_line_vectors(lines_to_batch, model_name)]

    logging.debug(
        f"Batch {batch_number}. Vectors calculated. len(vectors1)={len(vectors1)}. len(vectors2)={len(vectors2)}.")

    # Similarity matrix
    logging.debug(f"Calculating similarity matrix.")

    sim_matrix = get_sim_matrix(vectors1, vectors2, window)
    sim_matrix_best = best_per_row_with_ones(sim_matrix)

    # save picture
    if save_pic:
        vis_helper.save_pic(sim_matrix_best, lang_name_to,
                            lang_name_from, img_path, batch_number)

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

    return texts_from, texts_to

    # except Exception as e:
    #     logging.error(e, exc_info=True)
    #     return [], []


def align_texts(splitted_from, splitted_to, model_name, batch_size, window, batch_ids=[], save_pic=False, lang_from="", lang_to="", img_path=""):
    result = []
    task_list = [(lines_from_batch, lines_to_batch, line_ids_from, line_ids_to, batch_id)
                 for lines_from_batch, lines_to_batch,
                 line_ids_from, line_ids_to, batch_id
                 in get_batch_intersected(splitted_from, splitted_to, batch_size, window, batch_ids)]

    for lines_from_batch, lines_to_batch, line_ids_from, line_ids_to, batch_id in task_list:
        texts_from, texts_to = process_batch(lines_from_batch, lines_to_batch, line_ids_from,
                                             line_ids_to, batch_id, model_name, window, save_pic, lang_from, lang_to, img_path)
        result.append((batch_id, texts_from, texts_to))

    # sort by batch_id (will be useful with parallel processing)
    result.sort()

    return result


def align_db(db_path, model_name, batch_size, window, batch_ids=[], save_pic=False, lang_from="", lang_to="", img_path=""):
    result = []
    splitted_from = get_splitted_from(db_path)
    splitted_to = get_splitted_to(db_path)
    task_list = [(lines_from_batch, lines_to_batch, line_ids_from, line_ids_to, batch_id)
                 for lines_from_batch, lines_to_batch,
                 line_ids_from, line_ids_to, batch_id
                 in get_batch_intersected(splitted_from, splitted_to, batch_size, window, batch_ids)]

    count = 0
    for lines_from_batch, lines_to_batch, line_ids_from, line_ids_to, batch_id in task_list:
        print("batch:", count)
        texts_from, texts_to = process_batch(lines_from_batch, lines_to_batch, line_ids_from,
                                             line_ids_to, batch_id, model_name, window, save_pic, lang_from, lang_to, img_path)
        result.append((batch_id, texts_from, texts_to))
        count += 1

    # sort by batch_id (will be useful with parallel processing)
    result.sort()

    save_db(db_path, result)


# HELPERS

def get_splitted_from(db_path):
    """Get lines from splitted_from"""
    with sqlite3.connect(db_path) as db:
        res = db.execute(
            f'select f.text from splitted_from f order by f.id').fetchall()
    return [x[0] for x in res]


def get_splitted_to(db_path):
    """Get lines from splitted_to"""
    with sqlite3.connect(db_path) as db:
        res = db.execute(
            f'select t.text from splitted_to t order by t.id').fetchall()
    return [x[0] for x in res]


def best_per_row_with_ones(sim_matrix):
    """Transfor matrix by leaving only best match"""
    sim_matrix_best = np.zeros_like(sim_matrix)
    max_sim = sim_matrix.argmax(1)
    sim_matrix_best[range(sim_matrix.shape[0]), max_sim] = 1
    return sim_matrix_best


def get_batch_intersected(iter1, iter2, n, window, batch_ids=[], batch_shift=0):
    """Get batch with an additional window"""
    l1 = len(iter1)
    l2 = len(iter2)
    k = int(round(n * l2/l1))
    kdx = 0 - k

    if k < window*2:
        # subbatches will be intersected
        logging.warning(
            f"Batch for the second language is too small. k = {k}, window = {window}")

    counter = 0
    for ndx in range(0, l1, n):
        kdx += k
        if counter in batch_ids or len(batch_ids) == 0:
            yield iter1[ndx:min(ndx + n, l1)], \
                iter2[max(0, kdx - window + batch_shift):min(kdx + k + window + batch_shift, l2)], \
                list(range(ndx, min(ndx + n, l1))), \
                list(range(max(0, kdx - window + batch_shift), min(kdx + k + window + batch_shift, l2))), \
                counter
        counter += 1


def get_sim_matrix(vec1, vec2, window):
    """Calculate similarity matrix"""
    sim_matrix = np.zeros((len(vec1), len(vec2)))
    k = len(vec1)/len(vec2)
    for i, vector1 in enumerate(vec1):
        for j, vector2 in enumerate(vec2):
            if (j*k > i-window) & (j*k < i+window):
                sim = 1 - spatial.distance.cosine(vector1, vector2)
                sim_matrix[i, j] = max(sim, 0.01)
    return sim_matrix


# DATABASE HELPERS


def save_db(db_path, data):
    with sqlite3.connect(db_path) as db:
        rewrite_processing_batches(db, data)
        create_doc_index(db, data)


def create_doc_index(db, data):
    """Create document index in database"""
    batch_ids = [batch_id for batch_id, x, y in data]

    max_batch_id = max(batch_ids)
    doc_index = get_doc_index(db)

    if not doc_index:
        doc_index = [[] for _ in range(max_batch_id+1)]
    else:
        while len(doc_index) < max_batch_id+1:
            doc_index.append([])

    for batch_id in batch_ids:
        doc_index[batch_id] = []
        for batch_id, a, b, c, d in db.execute('SELECT f.batch_id, f.id, f.text_ids, t.id, t.text_ids FROM processing_from f join processing_to t on f.id=t.id where f.batch_id = :batch_id order by f.id', {"batch_id": batch_id}):
            doc_index[batch_id].append((a, b, c, d))

    update_doc_index(db, doc_index)


def update_doc_index(db, index):
    """Insert or update document index"""
    index = json.dumps(index)
    db.execute(
        'insert or replace into doc_index (id, contents) values ((select id from doc_index limit 1),?)', (index,))


def get_doc_index(db):
    """Get document index"""
    res = []
    try:
        cur = db.execute('SELECT contents FROM doc_index')
        res = json.loads(cur.fetchone()[0])
    except:
        logging.warning("can not fetch index db")
    return res


def rewrite_processing_batches(db, data):
    """Insert or rewrite batched data"""
    for batch_id, texts_from, texts_to in data:
        db.execute("delete from processing_from where batch_id=:batch_id", {
            "batch_id": batch_id})
        db.executemany(
            f"insert into processing_from(batch_id, text_ids, initial_id, text) values (?,?,?,?)", [(batch_id, a, b, c) for a, b, c in texts_from])
        db.execute("delete from processing_to where batch_id=:batch_id", {
            "batch_id": batch_id})
        db.executemany(
            f"insert into processing_to(batch_id, text_ids, initial_id, text) values (?,?,?,?)", [(batch_id, a, b, c) for a, b, c in texts_to])
    update_batch_progress(db, batch_id)


def update_batch_progress(db, batch_id):
    """Update batches table with already processed batches IDs"""
    db.execute(
        "insert or ignore into batches (batch_id, insert_ts) values (?, datetime('now'))", (batch_id,))


def init_document_db(db_path):
    """Init document database (alignment) with tables structure"""
    if os.path.isfile(db_path):
        os.remove(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute(
            'create table splitted_from(id integer primary key, text nvarchar, exclude integer, paragraph integer)')
        db.execute(
            'create table splitted_to(id integer primary key, text nvarchar, exclude integer, paragraph integer)')
        db.execute(
            'create table proxy_from(id integer primary key, text nvarchar)')
        db.execute('create table proxy_to(id integer primary key, text nvarchar)')
        db.execute(
            'create table processing_from(id integer primary key, batch_id integer, text_ids varchar, initial_id integer, text nvarchar)')
        db.execute(
            'create table processing_to(id integer primary key, batch_id integer, text_ids varchar, initial_id integer, text nvarchar)')
        db.execute(
            'create table doc_index(id integer primary key, contents varchar)')
        db.execute(
            'create table batches(id integer primary key, batch_id integer unique, insert_ts text)')


def fill_db_from_files(db_path, splitted_from, splitted_to, proxy_from, proxy_to):
    """Fill document database (alignment) with prepared document lines"""
    if not os.path.isfile(db_path):
        logging.info(f"Initializing database {db_path}")
        init_document_db(db_path)
    lines = []
    if os.path.isfile(splitted_from):
        with open(splitted_from, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany("insert into splitted_from(text, exclude) values (?,?)", [
                           (x.strip(), 0) for x in lines])

    if os.path.isfile(splitted_to):
        with open(splitted_to, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany("insert into splitted_to(text, exclude) values (?,?)", [
                           (x.strip(), 0) for x in lines])

    if os.path.isfile(proxy_from):
        with open(proxy_from, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany("insert into proxy_from(text) values (?)", [
                           (x.strip(),) for x in lines])

    if os.path.isfile(proxy_to):
        with open(proxy_to, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany("insert into proxy_to(text) values (?)", [
                           (x.strip(),) for x in lines])


def fill_db(db_path, splitted_from=[], splitted_to=[], proxy_from=[], proxy_to=[]):
    """Fill document database (alignment) with prepared document lines"""
    if not os.path.isfile(db_path):
        logging.info(f"Initializing database {db_path}")
        init_document_db(db_path)
    if len(splitted_from) > 0:
        splitted_from = handle_paragraph_marks(
            splitted_from, mark=splitter.PARAGRAPH_MARK)
        with sqlite3.connect(db_path) as db:
            db.executemany("insert into splitted_from(text, exclude, paragraph) values (?,?,?)", [
                           (x.strip(), 0, paragraph) for x, paragraph in splitted_from])
    if len(splitted_to) > 0:
        splitted_to = handle_paragraph_marks(
            splitted_to, mark=splitter.PARAGRAPH_MARK)
        with sqlite3.connect(db_path) as db:
            db.executemany("insert into splitted_to(text, exclude, paragraph) values (?,?,?)", [
                           (x.strip(), 0, paragraph) for x, paragraph in splitted_to])
    if len(proxy_from) > 0:
        with sqlite3.connect(db_path) as db:
            db.executemany("insert into proxy_from(text) values (?)", [
                           (x.strip(),) for x in proxy_from])
    if len(proxy_to) > 0:
        with sqlite3.connect(db_path) as db:
            db.executemany("insert into proxy_to(text) values (?)", [
                           (x.strip(),) for x in proxy_to])


def handle_paragraph_marks(lines, mark):
    res = []
    par_count = 0
    for line in lines:
        if line.endswith((mark+".", mark+"!", mark+"?")):
            par_count += 1
            line = line.replace(mark, "")
        res.append((line, par_count))
    return res
