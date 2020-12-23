"""Main module"""

import datetime
import logging
import os
import tempfile

import config
import constants as con
import editor
import helper
import language_helper
import output
import state_manager as state
from align_processor import AlignmentProcessor
from flask import Flask, abort, request, send_file
from flask_cors import CORS

helper.configure_logging()


#from mlflow import log_metric

app = Flask(__name__)
CORS(app)


@app.route("/items/<username>/raw/<lang>", methods=["GET", "POST"])
def items(username, lang):
    """Get uploaded user raw documents"""

    # TODO add language code validation

    helper.create_folders(username, lang)
    # load documents
    if request.method == "POST":
        if lang in request.files:
            file = request.files[lang]
            upload_folder = con.RAW_FOLDER
            filename = file.filename

            if request.form["type"] == "proxy":
                upload_folder = con.PROXY_FOLDER
                filename = request.form["rawFileName"]

            logging.debug(
                f"[{username}]. Loading lang document {file.filename}.")
            upload_path = os.path.join(
                con.UPLOAD_FOLDER, username, upload_folder, lang, filename)
            file.save(upload_path)
            if request.form["type"] == "raw":
                language_helper.split_by_sentences_and_save(
                    filename, lang, username)
            logging.debug(f"[{username}]. Success. {filename} is loaded.")
        return ('', 200)
    # return documents list
    files = {
        "items": {
            lang: helper.get_raw_files(os.path.join(
                con.UPLOAD_FOLDER, username, con.RAW_FOLDER, lang), username, lang)
        }
    }
    return files


@app.route("/items/<username>/splitted/<lang>/<int:id>/download", methods=["GET"])
def download_splitted(username, lang, id):
    """Download splitted document file"""
    logging.debug(f"[{username}]. Downloading {lang} {id} splitted document.")
    files = helper.get_files_list(os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang))
    if len(files) < id+1:
        abort(404)
    path = os.path.join(con.UPLOAD_FOLDER, username,
                        con.SPLITTED_FOLDER, lang, files[id])
    if not os.path.isfile(path):
        logging.debug(f"[{username}]. Document not found.")
        abort(404)
    logging.debug(f"[{username}]. Document found. Path: {path}. Sent to user.")
    return send_file(path, as_attachment=True)


