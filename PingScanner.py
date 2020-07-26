#!/usr/bin/env python3

import os
import threading
import argparse
import socket
import subprocess as sub
import time

parser = argparse.ArgumentParser(description='Simple script to rapidly ping hosts on the network')
parser.add_argument('-n', '--networkid', metavar='', help='Network ID. Ex. 192.168.1.')
parser.add_argument('-H', '--hostname', action='store_true', help='Try to reslove hostnames')
parser.add_argument('-m', '--mac', action='store_true', help='Show MAC addresses')

args = parser.parse_args()

#Function to get current IP
def getIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:

        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

#Function to take ip address, ping it, and add it to the upIps list if its up
def ping(ipAddr):    
    exit_code = os.system(f"ping -c 1 -W 1 {ipAddr} > /dev/null 2>&1") 
    outputText = ipAddr   

    if exit_code == 0:
        Lock.acquire()
        #if user requests mac addresses, look up in arp table
        if args.mac:
            macAddr = timeoutCommand(f"arp -n {ipAddr}", 1)
            if not len(macAddr.splitlines()) == 1:
                outputText += '\t|  ' + macAddr.splitlines()[1].split()[2]
            

        #if user requested hostname, try to resolve with netbios
        if args.hostname:
            hostName = timeoutCommand(f'nmblookup -A {ipAddr}', 1)
            if not hostName == '':
                outputText += '\t|  ' + hostName.splitlines()[1].split()[0]

        upIps.append(outputText)
        Lock.release()

#Function to call a command and only wait a specified amount of time for it to finish
def timeoutCommand(command, waitTime):
    #Call the command
    command = sub.Popen(command.split(), stdout=sub.PIPE, stderr=sub.PIPE, text=True)

    #Set the time counter to 0, and start counting up to waitTime, checking every .2 seconds to see if command finished successfully
    t = 0
    while t < waitTime and command.poll() is None:
        time.sleep(.2)
        t += .2

    #If command is still running, kill it and return nothing. Else return the commands output
    if command.poll() is None:
        command.kill()
        return ''
    else:
        return command.communicate()[0]


#List of IPs that respond to pings    
upIps = []

#Lock object to lock the list of IPs do there are no write errors from multiple threads accessing the same variable
Lock = threading.Lock()   

#if a network ID is provided, use it. otherwise, get it automatically
if args.networkid:
    networkId = args.networkid    
else:    
    networkId = getIp().split('.')
    del networkId[3]
    networkId = '.'.join(networkId) + '.'

#List to hold all threads, so they can all be joined later on. 
threadList = []


#Loop through all IPs on the network, creating a separate thread for each ping
for i in range(1,254):
    ip = networkId + str(i)
    x = threading.Thread(target=ping, args=(ip,))
    x.start()
    threadList.append(x)

#Wait for all ping threads to finish
for t in threadList:
    t.join()

#Sort the up IPs into ascending order, and print them
upIps.sort(key=lambda ip : int(ip.split('.')[3].split()[0]))
for ip in upIps:
    print(ip)




