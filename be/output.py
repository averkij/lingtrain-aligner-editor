import pickle
from datetime import datetime

import helper
import output_templates
from aligner import DocLine


def save_tmx(input_file, output_file, lang_from, lang_to, threshold):
    threshold_value = threshold/100
    tmx_template = output_templates.TMX_BLOCK.format(timestamp=datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'), \
        culture_from=helper.get_culture(lang_from), culture_to=helper.get_culture(lang_to))
    with open(output_file, mode="w", encoding="utf-8") as doc_out:
        doc_out.write(output_templates.TMX_BEGIN)
        for line_from_orig, line_from, line_to, candidates in helper.read_processing(input_file):            
            if line_to[0].text and line_to[1] > threshold_value:
                doc_out.write(tmx_template.format(text_from=line_from[0].text.strip(), text_to=line_to[0].text.strip()))
        doc_out.write(output_templates.TMX_END)

def save_plain_text(input_file, output_file, first_lang, threshold):
    threshold_value = threshold/100
    with open(output_file, mode="w", encoding="utf-8") as doc_out:
        for line_from_orig, line_from, line_to, candidates in helper.read_processing(input_file):

            #TODO Clean from newlines because of editing.

            if line_to[0].text and line_to[1] > threshold_value:
                if first_lang:
                    doc_out.write(line_from[0].text.strip() + "\n")
                else:
                    doc_out.write(line_to[0].text.strip() + "\n")
