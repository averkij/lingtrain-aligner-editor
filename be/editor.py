import pickle
import constants as con
import helper
import json
import logging

from aligner import DocLine

import sqlite3

def edit_doc(db_path, index_id, text, operation, target, text_type=con.TYPE_TO):    
    index = helper.get_doc_index(db_path)
    print("starting operation", operation, index_id)

    if target == "next":
        index_target_id = index_id+1        
    else:
        index_target_id = index_id-1

    update_index = True

    with sqlite3.connect(db_path) as db:
        if index_id < 0 or index_id >= len(index): return

        direction = 3 if text_type==con.TYPE_TO else 1  #[3] column in index is processing_to.text_ids
        line_ids = helper.parseJsonArray(index[index_id][direction])

        if operation == con.EDIT_ADD_PREV_END or operation == con.EDIT_ADD_NEXT_END:
            if index_target_id < 0 or index_target_id >= len(index):
                return
            processing_target_id = index[index_target_id][0]
            text_to_edit = helper.get_processing_text(db_path, text_type, processing_target_id)[0]
            text_to_update = text_to_edit + text
            # print(index)

            processing_text_ids = helper.parseJsonArray(index[index_target_id][direction])
            new_ids = processing_text_ids + line_ids
            new_ids = json.dumps(list(set(new_ids)))

            #update index ([0]processing_from.id, [1]processing_from.text_ids, [2]processing_to.id, [3]processing_to.text_ids)
            index[index_target_id][direction] = new_ids

            helper.update_processing(db, text_type, processing_target_id, new_ids, text_to_update)

        elif operation == con.ADD_EMPTY_LINE_BEFORE:
            from_id, to_id = helper.add_empty_processing_line(db)
            print("from_id", from_id, "to_id", to_id)
            index.insert(index_id, (from_id,"[]",to_id,"[]"))

        elif operation == con.ADD_EMPTY_LINE_AFTER:
            from_id, to_id = helper.add_empty_processing_line(db)
            print("from_id", from_id, "to_id", to_id)
            index.insert(index_id+1, (from_id,"[]",to_id,"[]"))

        elif operation == con.EDIT_LINE:
            processing_target_id = index[index_id][0]
            helper.update_processing(db, text_type, processing_target_id, json.dumps(line_ids), text)

            update_index = False

        elif operation == con.EDIT_CLEAR_LINE:
            processing_target_id = index[index_id][0]
            index[index_id][direction] = "[]"
            
            helper.clear_processing(db, text_type, processing_target_id)

        elif operation == con.EDIT_DELETE_LINE:
            index.pop(index_id)
            #TODO should we leave data in processing tables?
        else:
            return


        # print("new_ids", new_ids)

        if update_index:
            helper.update_doc_index(db, index)
