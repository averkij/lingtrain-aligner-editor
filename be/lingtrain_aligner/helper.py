import json
import logging
import sqlite3
from collections import defaultdict


def get_doc_index_original(db_path):
    """Get document index"""
    res = []
    try:
        with sqlite3.connect(db_path) as db:
            cur = db.execute('SELECT contents FROM doc_index')
            res = json.loads(cur.fetchone()[0])
    except:
        logging.warning("can not fetch index db")
    return res


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


def get_flatten_doc_index_with_batch_id(db_path):
    """Get document index"""
    res = []
    try:
        with sqlite3.connect(db_path) as db:
            cur = db.execute('SELECT contents FROM doc_index')
            data = json.loads(cur.fetchone()[0])
        for batch_id, sub_index in enumerate(data):
            res.extend(
                list(zip(sub_index, range(len(sub_index)), [batch_id]*len(sub_index))))
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


def add_empty_processing_line(db, batch_id):
    """Add empty processing line"""
    from_id = db.execute('insert into processing_from(batch_id, text_ids, text) values (:batch_id, :text_ids, :text) ', {
                         "batch_id": batch_id, "text_ids": "[]", "text": ''}).lastrowid
    to_id = db.execute('insert into processing_to(batch_id, text_ids, text) values (:batch_id, :text_ids, :text) ', {
                       "batch_id": batch_id, "text_ids": "[]", "text": ''}).lastrowid
    return (from_id, to_id)


def add_resolved_processing_line(db, batch_id, text_from, text_to):
    """Add processing line with text"""
    from_id = db.execute('insert into processing_from(batch_id, text_ids, text) values (:batch_id, :text_ids, :text) ', {
                         "batch_id": batch_id, "text_ids": "[]", "text": text_from}).lastrowid
    to_id = db.execute('insert into processing_to(batch_id, text_ids, text) values (:batch_id, :text_ids, :text) ', {
                       "batch_id": batch_id, "text_ids": "[]", "text": text_to}).lastrowid
    return (from_id, to_id)


def get_processing_from_by_id(db_path, start_id, end_id):
    """Get lines from processing by ids"""
    ids = [x for x in range(start_id, end_id + 1)]
    res = []
    with sqlite3.connect(db_path) as db:
        for id, text_from in db.execute(
            f'select f.id, f.text from processing_from f where f.id in ({",".join([str(x) for x in ids])})'
        ):
            res.append((id, text_from))
    return res


def get_processing_to_by_id(db_path, start_id, end_id):
    """Get lines from processing by ids"""
    ids = [x for x in range(start_id, end_id + 1)]
    res = []
    with sqlite3.connect(db_path) as db:
        for id, text_to, similarity in db.execute(
            f'select t.id, t.text, t.similarity from processing_to t where t.id in ({",".join([str(x) for x in ids])})'
        ):
            res.append((id, text_to, similarity))
    return res


def get_splitted_from_by_id(db_path, ids):
    """Get lines from splitted_from by ids"""
    res = []
    with sqlite3.connect(db_path) as db:
        for id, text_from, proxy_from, exclude in db.execute(
            f'select f.id, f.text, f.proxy_text, f.exclude from splitted_from f where f.id in ({",".join([str(x) for x in ids])})'
        ):
            res.append((id, text_from, proxy_from, exclude))
    return res


def get_splitted_to_by_id(db_path, ids):
    """Get lines from splitted_to by ids"""
    res = []
    with sqlite3.connect(db_path) as db:
        for id, text_to, proxy_to, exclude in db.execute(
            f'select t.id, t.text, t.proxy_text, t.exclude from splitted_to t where t.id in ({",".join([str(x) for x in ids])})'
        ):
            res.append((id, text_to, proxy_to, exclude))
    return res


def get_splitted_from_by_id_range(db_path, start_id, end_id):
    """Get lines from splitted_from by ids"""
    ids = [x for x in range(start_id, end_id + 1)]
    res = defaultdict(int)
    with sqlite3.connect(db_path) as db:
        for id, text_from, proxy_from in db.execute(
            f'select f.id, f.text, f.proxy_text from splitted_from f where f.id in ({",".join([str(x) for x in ids])})'
        ):
            res[id] = text_from
    return res


def get_splitted_to_by_id_range(db_path, start_id, end_id):
    """Get lines from splitted_to by ids"""
    ids = [x for x in range(start_id, end_id + 1)]
    res = defaultdict(int)
    with sqlite3.connect(db_path) as db:
        for id, text_to, proxy_to in db.execute(
            f'select t.id, t.text, t.proxy_text from splitted_to t where t.id in ({",".join([str(x) for x in ids])})'
        ):
            res[id] = text_to
    return res


def get_doc_page(db_path, text_ids):
    """Get processing lines page"""
    res = []
    with sqlite3.connect(db_path) as db:
        db.execute('DROP TABLE If EXISTS temp.text_ids')
        db.execute(
            'CREATE TEMP TABLE text_ids(rank integer primary key, id integer)')
        db.executemany('insert into temp.text_ids(id) values(?)', [
                       (x,) for x in text_ids])
        for batch_id, text_from, text_to in db.execute(
            '''SELECT
                f.batch_id, f.text, t.text
            FROM
                processing_from f
                join
                    processing_to t
                        on t.id=f.id
                join
                    temp.text_ids ti
                        on ti.id = f.id
            ORDER BY
                ti.rank
            '''
        ):
            res.append((text_from, text_to, batch_id))
    return res


def get_proxy_dict(items):
    """Get proxy sentences as array"""
    res = dict()
    for item in items:
        res[item[0]] = item[2]
    return res


def get_doc_items(index_items, db_path):
    """Get document items by ids"""
    res = []

    from_ids, to_ids = set(), set()
    for item in index_items:
        from_ids.update(json.loads(item[0][0][1]))
        to_ids.update(json.loads(item[0][0][3]))

    splitted_from = get_splitted_from_by_id(db_path, from_ids)
    splitted_to = get_splitted_to_by_id(db_path, to_ids)

    for i, (data, texts) in enumerate(zip(index_items, get_doc_page(db_path, [x[0][0][0] for x in index_items]))):
        res.append({
            "index_id": data[1],  # absolute position in index
            # from
            "batch_id": texts[2],
            "batch_index_id": data[0][1],    # relative position in index batch
            "text_from": texts[0],
            "line_id_from": data[0][0][1],  # array with ids
            # primary key in DB (processing_from)
            "processing_from_id": data[0][0][0],
            "proxy_from_array": get_proxy_dict(splitted_from),
            # to
            "text_to": texts[1],
            "line_id_to": data[0][0][3],  # array with ids
            # primary key in DB (processing_to)
            "processing_to_id": data[0][0][2],
            "proxy_to_array": get_proxy_dict(splitted_to),
        })
    return res


def get_processing_from(db_path):
    """Get lines from processing_from"""
    with sqlite3.connect(db_path) as db:
        res = db.execute(
            f'select f.text from processing_from f order by f.id').fetchall()
    return [x[0] for x in res]


def get_processing_to(db_path):
    """Get lines from processing_to"""
    with sqlite3.connect(db_path) as db:
        res = db.execute(
            f'select t.text from processing_to t order by t.id').fetchall()
    return [x[0] for x in res]


def get_unique_variants(variants_ids):
    res = set()
    for variant_ids in variants_ids:
        for ids in variant_ids:
            res.add(ids)
    return res


def get_string(dic, ids):
    s = " ".join([dic[x] for x in ids])
    return s


def lazy_property(func):
    """"Lazy initialization attribute"""
    attr_name = '_lazy_' + func.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    return _lazy_property
