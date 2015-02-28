import re
import sys

from fontTools.ttLib import TTFont

glyph_re = re.compile(r'''DEF_GLYPH\s+"([^"]+)"\s+ID\s+(\d+)\s+(?:(?:UNICODEVALUES\s+"([^"]+)"\s+)|(?:UNICODE\s+(\d+))\s+)?(?:TYPE\s+(MARK|BASE|LIGATURE)\s+)?(?:COMPONENTS\s+(\d+)\s+)?END_GLYPH''')

def process_glyphs(data):
    for glyph in data:
        m = glyph_re.match(glyph)
        assert m
        gname, gid, univalues, gchar, gclass, gcomponents = m.groups()
        assert gname
        assert gid

def process_features(data):
    for feature in data:
        pass

def process_langsys(data):
    for langsys in data:
        features = re.findall(r'(DEF_FEATURE.*?.END_FEATURE)', langsys, re.DOTALL)
        process_features(features)

def process_scripts(data):
    for script in data:
        langsys = re.findall(r'(DEF_LANGSYS.*?.END_LANGSYS)', script, re.DOTALL)
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
    if "TSIV" in font:
        volt = font["TSIV"].data.replace("\r", "\n")
        glyphs = re.findall(r'(DEF_GLYPH.*?.END_GLYPH)', volt, re.DOTALL)
        scripts = re.findall(r'(DEF_SCRIPT.*?.END_SCRIPT)', volt, re.DOTALL)
        groups = re.findall(r'(DEF_GROUP.*?.END_GROUP)', volt, re.DOTALL)
        sub_lookups = re.findall(r'DEF_LOOKUP.*?.AS_SUBSTITUTION.*?.END_SUBSTITUTION', volt, re.DOTALL)
        pos_lookups = re.findall(r'DEF_LOOKUP.*?.AS_POSITION.*?.END_POSITION', volt, re.DOTALL)
        anchors = re.findall(r'(DEF_ANCHOR.*?.END_ANCHOR)', volt, re.DOTALL)

        process_glyphs(glyphs)
        process_scripts(scripts)
        process_groups(groups)
        process_substitutions(sub_lookups)
        process_positioning(pos_lookups)
        process_anchors(anchors)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print 'Usage: %s fontfile' % sys.argv[0]
        sys.exit(1)
