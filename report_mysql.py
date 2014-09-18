from py.xml import html
from py.xml import raw

import time
import datetime
import py
import cgi

#import sqlite3
import MySQLdb
import MySQLdb.cursors

import json

import xml.etree.ElementTree as ET
from optparse import OptionParser
import sys

from lib.Configuration import  *
######################################################################################################
# Prepare variables
numtests = 0
suite_time_delta = 0.0
passed = 0
skipped = 0
failed = 0
errors = 0

# Connect to DB
#conn = sqlite3.connect('KFA-TEST-JSON-IMPORT')
conn = MySQLdb.connect(host=PREDEFINED_KEYWORDS['db_host'], # your host, usually localhost
                       user=PREDEFINED_KEYWORDS['db_user'], # your username
                       passwd=PREDEFINED_KEYWORDS['db_passwd'], # your password
                       db=PREDEFINED_KEYWORDS['db_name'], # name of the data base
                       cursorclass=MySQLdb.cursors.DictCursor) # name of the data base
# Enable access by column name
#conn.row_factory = sqlite3.Row
c = conn.cursor()

if(c):
    print("True")
else:
    print("False")

######################################################################################################
parser = OptionParser()
parser.add_option("-f","--file", dest="file", help="JInit XML report file")
parser.add_option("-o","--output", dest="output", help="Output HTML report file")
(options, args) = parser.parse_args()

if options.file is None:
  print '  == > ERROR: Please set JUnit file source'
  sys.exit(-1)

# Set JUNIT report filename
filename = options.file
# Parse report XML tree
tree = ET.parse(filename)
root = tree.getroot()
# Parse root XML attributes
if root.tag == 'testsuite':
    numtests = int(root.attrib['tests'])
    suite_time_delta = float(root.attrib['time'])
    
    passed = int(root.attrib['tests'])-int(root.attrib['failures'])
    skipped = int(root.attrib['skips'])
    failed = int(root.attrib['failures'])
    errors = int(root.attrib['errors'])
######################################################################################################

# Open HTLM report file
if options.output is None:
  logfile = py.std.codecs.open(options.file+'.html', 'w', encoding='utf-8')
else:
  logfile = py.std.codecs.open(options.output+'.html', 'w', encoding='utf-8')

# Get info for specified report from the DB
c.execute("SELECT date, test_run_cnt, devices, location, tests, filename FROM testcase_execution_log WHERE filename = %s ORDER BY date DESC ", [filename])
conf_data = c.fetchone()

conn.close()

if conf_data  is None:
  conf_data = {}
  conf_data['date'] = 'Date'
  conf_data['location'] = 'Location' 
  conf_data['devices'] = '"Device(s)"'
  conf_data['tests'] =  '"Test(s)"'
  conf_data['test_run_cnt'] = None
# Set test configuratios circumstances
configuration = {
            'Date'      : conf_data['date'],
            'Location'  : conf_data['location'],
            'Device(s)' : ', '.join(json.loads(conf_data['devices'])),
            'Test(s)'   : ', '.join(json.loads(conf_data['tests'])),
            'TestRun'   : str(conf_data['test_run_cnt'])
            }

# Prepare variables
test_logs = []
links_html = []
additional_html = []
generated = datetime.datetime.now()
tims_base_url = 'http://tims.cisco.com/warp.cmd?ent='



######################################################################################################
# Prepare variables
testclass = ''
testmethod = ''
time = 0
name = ''
path = ''
result = ''
report_log = ''
######################################################################################################


