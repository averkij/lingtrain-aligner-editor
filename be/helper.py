"""Misc helper functions"""

import glob
import json
import logging
import os
import pathlib
import pickle
import sqlite3
import sys
import uuid
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


def get_processing_list_with_state(username, lang_from, lang_to):
    """Get processing docs list with states"""
    res = []
    for guid, name, guid_from, guid_to, state_code, done_batches, total_batches in get_alignments_list(username, lang_from, lang_to):
        res.append({
            "guid": guid,
            "name": name,
            "guid_from": guid_from,
            "guid_to": guid_to,
            "state": (state_code, total_batches, done_batches),
            "imgs": get_files_list(os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username), mask=f"{guid}.best_*.png"),
            # "sim_grades": get_sim_grades(file)
        })
    return res


def get_raw_files(username, lang_code):
    """Get uploaded raw files list"""
    res = []
    for file, guid, _ in get_documents_list(username, lang_code):
        res.append({
            "name": file,
            "guid": guid,
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


def init_document_db(db_path):
    """Init document database (alignment) with tables structure"""
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
            'create table processing_from(id integer primary key, batch_id integer, text_ids varchar, initial_id integer, text nvarchar)')
        db.execute(
            'create table processing_to(id integer primary key, batch_id integer, text_ids varchar, initial_id integer, text nvarchar)')
        db.execute(
            'create table doc_index(id integer primary key, contents varchar)')


def fill_document_db(db_path, splitted_from, splitted_to, proxy_from, proxy_to):
    """Fill document database (alignment) with prepared document lines"""
    lines = []
    if os.path.isfile(splitted_from):
        with open(splitted_from, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany("insert into splitted_from(text) values (?)", [
                           (x.strip(),) for x in lines])

    if os.path.isfile(splitted_to):
        with open(splitted_to, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany("insert into splitted_to(text) values (?)", [
                           (x.strip(),) for x in lines])

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


def get_flatten_doc_index(db_path):
    """Get document index"""
    res = []
    try:
        with sqlite3.connect(db_path) as db:
            cur = db.execute('SELECT contents FROM doc_index')
            data = json.loads(cur.fetchone()[0])
        for _, sub_index in enumerate(data):
            res.extend(list(zip(sub_index, range(len(sub_index)))))
    except:
        logging.warning("can not fetch flatten index")
    return res


def get_clear_flatten_doc_index(db_path):
    """Get document index"""
    res = []
    try:
        with sqlite3.connect(db_path) as db:
            cur = db.execute('SELECT contents FROM doc_index')
            data = json.loads(cur.fetchone()[0])
        for _, sub_index in enumerate(data):
            res.extend(sub_index)
    except:
        logging.warning("can not fetch flatten index")
    return res


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


def add_empty_processing_line(db, batch_id):
    """Add empty processing line"""
    from_id = db.execute('insert into processing_from(batch_id, text_ids, text) values (:batch_id, :text_ids, :text) ', {
                         "batch_id": batch_id, "text_ids": "[]", "text": ''}).lastrowid
    to_id = db.execute('insert into processing_to(batch_id, text_ids, text) values (:batch_id, :text_ids, :text) ', {
                       "batch_id": batch_id, "text_ids": "[]", "text": ''}).lastrowid
    return (from_id, to_id)


def get_doc_page(db_path, text_ids):
    """Get processing lines page"""
    res = []
    with sqlite3.connect(db_path) as db:
        db.execute('DROP TABLE If EXISTS temp.text_ids')
        db.execute(
            'CREATE TEMP TABLE text_ids(rank integer primary key, id integer)')
        db.executemany('insert into temp.text_ids(id) values(?)', [
                       (x,) for x in text_ids])
        for batch_id, text_from, text_to, proxy_from, proxy_to in db.execute(
            '''SELECT
                f.batch_id, f.text, t.text, pf.text, pt.text
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
            res.append((text_from, text_to, proxy_from, proxy_to, batch_id))
    return res


def get_splitted_from_by_id(db_path, ids):
    """Get lines from splitted_from by ids"""
    res = []
    with sqlite3.connect(db_path) as db:
        for id, text_from, proxy_from in db.execute(
            f'select f.id, f.text, pf.text from splitted_from f left join proxy_from pf on pf.id = f.id where f.id in ({",".join([str(x) for x in ids])})'
        ):
            res.append((id, text_from, proxy_from))
    return res


def get_splitted_to_by_id(db_path, ids):
    """Get lines from splitted_to by ids"""
    res = []
    with sqlite3.connect(db_path) as db:
        for id, text_to, proxy_to in db.execute(
            f'select t.id, t.text, pt.text from splitted_to t left join proxy_to pt on pt.id = t.id where t.id in ({",".join([str(x) for x in ids])})'
        ):
            res.append((id, text_to, proxy_to))
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


def init_user_db(username):
    """Init user database with tables structure"""
    pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username)
                 ).mkdir(parents=True, exist_ok=True)
    db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)
    if not os.path.isfile(db_path):
        logging.info(f"creating user db: {db_path}")
        with sqlite3.connect(db_path) as db:
            db.execute(
                'create table documents(id integer primary key, guid varchar, lang varchar, name varchar)')
            db.execute(
                'create table alignments(id integer primary key, guid varchar, guid_from varchar, guid_to varchar, name varchar, state integer, curr_batches integer, total_batches integer)')


def alignment_exists(username, guid_from, guid_to):
    """Check if alignment already exists"""
    db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)
    with sqlite3.connect(db_path) as db:
        cur = db.execute("select * from alignments where guid_from=:guid_from and guid_to=:guid_to", {
                         "guid_from": guid_from, "guid_to": guid_to})
        return bool(cur.fetchone())


def register_alignment(username, guid, guid_from, guid_to, name, total_batches):
    """Register new alignment in database"""
    db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)
    if not alignment_exists(username,  guid_from, guid_to):
        with sqlite3.connect(db_path) as db:
            db.execute('insert into alignments(guid, guid_from, guid_to, name, state, curr_batches, total_batches) values (:guid, :guid_from, :guid_to, :name, 2, 0, :total_batches) ', {
                       "guid": guid, "guid_from": guid_from, "guid_to": guid_to, "name": name, "total_batches": total_batches})
    return


def get_alignment_id(username, guid_from, guid_to):
    """Return alignment id"""
    db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)
    with sqlite3.connect(db_path) as db:
        res = db.execute("select guid from alignments where guid_from=:guid_from and guid_to=:guid_to", {
                         "guid_from": guid_from, "guid_to": guid_to}).fetchone()
        return res[0] if res else None


def update_alignment_state(user_db_path, guid_from, guid_to, state, curr_batches=None, total_batches=None):
    """Update alignment state"""
    with sqlite3.connect(user_db_path) as db:
        if curr_batches and curr_batches >= 0 and total_batches:
            logging.info(
                f"updating alignment state total_batches {total_batches} curr_batches {curr_batches} state {state}")
            db.execute('update alignments set state=:state, curr_batches=:curr_batches, total_batches=:total_batches where guid_from=:guid_from and guid_to=:guid_to', {
                "guid_from": guid_from, "guid_to": guid_to, "state": state, "curr_batches": curr_batches, "total_batches": total_batches})
        else:
            db.execute('update alignments set state=:state where guid_from=:guid_from and guid_to=:guid_to', {
                "guid_from": guid_from, "guid_to": guid_to, "state": state})


def increment_alignment_state(user_db_path, guid_from, guid_to, state):
    """Increment alignment progress"""
    with sqlite3.connect(user_db_path) as db:
        curr_batches, total_batches = db.execute("select curr_batches, total_batches from alignments where guid_from=:guid_from and guid_to=:guid_to", {
            "guid_from": guid_from, "guid_to": guid_to}).fetchone()

        print("curr_batches", curr_batches)
        curr_batches += 1

        db.execute('update alignments set state=:state, curr_batches=:curr_batches where guid_from=:guid_from and guid_to=:guid_to', {
            "guid_from": guid_from, "guid_to": guid_to, "state": state, "curr_batches": curr_batches})


def update_alignment_state_by_align_id(user_db_path, align_id, state):
    """Update alignment state"""
    with sqlite3.connect(user_db_path) as db:
        db.execute('update alignments set state=:state where guid=:guid', {
            "guid": align_id, "state": state})


def file_exists(username, lang, name):
    """Check if file already exists"""
    db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)
    with sqlite3.connect(db_path) as db:
        cur = db.execute("select * from documents where lang=:lang and name=:name", {
                         "lang": lang, "name": name})
        return bool(cur.fetchone())


def register_file(username, lang, name):
    """Register new file in database"""
    db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)
    guid = uuid.uuid4().hex
    with sqlite3.connect(db_path) as db:
        db.execute('insert into documents(guid, lang, name) values (:guid, :lang, :name) ', {
            "guid": guid, "lang": lang, "name": name})


def get_documents_list(username, lang=None):
    """Get documents list by language code"""
    db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)
    with sqlite3.connect(db_path) as db:
        if not lang:
            return db.execute("select name, guid, lang from documents").fetchall()
        else:
            return db.execute("select name, guid, lang from documents where lang=:lang", {
                "lang": lang}).fetchall()


def get_filename(username, guid):
    """Get filename by id"""
    filename = [x[0] for x in get_documents_list(
        username) if x[1] == guid]
    return filename[0] if filename else None


def get_fileinfo(username, guid):
    """Get file info by id"""
    filename = [(x[0], x[2]) for x in get_documents_list(
        username) if x[1] == guid]
    return filename[0] if filename else None


def get_alignment_info(username, guid):
    """Get alignment info by id"""
    db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)
    with sqlite3.connect(db_path) as db:
        return db.execute("select name, guid_from, guid_to, state, curr_batches, total_batches from alignments where guid=:guid", {"guid": guid}).fetchone()


def get_alignments_list(username, lang_from, lang_to):
    """Get alignments list by language code"""
    db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)
    print("fetching processing list", db_path)
    with sqlite3.connect(db_path) as db:
        res = db.execute("""select
                                a.guid, a.name, a.guid_from, a.guid_to, a.state, a.curr_batches, a.total_batches
                            from
                                alignments a
                                    join documents d_from on d_from.guid=a.guid_from
                                    join documents d_to on d_to.guid=a.guid_to
                            where
                                d_from.lang=:lang_from and d_to.lang=:lang_to""", {
                         "lang_from": lang_from, "lang_to": lang_to}).fetchall()
        return res


def get_doc_items(index_items, db_path):
    """Get document items by ids"""
    res = []
    for i, (data, texts) in enumerate(zip(index_items, get_doc_page(db_path, [x[0][0][0] for x in index_items]))):
        res.append({
            "index_id": data[1],  # absolute position in index
            # from
            "batch_id": texts[4],
            "batch_index_id": data[0][1],    # relative position in index batch
            "text_from": texts[0],
            "line_id_from": data[0][0][1],  # array with ids
            # primary key in DB (processing_from)
            "processing_from_id": data[0][0][0],
            "proxy_from": texts[2],
            # to
            "text_to": texts[1],
            "line_id_to": data[0][0][3],  # array with ids
            # primary key in DB (processing_to)
            "processing_to_id": data[0][0][2],
            "proxy_to": texts[3],
        })
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


def get_batch_intersected(iter1, iter2, batch_ids, n=config.DEFAULT_BATCHSIZE, window=config.DEFAULT_WINDOW):
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
        if counter in batch_ids:
            yield iter1[ndx:min(ndx + n, l1)], \
                iter2[max(0, kdx - window):min(kdx + k + window, l2)], \
                list(range(ndx, min(ndx + n, l1))), \
                list(range(max(0, kdx - window), min(kdx + k + window, l2))), \
                counter
        counter += 1


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
