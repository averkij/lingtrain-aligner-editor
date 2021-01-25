"""Main module"""

import datetime
import logging
import os
import tempfile
import uuid

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


@app.route("/items/<username>/init", methods=["GET"])
def init_userspace(username):
    """Prepare user workspace"""
    helper.init_user_db(username)
    return ('', 200)


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

            if helper.file_exists(username, lang, filename):
                return ('File already exists', 400)

            if request.form["type"] == "proxy":
                upload_folder = con.PROXY_FOLDER
                filename = request.form["rawFileName"]
            else:
                helper.register_file(username, lang, filename)

            logging.info(
                f"[{username}]. Loading document {file.filename}.")
            upload_path = os.path.join(
                con.UPLOAD_FOLDER, username, upload_folder, lang, filename)
            file.save(upload_path)

            if request.form["type"] == "raw":
                language_helper.split_by_sentences_and_save(
                    filename, lang, username)
            logging.info(f"[{username}]. Success. {filename} is loaded.")
        return ('', 200)
    # return documents list
    files = {
        "items": {
            lang: helper.get_raw_files(username, lang)
        }
    }
    return files


@app.route("/items/<username>/splitted/<lang>/<guid>/download", methods=["GET"])
def download_splitted(username, lang, guid):
    """Download splitted document file"""
    logging.info(f"[{username}]. Downloading {lang} {guid} splitted document.")
    files = helper.get_files_list(os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang))
    filename = helper.get_filename(username, guid)
    if not filename:
        abort(404)
    path = os.path.join(con.UPLOAD_FOLDER, username,
                        con.SPLITTED_FOLDER, lang, filename)
    if not os.path.isfile(path):
        abort(404)
    logging.info(f"[{username}]. Document found. Path: {path}. Sent to user.")
    return send_file(path, as_attachment=True)


@app.route("/items/<username>/splitted/<lang>/<guid>/<int:count>/<int:page>", methods=["GET"])
def splitted(username, lang, guid, count, page):
    """Get splitted document page"""
    files = helper.get_files_list(os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang))
    filename = helper.get_filename(username, guid)
    if not filename:
        return {"items": {lang: []}}
    path = os.path.join(con.UPLOAD_FOLDER, username,
                        con.SPLITTED_FOLDER, lang, filename)
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


@app.route("/items/<username>/alignment/create", methods=["POST"])
def create_alignment(username):
    """Register new alignment"""
    id_from = request.form.get("id_from", '')
    id_to = request.form.get("id_to", '')
    name = request.form.get("name", '')

    if helper.alignment_exists(username, id_from, id_to):
        return ('', 200)

    batch_size = config.DEFAULT_BATCHSIZE
    file_from, lang_from = helper.get_fileinfo(username, id_from)
    file_to, lang_to = helper.get_fileinfo(username, id_to)

    splitted_from = os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang_from, file_from)
    splitted_to = os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang_to, file_to)
    proxy_to = os.path.join(con.UPLOAD_FOLDER, username,
                            con.PROXY_FOLDER, lang_to, file_to)
    proxy_from = os.path.join(
        con.UPLOAD_FOLDER, username, con.PROXY_FOLDER, lang_from, file_from)

    align_guid = uuid.uuid4().hex
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f"{align_guid}.db")

    helper.check_folder(db_folder)

    if not os.path.isfile(db_path):
        logging.info(f"Initializing database {db_path}")
        helper.init_document_db(db_path)
        helper.fill_document_db(db_path, splitted_from,
                                splitted_to, proxy_from, proxy_to)

    len_from, _ = helper.get_texts_length(db_path)

    is_last = len_from % batch_size > 0
    total_batches = len_from//batch_size + 1 if is_last else 0
    if config.TEST_RESTRICTION_MAX_BATCHES > 0:
        total_batches = min(config.TEST_RESTRICTION_MAX_BATCHES, total_batches)

    helper.register_alignment(username, align_guid,
                              id_from, id_to, name, total_batches)

    return ('', 200)


