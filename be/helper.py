import os
import sys
import constants as con
import pathlib
import pickle
import glob
import state_manager as state
import logging
from warnings import simplefilter
import sqlite3
import json

def get_files_list(folder, mask="*.txt"):
    return [os.path.basename(x) for x in get_files_list_with_path(folder, mask)]

def get_files_list_with_path(folder, mask="*.txt"):
    if not os.path.isdir(folder):
        return []
    return glob.glob("{0}/{1}".format(folder,mask))

def get_processing_list_with_state(folder, username):
    res = []
    for file in get_files_list_with_path(folder):
        res.append({
            "name": os.path.basename(file),
            "state": state.get_processing_state(file, (con.PROC_DONE,0,0)),
            "imgs": get_files_list(os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username), mask=f"{os.path.basename(file)}.best_*.png"),
            "sim_grades": get_sim_grades(file)
            })
    return res

def get_raw_files(folder, username, lang_code):
    res = []
    for file in get_files_list(folder):
        print(os.path.join(con.UPLOAD_FOLDER, username, con.PROXY_FOLDER, lang_code, file))
        res.append({
            "name": file,
            "has_proxy": os.path.isfile(os.path.join(con.UPLOAD_FOLDER, username, con.PROXY_FOLDER, lang_code, file))
        })
    return res

def get_sim_grades(processing_file):
    docs = pickle.load(open(processing_file, "rb"))
    return docs["sim_grades"]
    
def clean_img_user_foler(username, file):
    imgs = get_files_list_with_path(os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username), mask=f"{os.path.basename(file)}.best_*.png")
    for img in imgs:
        if os.path.isfile(img):
            os.remove(img)

def create_folders(username, lang):
    if username and lang:
        pathlib.Path(os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.RAW_FOLDER, lang)).mkdir(parents=True, exist_ok=True)    
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.PROXY_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.NGRAM_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.DONE_FOLDER, lang)).mkdir(parents=True, exist_ok=True)

