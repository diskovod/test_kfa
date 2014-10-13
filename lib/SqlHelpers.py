import MySQLdb
import MySQLdb.cursors

from Configuration import  *
#############################################################################################	
# SQL tools
#############################################################################################

def getDbConnector():
	return MySQLdb.connect(host=PREDEFINED_KEYWORDS['db_host'], # your host
						   user=PREDEFINED_KEYWORDS['db_user'], # your username
						   passwd=PREDEFINED_KEYWORDS['db_passwd'], # your password
						   db=PREDEFINED_KEYWORDS['db_name'], # name of the data base
						   cursorclass=MySQLdb.cursors.DictCursor) # enable hashing response

#############################################################################################
# TIMS Helpers
#############################################################################################
def genID(cursor, test_ids, table_type='device'):

	TC_TABLE_MAP = {'device' : 'testcase_data', 'host' : 'testcase_data_host'}

	# Split test ids by , or -
	sequence_ids = test_ids.split(',')
	range_ids = test_ids.split('-')

	# IF not sequence
	if  sequence_ids == [test_ids]:
		# AND not range
		if  range_ids == [test_ids]:
			# return 0
			test_array, test_tpl = genIDTemplate( conv_id_TIMStoDB(cursor, sequence_ids, table_type) )
			return  test_array, 'AND '+TC_TABLE_MAP[table_type]+'.tc_id IN(%s)' % test_tpl
		# ELSE return appropriate SQL statement
		else:
			test_array, test_tpl = genIDRange( conv_id_TIMStoDB(cursor, range_ids, table_type) )
			return test_array, 'AND '+TC_TABLE_MAP[table_type]+'.tc_id BETWEEN %s AND %s'
	else:
		test_array, test_tpl = genIDTemplate( conv_id_TIMStoDB(cursor, sequence_ids, table_type) )
		return  test_array, 'AND '+TC_TABLE_MAP[table_type]+'.tc_id IN(%s)' % test_tpl

def conv_id_TIMStoDB(cursor, raw_test_ids, table_type='device'):


	TC_TABLE_MAP = {'device' : 'testcase_data', 'host' : 'testcase_data_host'}

	#print raw_test_ids
	#  Check if TC id is TIMS id
	if raw_test_ids[0][:3] == 'Tvh' and raw_test_ids[0][-1] == 'c':
		# IF TIMS -> Select reald DB ids
		SQL = "SELECT tc_id FROM "+TC_TABLE_MAP[table_type]+" WHERE tims_id = %s OR tims_id = %s"

		# Fix one ID for 2 value in the template
		if len(raw_test_ids) > 1:
			SQL = "SELECT tc_id FROM "+TC_TABLE_MAP[table_type]+" WHERE tims_id IN ("+','.join(['%s']*len(raw_test_ids))+")"
			cursor.execute( SQL , raw_test_ids)
		else:
			cursor.execute( SQL , [raw_test_ids[0], raw_test_ids[0]] )

		converted_test_ids = cursor.fetchall()
		#print
		return [test['tc_id'] for test in converted_test_ids]
	else:
		# ELSE -> return back original ids
		return raw_test_ids

def genIDTemplate(test_ids):
	# Fix for last test ID in SQL expression
	test_cnt_fix = '%s'
	test_cnt_tpl = ''

	# Split IDs into array for SQLLite prepared statement fix
	#test_ids_array = test_ids.split(',')
	test_ids_array = test_ids
	# TODO fix test_ids_array
	tests_cnt = len(test_ids_array)

	# SQLite fix for many options in prepated statement
	for i in range(tests_cnt-1):
		test_cnt_tpl += '%s,'

	test_cnt_tpl += test_cnt_fix

	return test_ids_array, test_cnt_tpl

def genIDRange(test_ids):
	test_cnt_tpl = ''
	test_ids_array = test_ids
	return test_ids_array, test_cnt_tpl

#############################################################################################
# Data getters
#############################################################################################

