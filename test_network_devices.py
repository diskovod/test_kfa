import pytest
import pprint

import sys
import json

#from os import path as os_path
#import urllib
#from xml.dom import minidom
from datetime import datetime
from ntpath import basename as nt_basename
#from UcsSdk import *

################ Helpers Functions ######################
from lib.BasicHelpers import *
from lib.SqlHelpers import *
from lib.InteractiveHelpers import *
#########################################################

def pytest_generate_tests(metafunc):
	# called once per each test function
	funcarglist = metafunc.cls.params[metafunc.function.__name__]

	if len(funcarglist) > 0:
		argnames = list(funcarglist[0])
		metafunc.parametrize(argnames,
							 [[funcargs[name] for name in argnames]	for funcargs in funcarglist],
							 ids=[funcargs['id']+' | '+funcargs['device']+''  for funcargs in funcarglist])


#######Initialize Basic Helpers Class######################

basic_helpers_class = sshConnect()

###########################################################


#################################### TEST Class ####################################################################

class Test_NetworkDeviceTests:

	# Parse input options
	device_name = ''
	device_name = pytest.config.getoption("--device")

	dc_location = ''
	dc_location = pytest.config.getoption("--location")

	test_ids = ''
	test_ids = pytest.config.getoption("--test-id")

	junit_report = ''
	junit_report = pytest.config.getoption("--junitxml")
    #You need to write 'yes' or 'no' to this option
	test_rule = ''
	test_rule = pytest.config.getoption("--test_rule")

	# Arrays for processing inputs
	devices = []

	gen_simple = []
	gen_simple_w_setup = []

	test_cases_grp = []
	test_cases_uni = []

	test_rule_data = []
	# Connect to DB
	conn = getDbConnector()
	c = conn.cursor()

	# Get device groups
	groups = getGroups(c, device_name, test_ids) # TODO: Fix overkill group filtration at this lvl

	# Collect location short name to use in some tests cases (eg A10 partition name)
	# TODO: clean this code (add out of band checks, etc)
	loadLocation(c, dc_location)


	# Collect location IPv4-6 range to get more precise lvl of testing
	loadIpRanges(c, dc_location, basic_helpers_class.getSubnet)


	# Collect ISP AS and NAME to use in some test cases
	loadIspAS(c, dc_location)


	# Collect Tunnels numbers to use in some test cases
	loadTunnels(c, dc_location)


	# Load test cases from DB
	devices, gen_simple, gen_simple_w_setup, test_cases_grp, test_cases_uni = loadTestCases(c, groups, test_ids, device_name, dc_location, test_rule)


	###############################################################################################################################################################
	# Prepare test execution log dictionary
	TEST_LOG = {
				'date' 			: '',
				'test_run_cnt'	: 0,
				'devices' 		: '',
				'location'		: '',
				'tests'			: '',
				'filename'		: '',
				}

	# Set values (location,devices,filename,date)
	TEST_LOG['date'] = datetime.now()
	TEST_LOG['devices'] = json.dumps([device['dev_name'] for device in devices])
	TEST_LOG['location'] = dc_location
	TEST_LOG['filename'] = (lambda x: nt_basename(x) if x != None else None)(junit_report)

	###############################################################################################################################################################

	# IF test are set -> generate json list, ELSE -> ALL
	if test_ids != None:
		uni_tests = [test['tims_id'] for test in test_cases_uni]
		group_tests = [test['tims_id'] for test in test_cases_grp]
		if len(uni_tests)< 1 and len(group_tests) < 1:
			TEST_LOG['tests'] = json.dumps(['None'])
		else:
			TEST_LOG['tests'] = json.dumps(uni_tests + group_tests)
	else:
		TEST_LOG['tests'] = json.dumps(['ALL'])

	###############################################################################################################################################################

	# Select MAX test run number for our  test (device, tests, location)
	c.execute("SELECT MAX(test_run_cnt) FROM testcase_execution_log WHERE devices = %s AND location = %s AND tests = %s",
				[ TEST_LOG['devices'], TEST_LOG['location'], TEST_LOG['tests'] ])
	db_test_run_cnt  = c.fetchone()

	# IF test run number exist -> increase, ELSE -> set 1
	if db_test_run_cnt['MAX(test_run_cnt)'] == None:
		TEST_LOG['test_run_cnt'] = 1
	else:
		TEST_LOG['test_run_cnt'] = db_test_run_cnt['MAX(test_run_cnt)'] + 1

	###############################################################################################################################################################
	# Add to DB test execution log
	c.execute("INSERT INTO testcase_execution_log ( date, test_run_cnt, devices, location, tests, filename ) VALUES( %s, %s, %s, %s, %s, %s )",
				[ TEST_LOG['date'], TEST_LOG['test_run_cnt'], TEST_LOG['devices'], TEST_LOG['location'], TEST_LOG['tests'], TEST_LOG['filename'] ])


	###############################################################################################################################################################
	# Close DB connection
	###############################################################################################################################################################
	conn.commit()
	conn.close()


	###############################################################################################################################################################
	# Dynamicaly generated tests procedures input data
	###############################################################################################################################################################
	params = {
		'test_generic_simple': list(gen_simple),
		'test_generic_simple_w_setup' : list(gen_simple_w_setup),
	}
	###############################################################################################################################################################

	@pytest.mark.skipif("len(Test_NetworkDeviceTests.gen_simple) < 1")

	def test_generic_simple(self, input, output, device, host, url, id, descr, test_rule):

		basic_helpers_class.print_hdr(device, url, descr, id)

		# Get Device Connector
		connector = basic_helpers_class.getConnector(host,'ssh')
		# Dumb JSON test
		input_commands = replaceData(json.loads(input))
		# Get Data from Device\
		# TODO: find input data print field
		# TODO: find list output print field

		resp_array = basic_helpers_class.getData(connector,input_commands,'simple','ssh')

		# Verify expected result

		for item in test_rule:

			# data from rule table, rule_descr = db_output data
			rule_descr = item[0]["rule_description"]
			rule_type = item[0]["rule_type"]
			rule_id = item[0]["rule_id"]

			# Creating list of statuses for getting from py.test final status of test (PASSED/FAILED)
			data_status = []

			#Serializing data from db
			ser_rule_descr = replaceData(json.loads(rule_descr))

			#Checking rule_type data from db
			if(rule_type == "list"):

				#Comparing lists from device and db and making them similar(just for length)
				compared_device_list, compared_db_list = compareLists(resp_array, ser_rule_descr)

				#Comparing lists data, and get lists for printing
				final_device_data, final_db_data, list_status = getOutputData(compared_device_list, compared_db_list, rule_type)

				data_status.append(list_status)

				if (list_status == False):

					printErrorListData(final_device_data, final_db_data, rule_id)

			elif(rule_type == "text"):

				text_status = getOutputData(resp_array, ser_rule_descr, rule_type)

				data_status.append(text_status)

				if(text_status == False):

					printErrorTextData(ser_rule_descr, rule_id)

		if False in data_status:

			output_status = False
		else:
			output_status = True

		assert output_status == True, "Values are not equal"

	#	assert chk_word(resp_array,outputs) == True, "Values are not equal"

		return
		#ssh.close()

	@pytest.mark.skipif("len(Test_NetworkDeviceTests.gen_simple_w_setup) < 1")
	def test_generic_simple_w_setup(self, setup_pre, setup_post, input, output, device, host, url, id, descr):

		connector = basic_helpers_class.getConnector(host)
		basic_helpers_class.print_hdr(device, url, descr, id)

		# PRE setup steps
		json_setup = json.loads(setup_pre)

		if type(json_setup) == list:
			setup_pre_steps = replaceData(json_setup)
		else:
			setup_pre_steps = replaceData([json_setup])


		# Dumb JSON test
		input_commands = replaceData(json.loads(input))


		# Get Data from Device
		buffer = basic_helpers_class.getData(connector,[setup_pre_steps,input_commands],'simple_w_setup','ssh')

		basic_helpers_class.print_data(buffer.splitlines()[1:-1])

		# TODO add POST setup steps
		outputs = replaceData(json.loads(output))

		print ''
		print '== > Expected result:: '
		print ''
		# Print expected response
		#pprint.pprint(outputs, width=1)
		basic_helpers_class.print_data(outputs)
		# Verify expected result
		assert chk_word(buffer,outputs) == True, "Values are not equal"
		return
		#ssh.close()
