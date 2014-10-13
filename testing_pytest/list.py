def make_red(strs):
	return "<red>"+strs+"</red>"


def string_cmp(str1, str2):
	return str1 == str2


def diff_list(target, source, cmp_str=string_cmp):
	status = True
	#compare_list = zip(target, source)
	#compare_list = []

	f_source_list = []
	f_target_list = []

	i = 0

	target_len = len(target)
	source_len = len(source)


	if(target_len>source_len):
		while i<target_len:
			try:
				f_source_list.append(source[i])
				f_target_list.append(target[i])
			except IndexError:
				f_source_list.append("")

			i = i+1

	elif(source_len>target_len):
		while i<source_len:
			try:
				f_source_list.append(source[i])
				f_target_list.append(target[i])
			except IndexError:
				f_target_list.append("")

			i = i+1

	return f_source_list, f_target_list

	#return f_source_list



	#return status, compare_list


def main():
	list_a = ['123', '2123', '334', '4213', '7354', '9123']
	list_b = ['1213', '234', '3234', '4123', '534']

	#list_a[6] = '10'
	#print list_a
	f_source_list, f_target_list = diff_list(list_a, list_b)

	print f_source_list
	print f_target_list
	#status, res_list = diff_list(list_a, list_b)

	#print res_list


if "__main__" == __name__:
	main()