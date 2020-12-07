import pickle
import constants as con

from aligner import DocLine

def edit_doc(edit_file, line_id, text, text_type=con.TYPE_TO):
    docs = pickle.load(open(edit_file, "rb"))
    line_to_find = DocLine(line_id)
    for doc in docs["items"]:
        if line_to_find in doc:
            if text_type == con.TYPE_TO:
                tr = doc[line_to_find]["to"]
                doc[line_to_find]["to"] = (
                        DocLine(
                            tr[0].line_id,
                            text,
                            tr[0].proxy),
                        tr[1],
                        True) #IsEdited = True
            elif text_type == con.TYPE_FROM:
                doc[line_to_find]["from"] = (
                    DocLine(
                        line_id,
                        text
                        #TODO proxy saving for FROM text
                        # ,proxy= 
                        ),
                    True) #IsEdited = True
            else:
                raise Exception("Incorrect text type.")
            break

    pickle.dump(docs, open(edit_file, "wb"))