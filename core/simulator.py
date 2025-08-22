import time
import threading
import logging
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import queue

from .device import NetworkDevice, DeviceType, InterfaceState
from .topology_generator import NetworkTopology, NetworkLink, TopologyGenerator
from .config_parser import ParsedConfig

@dataclass
class SimulationEvent:
    timestamp: float
    event_type: str
    source_device: str
    target_device: Optional[str]
    description: str
    data: Dict[str, Any]

@dataclass
class FaultInjection:
    fault_type: str
    target_device: str
    target_interface: Optional[str]
    parameters: Dict[str, Any]
    duration: Optional[float]  # None for permanent faults
    start_time: Optional[float]

class NetworkSimulator:
    def __init__(self, topology: NetworkTopology):
        self.topology = topology
        self.topology_generator = TopologyGenerator()  # Store reference to topology generator
        self.devices: Dict[str, NetworkDevice] = {}
        self.simulation_running = False
        self.simulation_paused = False
        self.simulation_start_time = None
        self.simulation_time = 0.0
        
        # Event tracking
        self.events: List[SimulationEvent] = []
        self.event_queue = queue.Queue()
        
        # Fault injection
        self.active_faults: List[FaultInjection] = []
        self.fault_history: List[FaultInjection] = []
        
        # Statistics
        self.statistics = {
            'total_packets': 0,
            'total_errors': 0,
            'devices_online': 0,
            'devices_offline': 0,
            'links_active': 0,
            'links_failed': 0
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize devices
        self._initialize_devices()
        
        # Setup event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            'device_start': [],
            'device_stop': [],
            'link_failure': [],
            'link_recovery': [],
            'packet_sent': [],
            'packet_received': [],
            'error_occurred': []
        }
    
    def _initialize_devices(self):
        """Initialize network devices from topology"""
        self.logger.info("Initializing network devices...")
        
        for hostname, config in self.topology.devices.items():
            # Determine device type based on configuration
            device_type = self._determine_device_type(config)
            
            # Create device instance
            device = NetworkDevice(hostname, device_type, self._convert_config_for_device(config))
            self.devices[hostname] = device
            
            # Add neighbors based on topology
            neighbors = self.topology_generator.get_device_neighbors(hostname)
            for neighbor in neighbors:
                device.add_neighbor(neighbor)
        
        self.logger.info(f"Initialized {len(self.devices)} devices")
    
    def _determine_device_type(self, config: ParsedConfig) -> DeviceType:
        """Determine device type based on configuration"""
        # Check for router-specific configurations
        if config.routing_protocols or config.default_gateway:
            return DeviceType.ROUTER
        
        # Check for switch-specific configurations
        if config.vlans or any(intf.vlan for intf in config.interfaces):
            return DeviceType.SWITCH
        
        # Default to endpoint
        return DeviceType.ENDPOINT
    
    def _convert_config_for_device(self, config: ParsedConfig) -> Dict[str, Any]:
        """Convert parsed config to device-compatible format"""
        device_config = {
            'interfaces': []
        }
        
        for interface in config.interfaces:
            intf_config = {
                'name': interface.name,
                'ip_address': interface.ip_address,
                'subnet_mask': interface.subnet_mask,
                'bandwidth': interface.bandwidth,
                'mtu': interface.mtu,
                'vlan': interface.vlan,
                'description': interface.description
            }
            device_config['interfaces'].append(intf_config)
        
        return device_config
    
    def start_simulation(self):
        """Start the network simulation"""
        if self.simulation_running:
            self.logger.warning("Simulation is already running")
            return
        
        self.logger.info("Starting network simulation...")
        self.simulation_running = True
        self.simulation_paused = False
        self.simulation_start_time = time.time()
        
        # Start all devices
        for device in self.devices.values():
            device.start()
        
        # Start event processing thread
        self.event_thread = threading.Thread(target=self._process_events, daemon=True)
        self.event_thread.start()
        
        # Start fault injection thread
        self.fault_thread = threading.Thread(target=self._process_faults, daemon=True)
        self.fault_thread.start()
        
        # Start statistics collection thread
        self.stats_thread = threading.Thread(target=self._collect_statistics, daemon=True)
        self.stats_thread.start()
        
        self.logger.info("Network simulation started successfully")
    
    def stop_simulation(self):
        """Stop the network simulation"""
        if not self.simulation_running:
            self.logger.warning("Simulation is not running")
            return
        
        self.logger.info("Stopping network simulation...")
        self.simulation_running = False
        
        # Stop all devices
        for device in self.devices.values():
            device.stop()
        
        # Wait for devices to stop
        for device in self.devices.values():
            device.join(timeout=5)
        
        self.logger.info("Network simulation stopped")
    
    def pause_simulation(self):
        """Pause the network simulation"""
        if not self.simulation_running:
            self.logger.warning("Simulation is not running")
            return
        
        self.simulation_paused = True
        self.logger.info("Network simulation paused")
    
    def resume_simulation(self):
        """Resume the network simulation"""
        if not self.simulation_running:
            self.logger.warning("Simulation is not running")
            return
        
        self.simulation_paused = False
        self.logger.info("Network simulation resumed")
    
    def inject_fault(self, fault_type: str, target_device: str, 
                     target_interface: Optional[str] = None, 
                     parameters: Optional[Dict[str, Any]] = None,
                     duration: Optional[float] = None):
        """Inject a fault into the network"""
        if target_device not in self.devices:
            self.logger.error(f"Target device {target_device} not found")
            return
        
        fault = FaultInjection(
            fault_type=fault_type,
            target_device=target_device,
            target_interface=target_interface,
            parameters=parameters or {},
            duration=duration,
            start_time=time.time() if duration else None
        )
        
        self.active_faults.append(fault)
        self.fault_history.append(fault)
        
        # Apply the fault
        self._apply_fault(fault)
        
        self.logger.info(f"Fault injected: {fault_type} on {target_device}")
        
        # Record event
        self._record_event('fault_injected', target_device, None, 
                          f"Fault {fault_type} injected", {'fault': fault})
    
    def _apply_fault(self, fault: FaultInjection):
        """Apply a fault to the target device"""
        device = self.devices[fault.target_device]
        
        if fault.fault_type == 'interface_down':
            if fault.target_interface:
                device.set_interface_state(fault.target_interface, InterfaceState.DOWN)
            else:
                # Bring down all interfaces
                for intf_name in device.interfaces.keys():
                    device.set_interface_state(intf_name, InterfaceState.DOWN)
        
        elif fault.fault_type == 'link_failure':
            # Remove neighbors
            neighbors = device.neighbors.copy()
            for neighbor in neighbors:
                device.remove_neighbor(neighbor)
                # Also remove from the other device
                if neighbor in self.devices:
                    self.devices[neighbor].remove_neighbor(fault.target_device)
        
        elif fault.fault_type == 'high_cpu':
            # Simulate high CPU usage
            device.inject_fault('high_cpu')
        
        elif fault.fault_type == 'memory_leak':
            # Simulate memory issues
            device.inject_fault('high_cpu')  # Use existing fault type
        
        elif fault.fault_type == 'packet_loss':
            # Simulate packet loss
            device.inject_fault('high_cpu')  # Use existing fault type
        
        else:
            self.logger.warning(f"Unknown fault type: {fault.fault_type}")
    
    def _remove_fault(self, fault: FaultInjection):
        """Remove a fault from the target device"""
        device = self.devices[fault.target_device]
        
        if fault.fault_type == 'interface_down':
            if fault.target_interface:
                device.set_interface_state(fault.target_interface, InterfaceState.UP)
            else:
                # Bring up all interfaces
                for intf_name in device.interfaces.keys():
                    device.set_interface_state(intf_name, InterfaceState.UP)
        
        elif fault.fault_type == 'link_failure':
            # Restore neighbors based on topology
            neighbors = self.topology_generator.get_device_neighbors(fault.target_device)
            for neighbor in neighbors:
                device.add_neighbor(neighbor)
                # Also add to the other device
                if neighbor in self.devices:
                    self.devices[neighbor].add_neighbor(fault.target_device)
        
        self.logger.info(f"Fault removed: {fault.fault_type} from {fault.target_device}")
    
    def _process_faults(self):
        """Process fault injection and recovery"""
        while self.simulation_running:
            try:
                current_time = time.time()
                faults_to_remove = []
                
                for fault in self.active_faults:
                    if fault.duration and fault.start_time:
                        if current_time - fault.start_time >= fault.duration:
                            # Fault duration expired, remove it
                            self._remove_fault(fault)
                            faults_to_remove.append(fault)
                
                # Remove expired faults
                for fault in faults_to_remove:
                    self.active_faults.remove(fault)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error processing faults: {e}")
    
    def _process_events(self):
        """Process simulation events"""
        while self.simulation_running:
            try:
                # Process events from queue
                try:
                    event = self.event_queue.get(timeout=1)
                    self._handle_event(event)
                except queue.Empty:
                    pass
                
                # Update simulation time
                if not self.simulation_paused:
                    self.simulation_time = time.time() - self.simulation_start_time
                
            except Exception as e:
                self.logger.error(f"Error processing events: {e}")
    
    def _handle_event(self, event: SimulationEvent):
        """Handle a simulation event"""
        # Add to events list
        self.events.append(event)
        
        # Call registered event handlers
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    self.logger.error(f"Error in event handler: {e}")
        
        # Update statistics
        self._update_statistics(event)
    
    def _record_event(self, event_type: str, source_device: str, 
                     target_device: Optional[str], description: str, data: Dict[str, Any]):
        """Record a simulation event"""
        event = SimulationEvent(
            timestamp=time.time(),
            event_type=event_type,
            source_device=source_device,
            target_device=target_device,
            description=description,
            data=data
        )
        
        self.event_queue.put(event)
    
    def _update_statistics(self, event: SimulationEvent):
        """Update simulation statistics based on events"""
        if event.event_type == 'packet_sent':
            self.statistics['total_packets'] += 1
        elif event.event_type == 'error_occurred':
            self.statistics['total_errors'] += 1
        elif event.event_type == 'device_start':
            self.statistics['devices_online'] += 1
        elif event.event_type == 'device_stop':
            self.statistics['devices_offline'] += 1
    
    def _collect_statistics(self):
        """Collect real-time statistics from devices"""
        while self.simulation_running:
            try:
                if not self.simulation_paused:
                    # Count online/offline devices
                    online_count = 0
                    offline_count = 0
                    
                    for device in self.devices.values():
                        if device.is_alive():
                            online_count += 1
                        else:
                            offline_count += 1
                    
                    self.statistics['devices_online'] = online_count
                    self.statistics['devices_offline'] = offline_count
                    
                    # Count active/failed links
                    active_links = 0
                    failed_links = 0
                    
                    for link in self.topology.links:
                        source_device = self.devices.get(link.source_device)
                        target_device = self.devices.get(link.target_device)
                        
                        if (source_device and target_device and 
                            source_device.is_alive() and target_device.is_alive()):
                            active_links += 1
                        else:
                            failed_links += 1
                    
                    self.statistics['links_active'] = active_links
                    self.statistics['links_failed'] = failed_links
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error collecting statistics: {e}")
    
    def send_packet(self, source_device: str, target_device: str, 
                   packet_type: str, packet_data: Dict[str, Any]):
        """Send a packet between devices"""
        if source_device not in self.devices or target_device not in self.devices:
            self.logger.error(f"Invalid device names: {source_device} -> {target_device}")
            return
        
        source = self.devices[source_device]
        target = self.devices[target_device]
        
        # Create packet message
        packet = {
            'type': packet_type,
            'source': source_device,
            'target': target_device,
            'timestamp': time.time(),
            'data': packet_data
        }
        
        # Send packet
        target.send_message(packet)
        
        # Record event
        self._record_event('packet_sent', source_device, target_device, 
                          f"Packet sent: {packet_type}", packet_data)
        
        self.logger.debug(f"Packet sent from {source_device} to {target_device}: {packet_type}")
    
    def get_device_status(self, device_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific device"""
        if device_name not in self.devices:
            return None
        
        device = self.devices[device_name]
        return device.get_status()
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get overall network status"""
        status = {
            'simulation_running': self.simulation_running,
            'simulation_paused': self.simulation_paused,
            'simulation_time': self.simulation_time,
            'total_devices': len(self.devices),
            'active_faults': len(self.active_faults),
            'statistics': self.statistics.copy(),
            'devices': {}
        }
        
        # Get status of each device
        for hostname, device in self.devices.items():
            status['devices'][hostname] = {
                'online': device.is_alive(),
                'neighbors': device.neighbors.copy(),
                'interfaces': len(device.interfaces)
            }
        
        return status
    
    def get_simulation_events(self, event_type: Optional[str] = None, 
                             limit: Optional[int] = None) -> List[SimulationEvent]:
        """Get simulation events, optionally filtered by type"""
        events = self.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if limit:
            events = events[-limit:]
        
        return events
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        self.logger.info(f"Registered event handler for {event_type}")
    
    def export_simulation_log(self, output_file: str):
        """Export simulation events and statistics to a log file"""
        log_data = {
            'simulation_info': {
                'start_time': self.simulation_start_time,
                'end_time': time.time() if not self.simulation_running else None,
                'total_time': self.simulation_time,
                'total_events': len(self.events),
                'total_faults': len(self.fault_history)
            },
            'statistics': self.statistics,
            'events': [
                {
                    'timestamp': event.timestamp,
                    'event_type': event.event_type,
                    'source_device': event.source_device,
                    'target_device': event.target_device,
                    'description': event.description,
                    'data': event.data
                }
                for event in self.events
            ],
            'faults': [
                {
                    'fault_type': fault.fault_type,
                    'target_device': fault.target_device,
                    'target_interface': fault.target_interface,
                    'parameters': fault.parameters,
                    'duration': fault.duration,
                    'start_time': fault.start_time
                }
                for fault in self.fault_history
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        self.logger.info(f"Simulation log exported to {output_file}")
    
    def run_day1_scenario(self):
        """Run Day-1 network discovery scenario"""
        self.logger.info("Running Day-1 network discovery scenario...")
        
        # Simulate ARP discovery
        for device_name, device in self.devices.items():
            for interface in device.interfaces.values():
                if interface.ip_address:
                    # Send ARP request
                    arp_request = {
                        'type': 'arp_request',
                        'target_ip': interface.ip_address,
                        'source_mac': f"MAC_{device_name}_{interface.name}"
                    }
                    device.send_message(arp_request)
        
        # Simulate OSPF discovery for routers
        for device_name, device in self.devices.items():
            if device.device_type == DeviceType.ROUTER:
                # Send OSPF hello
                ospf_hello = {
                    'type': 'ospf_hello',
                    'source': device_name,
                    'neighbors': device.neighbors
                }
                device.send_message(ospf_hello)
        
        # Simulate neighbor discovery
        for device_name, device in self.devices.items():
            for neighbor in device.neighbors:
                # Send neighbor discovery message
                neighbor_msg = {
                    'type': 'neighbor_discovery',
                    'source': device_name,
                    'target': neighbor
                }
                device.send_message(neighbor_msg)
        
        self.logger.info("Day-1 scenario completed")
    
    def run_fault_scenario(self, scenario_type: str):
        """Run predefined fault scenarios"""
        self.logger.info(f"Running fault scenario: {scenario_type}")
        
        if scenario_type == 'link_failure':
            # Simulate link failures
            for link in self.topology.links[:2]:  # Fail first 2 links
                self.inject_fault('link_failure', link.source_device, 
                                link.source_interface, duration=30)
        
        elif scenario_type == 'interface_failure':
            # Simulate interface failures
            for device_name in list(self.devices.keys())[:2]:  # Fail first 2 devices
                device = self.devices[device_name]
                if device.interfaces:
                    first_interface = list(device.interfaces.keys())[0]
                    self.inject_fault('interface_down', device_name, first_interface, duration=30)
        
        elif scenario_type == 'device_failure':
            # Simulate device failures
            for device_name in list(self.devices.keys())[:1]:  # Fail first device
                self.inject_fault('high_cpu', device_name, duration=60)
        
        else:
            self.logger.warning(f"Unknown fault scenario: {scenario_type}")
        
        self.logger.info(f"Fault scenario {scenario_type} completed")

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("NetworkSimulator module loaded successfully")
    print("Use with TopologyGenerator to simulate network behavior") 