def getGroups(cursor, device_name, test_ids, table_type='device'):


	TABLE_MAP = {'device' : 'device_group', 'host': 'host_group'}
	FIELD_MAP = {'device' : 'dev_name', 'host' : 'host_shortname' }
	HOST_LIST_MAP = {'device' : 'device_list', 'host': 'host_list'}
	TC_TABLE_MAP = {'device' : 'testcase_data', 'host' : 'testcase_data_host'}

	#ID_MAP = {'device' : 'grp_id', 'host': 'host'}

	SQL = ""
	#SQL_BASE = "SELECT device_group.grp_id FROM device_group"
	SQL_BASE = "SELECT grp_id FROM "+TABLE_MAP[table_type]


	# Check if TC ID filter is applied
	#if test_ids:

		# Generate data for TC IDs template
	#	test_ids_array, test_cnt_tpl = genIDTemplate(test_ids)

		# Get device groups
	#	if device_name is not None:
	#		SQL = SQL_BASE + ", testcase_data WHERE device_group.grp_id = testcase_data.grp_id AND device_group.grp_id IN(SELECT grp_id FROM device_list WHERE dev_name LIKE %s) AND testcase_data.tc_id IN ("+test_cnt_tpl+")"
	#		cursor.execute( SQL , [ str(device_name)+'%' ] + test_ids_array )
	#	else:
	#		SQL = SQL_BASE + ", testcase_data WHERE device_group.grp_id = testcase_data.grp_id AND testcase_data.tc_id IN ("+test_cnt_tpl+")"
	#		cursor.execute( SQL , [] + test_ids_array )
	# No TC Filtering
	#else:

	# Get device groups
	if device_name is not None:
		SQL = SQL_BASE + " WHERE grp_id IN (SELECT grp_id FROM "+HOST_LIST_MAP[table_type]+" WHERE "+FIELD_MAP[table_type]+" LIKE %s)"
		cursor.execute( SQL , [ str(device_name)+'%' ] )

	elif test_ids is not None:
		test_array, test_tpl = genIDTemplate(test_ids.split(','))
		SQL = SQL_BASE + " WHERE grp_id IN (SELECT DISTINCT grp_id FROM "+TC_TABLE_MAP[table_type]+" WHERE tims_id IN ("+test_tpl+"))"
		cursor.execute( SQL , test_array )
	else:
		SQL = SQL_BASE
		cursor.execute( SQL )

	#print SQL
	return cursor.fetchall()

def getDevices(cursor, group, location, device_name, test_ids, table_type='device'):
	# Get devices for each group
	# TODO: Rework duplication in tests_ids SQL

	if table_type == 'device':
	# Load Devices

		if test_ids is None and device_name is not None:

			cursor.execute("SELECT dev_id, dev_host, dev_name, descr FROM device_list WHERE grp_id = %s AND loc_id = (SELECT loc_id FROM location WHERE loc_name = %s) AND dev_name LIKE %s",
				[ str(group), location, device_name+'%' ])

		elif test_ids is not None and device_name is None:

			cursor.execute("SELECT dev_id, dev_host, dev_name, descr FROM device_list WHERE grp_id = %s AND loc_id = (SELECT loc_id FROM location WHERE loc_name = %s)",
				[ str(group), location, ])

		elif test_ids is not None and device_name is not None:
			cursor.execute("SELECT dev_id, dev_host, dev_name, descr FROM device_list WHERE grp_id = %s AND loc_id = (SELECT loc_id FROM location WHERE loc_name = %s) AND dev_name LIKE %s",
				[ str(group), location, device_name+'%' ])


	elif table_type == 'host':
	# Load Hosts

		if test_ids is None and device_name is not None:

			cursor.execute("SELECT host_id, host_hostname, host_shortname, descr FROM host_list WHERE grp_id = %s  AND host_hostname LIKE %s",
				[ str(group), device_name+'%' ])

		elif test_ids is not None and device_name is None:

			cursor.execute("SELECT host_id, host_hostname, host_shortname, descr FROM host_list WHERE grp_id = %s ",
				[ str(group), ])

		elif test_ids is not None and device_name is not None:
			cursor.execute("SELECT host_id, host_hostname, host_shortname, descr FROM host_list WHERE grp_id = %s  AND host_hostname LIKE %s",
				[ str(group), device_name+'%' ])


	#result = cursor.fetchall()
	#print result
	#return result
	return cursor.fetchall()