@app.route("/items/<username>/splitted/<lang>/<int:id>/<int:count>/<int:page>", methods=["GET"])
def splitted(username, lang, id, count, page):
    """Get splitted document page"""
    files = helper.get_files_list(os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang))
    if len(files) < id+1:
        return con.EMPTY_LINES
    path = os.path.join(con.UPLOAD_FOLDER, username,
                        con.SPLITTED_FOLDER, lang, files[id])
    if not os.path.isfile(path):
        return {"items": {lang: []}}

    lines = []
    lines_count = 0
    symbols_count = 0
    shift = (page-1)*count

    with open(path, mode='r', encoding='utf-8') as input_file:
        while True:
            line = input_file.readline()
            if not line:
                break
            lines_count += 1
            symbols_count += len(line)
            if count > 0 and (lines_count <= shift or lines_count > shift+count):
                continue
            lines.append((line, lines_count))

    total_pages = (lines_count//count) + (1 if lines_count % count != 0 else 0)
    meta = {"lines_count": lines_count, "symbols_count": symbols_count,
            "page": page, "total_pages": total_pages}
    return {"items": {lang: lines}, "meta": {lang: meta}}


@app.route("/items/<username>/align/<lang_from>/<lang_to>/<int:id_from>/<int:id_to>", methods=["GET"])
def align(username, lang_from, lang_to, id_from, id_to):
    """Align two splitted documents"""

    batch_size = config.DEFAULT_BATCHSIZE
    files_from = helper.get_files_list(os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang_from))
    files_to = helper.get_files_list(os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang_to))
    logging.info(
        f"[{username}]. Aligning documents. {files_from[id_from]}, {files_to[id_to]}.")
    if len(files_from) < id_from+1 or len(files_to) < id_to+1:
        logging.info(f"[{username}]. Documents not found.")
        return con.EMPTY_SIMS

    splitted_from = os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang_from, files_from[id_from])
    splitted_to = os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang_to, files_to[id_to])
    proxy_to = os.path.join(con.UPLOAD_FOLDER, username,
                            con.PROXY_FOLDER, lang_to, files_to[id_to])
    proxy_from = os.path.join(
        con.UPLOAD_FOLDER, username, con.PROXY_FOLDER, lang_from, files_to[id_to])

    logging.info(f"[{username}]. Cleaning images.")
    helper.clean_img_user_foler(username, files_from[id_from])

    logging.debug(
        f"[{username}]. Preparing for alignment. {splitted_from}, {splitted_to}.")
    with open(splitted_from, mode="r", encoding="utf-8") as input_from, \
            open(splitted_to, mode="r", encoding="utf-8") as input_to:
        #  ,open(ngramed_proxy_ru, mode="r", encoding="utf-8") as input_proxy:
        lines_from = input_from.readlines()
        lines_to = input_to.readlines()
        #lines_ru_proxy = input_proxy.readlines()

    # TODO refactor to queues (!)
    # init

    print("adding splitted and proxy texts to database")
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f'{files_from[id_from]}.db')
    helper.check_folder(db_folder)
    helper.init_db(db_path)
    helper.fill_db(db_path, splitted_from, splitted_to, proxy_from, proxy_to)

    logging.info(f"{username}: initializing state")
    len_from, _ = helper.get_texts_length(db_path)

    if config.TEST_RESTRICTION_MAX_BATCHES > 0:
        total_batches = config.TEST_RESTRICTION_MAX_BATCHES
    else:
        is_last = len_from % batch_size > 0
        total_batches = len_from//batch_size + 1 if is_last else 0

    logging.info(f"{username}: total_batches: {total_batches}")
    state.init_processing(db_path, (con.PROC_INIT, total_batches, 0))

    # parallel processing
    logging.info(f"{username}: aligning started")
    res_img = os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER,
                           username, f"{files_from[id_from]}.db.png")
    res_img_best = os.path.join(
        con.STATIC_FOLDER, con.IMG_FOLDER, username, f"{files_from[id_from]}.db.best.png")

    task_list = [(lines_from_batch, lines_to_batch, line_ids_from, line_ids_to) for lines_from_batch, lines_to_batch,
                 line_ids_from, line_ids_to in helper.get_batch_intersected(lines_from, lines_to)][:total_batches]

    proc_count = config.PROCESSORS_COUNT

    proc = AlignmentProcessor(proc_count, db_path, res_img,
                              res_img_best, lang_from, lang_to)
    proc.add_tasks(task_list)
    proc.start()

    return con.EMPTY_LINES


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<int:file_id>/index")
def get_doc_index(username, lang_from, lang_to, file_id):
    """Get aligned document index"""
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(db_folder, mask="*.db")
    db_path = os.path.join(db_folder, f'{files[file_id]}')
    if not os.path.isfile(db_path):
        abort(404)

    index = helper.get_doc_index(db_path)

    return {"items": index}


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<int:file_id>/<int:count>/<int:page>", methods=["GET"])
def get_processing(username, lang_from, lang_to, file_id, count, page):
    """Get processing (aligned) document page"""
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(db_folder, mask="*.db")
    db_path = os.path.join(db_folder, f'{files[file_id]}')
    if not os.path.isfile(db_path):
        abort(404)

    index = helper.get_doc_index(db_path)
    shift = (page-1)*count
    pages = index[shift:shift+count]
    res = []

    for i, (data, texts) in enumerate(zip(pages, helper.get_doc_page(db_path, pages))):
        print(shift + i)
        # print("data",data)
        res.append({
            "index_id": shift + i,  # absolute position in index
            # from
            "text_from": texts[0],
            "line_id_from": data[1],  # array with ids
            # primary key in DB (processing_from)
            "processing_from_id": data[0],
            "proxy_from": texts[2],
            # to
            "text_to": texts[1],
            "line_id_to": data[3],  # array with ids
            "processing_to_id": data[2],  # primary key in DB (processing_to)
            "proxy_to": texts[3],
        })

    lines_count = len(index)
    total_pages = (lines_count//count) + (1 if lines_count % count != 0 else 0)
    meta = {"page": page, "total_pages": total_pages}

    return {"items": res, "meta": meta}


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<int:file_id>/candidates/<text_type>/<int:index_id>/<int:count_before>/<int:count_after>", methods=["GET"])
def get_processing_candidates(username, lang_from, lang_to, file_id, text_type, index_id, count_before, count_after):
    """Get splitted lines by some interval"""

    if text_type not in (con.TYPE_FROM, con.TYPE_TO):
        abort(404)
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(db_folder, mask="*.db")
    db_path = os.path.join(db_folder, f'{files[file_id]}')
    if not os.path.isfile(db_path):
        abort(404)

    index = helper.get_doc_index(db_path)
    if index_id < 0 or index_id >= len(index):
        return

    direction = 3 if text_type == con.TYPE_TO else 1
    if index_id > 0:
        line_ids = helper.parse_json_array(index[index_id-1][direction])
    else:
        line_ids = helper.parse_json_array(index[index_id][direction])

    while index_id > 0:
        print("line_ids", line_ids)
        if not line_ids:
            index_id -= 1
            line_ids = helper.parse_json_array(index[index_id][direction])
        else:
            break

    print("line_ids", line_ids)
    if not line_ids or index_id == 0:
        line_id = 1
    else:
        line_id = line_ids[0]

    id_from = line_id - count_before
    id_to = line_id + count_after

    candidates = helper.get_candidates_page(db_path, text_type, id_from, id_to)

    return {"items": candidates}


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<int:file_id>/edit", methods=["POST"])
def edit_processing(username, lang_from, lang_to, file_id):
    """Edit processing document"""

    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(db_folder, mask="*.db")
    db_path = os.path.join(db_folder, f'{files[file_id]}')
    if not os.path.isfile(db_path):
        abort(404)

    index_id, index_id_is_int = helper.try_parse_int(
        request.form.get("index_id", -1))
    text = request.form.get("text", '')
    text_type = request.form.get("text_type", con.TYPE_TO)
    operation = request.form.get("operation", "")
    target = request.form.get("target", "")
    candidate_line_id, _ = helper.try_parse_int(
        request.form.get("candidate_line_id", -1))
    candidate_text = request.form.get("candidate_text", '')

    print("OPERATION:", operation, "text_type:", text_type)

    # TODO перенести в edit_doc, там чекать валидность необходимых параметров
    if index_id_is_int:
        editor.edit_doc(db_path, index_id, text, operation,
                        target, candidate_line_id, candidate_text, text_type)
    else:
        abort(400)
    return ('', 200)


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<int:file_id>/download/<lang>/<file_format>/<int:threshold>", methods=["GET"])
def download_processsing(username, lang_from, lang_to, file_id, lang, file_format, threshold):
    """Download processsing document"""

    logging.debug(
        f"[{username}]. Downloading {lang_from}-{lang_to} {file_id} {lang} result document.")
    processing_folder = os.path.join(
        con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(processing_folder)
    processing_file = os.path.join(processing_folder, files[file_id])
    if not helper.check_file(processing_folder, files, file_id):
        abort(404)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    download_folder = os.path.join(
        con.UPLOAD_FOLDER, username, con.DOWNLOAD_FOLDER)
    helper.check_folder(download_folder)
    download_file = os.path.join(download_folder, "{0}_{1}_{2}.{3}".format(
        os.path.splitext(files[file_id])[0], lang, timestamp, file_format))

    logging.debug(
        f"[{username}]. Preparing file for downloading {download_file}.")

    # if file_format == con.FORMAT_TMX:
    #     output.save_tmx(processing_file, download_file,
    #                     lang_from, lang_to, threshold)
    # elif file_format == con.FORMAT_PLAIN:
    #     output.save_plain_text(processing_file, download_file,
    #                            first_lang=lang == lang_from, threshold=threshold)

    logging.debug(
        f"[{username}]. File {download_file} prepared. Sent to user.")
    return send_file(download_file, as_attachment=True)


@app.route("/items/<username>/processing/list/<lang_from>/<lang_to>", methods=["GET"])
def list_processing(username, lang_from, lang_to):
    """Get processing documents list"""

    # TODO add language validation

    logging.debug(
        f"[{username}]. Processing list. Language code lang_from: {lang_from}. Language code lang_to: {lang_to}.")
    if not lang_from or not lang_to:
        logging.debug(
            f"[{username}]. Wrong language code: {lang_from}-{lang_to}.")
        return con.EMPTY_FILES
    processing_folder = os.path.join(
        con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to)
    helper.check_folder(processing_folder)
    files = {
        "items": {
            lang_from: helper.get_processing_list_with_state(os.path.join(
                con.UPLOAD_FOLDER, username, con.DB_FOLDER, lang_from, lang_to), username)
        }
    }
    return files


@app.route("/items/<username>/align/stop/<lang_from>/<lang_to>/<int:file_id>", methods=["POST"])
def stop_alignment(username, lang_from, lang_to, file_id):
    """Stop alignment process"""

    logging.debug(
        f"[{username}]. Stopping alignment for {lang_from}-{lang_to} {file_id}.")
    processing_folder = os.path.join(
        con.UPLOAD_FOLDER, username, con.DB_FOLDER, lang_from, lang_to)
    files = helper.get_files_list(processing_folder, mask="*.db")
    processing_file = os.path.join(processing_folder, files[file_id])
    if not helper.check_file(processing_folder, files, file_id):
        abort(404)
    state.destroy_processing_state(processing_file)
    return ('', 200)


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

# Not API calls treated like static queries


@app.route("/<path:path>")
def route_frontend(path):
    """Route static requests"""
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