@app.route("/items/<username>/alignment/align", methods=["POST"])
def align(username):
    """Align two splitted documents"""

    align_guid = request.form.get("id", '')
    align_all = request.form.get("align_all", '')
    batch_ids = helper.parse_json_array(request.form.get("batch_ids", "[0]"))

    logging.info(
        f"align parameters align_guid {align_guid} align_all {align_all} batch_ids {batch_ids}")

    name, guid_from, guid_to, state, curr_batches, total_batches = helper.get_alignment_info(
        username, align_guid)
    file_from, lang_from = helper.get_fileinfo(username, guid_from)
    file_to, lang_to = helper.get_fileinfo(username, guid_to)

    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f"{align_guid}.db")
    user_db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)

    logging.info(
        f"align parameters align_guid {align_guid} align_all {align_all} batch_ids {batch_ids} name {name} guid_from {guid_from} guid_to {guid_to} total_batches {total_batches}")

    splitted_from = os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang_from, file_from)
    splitted_to = os.path.join(
        con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang_to, file_to)

    with open(splitted_from, mode="r", encoding="utf-8") as input_from, \
            open(splitted_to, mode="r", encoding="utf-8") as input_to:
        lines_from = input_from.readlines()
        lines_to = input_to.readlines()

    logging.info(f"[{username}]. Cleaning images.")
    helper.clean_img_user_foler(username, file_from)

    if align_all:
        batch_ids = list(range(total_batches))

    # exit if batch ids is empty
    batch_ids = [x for x in batch_ids if x < total_batches][:total_batches]
    if not batch_ids:
        abort(404)
    if align_all:
        helper.update_alignment_state(
            user_db_path, guid_from, guid_to, con.PROC_INIT, 0, total_batches)

    helper.update_alignment_state_by_align_id(
        user_db_path, align_guid, con.PROC_IN_PROGRESS)

    # parallel processing
    logging.info(f"{username}: aligning started")
    res_img = os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER,
                           username, f"{align_guid}.png")
    res_img_best = os.path.join(
        con.STATIC_FOLDER, con.IMG_FOLDER, username, f"{align_guid}.best.png")

    task_list = [(lines_from_batch, lines_to_batch, line_ids_from, line_ids_to, batch_id)
                 for lines_from_batch, lines_to_batch,
                 line_ids_from, line_ids_to, batch_id
                 in helper.get_batch_intersected(lines_from, lines_to, batch_ids)]

    proc_count = config.PROCESSORS_COUNT

    proc = AlignmentProcessor(
        proc_count, db_path, user_db_path, res_img, res_img_best, lang_from, lang_to, guid_from, guid_to)
    proc.add_tasks(task_list)
    proc.start()

    return con.EMPTY_LINES


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<align_guid>/index", methods=["GET"])
def get_doc_index(username, lang_from, lang_to, align_guid):
    """Get aligned document index"""
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f'{align_guid}.db')
    if not os.path.isfile(db_path):
        abort(404)
    index = helper.get_clear_flatten_doc_index(db_path)
    return {"items": index}


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<align_guid>/<int:count>/<int:page>", methods=["GET"])
def get_processing(username, lang_from, lang_to, align_guid, count, page):
    """Get processing (aligned) document page"""
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f'{align_guid}.db')
    if not os.path.isfile(db_path):
        abort(404)
    index = helper.get_flatten_doc_index(db_path)

    shift = (page-1)*count
    pages = list(zip(index[shift:shift+count], range(shift, shift+count)))
    res = helper.get_doc_items(pages, db_path)

    lines_count = len(index)
    total_pages = (lines_count//count) + (1 if lines_count % count != 0 else 0)
    meta = {"page": page, "total_pages": total_pages}
    return {"items": res, "meta": meta}


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<align_guid>", methods=["POST"])
def get_processing_by_ids(username, lang_from, lang_to, align_guid):
    """Get processing (aligned) items by ids"""
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f'{align_guid}.db')
    if not os.path.isfile(db_path):
        abort(404)

    index = helper.get_flatten_doc_index(db_path)
    index_ids = helper.parse_json_array(request.form.get("index_ids", "[]"))

    print("index_ids", index_ids)
    print("index", index)

    index_items = [(index[i], i) for i in index_ids]
    res = {}
    for i, item in zip(index_ids, helper.get_doc_items(index_items, db_path)):
        res[i] = item

    return {"items": res}


@app.route("/items/<username>/splitted/from/<lang_from>/<lang_to>/<align_guid>", methods=["POST"])
def get_splitted_from_by_ids(username, lang_from, lang_to, align_guid):
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f'{align_guid}.db')
    if not os.path.isfile(db_path):
        abort(404)
    text_ids = helper.parse_json_array(request.form.get("ids", "[]"))

    res = {}
    if text_ids:
        for id, text, proxy in helper.get_splitted_to_by_id(db_path, text_ids):
            res[id] = {
                "t": text,
                "p": proxy if proxy else ''
            }
    return {"items": res}


