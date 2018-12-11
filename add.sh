#!/bin/bash
for i in `seq 1 100`; do
	curl -d 'entry='${i} -X 'POST' 'http://10.1.0.1:80/board' &
done
