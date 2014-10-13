class getColor(object):
	def __init__(self):
		self.green = '\033[92m'
		self.blue = '\033[94m'
		self.red = '\033[91m'
		self.endc = '\033[0m'

	def greenText(self, str):
            return self.green + str + self.endc
	def redText(self, str):
		    return self.red + str + self.endc
	def blueText(self, str):
            return self.blue + str + self.endc

	def getTypeColor(self, str):
		if(str == 'file'):
			return self.greenText(str)
		if(str == 'dir'):
			return self.blueText(str)
	def getPathType(self, str, type):
		if(type == 'file'):
                        return self.greenText(str)
                if(type == 'dir'):
                        return self.blueText(str)
