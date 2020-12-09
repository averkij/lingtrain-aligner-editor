import pickle
import constants as con
import helper
import json
import logging

from aligner import DocLine

import sqlite3

def edit_doc(db_path, processing_id, line_ids_str, text, operation, text_type=con.TYPE_TO):    
    index = helper.get_doc_index(db_path)

    with sqlite3.connect(db_path) as db:
        line_ids = helper.parseJsonArray(line_ids_str)

        if operation == con.EDIT_TO_ADD_PREV_END:
            processing_id = processing_id-1

            if processing_id <= 0:
                logging.warning(f"{con.EDIT_TO_ADD_PREV_END} operation for processing_id=0")
                return

            direction = 3 #[3] column in index is processing_to.text_ids
            text_to_edit = helper.get_processing_text(db_path, text_type, processing_id)[0]
            text_to_update = text_to_edit + text
            # print(index)

            processing_text_ids = helper.parseJsonArray(index[processing_id-1][direction])
            new_ids = json.dumps(processing_text_ids + line_ids)
        else:
            return

        #update index ([0]processing_from.id, [1]processing_from.text_ids, [2]processing_to.id, [3]processing_to.text_ids)
        index_position = processing_id-1 #index is counting from zero
        index[index_position][direction] = new_ids    
        # print("new_ids", new_ids)

        helper.update_doc_index(db, db_path, index)
        helper.update_processing(db, db_path, text_type, processing_id, new_ids, text_to_update)