import ipcalc
import paramiko
from socket import timeout as socket_timeout

from os import popen as os_popen
from time import sleep as time_sleep

from Configuration import  *

#############################################################################################	
#  System basic helpers
#############################################################################################

class sshConnect(object):
    def __init__(self):
        pass

    def getConnector(self, host, type = 'ssh'):
        if type == 'ssh':
            return self.getSSH(host)
        elif type == 'ucs_xml':
            return None

    def getData(self, connector, input, test_type, conn_type = 'ssh'):

        if conn_type == 'ssh':

            if test_type =='simple':

                stdin,stdout,stderror = connector.exec_command(input)
                result = stdout.readlines()
                connector.close()

                return [line.strip() for line in result]

            elif test_type == 'simple_w_setup':

                channel = connector.invoke_shell()

                for step in input:
                    #time.sleep(0.1)
                    if type(step) == list:
                        for cmd in step:
                            channel.send(cmd+'\r')
                            #print cmd
                            buffer = self.read_resp(channel)
                            #print buffer
                    else:
                        channel.send(step+'\r')
                        buffer = self.read_resp(channel)
                        #print buffer

                result = buffer
                connector.close()

                return result

        elif conn_type == 'ucs_xml':
            return 0

    def getSSH(self, host):
        username = PREDEFINED_KEYWORDS['ssh_username']
        password = PREDEFINED_KEYWORDS['ssh_password']

        # Create ssh object
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


        host = host.replace('<DC>', PREDEFINED_KEYWORDS['location'])
        # Connect to to host using key
        if PREDEFINED_KEYWORDS['ldap_ssh_key'] != '':
            username = PREDEFINED_KEYWORDS['ldap_username']
            password = PREDEFINED_KEYWORDS['ldap_password']
            ssh.connect(host, username=username, password=password, key_filename=PREDEFINED_KEYWORDS['ldap_ssh_key'])
        else:
        # Connect to device by ssh
            ssh.connect(host, username=username, password=password)

        return ssh

    #def getUCSxml(host):
    #	pass

    def print_data(self, data):


        if type(data) is list:
            for line in data:
                if len(line) > 0:
                    if line[0]+line[-1] == '##':
                        print '[RegEXP]:',line.strip('#')
                    else:
                        print line

        if type(data) is str or type(data) is unicode:
            if len(data) > 0:
                if data[0]+data[-1] == '##':
                    print '[RegEXP]:',data.strip('#')
                else:
                    print data

        print ''

    def print_hdr(self, device, url, descr, id):

        try:
            rows, columns = os_popen('stty size', 'r').read().split()
        except ValueError:
            columns = '150'
            #pass

        print ''
        print ''
        print '-' * int(columns)
        print '***'
        print '****	DEVICE::', device
        print '****	TEST CASE::', url+' | '+descr
        print '***'
        print '-' * int(columns)
        print ''


    def getSubnet(self, ip_range):

        #print ip_range
        subnet = ipcalc.Network(ip_range)

        if subnet.v == 4:

            if str(subnet.netmask()) == '255.255.255.255':
                return str(subnet.host_first()).replace('.','\.')

            original_net = str(subnet.network()).split('.')
            #filtered_net = [e for e in original_net if int(e) != 0]
            # TODO: Add more sofisticated check
            if '0' in original_net:
                filtered_net = [e for e in original_net if int(e) != 0]
            else:
                filtered_net = original_net[:3]

            regexp = '\.d\{1,3}'
            result_net = '\.'.join(filtered_net)
            #print len(original_net), len(filtered_net), original_net, filtered_net
            for e in range(len(original_net)-len(filtered_net)-1):
                result_net += regexp

        elif subnet.v == 6:
            if str(subnet.netmask()) == 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff':
                return str(subnet.host_first())#.replace(':','\:')

            original_net = str(subnet.network()).split(':')
            # TODO: Add more sofisticated check
            if '0000' in original_net:
                filtered_net = [e for e in original_net if int(e,16) != 0]
                filtered_net = [e.lstrip('0') for e in list(filtered_net)]
            else:
                filtered_net = original_net[:7]
                filtered_net = [e.lstrip('0') for e in list(filtered_net)]


            #regexp = '\:d\{1,4}'
            result_net = ':'.join(filtered_net)
            #print len(ori  ginal_net), len(filtered_net), original_net, filtered_net
            #for e in range(len(original_net)-len(filtered_net)-1):
            #result_net += regexp

        return  result_net

    def read_resp(self, channel,timeout=4):
        buffer = ''


        while not channel.recv_ready():
            time_sleep(timeout)
            #continue
            #print "WAIT"

        while channel.recv_ready():
            try:
                buffer += channel.recv(1024)
                #time.sleep(0.2)
            except socket_timeout:
                break

        # Read data
        '''
        try:
            # Set non-bloking socket mode
            channel.settimeout(0.0)


            while True:
                # Use select for checking data readiness
                r, w, e = select.select([channel], [], [], timeout)
                # Check channel data ready
                if channel in r:
                    try:
                        x = channel.recv(1024)
                        buffer += x

                        if len(x) == 0:
                            break
                    # Catch socket timeout for non-blocking
                    except socket.timeout:
                        break
                # Close channel by timeout
                else:
                    break
        finally:
            #print buffer
            pass
        '''
        return buffer

    def loadSSHkey(self, ssh_key):
        PREDEFINED_KEYWORDS['ldap_ssh_key'] = ssh_key

    def loadShortName(self, host_shortname):
        PREDEFINED_KEYWORDS['host_shortname'] = host_shortname