def init_db(username, db_path):
    print("init database:", db_path)
    if os.path.isfile(db_path):
        os.remove(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute('create table splitted_from(id integer primary key, text nvarchar)')
        db.execute('create table splitted_to(id integer primary key, text nvarchar)')
        db.execute('create table proxy_from(id integer primary key, text nvarchar)')
        db.execute('create table proxy_to(id integer primary key, text nvarchar)')
        db.execute('create table processing_from(id integer primary key, text_ids varchar, initial_id integer, text nvarchar)')
        db.execute('create table processing_to(id integer primary key, text_ids varchar, initial_id integer, text nvarchar)')
        db.execute('create table doc_index(id integer primary key, contents varchar)')

def fill_db(db_path, splitted_from, splitted_to, proxy_from, proxy_to):
    lines = []
    if os.path.isfile(splitted_from):
        with open(splitted_from, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany(f"insert into splitted_from(text) values (?)", [(x.strip(),) for x in lines])

    if os.path.isfile(splitted_to):
        with open(splitted_to, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany(f"insert into splitted_to(text) values (?)", [(x.strip(),) for x in lines])

    if os.path.isfile(proxy_from):
        with open(proxy_from, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany(f"insert into proxy_from(text) values (?)", [(x.strip(),) for x in lines])

    if os.path.isfile(proxy_to):
        with open(proxy_to, mode="r", encoding="utf-8") as input_path:
            lines = input_path.readlines()
        with sqlite3.connect(db_path) as db:
            db.executemany(f"insert into proxy_to(text) values (?)", [(x.strip(),) for x in lines])

def create_doc_index(db_path):
    doc_index = []
    logging.info(f"creating index for {db_path}")

    with sqlite3.connect(db_path) as db:
        for x in db.execute('SELECT f.id, f.text_ids, t.id, t.text_ids FROM processing_from f join processing_to t on f.id=t.id order by f.id'):
            doc_index.append(x)
        db.execute('insert into doc_index(contents) values (?)', [json.dumps(doc_index)])
        
    logging.info(f"index successfully created for {db_path}")

def get_doc_index(db_path):
    res = []
    try:
        with sqlite3.connect(db_path) as db:
            cur = db.execute('SELECT contents FROM doc_index')
            res = json.loads(cur.fetchone()[0])
    except:
        logging.error("can not fetch index")
    return res

def update_doc_index(db, index):
    index = json.dumps(index)
    db.execute('update doc_index set contents = ?', [index])

def get_processing_text(db_path, text_type, processing_id):
    res = ("",)
    with sqlite3.connect(db_path) as db:
        if text_type == con.TYPE_FROM:
            cur = db.execute('select text from processing_from where id = :id', {"id": processing_id})
        else:
            cur = db.execute('select text from processing_to where id = :id', {"id": processing_id})
        res = (cur.fetchone())
    return res

def update_processing(db, text_type, processing_id, text_ids, text_to_update):
    if text_type == con.TYPE_FROM:
        db.execute('update processing_from set text_ids = :text_ids, text = :text where id = :id', \
            {"text_ids":text_ids, "text":text_to_update, "id":processing_id})
    else:            
        db.execute('update processing_to set text_ids = :text_ids, text = :text where id = :id', \
            {"text_ids":text_ids, "text":text_to_update, "id":processing_id})

def clear_processing(db, text_type, processing_id):
    if text_type == con.TYPE_FROM:
        db.execute('update processing_from set text_ids = "[]", text = "", initial_id = NULL where id = :id', \
            {"id":processing_id})
    else:            
        db.execute('update processing_to set text_ids = "[]", text = "", initial_id = NULL where id = :id', \
            {"id":processing_id})

def add_empty_processing_line(db):
    from_id = db.execute('insert into processing_from(text_ids, text) values (:text_ids, :text) ', {"text_ids":"[]", "text":''}).lastrowid
    to_id = db.execute('insert into processing_to(text_ids, text) values (:text_ids, :text) ', {"text_ids":"[]", "text":''}).lastrowid
    return (from_id, to_id)

def get_doc_page(db_path, page):
    res = []

    # print("> page", page)

    with sqlite3.connect(db_path) as db:
        db.execute('DROP TABLE If EXISTS temp.text_ids')
        db.execute('CREATE TEMP TABLE text_ids(rank integer primary key, id integer)')
        db.executemany('insert into temp.text_ids(id) values(?)', [(x[0],) for x in page])
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

def get_candidates_page(db_path, start_id, end_id):
    res = []

    with sqlite3.connect(db_path) as db:
        for id, splitted_to, proxy_to in db.execute(
        '''SELECT
                t.id, t.text, pt.text
            FROM
                splitted_to t
                left join
                    proxy_to pt
                        on pt.id=t.id
            WHERE
                t.id > :start_id and t.id < :end_id
            ''', { "start_id": start_id, "end_id": end_id }
            ):
            res.append((id, splitted_to, proxy_to))

    return res

def get_texts_length(db_path):
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
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True) 

def check_file(folder, files, file_id):
    if len(files) < file_id+1:
        logging.debug(f"Document with id={file_id} not found. folder: {folder}")
        return False
    processing_file = os.path.join(folder, files[file_id])
    if not os.path.isfile(processing_file):
        logging.debug(f"Document {processing_file} not found.")
        return False
    return True

def get_batch(iter1, iter2, iter3, n):
    l1 = len(iter1)
    l3 = len(iter3)
    k = int(round(n * l3/l1))    
    kdx = 0 - k
    for ndx in range(0, l1, n):
        kdx += k
        yield iter1[ndx:min(ndx + n, l1)], iter2[kdx:min(kdx + k, l3)], iter3[kdx:min(kdx + k, l3)]

def get_batch_intersected(iter1, iter2, n, window):
    l1 = len(iter1)
    l2 = len(iter2)
    k = int(round(n * l2/l1))
    kdx = 0 - k

    if k<window*2:
        #subbatches will be intersected
        logging.warning(f"Batch for the second language is too small. k = {k}, window = {window}")

    for ndx in range(0, l1, n):
        kdx += k
        yield iter1[ndx:min(ndx + n, l1)], \
        iter2[max(0,kdx - window):min(kdx + k + window, l2)], \
        list(range(ndx, min(ndx + n, l1))), \
        list(range(max(0,kdx - window), min(kdx + k + window, l2)))

def get_culture(langCode):
    if langCode in CULTURE_LIST:
        return CULTURE_LIST[langCode]
    return CULTURE_LIST[DEFAULT_CULTURE]

CULTURE_LIST = {
    "en": "en-US",
    "zh": "zh-CN",
    "ru": "ru-RU",
    "de": "de-DE"
}
DEFAULT_CULTURE = "en"

def read_processing(input_file):
    docs = pickle.load(open(input_file, "rb"))
    for doc in docs["items"]:
        for line in doc:
            yield line, doc[line]["from"], doc[line]["to"], doc[line]["cnd"]

def tryParseInt(value):
    try:
        return int(value), True
    except ValueError:
        return value, False

def parseJsonArray(str):
    if not str: return []
    try:
        return json.loads(str)
    except:
        return []

def configure_logging(level=logging.INFO):
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    simplefilter(action='ignore', category=FutureWarning)
    # logging.basicConfig(level=level, filename='app.log', filemode='a', format='%(asctime)s [%(levelname)s] - %(process)d: %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logging.basicConfig(stream=sys.stdout, level=level, filemode='a', format='%(asctime)s [%(levelname)s] - %(process)d: %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logging.getLogger('matplotlib.font_manager').disabled = True

#attribute
def lazy_property(fn):
    attr_name = '_lazy_' + fn.__name__
    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazy_property