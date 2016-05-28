#!/usr/bin/env python
# -*- coding: utf8

import os
from os.path import join
import csv
from datetime import datetime
from collections import defaultdict
from itertools import chain
import logging
logger = logging.getLogger('holdeplasser_uten_vei_to_html')

import requests
from jinja2 import Template

# utf8 file utility:
import codecs
def open_utf8(filename, *args, **kwargs):
    return codecs.open(filename, *args, encoding="utf-8-sig", **kwargs)
def read_utf8_file(filename):
    logger.debug('reading %s', filename)
    with open_utf8(filename, 'r') as f:
        return f.read()
def write_utf8_file(filename, content):
    logger.debug('writing %s', filename)
    with open_utf8(filename, 'w') as f:
        return f.write(content)
    
def get_spreadsheet():
    logger.debug('requesting spredsheet')
    response = requests.get('https://docs.google.com/spreadsheets/d/12-m7neLrK9MmQnNfBYsZMWluiBwBPFGNhW98ErWlNfg/export?format=csv')
    response.raise_for_status()
    logger.debug('returning spredsheet')    
    return response.content.split('\n')

def generate_map(holdeplassId, lat, lon):
    osm_url_api = 'null'
    map_html = '<div id="map{0}" style="width: 256px; height: 256px;position: relative"></div>'.format(holdeplassId)
    map_html += '<script>create_map(map{holdeplassId}, {lat}, {lon}, {osm_url_api})</script>'.format(holdeplassId=holdeplassId,
                                                                                                 osm_url_api=osm_url_api,
                                                                                                 lat=lat,
                                                                                                 lon=lon)
    return map_html

def generate_row(holdeplassId, lat, lon, *args):
    row = list()
    row.append(holdeplassId)
    row.append(lat)
    row.append(lon)
    for a in args: row.append(a.decode('utf8'))
    map_html = generate_map(holdeplassId, lat, lon)
    row.append(map_html)
    return row

def generate_tables():
    tables = defaultdict(list) # rows, by status
    spreadsheet = get_spreadsheet()
    reader = csv.reader(spreadsheet, delimiter=',', quotechar='"')
    first_line = reader.next()
    info = first_line[0].decode('utf8')
    
    for count, line in enumerate(reader):
        # if line[1] == 'Lat/Lon':
        #     print 'header', line
        split_lat_lon = line[1].split(',')
        if len(split_lat_lon) != 2:
            continue

        holdeplassId = line[0]
        lat, lon = split_lat_lon
        user_nick, status, comment = line[2], line[3], line[4]
        row = generate_row(holdeplassId, lat, lon,
                           user_nick, status, comment)
        status = status.lower()
        if status == '':
            status = 'ingen'
        tables[status].append(row)

    #print tables.keys()
    return tables, info

def render_and_write(filename, template, **kwargs):
    page = template.render(**kwargs)
    write_utf8_file(filename, page)

def write_csv(filename, table, header):
    with open_utf8(filename, 'w') as f:
        for row in chain([header], table):
            for item in row[:-1]:
                f.write('"%s";' % item)
            f.write('\n')

def main(template_dir='.', output_dir='.'):
    tables, info_index = generate_tables()
    index_template_filename = join(template_dir, 'index_template.html')
    index_template = Template(read_utf8_file(index_template_filename))
    template_filename = join(template_dir, 'template.html')
    template = Template(read_utf8_file(template_filename))

    last_update_datetime = datetime.now()
    last_update = last_update_datetime.strftime('%Y-%m-%d %H:%M')

    header = ['HoldeplassID', 'lat', 'lon', 'Jobbes med av', 'Status', 'Kommentar', 'Kart']
    kwargs= dict(last_update=last_update, header=header)
    
    index_info = list()
    total_length = 0
    for status in tables:
        t = tables[status]
        # write csv
        csvfile = join(output_dir, '%s-holdeplass-uten-vei.csv' % status)
        write_csv(csvfile, t, header)
        
        output_filename = '%s-holdeplass-uten-vei.html' % status
        output_filename_path = join(output_dir, output_filename)
        title = 'Holdeplasser med status "%s"' % status.capitalize()
        #print title
        info = u'csv filen <a href={0}>{0}</a> inneholder all informasjonen i tabellen under, denne kan åpnes i JOSM'.format(csvfile)
        render_and_write(output_filename, template, table=t, info=info, **kwargs)

        logger.info('status = "%s": %s', status, len(t))
        index_info.append((output_filename, status, [status, len(t)]))
        total_length += len(t)

    # all
    all_tables = chain(*tables.values())
    output_filename = 'alle-holdeplass-uten-vei.html'
    output_filename_path = join(output_dir, output_filename)
    render_and_write(output_filename_path, template, table=all_tables, title='Alle holdeplasser', **kwargs)
    index_info.append((output_filename, 'Alle', ['Alle', total_length]))

    # index
    output_filename = join(output_dir, 'index.html')
    header = ['Status', 'Antall']
    render_and_write(output_filename, index_template, table=index_info, header=header, info=info_index)
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s:%(levelname)s:%(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    main()
