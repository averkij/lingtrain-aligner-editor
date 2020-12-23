"""Misc helper functions"""

import glob
import json
import logging
import os
import pathlib
import pickle
import sqlite3
import sys
from warnings import simplefilter

import config
import constants as con
import state_manager as state


def get_files_list(folder, mask="*.txt"):
    """Get file names list by mask"""
    return [os.path.basename(x) for x in get_files_list_with_path(folder, mask)]


def get_files_list_with_path(folder, mask="*.txt"):
    """Get file paths list by mask"""
    if not os.path.isdir(folder):
        return []
    return glob.glob("{0}/{1}".format(folder, mask))


def get_processing_list_with_state(folder, username):
    """Get processing docs list with states"""
    res = []
    for file in get_files_list_with_path(folder, mask="*.db"):
        res.append({
            "name": os.path.basename(file),
            "state": state.get_processing_state(file, (con.PROC_DONE, 0, 0)),
            "imgs": get_files_list(os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username), mask=f"{os.path.basename(file)}.best_*.png"),
            # "sim_grades": get_sim_grades(file)
        })
    return res


def get_raw_files(folder, username, lang_code):
    """Get files from the raw folder"""
    res = []
    for file in get_files_list(folder):
        print(os.path.join(con.UPLOAD_FOLDER, username,
                           con.PROXY_FOLDER, lang_code, file))
        res.append({
            "name": file,
            "has_proxy": os.path.isfile(os.path.join(con.UPLOAD_FOLDER, username, con.PROXY_FOLDER, lang_code, file))
        })
    return res


def get_sim_grades(processing_file):
    """Get saved similarity grades"""
    docs = pickle.load(open(processing_file, "rb"))
    return docs["sim_grades"]


def clean_img_user_foler(username, file):
    """Clean user folder with images"""
    imgs = get_files_list_with_path(os.path.join(
        con.STATIC_FOLDER, con.IMG_FOLDER, username), mask=f"{os.path.basename(file)}.best_*.png")
    for img in imgs:
        if os.path.isfile(img):
            os.remove(img)


def create_folders(username, lang):
    """Create folders for a new user"""
    if username and lang:
        pathlib.Path(os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username)).mkdir(
            parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username,
                                  con.RAW_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username,
                                  con.SPLITTED_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username,
                                  con.PROXY_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username,
                                  con.NGRAM_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username,
                                  con.PROCESSING_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username,
                                  con.DONE_FOLDER, lang)).mkdir(parents=True, exist_ok=True)


