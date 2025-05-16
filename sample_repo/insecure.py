import os

password = "hardcoded-password"

def bad():
    eval("print('This is insecure')")
    os.system("rm -rf /")
