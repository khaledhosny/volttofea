#!/bin/env python3

import re
import sys

from collections import OrderedDict

from fontTools.ttLib import TTFont

glyph_re = re.compile(r'''DEF_GLYPH\s+"([^"]+)"\s+ID\s+(\d+)\s+(?:(?:UNICODEVALUES\s+"([^"]+)"\s+)|(?:UNICODE\s+(\d+))\s+)?(?:TYPE\s+(MARK|BASE|LIGATURE)\s+)?(?:COMPONENTS\s+(\d+)\s+)?END_GLYPH''')

def process_glyphs(data):
    glyphs = {
        "classes": OrderedDict([("BASE", []), ("LIGATURE", []), ("MARK", []), ("COMPONENT", [])])
    }

    for glyph in data:
        m = glyph_re.match(glyph)
        assert m
        gname, gid, univalues, gchar, gclass, gcomponents = m.groups()
        if gclass:
            glyphs["classes"][gclass].append(gname)
        assert gname
        assert gid

    return glyphs

def dump_glyphs(glyphs):
    text = ""
    classes = glyphs["classes"]
    for c in classes:
        text += "@GDEF_%s = [%s];\n" % (c, " ".join(classes[c]))

    text += """
table GDEF {
 GlyphClassDef %s;
} GDEF;""" % ", ".join("@GDEF_%s" % c for c in classes)
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

def sanitize_name(name, prefix):
    return prefix + '_' + name.replace(' ', '_')

def dump_features(features):
    text = ""
    for feature in features:
        tag, script, language, lookups = feature
        lookups = "\n  ".join(["lookup %s;" % sanitize_name(l, 'l') for l in lookups])
        text += """
feature %s {
 script %s;
 language %s;
  %s
} %s;
""" % (tag, script, language, lookups, tag)
    return text

def process_enums(data):
    glyphs = []
    for block in data:
        glyphs.extend(re.findall(r'GLYPH "(.*?.)"', block))
    return glyphs

def process_groups(data):
    groups = OrderedDict()
    for block in data:
        m = re.match(r'DEF_GROUP "(.*?.)"', block)
        name = m.groups()[0]
        enums = re.findall(r'(ENUM.*?.END_ENUM)', block, re.DOTALL)
        groups[name] = process_enums(enums)
    return groups

def dump_groups(groups):
    text = ""
    for name in groups:
        glyphs = groups[name]
        text += '%s = [%s];' % (sanitize_name(name, '@g'), ' '.join(glyphs))
        text += '\n'
    return text

flags_map = {
    "SKIP_MARKS": "IgnoreMarks",
    "SKIP_BASE": "IgnoreBaseGlyphs",
    # LIGATURES?
    "DIRECTION_RTL": "RightToLeft",
    # ???
}

ignored_flags = ["PROCESS_BASE", "PROCESS_MARKS", "ALL", "DIRECTION_LTR"]

def process_flags(flags):
    out = []

    flags = flags.replace("DIRECTION ", "DIRECTION_")
    flags = flags.split(" ")
    for flag in flags:
        if flag in flags_map:
            out.append(flags_map[flag])
        elif flag not in ignored_flags:
            raise NotImplemented("Unknown flag: %s" % flag)

    return out

def process_substitutions(data):
    lookups = OrderedDict()
    for block in data:
        m = re.match(r'DEF_LOOKUP "(.*?.)" (.*.)', block)
        name, flags = m.groups()
        context = re.findall(r'IN_CONTEXT(.*?.)END_CONTEXT', block, re.DOTALL)
        context = [c.strip() for c in context if c.strip()]
        if not context:
            # Simple substitution
            subs = []
            for sub in re.findall(r'SUB (.*?.)WITH (.*?.)END_SUB', block, re.DOTALL):
                subs.append([process_enums([i]) for i in sub])
            flags = process_flags(flags)
            lookups[name] = (flags, subs)
        else:
            pass

    return lookups

def dump_substitutions(substitutions):
    text = ""
    for name in substitutions:
        flags, subs = substitutions[name]
        name = sanitize_name(name, 'l')
        if not flags:
            flags = "0"
        flags = " ".join(flags)
        subs = "\n  ".join(["sub %s by %s;" % (" ".join(s[0]), " ".join(s[1])) for s in subs])
        text += """
lookup %s {
 lookupflag %s
  %s
} %s;
""" % (name, flags, subs, name)

    return text

def process_positioning(data):
    pass

def process_anchors(data):
    pass

def main(filename, outfilename):
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

        glyphs = process_glyphs(glyphs)
        features = process_scripts(scripts)
        groups = process_groups(groups)
        substitutions = process_substitutions(sub_lookups)
        process_positioning(pos_lookups)
        process_anchors(anchors)

        out += dump_substitutions(substitutions)
        out += dump_groups(groups)
        out += dump_features(features)
        out += dump_glyphs(glyphs)
        out += "\n"

        with open(outfilename, 'w') as outfile:
            outfile.write(out)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        print('Usage: %s fontfile feafile' % sys.argv[0])
        sys.exit(1)
