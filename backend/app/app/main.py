import os
import sys, getopt
import re
import psutil
import socket

# TO SUPPORT RUN python main.py in windows,but I use python "app/main.py" to start in liunx
os.sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# support to get correct rmt_library
sys.path.append('/usr/lib/python3/dist-packages')

import fastapi
from fastapi import routing, FastAPI
from app.extensions.routing import APIRouter as MyAPIRouter, APIRoute as MyAPIRoute

# rewrite APIRouter and APIRoute and add parameter exclude_dependencies to deny global dependencies
fastapi.APIRouter = routing.APIRouter = MyAPIRouter
fastapi.APIRoute = routing.APIRoute = MyAPIRoute

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.api.api_v1.websocket import socket_app
from app.middleware import register_middleware
import rmt_py_wrapper

# app
app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
# set middleware
register_middleware(app)

# set router
app.include_router(api_router, prefix=settings.API_V1_STR)
# set socketio
app.mount('/', socket_app)

def valid_ip(ip):
    # pass the regular expression
    # and the string in search() method
    regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    if(re.search(regex, ip)):
        return True
    else:
        return False

def valid_interface(interface):
    interface_addrs = psutil.net_if_addrs().get(interface) or []
    return socket.AF_INET in [snicaddr.family for snicaddr in interface_addrs]

if __name__ == '__main__':
    argv =sys.argv[1:]
    my_ip = "0.0.0.0"
    my_port = 8080
    my_interface = ""
    opts, args = getopt.getopt(argv,"i:p:n:",["ip=","port=","net_interface="])
    for opt, arg in opts:
        if opt in ("-i", "--ip"):
            my_ip = arg
            if not valid_ip(my_ip):
                print("IP({}) is invalid.".format(my_ip))
                sys.exit(2)
        elif opt in ("-p", "--port"):
            my_port = arg
            if not my_port.isnumeric():
                print("Port({}) is invalid.".format(my_port))
                sys.exit(2)
            my_port = int(my_port)
        elif opt in ("-n", "--net-interface"):
            my_interface = arg
            if not valid_interface(my_interface):
                print("Interface({}) is invalid or inactive.".format(my_interface))
                sys.exit(2)            

    import uvicorn
    if len(my_interface) > 0:
        print("Use interface({}) for RMT server".format(my_interface))
        rmt_py_wrapper.rmt_server_configure(my_interface, 0)
    else:
        rmt_py_wrapper.rmt_server_configure("", 0)
    rmt_py_wrapper.rmt_server_init()
    uvicorn.run(app='main:app', host=my_ip, port=my_port)
    rmt_py_wrapper.rmt_server_deinit()
