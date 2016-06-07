#!/bin/env python3

import re
import sys

from collections import OrderedDict

from fontTools.ttLib import TTFont

glyph_re = re.compile(r'''DEF_GLYPH\s+"([^"]+)"\s+ID\s+(\d+)\s+(?:(?:UNICODEVALUES\s+"([^"]+)"\s+)|(?:UNICODE\s+(\d+))\s+)?(?:TYPE\s+(MARK|BASE|LIGATURE)\s+)?(?:COMPONENTS\s+(\d+)\s+)?END_GLYPH''')

def process_glyphs(data):
    gdef = {
        "classes": OrderedDict([("BASE", []), ("LIGATURE", []), ("MARK", []), ("COMPONENT", [])])
    }

    for glyph in data:
        m = glyph_re.match(glyph)
        assert m
        gname, gid, univalues, gchar, gclass, gcomponents = m.groups()
        if gclass:
            gdef["classes"][gclass].append(gname)
        assert gname
        assert gid

    return gdef

def dump_gdef(gdef):
    text = ""
    classes = gdef["classes"]
    for k in classes:
        text += "@GDEF_%s = [%s];\n" % (k, " ".join(classes[k]))

    text += "table GDEF {\nGlyphClassDef %s;\n} GDEF;" % ", ".join("@GDEF_%s" % k for k in classes)
    return text

def process_features(data):
    for block in data:
        pass

def process_langsys(data):
    for block in data:
        features = re.findall(r'(DEF_FEATURE.*?.END_FEATURE)', block, re.DOTALL)
        process_features(features)

def process_scripts(data):
    for block in data:
        langsys = re.findall(r'(DEF_LANGSYS.*?.END_LANGSYS)', block, re.DOTALL)
        process_langsys(langsys)

def process_groups(data):
    pass

def process_substitutions(data):
    pass

def process_positioning(data):
    pass

def process_anchors(data):
    pass

def main(filename):
    font = TTFont(filename)
    out = ""

    if "TSIV" in font:
        tsiv = font["TSIV"].data.decode("utf-8").replace("\r", "\n")
        glyphs = re.findall(r'(DEF_GLYPH.*?.END_GLYPH)', tsiv, re.DOTALL)
        scripts = re.findall(r'(DEF_SCRIPT.*?.END_SCRIPT)', tsiv, re.DOTALL)
        groups = re.findall(r'(DEF_GROUP.*?.END_GROUP)', tsiv, re.DOTALL)
        sub_lookups = re.findall(r'DEF_LOOKUP.*?.AS_SUBSTITUTION.*?.END_SUBSTITUTION', tsiv, re.DOTALL)
        pos_lookups = re.findall(r'DEF_LOOKUP.*?.AS_POSITION.*?.END_POSITION', tsiv, re.DOTALL)
        anchors = re.findall(r'(DEF_ANCHOR.*?.END_ANCHOR)', tsiv, re.DOTALL)

        gdef = process_glyphs(glyphs)
        process_scripts(scripts)
        process_groups(groups)
        process_substitutions(sub_lookups)
        process_positioning(pos_lookups)
        process_anchors(anchors)

        out += dump_gdef(gdef)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print('Usage: %s fontfile' % sys.argv[0])
        sys.exit(1)
