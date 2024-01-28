# check install numpy library
import subprocess

def install_lib():
        install_process = subprocess.Popen(['mayapy', '-m', 'pip', 'install', 'numpy'])
        install_process.wait()