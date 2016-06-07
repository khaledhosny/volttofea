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

def process_features(data, script, language):
    features = []
    for block in data:
        m = re.match(r'DEF_FEATURE NAME "(.*?.)" TAG "(.*?.)"', block)
        name, tag = m.groups()
        lookups = re.findall(r'LOOKUP "(.*?.)"', block)
        feature = (tag, script, language, lookups)
        features.append(feature)
    return features

def process_langsys(data, script):
    features = []
    for block in data:
        m = re.match(r'DEF_LANGSYS NAME "(.*?.)" TAG "(.*?.)"', block)
        name, tag = m.groups()
        feadata = re.findall(r'(DEF_FEATURE.*?.END_FEATURE)', block, re.DOTALL)
        features.extend(process_features(feadata, script, tag))
    return features

def process_scripts(data):
    features = []
    for block in data:
        m = re.match(r'DEF_SCRIPT NAME "(.*?.)" TAG "(.*?.)"', block)
        name, tag = m.groups()
        langsys = re.findall(r'(DEF_LANGSYS.*?.END_LANGSYS)', block, re.DOTALL)
        features.extend(process_langsys(langsys, tag))
    return features

def make_lookup_name(name):
    return 'l_' + name.replace(' ', '_')

def dump_features(features):
    text = ""
    for feature in features:
        tag, script, language, lookups = feature
        lookups = "\n  ".join(["lookup %s;" % make_lookup_name(l) for l in lookups])
        text += """
feature %s {
 script %s;
 language %s;
  %s
} %s;
""" % (tag, script, language, lookups, tag)
    return text

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
        features = process_scripts(scripts)
        process_groups(groups)
        process_substitutions(sub_lookups)
        process_positioning(pos_lookups)
        process_anchors(anchors)

        out += dump_features(features)
        out += dump_gdef(gdef)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print('Usage: %s fontfile' % sys.argv[0])
        sys.exit(1)
