import pytest
#import pprint

def pytest_addoption(parser):
	parser.addoption("--device", dest="device", help="Device name wildcard for group filtration")
	parser.addoption("--location", dest="location", default="LON5", help="DC location name wildcard for group filtration (Default is LON5)")
	#parser.addoption("--update", dest="update", action="store_true", default=False,  help="Update Test Cases descriptions from TIMS")
	#parser.addoption("--force", dest="force", action="store_true", default=False, help="Force update (works only with TC Description now)")
	parser.addoption("--key", dest="key", help="SSH Key for key auth")
	parser.addoption("--test-id", dest="test-id", help="Execute individual test(s)")

