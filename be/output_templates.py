"""Output templates"""

TMX_BEGIN = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<tmx version="1.4">
    <header creationtool="Lingtrain Aligner" segtype="sentence" adminlang="ru-RU" srclang="ru-RU" datatype="xml" creationdate="20190909T153841Z" creationid="LINGTRAIN"/>
    <body>"""

TMX_END = """
    </body>
</tmx>"""

TMX_BLOCK = """
        <tu creationdate="{timestamp}" creationid="LINGTRAIN">
            <tuv xml:lang="{culture_from}">
                <seg>{{text_from}}</seg>
            </tuv>
            <tuv xml:lang="{culture_to}">
                <seg>{{text_to}}</seg>
            </tuv>
        </tu>"""
