#!/bin/sh
/opt/local/bin/python holdeplasser_uten_vei_to_html.py
git add *
git com -am "data update"
git push
