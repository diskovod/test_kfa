import re

from Configuration import  *
from color import *
#############################################################################################
# Interactive tools
#############################################################################################

def chk_one(input,word):
	#print(word)
	# Function checks if ONE WORD presents the output
	# Check if input is RegEXP
	fl_regexp = False
	if ( word[0] == '#' and word[-1] == '#' ):
		fl_regexp = True

	# IF RegEXP -> user re.serach
	if fl_regexp:
		if re.search(word[1:-1],input):
			return True
	# ELSE use in for search
	else:
		if word in input:
			return True

	return False

def chk_multi(inputs,words,start=0):
	# Function checks IF ALL INPUTS exist in the output in correct order
	# Build expected array of results (True*len of output)
	fl_etalon = [True]*len(words)
	fl_result = []

	# Builds result array (IF OK -> Append True)
	for word in words:

		for i in range(start,len(inputs)):

			if chk_one(inputs[i],word):
				start = i+1
				fl_result.append(True)
				break


	# IF results not eq -> check failed
	if fl_etalon == fl_result:
		return True

	return False

def chk_single(inputs,word,start=0):
	# Function checks IF INPUT(s) exists at least ONCE in the output
	for i in range(start,len(inputs)):
		if chk_one(inputs[i],word):
			return True

	return False

def chk_word(buffer,words):
	# Fucntion check IF INPUT word exist in the output
	result = False
	fl_multi = True

	# IF INPUT is single (chk_string) use singe search, ELSE use multi search
	if type(words) is str or type(words) is unicode:
		fl_multi = False

	# IF OUTPUT is string -> split by new line to array, and filter first line (duplciation of input cmd)
	if type(buffer) is str or type(buffer) is unicode:
		# Split string to array
		data_array = buffer.splitlines()
		start = 1
	# ELSE -> process as array
	else:
		# Process array
		data_array = buffer
		start = 0

	# Remove empty lines from output
	data_array = filter(lambda x:x!='',data_array)

	# Process multi line result or single line
	if fl_multi:
		result = chk_multi(data_array,words,start)
	else:
		result = chk_single(data_array,words,start)

	return result

def replaceData(input_data):

	print input_data
	# Functions replaces template from INPUT by specific data
	# IF INPUT is array -> process each element
	if type(input_data) == list:
		# Check each element and replace if template exists - <template>
		for data in input_data:
			# Replace first template
			replace = re.search("<[a-z_0-9]+>",data)

			changed_data = data

			# Process second and so on templates if they peresent in the string
			while replace != None:

				var_data = PREDEFINED_KEYWORDS[replace.group()[1:-1]]
				# Replace escaping \\. by . if string not RegEXP
				if changed_data[0]+changed_data[-1] != '##':
					var_data = var_data.replace('\\.', '.')

				changed_data = re.sub(replace.group(),var_data,changed_data)
				input_data[input_data.index(data)] = changed_data
				data = changed_data

				replace = re.search("<[a-z_0-9]+>",changed_data)
			#else:
			#	continue
			#continue
	else:
	# ELSE -> process as one string line
		replace = re.search("<[a-z_0-9]+>",input_data)

		changed_data = input_data
		# Process second and so on templates if they peresent in the string
		while replace != None:

			var_data = PREDEFINED_KEYWORDS[replace.group()[1:-1]]
			# Replace escaping \\. by . if string not RegEXP
			if changed_data[0]+changed_data[-1] != '##':
				var_data = var_data.replace('\\.', '.')

			changed_data = re.sub(replace.group(),var_data,changed_data)
			input_data = changed_data

			replace = re.search("<[a-z_0-9]+>",changed_data)

	return input_data

def string_cmp(str1, str2):
    return str1 == str2

def compareLists(device_list, db_list):

	f_device_list = []
	f_db_list = []

	i = 0

	device_list_len = len(device_list)
	db_list__len = len(db_list)


	if(device_list_len>db_list__len):
		while i<device_list_len:
			try:
				f_device_list.append(device_list[i])
				f_db_list.append(db_list[i])
			except IndexError:
				f_db_list.append("")

			i = i+1

	elif(db_list__len>device_list_len):
		while i<db_list__len:
			try:
				f_device_list.append(device_list[i])
				f_db_list.append(db_list[i])
			except IndexError:
				f_device_list.append("")

			i = i+1
	else:
		while i<db_list__len:

			f_device_list.append(device_list[i])
			f_db_list.append(db_list[i])

			i = i+1

	return f_device_list, f_db_list


def getOutputData(device_output, db_output, rule_type):

	color_cl = getColor()
	final_device_list = []
	final_db_list = []
	compare_list = []
	status = True

	if(rule_type == "list"):

		list_status = True
		i = 0

		while i<len(device_output):

			if (device_output[i] == db_output[i]):
				final_db_list.append(db_output[i])
				final_device_list.append(device_output[i])

			else:

				failed_db_data = color_cl.redText(str(db_output[i]))
				failed_device_data = color_cl.redText(str(device_output[i]))

				final_device_list.append(failed_device_data)
				final_db_list.append(failed_db_data)

				list_status = False

			i = i + 1

		return final_device_list, final_db_list, list_status

	elif(rule_type == "text"):

		if db_output in device_output:
			text_status = True
		else:
			text_status = False

		return text_status


def printErrorListData(final_device_list, final_db_list, rule_id):

	color_cl = getColor()
	i = 0
	j = 0
	print "----------------------------------------------"
	print color_cl.redText("Printing Error Log for rule id: %s" % (rule_id))
	print "----------------------------------------------"
	print "Output data from device:"

	while i<len(final_device_list):


		if(final_device_list[i] == ""):
			miss_val_text = color_cl.redText("<Missing value>")
			print "%s. %s" % (i, miss_val_text)
		else:
			print "%s. %s" % (i, final_device_list[i])

		i = i+1

	print "------------------------------------------------------------------"
	print ""
	print "Output db data:"

	while j<len(final_db_list):

		if(final_db_list[j] == None):
			unexp_val_text = color_cl.redText("<Unexpected value>")
			print "2. "

		else:

			print "%s. %s" % (j, final_db_list[j])

		j = j+1

	print "-----------------------------------------------------------------"


def printErrorTextData(ser_rule_descr, rule_id):

	color_cl = getColor()
	print "----------------------------------------------"
	print color_cl.blueText("Printing Error Log for rule id: %s" % (rule_id))
	print "----------------------------------------------"

	print color_cl.redText("%s was not found in output device data!" % (ser_rule_descr))
