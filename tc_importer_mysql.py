import json
import urllib
from xml.dom import minidom
import pprint
import re
#import sqlite3
import MySQLdb
import sys
import time

from lib.Configuration import  *

from optparse import OptionParser

parser = OptionParser()

parser.add_option("-u","--url", dest="url", help="Base url for tests import")
(options, args) = parser.parse_args()

if options.url is None:
	print '  == > ERROR: Please set base URL'
	sys.exit(-1)

base_url = options.url
#tims_id = 'Tvh696219c'
url = "http://tims.cisco.com/xml/"





template_dict = {


	#'title'  :  {
	#				'name': { 
	#							'db_map'   : {'db' : "testcase_data", 'field' : "desc"},
	#					    }
	#			},

	'data'   :  {
					'input'  : { 'db_map' : {'db' : "testcase_data", 'field' : "input_data"} }, 
	            	'output' : { 'db_map' : {'db' : "testcase_data", 'field' : "output_data"} },
	            	'name'   : { 'db_map'   : {'db' : "testcase_data", 'field' : "descr"} }
	            },

	'setup'  :  {
					'name'       : { 'db_map' : {'db' : "testcase_setup", 'field' : "setup_name"} }, 
					'pre_setup'  : { 'db_map' : {'db' : "testcase_setup", 'field' : "pre_data"} }, 
					'post_setup' : { 'db_map' : {'db' : "testcase_setup", 'field' : "post_data"} }
				},

	'device' :  {
					'group' : { 'db_map' : {'db' : "device_group", 'field' : "grp_keyword"} },
					'name' : { 'db_map' : {'db' : "device_list", 'field' : "dev_name"} }
				}


				}


#test2db_map_dict = {
#	'input'      : {'db' : "testcase_data", 'field' : "input_data"}
#	'output'     : {'db' : "testcase_data", 'field' : "output_data"}
#	'pre_setup'  : {'db' : "testcase_setup", 'field' : "pre_data"}
#	'post_setup' : {'db' : "testcase_setup", 'field' : "post_data"}
#	'name'       : {'db' : "testcase_setup", 'field' : "setup_name"}
#	'group'      : {'db' : "device_group", 'field' : "grp_keyword"}
#}


#sys.stdout.write('Collecting TC URLs... ')



#==============================================================================================
# Tests group loading
# Prepare TIMS test cases dictionary
collector_dict = { 'folders' : [], 'test_cases' : [] }
#collector_dict['folders'].append('http://tims.cisco.com/xml/Tvh695901f/entity.svc')
collector_dict['folders'].append(base_url)
t_start = time.time()
# Go through folders tree
while len(collector_dict['folders']) > 0:

	# Parse folder content
	for link in collector_dict['folders']:
		dom = minidom.parse(urllib.urlopen(link))

		# Parse type of contennt (ChildID tag)
		for paragraph in dom.getElementsByTagName('ChildID'):

			# IF folder-> add as folder
			if  paragraph.attributes['entity'].value == 'folder':
				collector_dict['folders'].append(paragraph.attributes['xlink:href'].value)

			# IF case-> add as test_case
			if  paragraph.attributes['entity'].value == 'case':
				collector_dict['test_cases'].append(paragraph.attributes['xlink:href'].value)

		# Clear dictionary from processed folders (due the while statement logic)
		collector_dict['folders'].remove(link)

#pprint.pprint(collector_dict['test_cases'])
print 'DONE:', (time.time()-t_start), 's'

print 'ALL TCs: ', len(collector_dict['test_cases'])

#==============================================================================================

# Connect to DB
conn = MySQLdb.connect(host=PREDEFINED_KEYWORDS['db_host'], # your host, usually localhost
                       user=PREDEFINED_KEYWORDS['db_user'], # your username
                       passwd=PREDEFINED_KEYWORDS['db_passwd'], # your password
                       db=PREDEFINED_KEYWORDS['db_name']) # name of the data base
# Add access by column name
# Add access by column name
#conn.row_factory = sqlite3.Row
c = conn.cursor()

#==============================================================================================
# Skip urls which are already loaded ( speedup import)

c.execute('SELECT tims_id FROM testcase_data')
tc_in_db = c.fetchall()
filtered_urls = []
#print tc_in_db['tims_id']
for tc in tc_in_db:
	#print tc
	if url+tc[0]+'/entity.svc' in collector_dict['test_cases']:
		collector_dict['test_cases'].remove(url+tc[0]+'/entity.svc')

#==============================================================================================

print 'NOT IMPORTED TCs: ', len(collector_dict['test_cases'])

sys.stdout.write('Adding TC to DB... ')


