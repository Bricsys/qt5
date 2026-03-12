#!/bin/bash

find . \( -name "*.dylib" -o -regex ".*/\([^/]*\)\.framework/Versions/A/\1$" \) -type f | while read bin; do
    dsymutil "$bin" -o "$1/${2:1}/$(basename "$bin").dSYM" 2>&1 | grep -v "no debug symbols"; true
    strip -S "$bin"
done