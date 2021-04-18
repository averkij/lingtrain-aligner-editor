import sqlite3

import constants as con
from lingtrain_aligner import helper


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


def switch_excluded_splitted_to(db_path, id):
    """Mark splitted_to line as unused"""
    with sqlite3.connect(db_path) as db:
        exclude = db.execute("select exclude from splitted_to where id=:id", {
            "id": id}).fetchone()
        if exclude:
            db.execute('update splitted_to set exclude=:exclude where id=:id', {
                "exclude": (exclude[0] + 1) % 2, "id": id})
    return


def switch_excluded_splitted_from(db_path, id):
    """Mark splitted_from line as unused"""
    with sqlite3.connect(db_path) as db:
        exclude = db.execute("select exclude from splitted_from where id=:id", {
            "id": id}).fetchone()
        if exclude:
            db.execute('update splitted_from set exclude=:exclude where id=:id', {
                "exclude": (exclude[0] + 1) % 2, "id": id})
    return


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
                    sf.id, sf.text, sf.proxy_text
                FROM
                    splitted_from sf
                WHERE
                    sf.id >= :id_from and sf.id <= :id_to
                ''', {"id_from": id_from, "id_to": id_to}
            ):
                res.append({"id": id, "text": splitted, "proxy": proxy})
        elif text_type == con.TYPE_TO:
            for id, splitted, proxy in db.execute(
                '''SELECT
                    st.id, st.text, st.proxy_text
                FROM
                    splitted_to st
                WHERE
                    st.id >= :id_from and st.id <= :id_to
                ''', {"id_from": id_from, "id_to": id_to}
            ):
                res.append({"id": id, "text": splitted, "proxy": proxy})
    return res


def read_processing(db_path):
    """Read the processsing document"""
    ordered_text_ids = [x[0][0] for x in helper.get_flatten_doc_index(db_path)]
    with sqlite3.connect(db_path) as db:
        db.execute('DROP TABLE If EXISTS temp.dl_ids')
        db.execute(
            'CREATE TEMP TABLE dl_ids(rank integer primary key, id integer)')
        db.executemany('insert into temp.dl_ids(id) values(?)', [
                       (x,) for x in ordered_text_ids])
        return db.execute("""
            SELECT
                f.text, t.text
            FROM
                processing_from f
                join
                    processing_to t
                        on t.id=f.id
                join
                    temp.dl_ids ti
                        on ti.id = f.id
            ORDER BY
                ti.rank
                """).fetchall()
