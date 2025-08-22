import re
import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import ipaddress

@dataclass
class ParsedInterface:
    name: str
    ip_address: str
    subnet_mask: str
    bandwidth: int
    mtu: int
    vlan: Optional[int]
    description: str
    shutdown: bool
    encapsulation: Optional[str]

@dataclass
class ParsedConfig:
    hostname: str
    interfaces: List[ParsedInterface]
    routing_protocols: List[str]
    vlans: List[int]
    ospf_areas: List[str]
    bgp_asn: Optional[int]
    default_gateway: Optional[str]
    dns_servers: List[str]
    ntp_servers: List[str]
    access_lists: Dict[str, List[str]]
    route_maps: Dict[str, List[str]]

class ConfigParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common Cisco IOS patterns
        self.patterns = {
            'hostname': r'hostname\s+(\S+)',
            'interface': r'interface\s+(\S+)',
            'ip_address': r'ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)',
            'description': r'description\s+(.+)',
            'shutdown': r'shutdown',
            'no_shutdown': r'no\s+shutdown',
            'bandwidth': r'bandwidth\s+(\d+)',
            'mtu': r'mtu\s+(\d+)',
            'vlan': r'switchport\s+access\s+vlan\s+(\d+)',
            'encapsulation': r'encapsulation\s+(\S+)',
            'ospf': r'router\s+ospf\s+(\d+)',
            'bgp': r'router\s+bgp\s+(\d+)',
            'default_gateway': r'ip\s+route\s+0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)',
            'dns_server': r'ip\s+name-server\s+(\d+\.\d+\.\d+\.\d+)',
            'ntp_server': r'ntp\s+server\s+(\d+\.\d+\.\d+\.\d+)',
            'access_list': r'access-list\s+(\d+)\s+(.+)',
            'route_map': r'route-map\s+(\S+)\s+(.+)'
        }
    
    def parse_config_file(self, file_path: str) -> ParsedConfig:
        """Parse a router configuration file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        self.logger.info(f"Parsing configuration file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract basic information
        hostname = self._extract_hostname(content)
        interfaces = self._extract_interfaces(content)
        routing_protocols = self._extract_routing_protocols(content)
        vlans = self._extract_vlans(content)
        ospf_areas = self._extract_ospf_areas(content)
        bgp_asn = self._extract_bgp_asn(content)
        default_gateway = self._extract_default_gateway(content)
        dns_servers = self._extract_dns_servers(content)
        ntp_servers = self._extract_ntp_servers(content)
        access_lists = self._extract_access_lists(content)
        route_maps = self._extract_route_maps(content)
        
        return ParsedConfig(
            hostname=hostname,
            interfaces=interfaces,
            routing_protocols=routing_protocols,
            vlans=vlans,
            ospf_areas=ospf_areas,
            bgp_asn=bgp_asn,
            default_gateway=default_gateway,
            dns_servers=dns_servers,
            ntp_servers=ntp_servers,
            access_lists=access_lists,
            route_maps=route_maps
        )
    
    def _extract_hostname(self, content: str) -> str:
        """Extract hostname from configuration"""
        match = re.search(self.patterns['hostname'], content)
        if match:
            return match.group(1)
        return "unknown"
    
    def _extract_interfaces(self, content: str) -> List[ParsedInterface]:
        """Extract interface configurations"""
        interfaces = []
        
        # Find all interface blocks
        interface_blocks = re.findall(
            r'interface\s+(\S+)(.*?)(?=interface|\Z)', 
            content, 
            re.DOTALL
        )
        
        for interface_name, interface_config in interface_blocks:
            try:
                # Extract IP address and subnet mask
                ip_match = re.search(self.patterns['ip_address'], interface_config)
                ip_address = ""
                subnet_mask = ""
                if ip_match:
                    ip_address = ip_match.group(1)
                    subnet_mask = ip_match.group(2)
                
                # Extract description
                desc_match = re.search(self.patterns['description'], interface_config)
                description = desc_match.group(1) if desc_match else ""
                
                # Check if interface is shutdown
                shutdown = bool(re.search(self.patterns['shutdown'], interface_config))
                
                # Extract bandwidth
                bw_match = re.search(self.patterns['bandwidth'], interface_config)
                bandwidth = int(bw_match.group(1)) if bw_match else 100
                
                # Extract MTU
                mtu_match = re.search(self.patterns['mtu'], interface_config)
                mtu = int(mtu_match.group(1)) if mtu_match else 1500
                
                # Extract VLAN
                vlan_match = re.search(self.patterns['vlan'], interface_config)
                vlan = int(vlan_match.group(1)) if vlan_match else None
                
                # Extract encapsulation
                encap_match = re.search(self.patterns['encapsulation'], interface_config)
                encapsulation = encap_match.group(1) if encap_match else None
                
                interface = ParsedInterface(
                    name=interface_name,
                    ip_address=ip_address,
                    subnet_mask=subnet_mask,
                    bandwidth=bandwidth,
                    mtu=mtu,
                    vlan=vlan,
                    description=description,
                    shutdown=shutdown,
                    encapsulation=encapsulation
                )
                
                interfaces.append(interface)
                
            except Exception as e:
                self.logger.warning(f"Error parsing interface {interface_name}: {e}")
                continue
        
        return interfaces
    
    def _extract_routing_protocols(self, content: str) -> List[str]:
        """Extract routing protocols from configuration"""
        protocols = []
        
        # Check for OSPF
        if re.search(self.patterns['ospf'], content):
            protocols.append('OSPF')
        
        # Check for BGP
        if re.search(self.patterns['bgp'], content):
            protocols.append('BGP')
        
        # Check for EIGRP (basic check)
        if re.search(r'router\s+eigrp', content):
            protocols.append('EIGRP')
        
        # Check for RIP (basic check)
        if re.search(r'router\s+rip', content):
            protocols.append('RIP')
        
        return protocols
    
    def _extract_vlans(self, content: str) -> List[int]:
        """Extract VLAN configurations"""
        vlans = []
        
        # Find VLAN definitions
        vlan_matches = re.findall(r'vlan\s+(\d+)', content)
        for vlan_match in vlan_matches:
            try:
                vlans.append(int(vlan_match))
            except ValueError:
                continue
        
        return list(set(vlans))  # Remove duplicates
    
    def _extract_ospf_areas(self, content: str) -> List[str]:
        """Extract OSPF area information"""
        areas = []
        
        # Find OSPF area assignments
        area_matches = re.findall(r'network\s+\d+\.\d+\.\d+\.\d+\s+\d+\.\d+\.\d+\.\d+\s+area\s+(\S+)', content)
        for area_match in area_matches:
            areas.append(area_match)
        
        return list(set(areas))
    
    def _extract_bgp_asn(self, content: str) -> Optional[int]:
        """Extract BGP ASN"""
        match = re.search(self.patterns['bgp'], content)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None
    
    def _extract_default_gateway(self, content: str) -> Optional[str]:
        """Extract default gateway"""
        match = re.search(self.patterns['default_gateway'], content)
        if match:
            return match.group(1)
        return None
    
    def _extract_dns_servers(self, content: str) -> List[str]:
        """Extract DNS servers"""
        servers = []
        matches = re.findall(self.patterns['dns_server'], content)
        for match in matches:
            servers.append(match)
        return servers
    
    def _extract_ntp_servers(self, content: str) -> List[str]:
        """Extract NTP servers"""
        servers = []
        matches = re.findall(self.patterns['ntp_server'], content)
        for match in matches:
            servers.append(match)
        return servers
    
    def _extract_access_lists(self, content: str) -> Dict[str, List[str]]:
        """Extract access lists"""
        access_lists = {}
        
        # Find access-list definitions
        acl_matches = re.findall(r'access-list\s+(\d+)\s+(.+)', content)
        for acl_id, acl_content in acl_matches:
            if acl_id not in access_lists:
                access_lists[acl_id] = []
            access_lists[acl_id].append(acl_content.strip())
        
        return access_lists
    
    def _extract_route_maps(self, content: str) -> Dict[str, List[str]]:
        """Extract route maps"""
        route_maps = {}
        
        # Find route-map definitions
        rm_matches = re.findall(r'route-map\s+(\S+)\s+(.+)', content)
        for rm_name, rm_content in rm_matches:
            if rm_name not in route_maps:
                route_maps[rm_name] = []
            route_maps[rm_name].append(rm_content.strip())
        
        return route_maps
    
    def validate_config(self, config: ParsedConfig) -> List[str]:
        """Validate parsed configuration for common issues"""
        issues = []
        
        # Check for duplicate IP addresses
        ip_addresses = {}
        for interface in config.interfaces:
            if interface.ip_address:
                if interface.ip_address in ip_addresses:
                    issues.append(f"Duplicate IP address {interface.ip_address} on interfaces {ip_addresses[interface.ip_address]} and {interface.name}")
                else:
                    ip_addresses[interface.ip_address] = interface.name
        
        # Check for MTU mismatches
        mtu_values = {}
        for interface in config.interfaces:
            if interface.mtu:
                if interface.mtu in mtu_values:
                    issues.append(f"MTU mismatch: {interface.name} and {mtu_values[interface.mtu]} have same MTU {interface.mtu}")
                else:
                    mtu_values[interface.mtu] = interface.name
        
        # Check for missing default gateway
        if not config.default_gateway:
            issues.append("No default gateway configured")
        
        # Check for routing protocol conflicts
        if 'OSPF' in config.routing_protocols and 'BGP' in config.routing_protocols:
            issues.append("Both OSPF and BGP configured - potential routing conflicts")
        
        # Check for VLAN configuration issues
        for interface in config.interfaces:
            if interface.vlan and interface.vlan not in config.vlans:
                issues.append(f"Interface {interface.name} configured for VLAN {interface.vlan} but VLAN not defined")
        
        return issues
    
    def export_to_json(self, config: ParsedConfig, output_file: str):
        """Export parsed configuration to JSON format"""
        config_dict = {
            'hostname': config.hostname,
            'interfaces': [
                {
                    'name': intf.name,
                    'ip_address': intf.ip_address,
                    'subnet_mask': intf.subnet_mask,
                    'bandwidth': intf.bandwidth,
                    'mtu': intf.mtu,
                    'vlan': intf.vlan,
                    'description': intf.description,
                    'shutdown': intf.shutdown,
                    'encapsulation': intf.encapsulation
                }
                for intf in config.interfaces
            ],
            'routing_protocols': config.routing_protocols,
            'vlans': config.vlans,
            'ospf_areas': config.ospf_areas,
            'bgp_asn': config.bgp_asn,
            'default_gateway': config.default_gateway,
            'dns_servers': config.dns_servers,
            'ntp_servers': config.ntp_servers,
            'access_lists': config.access_lists,
            'route_maps': config.route_maps
        }
        
        with open(output_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        self.logger.info(f"Configuration exported to {output_file}")

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create parser instance
    parser = ConfigParser()
    
    # Example configuration content (for testing)
    sample_config = """
    hostname R1
    !
    interface GigabitEthernet0/0
     description WAN Interface
     ip address 192.168.1.1 255.255.255.0
     no shutdown
     bandwidth 1000
     mtu 1500
    !
    interface GigabitEthernet0/1
     description LAN Interface
     ip address 10.0.0.1 255.255.255.0
     no shutdown
     bandwidth 1000
     mtu 1500
    !
    router ospf 1
     network 10.0.0.0 0.0.0.255 area 0
     network 192.168.1.0 0.0.0.255 area 0
    !
    ip route 0.0.0.0 0.0.0.0 192.168.1.254
    """
    
    # Write sample config to file for testing
    with open('sample_config.txt', 'w') as f:
        f.write(sample_config)
    
    try:
        # Parse the configuration
        config = parser.parse_config_file('sample_config.txt')
        
        # Print parsed information
        print(f"Hostname: {config.hostname}")
        print(f"Interfaces: {len(config.interfaces)}")
        for intf in config.interfaces:
            print(f"  {intf.name}: {intf.ip_address}/{intf.subnet_mask}")
        
        print(f"Routing Protocols: {config.routing_protocols}")
        print(f"Default Gateway: {config.default_gateway}")
        
        # Validate configuration
        issues = parser.validate_config(config)
        if issues:
            print("\nConfiguration Issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\nNo configuration issues found")
        
        # Export to JSON
        parser.export_to_json(config, 'parsed_config.json')
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Clean up test file
    if os.path.exists('sample_config.txt'):
        os.remove('sample_config.txt') 