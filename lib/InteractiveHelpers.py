import re

from Configuration import  *
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