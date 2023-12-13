import subprocess

def open_terminal(command):
    subprocess.Popen(['start', 'cmd', '/k', command], shell=True)

nb_agents = 3
open_terminal(f'python scripts/server.py -nb {nb_agents}')
for i in range(nb_agents):
    open_terminal('python scripts/agent.py')