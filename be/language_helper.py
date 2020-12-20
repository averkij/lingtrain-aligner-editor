import re
import razdel


RU_CODE = "ru"
ZH_CODE = "zh"
DE_CODE = "de"
EN_CODE = "en"
FR_CODE = "fr"
IT_CODE = "it"
TR_CODE = "tr"
ES_CODE = "es"
PL_CODE = "pl"
PT_CODE = "pt"
HU_CODE = "hu"
CZ_CODE = "cz"
LANGUAGES = [RU_CODE, ZH_CODE, DE_CODE, EN_CODE, FR_CODE, IT_CODE, TR_CODE, ES_CODE, PL_CODE, PT_CODE, HU_CODE, CZ_CODE]

pattern_ru_orig = re.compile(r'[a-zA-Z\(\)\[\]\/\<\>•\'\n]+')
double_spaces = re.compile(r'[\s]+')
double_commas = re.compile(r'[,]+')
double_dash = re.compile(r'[-—]+')
german_quotes = re.compile(r'[»«“„]+')
pattern_zh = re.compile(r'[」「“”„‟\x1a⓪①②③④⑤⑥⑦⑧⑨⑩⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽*a-zA-Zа-яА-Я\(\)\[\]\s\n\/\-\:•＂＃＄％＆＇（）＊＋－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》【】〔〕〖〗〘〙〜〟〰〾〿–—‘’‛‧﹏〉]+')
pat_comma = re.compile(r'[\.]+')
first_numbers = re.compile(r'^[0-9,\.]+')
last_punct = re.compile(r'[,\.]+$')
multiple_spaces = re.compile(r'\s+')
pattern_ru = re.compile(r'[a-zA-Z\.\(\)\[\]\/\-\:!?\<\>;•\"\'«»——,]+')
pattern_ru_letters_only = re.compile(r'[^а-яА-Я\s]+')

DEFAULT_PREPROCESSING = [
    (double_spaces, ' '),
    (double_commas, ','),
    (double_dash, '—')
]

def isLangCodeValid(langcode):
    return langcode in LANGUAGES

def split_by_razdel(line):
    return list(x.text for x in razdel.sentenize(line))

def split_zh(line):
    return list(re.findall(u'[^!?。！？\.\!\?]+[!?。！？\.\!\?]?', line, flags=re.U))

def preprocess(line, re_list, splitter):
    for pat, val in re_list:
        line = re.sub(pat, val, line)
    return splitter(line)

def split_by_sentences(lines, langcode):
    line = ' '.join(lines)
    if langcode == RU_CODE:
        sentences = preprocess(line, [
            (pattern_ru_orig, ''),
            *DEFAULT_PREPROCESSING
        ],
        split_by_razdel)
        return sentences
    elif langcode == DE_CODE:
        sentences = preprocess(line, [
            (german_quotes, ''),
            *DEFAULT_PREPROCESSING
        ],
        split_by_razdel)
        return sentences
    elif langcode == ZH_CODE:
        sentences = preprocess(line, [
            (pat_comma, '。'),
            (pattern_zh, '')
        ],
        split_zh)
        return sentences

    #apply default splitting
    sentences = preprocess(line, [
            *DEFAULT_PREPROCESSING
        ],
        split_by_razdel)
    return sentences