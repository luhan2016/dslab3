#!/bin/bash
for i in `seq 1 20`; do
	curl -d 'entry=vessel1:'${i} -X 'POST' 'http://10.1.0.1:80/board' &
	curl -d 'entry=vessel2:'${i} -X 'POST' 'http://10.1.0.2:80/board' &
	curl -d 'entry=vessel3:'${i} -X 'POST' 'http://10.1.0.3:80/board' 
done
