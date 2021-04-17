"""Output functions for downloading"""

from datetime import datetime

import editor_helper
import misc
import output_templates


def save_tmx(db_path, output_file, lang_from, lang_to):
    """Save text document in TMX format"""
    tmx_template = output_templates.TMX_BLOCK.format(timestamp=datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'),
                                                     culture_from=misc.get_culture(lang_from), culture_to=misc.get_culture(lang_to))
    with open(output_file, mode="w", encoding="utf-8") as doc_out:
        doc_out.write(output_templates.TMX_BEGIN)
        res = editor_helper.read_processing(db_path)
        for text_from, text_to in res:
            doc_out.write(tmx_template.format(
                text_from=text_from.strip(), text_to=text_to.strip()))
        doc_out.write(output_templates.TMX_END)


def save_plain_text(db_path, output_file, first_lang):
    """Save text document in TXT format"""
    with open(output_file, mode="w", encoding="utf-8") as doc_out:
        res = editor_helper.read_processing(db_path)
        if first_lang:
            text = "\n".join([text_from.strip() for text_from, text_to in res])
        else:
            text = "\n".join([text_to.strip() for text_from, text_to in res])
        doc_out.write(text)
