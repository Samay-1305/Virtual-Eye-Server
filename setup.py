import subprocess
import platform
import socket
import json
import os

def get_hostname(self):
    network_command = 'ipconfig' if platform.system() == 'Windows' else 'ifconfig'
    command_result = subprocess.Popen(network_command, stdout=subprocess.PIPE).communicate()[0].decode()
    bind_attempt_order = ['192.168.', '169.154.', '10.0.']
    for ip_addr in bind_attempt_order:
        if ip_addr in command_result:
            ip_start_ind = command_result.index(ip_addr)
            ip_stop_ind = ip_start_ind + (command_result[ip_start_ind:]).index('\n')
            hostname = command_result[ip_start_ind:ip_stop_ind].strip()
            break
    else:
        hostname = socket.gethostname()
    return hostname

SERVER_CONFIG_FILE = "config//server_config.json"
setup_completed = False
with open(SERVER_CONFIG_FILE, "r") as config_file_object:
    server_config_data = json.loads(config_file_object.read())

server_config_data["host"] = get_hostname()

with open(SERVER_CONFIG_FILE, "w") as config_file_object:
    config_file_object.write(json.dumps(server_config_data, indent=4))

path = os.getcwd()
cmd = "cd {} && Run pip install -r requirements.txt".format(path)
os.system(cmd)