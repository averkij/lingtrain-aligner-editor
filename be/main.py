import datetime
import logging
import os
import pickle
import sys
import tempfile
from multiprocessing import Process

from flask import Flask, abort, request, send_file
from flask_cors import CORS

import helper
helper.configure_logging()

import aligner
import config
import constants as con
import editor
import output
import splitter
import state_manager as state
from aligner import DocLine 

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
            upload_folder = con.RAW_FOLDER
            filename = file.filename

            if request.form["type"] == "proxy":
                upload_folder = con.PROXY_FOLDER
                filename = request.form["rawFileName"]
            
            logging.debug(f"[{username}]. Loading lang document {file.filename}.")
            upload_path = os.path.join(con.UPLOAD_FOLDER, username, upload_folder, lang, filename)
            file.save(upload_path)
            if request.form["type"] == "raw":
                splitter.split_by_sentences(filename, lang, username)
            logging.debug(f"[{username}]. Success. {filename} is loaded.")
        return ('', 200)
    #return documents list
    files = {
        "items": {
            lang: helper.get_raw_files(os.path.join(con.UPLOAD_FOLDER,username, con.RAW_FOLDER, lang), username, lang)
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

@app.route("/items/<username>/align/<lang_from>/<lang_to>/<int:id_from>/<int:id_to>", methods=["GET"])
def align(username, lang_from, lang_to, id_from, id_to):
    files_from = helper.get_files_list(os.path.join(con.UPLOAD_FOLDER,username, con.SPLITTED_FOLDER, lang_from))
    files_to = helper.get_files_list(os.path.join(con.UPLOAD_FOLDER,username, con.SPLITTED_FOLDER, lang_to))
    logging.info(f"[{username}]. Aligning documents. {files_from[id_from]}, {files_to[id_to]}.")
    if len(files_from) < id_from+1 or len(files_to) < id_to+1:
        logging.info(f"[{username}]. Documents not found.")
        return con.EMPTY_SIMS
    
    processing_folder_from_to = os.path.join(con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to)
    helper.check_folder(processing_folder_from_to)
    processing_from_to = os.path.join(processing_folder_from_to, files_from[id_from])
    
    res_img = os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username, f"{files_from[id_from]}.png")
    res_img_best = os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username, f"{files_from[id_from]}.best.png")
    splitted_from = os.path.join(con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang_from, files_from[id_from])
    splitted_to = os.path.join(con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang_to, files_to[id_to])
    proxy_to = os.path.join(con.UPLOAD_FOLDER, username, con.PROXY_FOLDER, lang_to, files_to[id_to])
    proxy_from = os.path.join(con.UPLOAD_FOLDER, username, con.PROXY_FOLDER, lang_from, files_to[id_to])
    
    logging.info(f"[{username}]. Cleaning images.")
    helper.clean_img_user_foler(username, files_from[id_from])
    
    logging.debug(f"[{username}]. Preparing for alignment. {splitted_from}, {splitted_to}.")
    with open(splitted_from, mode="r", encoding="utf-8") as input_from, \
         open(splitted_to, mode="r", encoding="utf-8") as input_to:
        #  ,open(ngramed_proxy_ru, mode="r", encoding="utf-8") as input_proxy:
        lines_from = input_from.readlines()
        lines_to = input_to.readlines()
        #lines_ru_proxy = input_proxy.readlines()
    
    lines_proxy_to = []
    if os.path.isfile(proxy_to):
        logging.info(f"[{username}]. Proxy file detected (to). Path: {proxy_to}")
        with open(proxy_to, mode="r", encoding="utf-8") as input_proxy_to:
            lines_proxy_to = input_proxy_to.readlines()

    #TODO refactor to queues (!)
    #init
    
    print("adding splitted and proxy texts to database")
    db_folder = os.path.join(con.UPLOAD_FOLDER, username, con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f'{files_from[id_from]}.db')
    helper.check_folder(db_folder)
    helper.init_db(username, db_path)
    helper.fill_db(db_path, splitted_from, splitted_to, proxy_from, proxy_to)
    
    print("aligning...")
    state.init_processing(processing_from_to, (con.PROC_INIT, config.TEST_RESTRICTION_MAX_BATCHES, 0))    
    alignment = Process(target=aligner.serialize_docs, args=(lines_from, lines_to, lines_proxy_to, processing_from_to, res_img, res_img_best, lang_from, lang_to, db_path), daemon=True)
    alignment.start()

    #aligner.serialize_docs(lines_from, lines_to, processing_from_to, res_img, res_img_best, lang_from, lang_to)
    return con.EMPTY_LINES

