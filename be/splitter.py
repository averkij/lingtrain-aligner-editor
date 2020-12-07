import os
import re
import razdel
import sqlite3

import constants as con
import language_helper

def split_by_sentences(filename, langcode, username, db_path, direction):
    raw = os.path.join(con.UPLOAD_FOLDER, username, con.RAW_FOLDER, langcode, filename)
    splitted = os.path.join(con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, langcode, filename)

    with sqlite3.connect(db_path) as db:
        with open(raw, mode='r', encoding='utf-8') as input_file, open(splitted, mode='w', encoding='utf-8') as out_file:
            if language_helper.isLangCodeValid(langcode):
                sentences = language_helper.split_by_sentences(input_file.readlines(), langcode)
            else:
                raise Exception("Unknown language code.")
            
            count = 1
            for x in sentences:
                if count < len(sentences)-1:
                    out_file.write(x.strip() + "\n")
                else:
                    out_file.write(x.strip())
                count += 1
                
            #write to db
            if direction == "from":
                db.executemany(f"insert into splitted_from(text) values (?)", [(x.strip(),) for x in sentences])
            else:
                db.executemany(f"insert into splitted_to(text) values (?)", [(x.strip(),) for x in sentences])