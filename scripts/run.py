import subprocess

def open_terminal(command):
    subprocess.Popen(['start', 'cmd', '/k', command], shell=True)


open_terminal('python scripts/server.py -nb 4')
for i in range(4):
    open_terminal('python scripts/agent.py')