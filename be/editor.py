import pickle
import constants as con
import helper
import json
import logging

from aligner import DocLine

import sqlite3

def edit_doc(db_path, index_id, processing_id, processing_target_id, line_ids_str, text, operation, text_type=con.TYPE_TO):    
    index = helper.get_doc_index(db_path)

    print("processing_target_id", processing_target_id)

    with sqlite3.connect(db_path) as db:
        line_ids = helper.parseJsonArray(line_ids_str)

        if operation == con.EDIT_TO_ADD_PREV_END:
            if processing_target_id <= 0:
                logging.warning(f"{con.EDIT_TO_ADD_PREV_END} operation for processing_id=0")
                return

            direction = 3 #[3] column in index is processing_to.text_ids
            text_to_edit = helper.get_processing_text(db_path, text_type, processing_target_id)[0]
            text_to_update = text_to_edit + text
            # print(index)

            processing_text_ids = helper.parseJsonArray(index[index_id-1][direction])
            new_ids = json.dumps(processing_text_ids + line_ids)

            #update index ([0]processing_from.id, [1]processing_from.text_ids, [2]processing_to.id, [3]processing_to.text_ids)
            index[index_id-1][direction] = new_ids

            helper.update_processing(db, db_path, text_type, processing_target_id, new_ids, text_to_update)
        elif operation == con.EDIT_DELETE_LINE:
            print("deleting data", index_id)
            index.pop(index_id)
            #TODO should we leave data in processing tables?
        else:
            return


        # print("new_ids", new_ids)

        helper.update_doc_index(db, db_path, index)