def getTests(cursor, group, test_ids, table_type='device'):

	TC_TABLE_MAP = {'device' : 'testcase_data', 'host' : 'testcase_data_host'}
	TC_FIELD_NAME_MAP = {'device' : 'dev_name', 'host' : 'host_shortname'}

	SQL = ""
	SQL_BASE = "SELECT "+TC_FIELD_NAME_MAP[table_type]+", setup_id, input_data, output_data, tims_id, descr FROM "+TC_TABLE_MAP[table_type]+" WHERE type_id = 1"



	# Check if TC ID filter is applied
	if test_ids:

		# Generate data for TC IDs template
		test_ids_array, test_cnt_tpl = genID(cursor, test_ids, table_type)

		# Get test cases for each group ( grouped )
		SQL = SQL_BASE + " AND in_group = 1 AND grp_id = %s " + test_cnt_tpl
		cursor.execute( SQL , [ str(group) ] + map(str,test_ids_array) )
		test_cases_grp = cursor.fetchall()

		# Get test cases for each group ( individual )
		SQL = SQL_BASE + " AND in_group = 0 AND grp_id = %s " + test_cnt_tpl
		cursor.execute( SQL , [ str(group) ] + map(str,test_ids_array) )
		test_cases_uni = cursor.fetchall()
	# No TC Filtering
	else:
		# Get test cases for each group ( grouped )
		SQL = SQL_BASE + " AND in_group = 1 AND grp_id = %s"
		cursor.execute( SQL , [ str(group) ] )
		test_cases_grp = cursor.fetchall()

		# Get test cases for each group ( individual )
		SQL = SQL_BASE + " AND in_group = 0 AND grp_id = %s"
		cursor.execute( SQL , [ str(group) ] )
		test_cases_uni = cursor.fetchall()

	return test_cases_grp, test_cases_uni

def getTestRulesData(cursor, dev_id, test_ids):

	rule_list = []

	#Get rule id from database
	get_ids = cursor.execute("""SELECT * FROM rule_id_table WHERE test_id = '%s' and device_id = %s""" % (test_ids, dev_id))
	f_get_ids = cursor.fetchall()
	#Getting all rules from
	for item in f_get_ids:
		f_rule_id = item['rule_id']

		#Get rule data from database
		get_rule_data = cursor.execute("""SELECT * FROM rule_data_table WHERE rule_id = '%s'""" % (f_rule_id))
		f_rule_data = cursor.fetchall()
		rule_list.append(f_rule_data)

	return rule_list

#############################################################################################
# Load location specific data
#############################################################################################

def loadLocation(db_cursor, location):
	db_cursor.execute("SELECT loc_name FROM location WHERE loc_name = %s",  [ location ])
	loc_zone = db_cursor.fetchone()['loc_name']
	PREDEFINED_KEYWORDS['location'] = loc_zone.lower()
	PREDEFINED_KEYWORDS['location_upper'] = loc_zone.upper()

def loadIpRanges(db_cursor, location, getSubnetFunc):
	db_cursor.execute("SELECT loc_type_name, ip_range FROM location_ip_range INNER JOIN location_ip_type ON location_ip_range.loc_type_id = location_ip_type.loc_type_id  \
				INNER JOIN location ON location_ip_range.loc_id = location.loc_id WHERE location.loc_name = %s ",  [ location ])
	loc_ip_range = db_cursor.fetchall()
	#print dict(loc_ip_range)
	for net_range in loc_ip_range:
		#pprint.pprint(net_range['ip_range'])
		#pprint.pprint(net_range['loc_type_name'])
		if net_range['ip_range'] is not None:
			PREDEFINED_KEYWORDS[net_range['loc_type_name']] = getSubnetFunc(net_range['ip_range'])

def loadIspAS(db_cursor, location):
	db_cursor.execute("SELECT isp_as, isp_num, isp_name FROM location_isp_data \
				INNER JOIN location ON location_isp_data.loc_id = location.loc_id WHERE location.loc_name = %s",  [ location ])
	isps = db_cursor.fetchall()
	#print isps
	for isp in isps:
		if isp['isp_as'] is not None:
			PREDEFINED_KEYWORDS[isp['isp_num']+'_isp_as'] = isp['isp_as']
			PREDEFINED_KEYWORDS[isp['isp_num']+'_isp_name'] = isp['isp_name']

def loadTunnels(db_cursor, location):
	db_cursor.execute("SELECT tunnel_int, tunnel_num FROM location_tunnel_data \
				INNER JOIN location ON location_tunnel_data.loc_id = location.loc_id WHERE location.loc_name = %s",  [ location ])
	tunnels = db_cursor.fetchall()
	#print isps
	for tunnel in tunnels:
		if tunnel['tunnel_int'] is not None:
			PREDEFINED_KEYWORDS[tunnel['tunnel_int']] = tunnel['tunnel_num']

