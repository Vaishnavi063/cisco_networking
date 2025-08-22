import threading
import time
import queue
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import ipaddress

class DeviceType(Enum):
    ROUTER = "router"
    SWITCH = "switch"
    ENDPOINT = "endpoint"

class InterfaceState(Enum):
    UP = "up"
    DOWN = "down"
    ADMIN_DOWN = "admin_down"

@dataclass
class Interface:
    name: str
    ip_address: str
    subnet_mask: str
    bandwidth: int  # in Mbps
    mtu: int
    state: InterfaceState
    vlan: Optional[int] = None
    description: str = ""

class NetworkDevice(threading.Thread):
    def __init__(self, hostname: str, device_type: DeviceType, config: Dict[str, Any]):
        super().__init__()
        self.hostname = hostname
        self.device_type = device_type
        self.config = config
        self.message_queue = queue.Queue()
        self.running = True
        self.interfaces: Dict[str, Interface] = {}
        self.neighbors: List[str] = []
        self.routing_table: Dict[str, str] = {}
        self.arp_table: Dict[str, str] = {}
        self.statistics = {
            'packets_sent': 0,
            'packets_received': 0,
            'errors': 0,
            'uptime': 0
        }
        
        # Setup logging
        self.logger = logging.getLogger(f"device.{hostname}")
        self.logger.setLevel(logging.INFO)
        
        # Initialize interfaces from config
        self._initialize_interfaces()
        
    def _initialize_interfaces(self):
        """Initialize device interfaces from configuration"""
        for interface_data in self.config.get('interfaces', []):
            interface = Interface(
                name=interface_data['name'],
                ip_address=interface_data['ip_address'],
                subnet_mask=interface_data['subnet_mask'],
                bandwidth=interface_data.get('bandwidth', 100),
                mtu=interface_data.get('mtu', 1500),
                state=InterfaceState.UP,
                vlan=interface_data.get('vlan'),
                description=interface_data.get('description', '')
            )
            self.interfaces[interface.name] = interface
    
    def add_neighbor(self, neighbor_hostname: str):
        """Add a neighbor device"""
        if neighbor_hostname not in self.neighbors:
            self.neighbors.append(neighbor_hostname)
            self.logger.info(f"Added neighbor: {neighbor_hostname}")
    
    def remove_neighbor(self, neighbor_hostname: str):
        """Remove a neighbor device"""
        if neighbor_hostname in self.neighbors:
            self.neighbors.remove(neighbor_hostname)
            self.logger.info(f"Removed neighbor: {neighbor_hostname}")
    
    def send_message(self, message: Dict[str, Any]):
        """Send a message to this device"""
        self.message_queue.put(message)
    
    def process_message(self, message: Dict[str, Any]):
        """Process incoming messages"""
        msg_type = message.get('type')
        self.statistics['packets_received'] += 1
        
        if msg_type == 'arp_request':
            self._handle_arp_request(message)
        elif msg_type == 'ospf_hello':
            self._handle_ospf_hello(message)
        elif msg_type == 'routing_update':
            self._handle_routing_update(message)
        elif msg_type == 'ping':
            self._handle_ping(message)
        else:
            self.logger.warning(f"Unknown message type: {msg_type}")
    
    def _handle_arp_request(self, message: Dict[str, Any]):
        """Handle ARP requests"""
        target_ip = message.get('target_ip')
        source_mac = message.get('source_mac')
        
        # Check if we have the target IP
        for interface in self.interfaces.values():
            if interface.ip_address == target_ip:
                # Send ARP reply
                reply = {
                    'type': 'arp_reply',
                    'target_mac': source_mac,
                    'source_ip': target_ip,
                    'source_mac': f"MAC_{self.hostname}_{interface.name}"
                }
                self.logger.info(f"ARP reply for {target_ip}")
                return reply
        
        # Forward ARP request to other interfaces
        self._forward_arp_request(message)
    
    def _handle_ospf_hello(self, message: Dict[str, Any]):
        """Handle OSPF hello messages"""
        if self.device_type == DeviceType.ROUTER:
            # Send OSPF hello reply
            reply = {
                'type': 'ospf_hello_reply',
                'source': self.hostname,
                'neighbors': self.neighbors
            }
            self.logger.info(f"OSPF hello reply sent")
    
    def _handle_routing_update(self, message: Dict[str, Any]):
        """Handle routing updates"""
        if self.device_type == DeviceType.ROUTER:
            route = message.get('route')
            if route:
                self.routing_table[route['destination']] = route['next_hop']
                self.logger.info(f"Updated routing table: {route['destination']} -> {route['next_hop']}")
    
    def _handle_ping(self, message: Dict[str, Any]):
        """Handle ping messages"""
        target_ip = message.get('target_ip')
        source_ip = message.get('source_ip')
        
        # Check if we can reach the target
        if self._can_reach_ip(target_ip):
            reply = {
                'type': 'ping_reply',
                'target_ip': source_ip,
                'source_ip': target_ip,
                'ttl': message.get('ttl', 64)
            }
            self.logger.info(f"Ping reply sent to {source_ip}")
        else:
            # Forward ping to appropriate interface
            self._forward_ping(message)
    
    def _can_reach_ip(self, target_ip: str) -> bool:
        """Check if this device can reach the target IP"""
        for interface in self.interfaces.values():
            if interface.state == InterfaceState.UP:
                try:
                    interface_network = ipaddress.IPv4Network(
                        f"{interface.ip_address}/{interface.subnet_mask}", 
                        strict=False
                    )
                    target_network = ipaddress.IPv4Network(target_ip)
                    if target_network.subnet_of(interface_network):
                        return True
                except ValueError:
                    continue
        return False
    
    def _forward_arp_request(self, message: Dict[str, Any]):
        """Forward ARP request to other interfaces"""
        for interface in self.interfaces.values():
            if interface.state == InterfaceState.UP:
                # In a real implementation, this would send to connected devices
                self.logger.debug(f"Forwarding ARP request via {interface.name}")
    
    def _forward_ping(self, message: Dict[str, Any]):
        """Forward ping to appropriate interface"""
        target_ip = message.get('target_ip')
        for interface in self.interfaces.values():
            if interface.state == InterfaceState.UP:
                # In a real implementation, this would send to connected devices
                self.logger.debug(f"Forwarding ping via {interface.name}")
    
    def simulate_periodic_tasks(self):
        """Simulate periodic network tasks"""
        current_time = time.time()
        
        # Update uptime
        self.statistics['uptime'] = current_time
        
        # Send keep-alive messages to neighbors
        if self.neighbors:
            for neighbor in self.neighbors:
                keepalive = {
                    'type': 'keepalive',
                    'source': self.hostname,
                    'timestamp': current_time
                }
                # In a real implementation, this would send to the neighbor
                self.logger.debug(f"Keepalive sent to {neighbor}")
        
        # OSPF hello messages for routers
        if self.device_type == DeviceType.ROUTER:
            ospf_hello = {
                'type': 'ospf_hello',
                'source': self.hostname,
                'neighbors': self.neighbors,
                'timestamp': current_time
            }
            # In a real implementation, this would broadcast to all interfaces
            self.logger.debug("OSPF hello sent")
    
    def run(self):
        """Main device simulation loop"""
        self.logger.info(f"Device {self.hostname} started")
        start_time = time.time()
        
        while self.running:
            try:
                # Process incoming messages
                try:
                    message = self.message_queue.get(timeout=1)
                    self.process_message(message)
                except queue.Empty:
                    pass
                
                # Perform periodic tasks
                self.simulate_periodic_tasks()
                
                # Small delay to prevent CPU overuse
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in device {self.hostname}: {e}")
                self.statistics['errors'] += 1
        
        self.logger.info(f"Device {self.hostname} stopped")
    
    def stop(self):
        """Stop the device simulation"""
        self.running = False
        self.logger.info(f"Stopping device {self.hostname}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current device status"""
        return {
            'hostname': self.hostname,
            'device_type': self.device_type.value,
            'interfaces': {name: {
                'ip_address': intf.ip_address,
                'subnet_mask': intf.subnet_mask,
                'bandwidth': intf.bandwidth,
                'mtu': intf.mtu,
                'state': intf.state.value,
                'vlan': intf.vlan
            } for name, intf in self.interfaces.items()},
            'neighbors': self.neighbors,
            'routing_table': self.routing_table,
            'statistics': self.statistics
        }
    
    def set_interface_state(self, interface_name: str, state: InterfaceState):
        """Set interface state"""
        if interface_name in self.interfaces:
            self.interfaces[interface_name].state = state
            self.logger.info(f"Interface {interface_name} state changed to {state.value}")
    
    def inject_fault(self, fault_type: str, **kwargs):
        """Inject various types of faults for testing"""
        if fault_type == 'interface_down':
            interface_name = kwargs.get('interface_name')
            if interface_name in self.interfaces:
                self.set_interface_state(interface_name, InterfaceState.DOWN)
                self.logger.warning(f"Fault injected: Interface {interface_name} is down")
        
        elif fault_type == 'link_failure':
            neighbor = kwargs.get('neighbor')
            if neighbor in self.neighbors:
                self.remove_neighbor(neighbor)
                self.logger.warning(f"Fault injected: Link to {neighbor} failed")
        
        elif fault_type == 'high_cpu':
            # Simulate high CPU usage
            self.logger.warning("Fault injected: High CPU usage")
        
        else:
            self.logger.warning(f"Unknown fault type: {fault_type}") 