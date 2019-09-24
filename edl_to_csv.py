#!/usr/local/bin/python3

import sys
from marker.resolve_marker_edl import ResolveMarkerEDL

edl_file = open(sys.argv[1], 'r')
edl_content = edl_file.read()
edl_file.close()

headers, markers = ResolveMarkerEDL.parse(edl_content)

print(headers)
for m in markers:
    # print(m.in_point.timecode)
    print(m.out_point.frame, m.out_point.timecode)
