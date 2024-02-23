# check install numpy library
# import subprocess
import os
from zipfile import ZipFile as zp

def install_lib():
    # install_process = subprocess.Popen(['mayapy', '-m', 'pip', 'install', 'numpy'])
    # install_process.wait()
    # if install_process.returncode != 0:
    try:
        current_module_dir = os.path.abspath(os.path.join(__file__ ,"../.."))
        zipDir = (os.path.join(current_module_dir, 'numpy.zip')).replace('\\', '/')
        with zp(zipDir, 'r') as zip_ref:
            zip_ref.extractall(path=current_module_dir)
            print("Numpy extracted successfully from numpy.zip.")
    except Exception as e:
        print("Error extracting numpy.zip:", e, ". Please try Extract Here manually")