def init_db(db_path):
    """Init database with tables structure"""

    print("init database:", db_path)
    if os.path.isfile(db_path):
        os.remove(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute(
            'create table splitted_from(id integer primary key, text nvarchar)')
        db.execute(
            'create table splitted_to(id integer primary key, text nvarchar)')
        db.execute(
            'create table proxy_from(id integer primary key, text nvarchar)')
        db.execute('create table proxy_to(id integer primary key, text nvarchar)')
        db.execute(
            'create table processing_from(id integer primary key, text_ids varchar, initial_id integer, text nvarchar)')
        db.execute(
            'create table processing_to(id integer primary key, text_ids varchar, initial_id integer, text nvarchar)')
        db.execute(
            'create table doc_index(id integer primary key, contents varchar)')


def fill_db(db_path, splitted_from, splitted_to, proxy_from, proxy_to):
    """Fill database with prepared document lines"""
    lines = []
    if os.path.isfile(splitted_from):
        with open(splitted_from, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany(f"insert into splitted_from(text) values (?)", [
                           (x.strip(),) for x in lines])

    if os.path.isfile(splitted_to):
        with open(splitted_to, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany(f"insert into splitted_to(text) values (?)", [
                           (x.strip(),) for x in lines])

    if os.path.isfile(proxy_from):
        with open(proxy_from, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany(f"insert into proxy_from(text) values (?)", [
                           (x.strip(),) for x in lines])

    if os.path.isfile(proxy_to):
        with open(proxy_to, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany(f"insert into proxy_to(text) values (?)", [
                           (x.strip(),) for x in lines])


def create_doc_index(db):
    """Create document index in database in the end of alignment"""
    doc_index = []
    for x in db.execute('SELECT f.id, f.text_ids, t.id, t.text_ids FROM processing_from f join processing_to t on f.id=t.id order by f.id'):
        doc_index.append(x)

    db.execute('insert into doc_index(contents) values (?)',
               [json.dumps(doc_index)])


def get_doc_index(db_path):
    """Get document index"""
    res = []
    try:
        with sqlite3.connect(db_path) as db:
            cur = db.execute('SELECT contents FROM doc_index')
            res = json.loads(cur.fetchone()[0])
    except:
        logging.warning("can not fetch index")
    return res


def update_doc_index(db, index):
    """Update document index"""
    index = json.dumps(index)
    db.execute('update doc_index set contents = ?', [index])


def get_processing_text(db_path, text_type, processing_id):
    """Get processing document line"""
    res = ("",)
    with sqlite3.connect(db_path) as db:
        if text_type == con.TYPE_FROM:
            cur = db.execute('select text from processing_from where id = :id', {
                             "id": processing_id})
        else:
            cur = db.execute('select text from processing_to where id = :id', {
                             "id": processing_id})
        res = (cur.fetchone())
    return res


def get_candidates_page(db_path, text_type, id_from, id_to):
    """Get splitted lines page"""
    res = []
    with sqlite3.connect(db_path) as db:
        if text_type == con.TYPE_FROM:
            for id, splitted, proxy in db.execute(
                '''SELECT
                    sf.id, sf.text, pf.text
                FROM
                    splitted_from sf
                    left join
                        proxy_from pf
                            on pf.id=sf.id
                WHERE
                    sf.id >= :id_from and sf.id <= :id_to
                ''', {"id_from": id_from, "id_to": id_to}
            ):
                res.append({"id": id, "text": splitted, "proxy": proxy})
        elif text_type == con.TYPE_TO:
            for id, splitted, proxy in db.execute(
                '''SELECT
                    st.id, st.text, pt.text
                FROM
                    splitted_to st
                    left join
                        proxy_to pt
                            on pt.id=st.id
                WHERE
                    st.id >= :id_from and st.id <= :id_to
                ''', {"id_from": id_from, "id_to": id_to}
            ):
                res.append({"id": id, "text": splitted, "proxy": proxy})
    return res


def update_processing(db, text_type, processing_id, text_ids, text_to_update):
    """Update processing line"""
    if text_type == con.TYPE_FROM:
        db.execute('update processing_from set text_ids = :text_ids, text = :text where id = :id',
                   {"text_ids": text_ids, "text": text_to_update, "id": processing_id})
    else:
        db.execute('update processing_to set text_ids = :text_ids, text = :text where id = :id',
                   {"text_ids": text_ids, "text": text_to_update, "id": processing_id})


def clear_processing(db, text_type, processing_id):
    """Clear processing line"""
    if text_type == con.TYPE_FROM:
        db.execute('update processing_from set text_ids = "[]", text = "", initial_id = NULL where id = :id',
                   {"id": processing_id})
    else:
        db.execute('update processing_to set text_ids = "[]", text = "", initial_id = NULL where id = :id',
                   {"id": processing_id})


def add_empty_processing_line(db):
    """Add empty processing line"""
    from_id = db.execute('insert into processing_from(text_ids, text) values (:text_ids, :text) ', {
                         "text_ids": "[]", "text": ''}).lastrowid
    to_id = db.execute('insert into processing_to(text_ids, text) values (:text_ids, :text) ', {
                       "text_ids": "[]", "text": ''}).lastrowid
    return (from_id, to_id)


def get_doc_page(db_path, page):
    """Get processing lines page"""
    res = []
    with sqlite3.connect(db_path) as db:
        db.execute('DROP TABLE If EXISTS temp.text_ids')
        db.execute(
            'CREATE TEMP TABLE text_ids(rank integer primary key, id integer)')
        db.executemany('insert into temp.text_ids(id) values(?)', [
                       (x[0],) for x in page])
        for text_from, text_to, proxy_from, proxy_to in db.execute(
            '''SELECT
                f.text, t.text, pf.text, pt.text
            FROM
                processing_from f
                join
                    processing_to t
                        on t.id=f.id
                left join
                    proxy_from pf
                        on pf.id=f.initial_id
                left join
                    proxy_to pt
                        on pt.id=t.initial_id
                join
                    temp.text_ids ti
                        on ti.id = f.id
            ORDER BY
                ti.rank
            '''
        ):
            res.append((text_from, text_to, proxy_from, proxy_to))
    return res


def get_texts_length(db_path):
    """Get splitted lines count"""
    res = []

    with sqlite3.connect(db_path) as db:
        cur = db.execute(
            '''SELECT
                (select count(*) as len1 from splitted_from),
                (select count(*) as len2 from splitted_to)
            '''
        )
        res = (cur.fetchone())
    return res


def check_folder(folder):
    """Check if folder exists"""
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)


def check_file(folder, files, file_id):
    """Check if file exists"""
    if len(files) < file_id+1:
        logging.debug(
            f"Document with id={file_id} not found. folder: {folder}")
        return False
    processing_file = os.path.join(folder, files[file_id])
    if not os.path.isfile(processing_file):
        logging.debug(f"Document {processing_file} not found.")
        return False
    return True


def get_batch(iter1, iter2, iter3, n):
    """Get batch"""
    l1 = len(iter1)
    l3 = len(iter3)
    k = int(round(n * l3/l1))
    kdx = 0 - k
    for ndx in range(0, l1, n):
        kdx += k
        yield iter1[ndx:min(ndx + n, l1)], iter2[kdx:min(kdx + k, l3)], iter3[kdx:min(kdx + k, l3)]


def get_batch_intersected(iter1, iter2, n=config.DEFAULT_BATCHSIZE, window=config.DEFAULT_WINDOW):
    """Get batch with an additional window"""
    l1 = len(iter1)
    l2 = len(iter2)
    k = int(round(n * l2/l1))
    kdx = 0 - k

    if k < window*2:
        # subbatches will be intersected
        logging.warning(
            f"Batch for the second language is too small. k = {k}, window = {window}")

    for ndx in range(0, l1, n):
        kdx += k
        yield iter1[ndx:min(ndx + n, l1)], \
            iter2[max(0, kdx - window):min(kdx + k + window, l2)], \
            list(range(ndx, min(ndx + n, l1))), \
            list(range(max(0, kdx - window), min(kdx + k + window, l2)))


def get_culture(lang_code):
    """Get language culture"""
    if lang_code in con.CULTURE_LIST:
        return con.CULTURE_LIST[lang_code]
    return con.CULTURE_LIST[con.DEFAULT_CULTURE]


def try_parse_int(value):
    """Try parse int"""
    try:
        return int(value), True
    except ValueError:
        return value, False


def parse_json_array(json_str):
    """Parse JSON string array"""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except:
        return []


def configure_logging(level=logging.INFO):
    """"Configure logging module"""
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    simplefilter(action='ignore', category=FutureWarning)
    # logging.basicConfig(level=level, filename='app.log', filemode='a', format='%(asctime)s [%(levelname)s] - %(process)d: %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logging.basicConfig(stream=sys.stdout, level=level, filemode='a',
                        format='%(asctime)s [%(levelname)s] - %(process)d: %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logging.getLogger('matplotlib.font_manager').disabled = True


def lazy_property(func):
    """"Lazy initialization attribute"""
    attr_name = '_lazy_' + func.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    return _lazy_property
