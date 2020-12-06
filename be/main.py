import datetime
import logging
import os
import pickle
import sys
import tempfile
# from multiprocessing import Process

from flask import Flask, abort, request, send_file
from flask_cors import CORS

import helper
helper.configure_logging()

import aligner
import constants as con
import splitter

#from mlflow import log_metric

app = Flask(__name__)
CORS(app)

@app.route('/api/hello')
def start():
    return "Hallo, Welt."

@app.route("/items/<username>/raw/<lang>", methods=["GET", "POST"])
def items(username, lang):

    #TODO add language code validation

    helper.create_folders(username, lang)
    #load documents
    if request.method == "POST":
        if lang in request.files:
            file = request.files[lang]
            logging.debug(f"[{username}]. Loading lang document {file.filename}.")
            raw_path = os.path.join(con.UPLOAD_FOLDER, username, con.RAW_FOLDER, lang, file.filename)
            file.save(raw_path)

            splitter.split_by_sentences(file.filename, lang, username)

            logging.debug(f"[{username}]. Success. {file.filename} is loaded.")
        return ('', 200)
    #return documents list
    files = {
        "items": {
            lang: helper.get_files_list(os.path.join(con.UPLOAD_FOLDER,username, con.RAW_FOLDER, lang))
        }
    }
    return files

@app.route("/items/<username>/splitted/<lang>/<int:id>/download", methods=["GET"])
def download_splitted(username, lang, id):
    logging.debug(f"[{username}]. Downloading {lang} {id} splitted document.")
    files = helper.get_files_list(os.path.join(con.UPLOAD_FOLDER,username, con.SPLITTED_FOLDER, lang))
    if len(files) < id+1:
        abort(404)
    path = os.path.join(con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang, files[id])
    if not os.path.isfile(path):
        logging.debug(f"[{username}]. Document not found.")
        abort(404)
    logging.debug(f"[{username}]. Document found. Path: {path}. Sent to user.")
    return send_file(path, as_attachment=True)  

@app.route("/items/<username>/splitted/<lang>/<int:id>/<int:count>/<int:page>", methods=["GET"])
def splitted(username, lang, id, count, page):
    files = helper.get_files_list(os.path.join(con.UPLOAD_FOLDER,username, con.SPLITTED_FOLDER, lang))
    if len(files) < id+1:
        return con.EMPTY_LINES
    path = os.path.join(con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang, files[id])    
    if not os.path.isfile(path):
        return {"items":{lang:[]}}

    lines = []
    lines_count = 0
    symbols_count = 0
    shift = (page-1)*count

    with open(path, mode='r', encoding='utf-8') as input_file:
        while True:
            line = input_file.readline()
            if not line:
                break
            lines_count+=1
            symbols_count+=len(line)
            if count>0 and (lines_count<=shift or lines_count>shift+count):
                continue
            lines.append((line, lines_count))

    total_pages = (lines_count//count) + (1 if lines_count%count != 0 else 0)
    meta = {"lines_count": lines_count, "symbols_count": symbols_count, "page": page, "total_pages": total_pages}
    return {"items":{lang:lines}, "meta":{lang:meta}}

@app.route("/items/<username>/align/<lang_from>/<lang_to>/<int:id_from>", methods=["GET"])
def align(username, lang_from, lang_to, id_from):
    files_from = helper.get_files_list(os.path.join(con.UPLOAD_FOLDER,username, con.RAW_FOLDER, lang_from))
    # files_to = helper.get_files_list(os.path.join(con.UPLOAD_FOLDER,username, con.SPLITTED_FOLDER, lang_to))
    
    print(files_from, id_from)

    # logging.info(f"[{username}]. Aligning documents. {files_from[id_from]}, {files_to[id_to]}.")
    if len(files_from) < id_from+1:
        logging.info(f"[{username}]. Documents not found.")
        return con.EMPTY_SIMS
    
    processing_folder_from_to = os.path.join(con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to)
    helper.check_folder(processing_folder_from_to)
    processing_from_to = os.path.join(processing_folder_from_to, files_from[id_from])
    
    res_img = f"{files_from[id_from]}.png"
    res_img_path = os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username, res_img)
    res_path = os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username, f"{files_from[id_from]}.html.bin")
    splitted_from = os.path.join(con.UPLOAD_FOLDER, username, con.RAW_FOLDER, lang_from, files_from[id_from])
    # splitted_to = os.path.join(con.UPLOAD_FOLDER, username, con.RAW_FOLDER, lang_to, files_to[id_to])
    
    logging.info(f"[{username}]. Cleaning images.")
    helper.clean_img_user_foler(username, files_from[id_from])
    
    # logging.debug(f"[{username}]. Preparing for alignment. {splitted_from}, {splitted_to}.")
    with open(splitted_from, mode="r", encoding="utf-8") as input_from:
        #  ,open(ngramed_proxy_ru, mode="r", encoding="utf-8") as input_proxy:
        lines_from = input_from.read()
        # lines_to = input_to.readlines()
        #lines_ru_proxy = input_proxy.readlines()
        

    #TODO refactor to queues (!)
    # state.init_processing(processing_from_to, (con.PROC_INIT, config.TEST_RESTRICTION_MAX_BATCHES, 0))   
    # alignment = Process(target=aligner.serialize_docs, args=(lines_from, lines_to, processing_from_to, res_img, res_img_best, lang_from, lang_to), daemon=True)
    # alignment.start()

    aligner.calculate_graphs(lines_from, processing_from_to, res_img, res_img_path, res_path, lang_from, lang_to)
    return con.EMPTY_LINES

@app.route("/items/<username>/processing/list/<int:file_id>/<lang_from>/<lang_to>", methods=["GET"])
def list_processing(username, file_id, lang_from, lang_to):

    raw_folder = os.path.join(con.UPLOAD_FOLDER, username, con.RAW_FOLDER, lang_from)
    files = helper.get_files_list(raw_folder)        
    res_path = os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username, f"{files[file_id]}.html.bin")
    
    if not os.path.isfile(res_path):
        abort(404)

    res = pickle.load(open(res_path, "rb"))
    return res

# @app.route("/items/<username>/align/stop/<lang_from>/<lang_to>/<int:file_id>", methods=["POST"])
# def stop_alignment(username, lang_from, lang_to, file_id):
#     logging.debug(f"[{username}]. Stopping alignment for {lang_from}-{lang_to} {file_id}.")
#     processing_folder = os.path.join(con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to)
#     files = helper.get_files_list(processing_folder)
#     processing_file = os.path.join(processing_folder, files[file_id])
#     if not helper.check_file(processing_folder, files, file_id):
#         abort(404)
#     state.destroy_processing_state(processing_file)
#     return ('', 200)

# Not API calls treated like static queries
@app.route("/<path:path>")
def route_frontend(path):
    # ...could be a static file needed by the front end that
    # doesn't use the `static` path (like in `<script src="bundle.js">`)
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    # ...or should be handled by the SPA's "router" in front end
    else:
        index_path = os.path.join(app.static_folder, "index.html")
        return send_file(index_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=80)