@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<int:file_id>/index")
def get_doc_index(username, lang_from, lang_to, file_id):
    db_folder = os.path.join(con.UPLOAD_FOLDER, username, con.DB_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(db_folder, mask="*.db")
    db_path = os.path.join(db_folder, f'{files[file_id]}')
    if not os.path.isfile(db_path):
        abort(404)

    index = helper.get_doc_index(db_path)
    # lines_count = len(index)
    # total_pages = (lines_count//count) + (1 if lines_count%count != 0 else 0)

    return {"items": index}    

@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<int:file_id>/<int:count>/<int:page>", methods=["GET"])
def get_processing(username, lang_from, lang_to, file_id, count, page):
    db_folder = os.path.join(con.UPLOAD_FOLDER, username, con.DB_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(db_folder, mask="*.db")
    db_path = os.path.join(db_folder, f'{files[file_id]}')
    if not os.path.isfile(db_path):
        abort(404)

    index = helper.get_doc_index(db_path)

    wnd = 20
    shift = (page-1)*count
    # pages = index[shift:shift+count]

    start_index = max(0, shift-wnd)
    end_index = min(shift+count+wnd, len(index))
    pages_wnd = index[start_index:end_index]

    print("start:", start_index, "end:", end_index)

    res = []

    items = helper.get_doc_page(db_path, pages_wnd)

    text_from_len, text_to_len = helper.get_texts_length(db_path)
    k = text_to_len/text_from_len
    candidates = helper.get_candidates_page(db_path, round(k*shift)-wnd, round(k*shift)+count+wnd)

    print("from_len:", text_from_len, "to_len:", text_to_len)

    for i in range(min(wnd, shift), min(min(wnd, shift)+count, wnd+len(index)-shift)):
        print(i)
        res.append({
            #from
            "text_from": items[i][0],
            "line_id_from": pages_wnd[i][1],        #array with ids
            "processing_from_id": pages_wnd[i][0],  #primary key in DB (processing_from)
            "proxy_from": items[i][2],
            #to
            "text_to": items[i][1],
            "line_id_to": pages_wnd[i][3],          #array with ids
            "processing_to_id": pages_wnd[i][2],    #primary key in DB (processing_to)
            "proxy_to": items[i][3],
            #candidates
            "trans": [{
                "text": texts[1], 
                "processing_to_id": texts[0],       #primary key in DB (proxy_to)
                "proxy": texts[2],
                "sim": 1
                } for texts in candidates[max(0,round(i*k)-wnd) : round(i*k)+wnd]]
            })

    # items_wnd = helper.get_doc_page(db_path, pages_wnd)

    # for texts, data in zip(items, pages):
    #     res.append({
    #         #from
    #         "text_from": texts[0],
    #         "line_id_from": data[1],
    #         "processing_from_id": data[0],
    #         "proxy_from": texts[2],
    #         #to
    #         "text_to": texts[1],
    #         "line_id_to": data[3],
    #         "processing_to_id": data[2],
    #         "proxy_to": texts[3],
    #         #candidates
    #         "trans": [{
    #             "text": "t[0].text.strip()", 
    #             "line_id_to": "t[0].line_id",
    #             "proxy": "t[0].proxy",
    #             "sim": 1
    #             }  ]
    #         })

    lines_count = len(index)
    total_pages = (lines_count//count) + (1 if lines_count%count != 0 else 0)
    meta = {"page": page, "total_pages": total_pages}

    return {"items": res, "meta": meta}



    # processing_folder = os.path.join(con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to)
    # files = helper.get_files_list(processing_folder)
    # processing_file = os.path.join(processing_folder, files[file_id])
    # if not helper.check_file(processing_folder, files, file_id):
    #     abort(404)

    # res = []
    # lines_count = 0    
    # shift = (page-1)*count
    # for line_from_orig, line_from, line_to, candidates in helper.read_processing(processing_file):
    #     lines_count += 1
    #     if count>0 and (lines_count<=shift or lines_count>shift+count):
    #         continue
    #     res.append({
    #         "text": line_from[0].text.strip(),
    #         "line_id": line_from[0].line_id,
    #         "text_orig": line_from_orig.text.strip(),
    #         "trans": [{
    #             "text": t[0].text.strip(), 
    #             "line_id": t[0].line_id,
    #             "proxy": t[0].proxy,
    #             "sim": t[1]
    #             } for t in candidates],
    #         "selected": {
    #             "text": line_to[0].text.strip(),
    #             "line_id": line_to[0].line_id,
    #             "proxy": line_to[0].proxy,
    #             "sim": line_to[1]
    #             }})
    # total_pages = (lines_count//count) + (1 if lines_count%count != 0 else 0)
    # meta = {"page": page, "total_pages": total_pages}
    # return {"items": res, "meta": meta}

@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<int:file_id>/edit", methods=["POST"])
def edit_processing(username, lang_from, lang_to, file_id):
    db_folder = os.path.join(con.UPLOAD_FOLDER, username, con.DB_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(db_folder, mask="*.db")
    db_path = os.path.join(db_folder, f'{files[file_id]}')
    if not os.path.isfile(db_path):
        abort(404)

    line_ids = request.form.get("line_id", "[]")
    processing_id, processing_id_is_int = helper.tryParseInt(request.form.get("processing_id", -1))
    text = request.form.get("text", '')
    text_type = request.form.get("text_type", con.TYPE_TO)
    operation = request.form.get("operation", "")

    print("operation", operation)

    if processing_id_is_int and processing_id >= 0:
        editor.edit_doc(db_path, processing_id, line_ids, text, operation, text_type)
    else:
        abort(400)
    return ('', 200)

@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<int:file_id>/download/<lang>/<file_format>/<int:threshold>", methods=["GET"])
def download_processsing(username, lang_from, lang_to, file_id, lang, file_format, threshold):
    logging.debug(f"[{username}]. Downloading {lang_from}-{lang_to} {file_id} {lang} result document.")
    processing_folder = os.path.join(con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(processing_folder)
    processing_file = os.path.join(processing_folder, files[file_id])
    if not helper.check_file(processing_folder, files, file_id):
        abort(404)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")    
    download_folder = os.path.join(con.UPLOAD_FOLDER, username, con.DOWNLOAD_FOLDER)
    helper.check_folder(download_folder)
    download_file = os.path.join(download_folder, "{0}_{1}_{2}.{3}".format(os.path.splitext(files[file_id])[0], lang, timestamp, file_format))
    
    logging.debug(f"[{username}]. Preparing file for downloading {download_file}.")

    if file_format==con.FORMAT_TMX:
        output.save_tmx(processing_file, download_file, lang_from, lang_to, threshold)
    elif file_format==con.FORMAT_PLAIN:
        output.save_plain_text(processing_file, download_file, first_lang = lang==lang_from, threshold=threshold)

    logging.debug(f"[{username}]. File {download_file} prepared. Sent to user.")
    return send_file(download_file, as_attachment=True)  

@app.route("/items/<username>/processing/list/<lang_from>/<lang_to>", methods=["GET"])
def list_processing(username, lang_from, lang_to):
    
    #TODO add language validation

    logging.debug(f"[{username}]. Processing list. Language code lang_from: {lang_from}. Language code lang_to: {lang_to}.")
    if not lang_from or not lang_to:
        logging.debug(f"[{username}]. Wrong language code: {lang_from}-{lang_to}.")
        return con.EMPTY_FILES
    processing_folder = os.path.join(con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to)
    helper.check_folder(processing_folder)    
    files = {
        "items": {
            lang_from: helper.get_processing_list_with_state(os.path.join(con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to), username)
        }
    }
    return files

@app.route("/items/<username>/align/stop/<lang_from>/<lang_to>/<int:file_id>", methods=["POST"])
def stop_alignment(username, lang_from, lang_to, file_id):
    logging.debug(f"[{username}]. Stopping alignment for {lang_from}-{lang_to} {file_id}.")
    processing_folder = os.path.join(con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(processing_folder)
    processing_file = os.path.join(processing_folder, files[file_id])
    if not helper.check_file(processing_folder, files, file_id):
        abort(404)
    state.destroy_processing_state(processing_file)
    return ('', 200)


@app.route("/debug/items", methods=["GET"])
def show_items_tree():
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
