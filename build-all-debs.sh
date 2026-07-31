#!/bin/bash
set -e
mkdir -p dist
for d in 01-* 02-* 03-* 04-* 05-* 06-* 07-* 08-* 09-* 10-*; do
    if [ -d "$d" ]; then
        echo "Building $d..."
        (cd "$d" && dpkg-buildpackage -us -uc -b)
    fi
done
mv *.deb dist/
echo "All done!"
