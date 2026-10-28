#!/usr/bin/env python3
"""Print "depName currentValue" for each custom-manager match in a file.

Python's re stands in for Renovate's RE2 here: the patterns use only the
shared subset (no lookaround or backreferences), with (?<name>) rewritten.
"""
import json
import re
import sys

config = json.load(open(sys.argv[1]))
text = open(sys.argv[2]).read()
found = []
for manager in config["customManagers"]:
    for pattern in manager["matchStrings"]:
        regex = re.compile(pattern.replace("(?<", "(?P<"))
        for m in regex.finditer(text):
            found.append((m.start(), f"{m['depName']} {m['currentValue']}"))
for _, line in sorted(found):
    print(line)