@app.route("/items/<username>/splitted/to/<lang_from>/<lang_to>/<align_guid>", methods=["POST"])
def get_splitted_to_by_ids(username, lang_from, lang_to, align_guid):
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f'{align_guid}.db')
    if not os.path.isfile(db_path):
        abort(404)
    text_ids = helper.parse_json_array(request.form.get("ids", "[]"))

    res = {}
    if text_ids:
        for id, text, proxy in helper.get_splitted_to_by_id(db_path, text_ids):
            res[id] = {
                "t": text,
                "p": proxy if proxy else ''
            }

    return {"items": res}


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<align_guid>/candidates/<text_type>/<int:index_id>/<int:count_before>/<int:count_after>", methods=["GET"])
def get_processing_candidates(username, lang_from, lang_to, align_guid, text_type, index_id, count_before, count_after):
    """Get splitted lines by some interval"""
    if text_type not in (con.TYPE_FROM, con.TYPE_TO):
        abort(404)
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f'{align_guid}.db')
    if not os.path.isfile(db_path):
        abort(404)

    index = helper.get_clear_flatten_doc_index(db_path)
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


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<align_guid>/edit", methods=["POST"])
def edit_processing(username, lang_from, lang_to, align_guid):
    """Edit processing document"""
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f'{align_guid}.db')
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
    batch_id, _ = helper.try_parse_int(
        request.form.get("batch_id", -1))
    batch_index_id, _ = helper.try_parse_int(
        request.form.get("batch_index_id", -1))

    print("OPERATION:", operation, "text_type:", text_type)

    # TODO перенести в edit_doc, там чекать валидность необходимых параметров
    if index_id_is_int:
        editor.edit_doc(db_path, index_id, text, operation,
                        target, candidate_line_id, candidate_text, batch_id, batch_index_id, text_type)
    else:
        abort(400)
    return ('', 200)


@app.route("/items/<username>/processing/<lang_from>/<lang_to>/<align_guid>/download/<lang>/<file_format>", methods=["GET"])
def download_processsing(username, lang_from, lang_to, align_guid, lang, file_format):
    """Download processsing document"""
    logging.info(
        f"[{username}]. Downloading {lang_from}-{lang_to} {align_guid} {lang} result document.")
    db_folder = os.path.join(con.UPLOAD_FOLDER, username,
                             con.DB_FOLDER, lang_from, lang_to)
    db_path = os.path.join(db_folder, f'{align_guid}.db')
    if not os.path.isfile(db_path):
        abort(404)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    download_folder = os.path.join(
        con.UPLOAD_FOLDER, username, con.DOWNLOAD_FOLDER)
    helper.check_folder(download_folder)
    download_file = os.path.join(download_folder, "{0}_{1}_{2}.{3}".format(
        align_guid, lang, timestamp, file_format))

    logging.debug(
        f"[{username}]. Preparing file for downloading {download_file}.")

    if file_format == con.FORMAT_TMX:
        output.save_tmx(db_path, download_file, lang_from, lang_to)
    elif file_format == con.FORMAT_PLAIN:
        output.save_plain_text(db_path, download_file,
                               first_lang=lang == lang_from)

    logging.debug(
        f"[{username}]. File {download_file} prepared. Sent to user.")
    return send_file(download_file, as_attachment=True)


@app.route("/items/<username>/processing/list/<lang_from>/<lang_to>", methods=["GET"])
def list_processing(username, lang_from, lang_to):
    """Get processing documents list"""
    logging.debug(
        f"[{username}]. Processing list. Language code lang_from: {lang_from}. Language code lang_to: {lang_to}.")
    if not lang_from or not lang_to:
        logging.warning(
            f"[{username}]. Wrong language code: {lang_from}-{lang_to}.")
        return con.EMPTY_FILES
    processing_folder = os.path.join(
        con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang_from, lang_to)
    helper.check_folder(processing_folder)
    files = {
        "items": {
            lang_from: helper.get_processing_list_with_state(
                username, lang_from, lang_to)
        }
    }
    return files


@app.route("/items/<username>/align/stop/<lang_from>/<lang_to>/<aling_id>", methods=["POST"])
def stop_alignment(username, lang_from, lang_to, aling_id):
    """Stop alignment process"""
    logging.info(
        f"[{username}]. Stopping alignment for {lang_from}-{lang_to}.")
    user_db_path = os.path.join(con.UPLOAD_FOLDER, username, con.USER_DB_NAME)
    helper.update_alignment_state_by_align_id(
        user_db_path, aling_id, con.PROC_IN_PROGRESS_DONE)
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
