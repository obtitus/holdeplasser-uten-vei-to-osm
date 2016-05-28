#!/bin/sh
/opt/local/bin/python holdeplasser_uten_vei_to_html.py
git add *.html *.csv
git com -am "data update"
git push
