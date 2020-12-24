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

            splitted_path = os.path.join(con.UPLOAD_FOLDER, username, con.RAW_FOLDER, lang, file.filename)
            align(username, lang, file.filename)

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
def align(username, lang_from, filename):
    res_path = os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username, f"{filename}.html.bin")
    splitted_from = os.path.join(con.UPLOAD_FOLDER, username, con.RAW_FOLDER, lang_from, filename)
    res_img = f"{filename}.png"
    res_img_path = os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username, res_img)

    with open(splitted_from, mode="r", encoding="utf-8") as input_from:
        lines_from = input_from.read()

    aligner.calculate_graphs(lines_from, res_path, res_img_path, res_img)
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

@app.route("/debug/items", methods=["GET"])
def show_items_tree():
    """Show all files in data folder"""

    tree_path = os.path.join(tempfile.gettempdir(), "items_tree.txt")
    logging.debug(f"Temp file for tree structure: {tree_path}.")
    with open(tree_path, mode="w", encoding="utf-8") as tree_out:
        for root, dirs, files in os.walk(con.UPLOAD_FOLDER):
            level = root.replace(con.UPLOAD_FOLDER, '').count(os.sep)
            indent = ' ' * 4 * (level)
            tree_out.write(f"{indent}{os.path.basename(root)}" + "\n")
            subindent = ' ' * 4 * (level + 1)
            for file in files:
                tree_out.write(f"{subindent}{file}" + "\n")
    return send_file(tree_path)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=80)
