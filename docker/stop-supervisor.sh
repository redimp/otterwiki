#!/usr/bin/env sh
# https://serverfault.com/a/922943
printf "READY\n";

while read line; do
  echo "Processing Event: $line" >&2;
  kill $PPID
done < /dev/stdin