# Process collected links of test cases
for link in collector_dict['test_cases']:

	# Prepare dictionry, data variables
	test_dict = {}
	auto_data = ''
	SQL = ''
	# Get TIMS ID from link
	tims_id =  link.split('http://tims.cisco.com/xml/')[1].split('/entity.svc')[0]

	# Parse XML url
	dom = minidom.parse(urllib.urlopen(link))

	# Find 'AUTO-TEST' paragraph
	for paragraph in dom.getElementsByTagName('Detail'):

		# Get 'AUTO-TEST' paragraph values into auto_data variable
		#print link,paragraph.getElementsByTagName('Name')[0].firstChild.data
		if paragraph.getElementsByTagName('Name')[0].firstChild.data == 'AUTO-TEST':
			auto_data =  paragraph.getElementsByTagName('Value')[0].firstChild.data.splitlines()

	# Parse 'AUTO-TEST' paragraph values into dictionary
	print '==> Processinng: '+link
	for data in auto_data:
		#print 'TC-DATA: ',data
		if len(data) > 1:
			#print '##########################################################'	
			#print data.split('=',1)[0],data.split('=',1)[1]
			# Split each liny by '=', but only once (character could be in data fields, bu always present in the each line)
			
			test_dict[data.split('=',1)[0].strip()] = json.loads(data.split('=',1)[1].strip())

	#pprint.pprint(test_dict)



	OPERATIONS_DICT = {}

	# Process collected auto data options from test_dict
	for option in test_dict:

		# Prepare variables
		SQL_SELECT = ''
		SQL_UPDATE = ''
		fl_in = 0
		sql_statement_array = []

		# Check if option is present in template dict
		if option in template_dict:
			# Check if value for that option is present in template dict
			for value in test_dict[option]:
				if value in template_dict[option]:
					#print 'SQL:: ', 'UPDATE '+template_dict[option][value]['db_map']['db']+' SET '+template_dict[option][value]['db_map']['field']+' = '+re.escape(json.dumps(test_dict[option][value]))
					#print 'SQL:: ', 'UPDATE '+template_dict[option][value]['db_map']['db']+' SET '+template_dict[option][value]['db_map']['field']+' = '+json.dumps(test_dict[option][value])

					##########################################################################################################################################################
					# Setup data parser
					##########################################################################################################################################################
					if option == 'setup':

						
						if fl_in == 0:
							
							OPERATIONS_DICT.update( { '1' :  { 
																'SQL_UPD' : '',
																'SQL_SEL' : '',
																'UPD_FIELDS' : [],
																'UPD_DATA' : [],
																'SEL_DATA' : [],
																'UPD_FLAG' : False
															  } 
													} )

							SQL_UPDATE = 'INSERT INTO '+template_dict[option][value]['db_map']['db']+' ( %s ) VALUES( %%s, %%s, %%s )'
							OPERATIONS_DICT['1']['SQL_UPD'] = SQL_UPDATE
							OPERATIONS_DICT['1']['UPD_FLAG'] = True
							#print SQL_UPDATE	

						fl_in = 1

						if value == 'name':
							#print 'SELECT setup_id FROM '+template_dict[option][value]['db_map']['db']+' WHERE '+template_dict[option][value]['db_map']['field']+' = "'+test_dict[option][value]+'"'
							SQL_SELECT = 'SELECT setup_id FROM '+template_dict[option][value]['db_map']['db']+' WHERE '+template_dict[option][value]['db_map']['field']+' =  %s'
							OPERATIONS_DICT['1']['SQL_SEL'] = SQL_SELECT

							#OPERATIONS_DICT['1']['SEL_DATA'].append(template_dict[option][value]['db_map']['field'])
							OPERATIONS_DICT['1']['SEL_DATA'].append(test_dict[option][value])

						if value == 'pre_setup':

							OPERATIONS_DICT['1']['UPD_FIELDS'].append(template_dict[option][value]['db_map']['field'])
							OPERATIONS_DICT['1']['UPD_DATA'].append(json.dumps(test_dict[option][value]))

						if value == 'post_setup':
			
							OPERATIONS_DICT['1']['UPD_FIELDS'].append(template_dict[option][value]['db_map']['field'])
							OPERATIONS_DICT['1']['UPD_DATA'].append(son.dumps(test_dict[option][value]))
						if value == 'name':
			
							OPERATIONS_DICT['1']['UPD_FIELDS'].append(template_dict[option][value]['db_map']['field'])
							OPERATIONS_DICT['1']['UPD_DATA'].append(test_dict[option][value])

					##########################################################################################################################################################
					# Device data parser
					##########################################################################################################################################################
					if option == 'device':
						#print 'DEVICE'

						if fl_in == 0:

							OPERATIONS_DICT.update( { '2' :  { 
																'SQL_UPD' : '',
																'SQL_SEL' : '',
																'UPD_FIELDS' : [],
																'UPD_DATA' : [],
																'SEL_DATA' : [],
																'UPD_FLAG' : False
															  } 
													} )


						fl_in = 1

						if value == 'group':
							SQL_SELECT = 'SELECT grp_id FROM '+template_dict[option][value]['db_map']['db']+' WHERE '+template_dict[option][value]['db_map']['field']+' = %s'
							OPERATIONS_DICT['2']['SQL_SEL'] = SQL_SELECT
							OPERATIONS_DICT['2']['SEL_DATA'].append(test_dict[option][value])

						#if value == 'device':


					##########################################################################################################################################################
					# Data data parser
					##########################################################################################################################################################
					if option == 'data':
						#print 'DATA'

						if fl_in == 0:

							OPERATIONS_DICT.update( { '3' :  { 
																'SQL_UPD' : '',
																'SQL_SEL' : '',
																'UPD_FIELDS' : [],
																'UPD_DATA' : [],
																'SEL_DATA' : [],
																'UPD_FLAG' : False
															  } 
													} )

							SQL_SELECT = 'SELECT tims_id FROM '+template_dict[option][value]['db_map']['db']+' WHERE tims_id =  %s'
							OPERATIONS_DICT['3']['SQL_SEL'] = SQL_SELECT
							OPERATIONS_DICT['3']['SEL_DATA'].append(tims_id)

							SQL_UPDATE = 'INSERT INTO '+template_dict[option][value]['db_map']['db']+' ( setup_id, grp_id, in_group, dev_name, tims_id, %s ) VALUES( %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s )'
							OPERATIONS_DICT['3']['SQL_UPD'] = SQL_UPDATE
							OPERATIONS_DICT['3']['UPD_FLAG'] = True

						fl_in = 1


						if value == 'input':
			
							OPERATIONS_DICT['3']['UPD_FIELDS'].append(template_dict[option][value]['db_map']['field'])
							OPERATIONS_DICT['3']['UPD_DATA'].append(json.dumps(test_dict[option][value]))


						if value == 'output':
			
							OPERATIONS_DICT['3']['UPD_FIELDS'].append(template_dict[option][value]['db_map']['field'])
							OPERATIONS_DICT['3']['UPD_DATA'].append(json.dumps(test_dict[option][value]))

						if value == 'name':
			
							OPERATIONS_DICT['3']['UPD_FIELDS'].append(template_dict[option][value]['db_map']['field'])
							OPERATIONS_DICT['3']['UPD_DATA'].append(test_dict[option][value])


						

				else:
					print 'WARNING:: Incorrect value'

			#print SQL_UPDATE, sql_statement_array

		else:
			print 'WARNING:: Incorrect option'

					
	#print SQL_UPDATE, sql_statement_array
	#pprint.pprint(OPERATIONS_DICT)


	

	sel_result = None

	setup_id = None
	grp_id = None
	dev_name = None
	in_group = None
	
	#print sorted(OPERATIONS_DICT)

	for order in sorted(OPERATIONS_DICT):


		if len(OPERATIONS_DICT[order]['SQL_SEL']) > 0:
			#print OPERATIONS_DICT[order]['SQL_SEL'], OPERATIONS_DICT[order]['SEL_DATA']
			c.execute(OPERATIONS_DICT[order]['SQL_SEL'], OPERATIONS_DICT[order]['SEL_DATA'])

			select_result = c.fetchall()

			if len(select_result) == 1:
				sel_result = select_result[0][0]


		if order == '1':
			setup_id = sel_result
			if len(select_result) < 1 and len(OPERATIONS_DICT[order]['SQL_UPD']) > 0:
				c.execute( OPERATIONS_DICT[order]['SQL_UPD'] % ','.join(OPERATIONS_DICT[order]['UPD_FIELDS']) , OPERATIONS_DICT[order]['UPD_DATA'])
				conn.commit()
				setup_id = c.lastrowid
			else:
				print 'WARNING:: Setup data already exist', tims_id

			#print 'setup_id == ', setup_id

		if order == '2':
			grp_id = sel_result
			#print 'grp_id == ', grp_id

			fl_uniq_device = False

			if 'name' in test_dict['device']:
				#print test_dict['device']['name']
				c.execute('SELECT dev_name FROM device_list WHERE dev_name = %s ',  [ test_dict['device']['name'] ] ) # TODO: not working now
		
				if c.fetchone() is not None:
					fl_uniq_device = True


			if fl_uniq_device :
				#print 'dev_name == ', dev_name
				dev_name = test_dict['device']['name']
				in_group = 0

			if not fl_uniq_device:
				in_group = 1
				#print 'in_group == ', in_group
			
		if order == '3':
			if len(select_result) < 1 and len(OPERATIONS_DICT[order]['SQL_UPD']) > 0:
				c.execute( OPERATIONS_DICT[order]['SQL_UPD'] % ','.join(OPERATIONS_DICT[order]['UPD_FIELDS']) , [ setup_id, grp_id, in_group, dev_name, tims_id ] + OPERATIONS_DICT[order]['UPD_DATA'])
				conn.commit()
			else:
				print 'WARNING:: TC  data already exist', tims_id


			#if order == '3':
			#	print 'grp_id == ', sel_result

print 'DONE'
		