# Go throught report XML
for child in root:
    links_html = []
    additional_html = []

    # IF tag is testcase -> extract testclass, time, and testmethod
    if child.tag == 'testcase':# and child.attrib['']:
        testclass = child.attrib['classname']
        testmethod = child.attrib['name']
        time = float(child.attrib['time'])

        # Extract TIMS ID from testmethod
        try:
            name = testmethod.split('[')[1].split(' |')[0]
        except:
            name = ''
        # Generate TIMS URL
        path = tims_base_url+name

    # Flag for Failed test cases
    fl_fail = False
    # Go throught testcase child XML structure
    for post_child in child:

        # IF Failed test -> set fl_fail flag and mark test as Failed
        if child.tag == 'testcase' and post_child.tag =='failure':
            result = 'Failed'
            report_log = post_child.text
            fl_fail = True
        # IF fl_fail flasg is set add stdout info from log, ELSE -> mark as Passed
        elif child.tag == 'testcase' and post_child.tag =='system-out':
            if fl_fail:
                result = 'Failed'
                report_log += post_child.text
            else:
                result = 'Passed'
                report_log = post_child.text
        # IF skipped-> mark as Skipped
        elif child.tag == 'testcase' and post_child.tag =='skipped':
            result = 'Skipped'
            report_log = post_child.text

######################################################################################################
    # Generate TIMS link in HTML from gathered data
    links_html = html.a(name, href=path, target='_blank')
    log = html.div(class_='log')

    # Paint traceback
    for line in report_log.splitlines():
        separator = line.startswith('_ ' * 10)
        if separator:
            log.append(line[:80])
        else:
            exception = line.startswith("E   ")
            #print line
            if exception:
                log.append(html.span(raw(cgi.escape(line)), class_='error'))
            else:
                log.append(raw(cgi.escape(line)))

        log.append(html.br())
    # Add traceback as debug HTML section
    additional_html.append(log)
######################################################################################################
    # Generate HTML row with all data  
    test_logs.append(html.tr([
                    html.td(result, class_='col-result'),
                    html.td(testclass, class_='col-class'),
                    html.td(testmethod, class_='col-name'),
                    html.td(round(time, 3), class_='col-duration'),
                    html.td(links_html, class_='col-links'),
                    html.td(additional_html, class_='debug')], class_=result.lower() + ' results-table-row'))


# Generate HTML doc
doc = html.html(
           html.head(
               html.meta(charset='utf-8'),
               html.title('Test Report'),
               html.link(rel='stylesheet', href='html/style.css'),
               html.script(src='html/jquery.js'),
               html.script(src='html/main.js')),
           html.body(
               html.p('Report generated on %s at %s by ASM %s' % (
                   generated.strftime('%d-%b-%Y'),
                   generated.strftime('%H:%M:%S'),
                   'v0.0.1'),
               html.h2('Configuration'),
               html.table(
                   [html.tr(html.td(k), html.td(v)) for k, v in sorted(configuration.items()) if v],
                   id='configuration'),
               html.h2('Summary'),
               html.p(
                   '%i tests ran in %i seconds.' % (numtests , suite_time_delta ), #'''numtests''' '''suite_time_delta'''
                   html.br(),
                   html.span('%i passed' % passed, class_='passed'), ', ', #'self.passed'
                   html.span('%i skipped' % skipped, class_='skipped'), ', ', #'self.skipped'
                   html.span('%i failed' % failed, class_='failed'), ', ', #'self.failed'
                   html.span('%i errors' % errors, class_='error'), '.', #'self.errors'
                   html.br()),
                   #html.span('%i expected failures' % 0, class_='skipped'), ', ', #'self.xfailed'
                   #html.span('%i unexpected passes' % 0, class_='failed'), '.'), #'self.xpassed'
               html.h2('Results'),
               html.table([
                   html.thead(html.tr([
                       html.th('Result', class_='sortable', col='result'),
                       html.th('Class', class_='sortable', col='class'),
                       html.th('Name', class_='sortable', col='name'),
                       html.th('Duration', class_='sortable numeric', col='duration'),
                       html.th('Links')]), id='results-table-head'),
                   html.tbody(*test_logs, id='results-table-body')], id='results-table'))))

# Write HTML report file
logfile.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">' + doc.unicode(indent=2))
logfile.close()