#!/usr/bin/python
#title          :cherokee-remote.py
#description    :A remote SSH cherokee admin helper, 
#                it will run cherokee-admin remotely and stablish a secure ssh tunnel to the admin port.
#                Implemented with python fabric.
#author         :Sergio Aguilar <chekolyn@gmail.com>
#date           :2013-04-02
#version        :0.0.1
#license        :GPL v2 
#============================================================================

import os                   # To suppress webbroser message
import sys                  # To count arguments
import argparse             # For arguments
import webbrowser           # To open the web browser
import socket               # To check for the host
import fabric               # For ssh connectivity
from fabric import api      
from fabric.api import *



# Variables:
USER = "username"
HOST="hostname"
RPORT="9090"
LPORT="9000"
SSH_CONNECT="ssh -f -N -L %s:localhost:%s " % (LPORT, RPORT)

# Screen settings:
# -d Detach mode, This creates a new session but doesn't  attach  to  it.
# -S Session name
# sleep 1 required, otherwise it will fail.
CHEROKEE_ADMIN="screen -dmS CHEROKEE cherokee-admin -u -t; sleep 1"

# Env
env.host_string = "%s@%s" % (USER, HOST)
#env.key_filename = ["/path/to/ssh/key"]
#env.colors = True
env.warn_only  = True # Wont abort if remote command execution fails
#env.show = ['debug'] 
#fabric.state.output['running'] = True
#env.output_prefix = False

# Parser:
cherokee_remote_desc="""A remote SSH cherokee admin helper, 
it will run cherokee-admin remotely and stablish a secure ssh tunnel to the admin port.
Implemented with python fabric."""
parser = argparse.ArgumentParser(description=cherokee_remote_desc)
parser.add_argument('-a', '--admin', action='store_true', help='Start the remote cherokee-admin', default=False)
parser.add_argument('-u', '--user', help='Username for ssh connection', default=USER)
parser.add_argument('-H', '--host', help='Hostname for ssh connection', default=HOST)
parser.add_argument('-t', '--tunnel', action='store_true', help="Just connect to remote cherokee-admin. Using ssh port forwarding.", default=False)
parser.add_argument('--start',  action='store_true', help="Will start the the full cherokee-remote process", default=False)
parser.add_argument('--stop',   action='store_true', help="Will stop the remote cherokee-admin and tunnel", default=False)
parser.add_argument('--status', action='store_true', help="Display status", default=False)
parser.add_argument('-v', '--verbose', action='store_true', help="Verbose On/Off; with fabric debug lever Off", default=False)
parser.add_argument('-vv', '--debug', action='store_true', help="Debug On/Off; with fabric debug level On", default=False)
parser.add_argument('-w', '--webpage', action='store_true', help='Opens the admin webpage in the web browser', default=False)

# nargs="?" wont make error if missing argument
args = parser.parse_args()

def setup():
  env.host_string = "%s@%s" % (USER, HOST)
  env.key_filename = ["/path/to/ssh/key"]
  
def get_cherokee_admin_pid():
  admin_pid = run("pidof cherokee-admin")
  return admin_pid
  
def run_cheroke_admin():
  sudo(CHEROKEE_ADMIN)
  

def kill_cherokee_admin():
  pid = get_cherokee_admin_pid()
  sudo("kill -9 %s" % pid)
  
def cherokee_admin_tunnel():
  
  if get_cherokee_admin_tunnel_pid():
    print "Tunnel already exists!"
  elif int(get_cherokee_admin_pid()):
    global SSH_CONNECT
    SSH_CONNECT += env.host_string 
    local(SSH_CONNECT)   
  else:
    print "No cherokee-admin running remotely"
    

def get_cherokee_admin_tunnel_pid():
  # Capture = True required  to enable return on local fabric function:
  return local("ps aux | grep [s]sh | grep 9000 | awk '{print $2}'", capture=True)

def test_hostname(host):
  try:
    socket.gethostbyname(host)
    return True
  except:
    return False

def cherokee_admin_tunnel_end():
  local_pid = get_cherokee_admin_tunnel_pid()
  command = "kill -9 %s" % local_pid
  local(command)
  
def browser_launch():
  # Suppresses the chrome error message:
  # "Created new window in existing browser session."
  # There is still a bug when launching chrome for the first time. 
  # those are chrome related bugs. No errors on Firefox.
  # Suggestion from: 
  # http://stackoverflow.com/questions/2323080/how-can-i-disable-the-webbrowser-message-in-python
  savout = os.dup(1)
  os.close(1)
  os.open(os.devnull, os.O_RDWR)
  try:
    webbrowser.open_new_tab('http://localhost:' + LPORT)
  finally:
   os.dup2(savout, 1)
  
def start():
  # Start remote cherokee-admin
  run_cheroke_admin()
  
  # Create tunnel to remote cherokee-admin:
  cherokee_admin_tunnel()
  
  # Open remote cherokee admin in local port:
  browser_launch()
  
def stop():
  # Stop tunnel:
  cherokee_admin_tunnel_end()
  
  # Stop remote cheroke-admin:
  kill_cherokee_admin()

if __name__ == '__main__':
  
  # Define verbose_level
  show_var= 'output'
  hide_var = 'everything'
 
  if args.verbose:
    show_var = 'everything'
    hide_var = 'warnings'
    
  if args.debug:
    show_var = 'everything'
    hide_var = 'aborts'
    fabric.state.output['debug'] = True
    
    
  # Not verbose or debug:
  
  # Debug hide settings:
  #with hide():
  with settings(show(show_var), hide(hide_var)) :
    
    if args.debug:
      print "Arguments to command= %s" % args
      print "Fabric.state.output Variable:"
      print fabric.state.output
    
    # Check for arguments:
    if len(sys.argv) == 1:
      parser.print_help()
    else:
      
      # Test if we have a valid host:
      if not test_hostname(args.host):
        print "DNS error, host can't be resolve. Host: %s" % args.host
        exit()
      
      # Start cherokee-admin:
      if args.admin:
        run_cheroke_admin()
      
      # Open Webpage
      if args.webpage:
        browser_launch()
      
      # Set the host_string variable with args variable:
      # there will always be these 2 variables because of the defaults:
      if args.user and args.host:
        env.host_string = "%s@%s" % (args.user, args.host)
        
      if args.tunnel:
        print "Creating tunnel"
        cherokee_admin_tunnel()
        
      if args.start:
        print "Starting Cherokee-remote"
        start()
        
      if args.stop:
        print "Stoping Cherokee-remote"
        stop()
        
      if args.status:
        print "***Current cherokee-remote status***"
        admin_pid = get_cherokee_admin_pid()
        tunnel_pid = get_cherokee_admin_tunnel_pid()
        
        status = "BAD!!!"
        if admin_pid and tunnel_pid:
          status = "OK!"
          
        print "Status: %s" % status        
        print "Remote cherokee-admin pid: %s" % admin_pid
        print "Tunnel pid: %s" % tunnel_pid
        
        
      # No action message:
      if not ( args.tunnel or args.start or args.stop or args.status or args.admin or args.webpage ):
        parser.print_help()
        print ""
        print "**** No action specified****"