#############################################################################################
# Load test case(s) data
#############################################################################################

def loadTestCases(db_cursor, groups, test_ids, device_name, location, test_rule, table_type='device'):


	#TABLE_MAP = {'device' : 'device_group', 'host': 'host_gorup'}
	TC_FIELD_NAME_MAP = {'device' : 'dev_name', 'host' : 'host_shortname' }
	TC_FIELD_HOST_MAP = {'device' : 'dev_host', 'host' : 'host_hostname' }
	#TC_TABLE_MAP = {'device' : 'testcase_data', 'host' : 'testcase_data_host'}

	# Init arrays
	gen_simple = []
	gen_simple_w_setup = []


	for group in groups:

		# Get devices for each group
		devices = getDevices(db_cursor, group['grp_id'], location, device_name, test_ids, table_type)


		# Get test cases for each group ( grouped )
		# Get test cases for each group ( individual )
		test_cases_grp, test_cases_uni = getTests(db_cursor, group['grp_id'], test_ids, table_type)

		#Getting device id from tuple
		dev_id = int(devices[0]['dev_id'])

		#Get rules data
		test_rules_data = getTestRulesData(db_cursor,dev_id, test_ids)

		#print 'GRP:', test_cases_grp
		#print 'UNI:', test_cases_uni

		for device in devices:

			for test in test_cases_grp:


				if test['setup_id'] is None:
					gen_simple.append(dict(input=test['input_data'], output=test['output_data'].strip(), device=device[TC_FIELD_HOST_MAP[table_type]]+' | '+device[TC_FIELD_NAME_MAP[table_type]], host=device[TC_FIELD_HOST_MAP[table_type]],
											url='http://tims.cisco.com/warp.cmd?ent='+test['tims_id'], id=test['tims_id'], descr=test['descr'], test_rule=test_rules_data))

				else:
					db_cursor.execute("SELECT pre_data, post_data FROM testcase_setup WHERE setup_id= %s", [ str(test['setup_id']) ])
					setup = db_cursor.fetchone()
					#print setup
					gen_simple_w_setup.append(dict(setup_pre=setup['pre_data'],  setup_post=setup['post_data'],
														input=test['input_data'],     output=test['output_data'].strip(),
													 device=device[TC_FIELD_HOST_MAP[table_type]]+' | '+device[TC_FIELD_NAME_MAP[table_type]],  host=device[TC_FIELD_HOST_MAP[table_type]],
														 url='http://tims.cisco.com/warp.cmd?ent='+test['tims_id'], id=test['tims_id'], descr=test['descr']))


			for test in test_cases_uni:
				if test[TC_FIELD_NAME_MAP[table_type]] == device[TC_FIELD_NAME_MAP[table_type]] and test['setup_id'] is None:
					gen_simple.append(dict(input=test['input_data'], output=test['output_data'].strip(), device=device[TC_FIELD_HOST_MAP[table_type]]+' | '+device[TC_FIELD_NAME_MAP[table_type]], host=device[TC_FIELD_HOST_MAP[table_type]],
											url='http://tims.cisco.com/warp.cmd?ent='+test['tims_id'], id=test['tims_id'], descr=test['descr'], test_rule = test_rules_data))

				if test[TC_FIELD_NAME_MAP[table_type]] == device[TC_FIELD_NAME_MAP[table_type]] and test['setup_id'] is not None:
					db_cursor.execute("SELECT pre_data, post_data FROM testcase_setup WHERE setup_id = %s", [ str(test['setup_id']) ])
					setup = db_cursor.fetchone()
					#print setup
					gen_simple_w_setup.append(dict(setup_pre=setup['pre_data'],  setup_post=setup['post_data'],
														input=test['input_data'],     output=test['output_data'].strip(),
													 device=device[TC_FIELD_HOST_MAP[table_type]]+' | '+device[TC_FIELD_NAME_MAP[table_type]],  host=device[TC_FIELD_HOST_MAP[table_type]],
														 url='http://tims.cisco.com/warp.cmd?ent='+test['tims_id'], id=test['tims_id'], descr=test['descr']))

	return devices[:], gen_simple[:], gen_simple_w_setup[:], test_cases_grp[:], test_cases_uni[:]