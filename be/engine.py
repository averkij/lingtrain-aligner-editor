"""Lingtrain alignment engine"""


import logging
import os
import sqlite3

import config
import model_dispatcher


def get_line_vectors(lines):
    """Calculate embedding of the string"""
    return model_dispatcher.models[config.MODEL].embed(lines)


# DATABASE HELPERS


def init_document_db(db_path):
    """Init document database (alignment) with tables structure"""
    if os.path.isfile(db_path):
        os.remove(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute(
            'create table splitted_from(id integer primary key, text nvarchar, exclude integer)')
        db.execute(
            'create table splitted_to(id integer primary key, text nvarchar, exclude integer)')
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


def fill_document_db(db_path, splitted_from, splitted_to, proxy_from, proxy_to):
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
