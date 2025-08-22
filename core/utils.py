import os
import json
import logging
import ipaddress
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import hashlib
import re
import time

class NetworkUtils:
    """Utility functions for network operations"""
    
    @staticmethod
    def is_valid_ip(ip_string: str) -> bool:
        """Check if a string is a valid IP address"""
        try:
            ipaddress.ip_address(ip_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_subnet_mask(mask_string: str) -> bool:
        """Check if a string is a valid subnet mask"""
        try:
            mask = ipaddress.IPv4Address(mask_string)
            mask_int = int(mask)
            
            # Convert to binary and check if it's a valid subnet mask
            binary = bin(mask_int)[2:].zfill(32)
            
            # Check if it's all 1s followed by all 0s
            found_zero = False
            for bit in binary:
                if bit == '0':
                    found_zero = True
                elif found_zero and bit == '1':
                    return False
            
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_network_address(ip_address: str, subnet_mask: str) -> str:
        """Get network address from IP and subnet mask"""
        try:
            network = ipaddress.IPv4Network(f"{ip_address}/{subnet_mask}", strict=False)
            return str(network.network_address)
        except ValueError:
            return ""
    
    @staticmethod
    def get_broadcast_address(ip_address: str, subnet_mask: str) -> str:
        """Get broadcast address from IP and subnet mask"""
        try:
            network = ipaddress.IPv4Network(f"{ip_address}/{subnet_mask}", strict=False)
            return str(network.broadcast_address)
        except ValueError:
            return ""
    
    @staticmethod
    def get_usable_hosts(ip_address: str, subnet_mask: str) -> int:
        """Get number of usable hosts in a subnet"""
        try:
            network = ipaddress.IPv4Network(f"{ip_address}/{subnet_mask}", strict=False)
            return network.num_addresses - 2  # Subtract network and broadcast
        except ValueError:
            return 0
    
    @staticmethod
    def is_same_subnet(ip1: str, mask1: str, ip2: str, mask2: str) -> bool:
        """Check if two IP addresses are in the same subnet"""
        try:
            network1 = ipaddress.IPv4Network(f"{ip1}/{mask1}", strict=False)
            network2 = ipaddress.IPv4Network(f"{ip2}/{mask2}", strict=False)
            return network1 == network2
        except ValueError:
            return False
    
    @staticmethod
    def calculate_bandwidth_utilization(current_usage: int, capacity: int) -> float:
        """Calculate bandwidth utilization percentage"""
        if capacity <= 0:
            return 0.0
        return (current_usage / capacity) * 100
    
    @staticmethod
    def estimate_latency(distance_km: float, link_type: str) -> float:
        """Estimate latency based on distance and link type"""
        # Speed of light in fiber: ~200,000 km/s
        # Speed of light in air: ~300,000 km/s
        
        if link_type == 'fiber':
            speed = 200000  # km/s
        elif link_type == 'wireless':
            speed = 300000  # km/s
        else:
            speed = 200000  # Default to fiber
        
        # Calculate propagation delay
        propagation_delay = distance_km / speed
        
        # Add processing delays
        processing_delay = 0.001  # 1ms base processing delay
        
        return (propagation_delay + processing_delay) * 1000  # Convert to milliseconds

class FileUtils:
    """Utility functions for file operations"""
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """Ensure a directory exists, create if it doesn't"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except OSError:
            return False
    
    @staticmethod
    def safe_write_json(data: Any, file_path: str, backup: bool = True) -> bool:
        """Safely write JSON data to a file with optional backup"""
        try:
            # Create backup if requested
            if backup and os.path.exists(file_path):
                backup_path = f"{file_path}.backup"
                os.rename(file_path, backup_path)
            
            # Write new data
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            logging.error(f"Error writing JSON file {file_path}: {e}")
            return False
    
    @staticmethod
    def safe_read_json(file_path: str) -> Optional[Any]:
        """Safely read JSON data from a file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error reading JSON file {file_path}: {e}")
            return None
    
    @staticmethod
    def find_config_files(directory: str, pattern: str = "*.dump") -> List[str]:
        """Find configuration files in a directory"""
        config_files = []
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.dump') or re.match(pattern, file):
                        config_files.append(os.path.join(root, file))
        except Exception as e:
            logging.error(f"Error searching for config files: {e}")
        
        return config_files
    
    @staticmethod
    def get_file_hash(file_path: str) -> Optional[str]:
        """Calculate MD5 hash of a file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating file hash: {e}")
            return None

class LogUtils:
    """Utility functions for logging"""
    
    @staticmethod
    def setup_logging(log_file: str, level: str = "INFO", 
                     format_string: Optional[str] = None) -> logging.Logger:
        """Setup logging configuration"""
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            FileUtils.ensure_directory(log_dir)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format=format_string,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger()
    
    @staticmethod
    def log_function_call(func_name: str, args: tuple, kwargs: dict, 
                         logger: logging.Logger) -> None:
        """Log function call details"""
        logger.debug(f"Function call: {func_name}")
        logger.debug(f"Arguments: {args}")
        logger.debug(f"Keyword arguments: {kwargs}")
    
    @staticmethod
    def log_performance(func_name: str, start_time: float, 
                       logger: logging.Logger) -> None:
        """Log function performance"""
        execution_time = time.time() - start_time
        logger.info(f"Function {func_name} executed in {execution_time:.4f} seconds")

class ValidationUtils:
    """Utility functions for validation"""
    
    @staticmethod
    def validate_ip_range(start_ip: str, end_ip: str) -> bool:
        """Validate that start IP is less than end IP"""
        try:
            start = ipaddress.IPv4Address(start_ip)
            end = ipaddress.IPv4Address(end_ip)
            return start < end
        except ValueError:
            return False
    
    @staticmethod
    def validate_vlan_id(vlan_id: int) -> bool:
        """Validate VLAN ID (1-4094)"""
        return 1 <= vlan_id <= 4094
    
    @staticmethod
    def validate_mtu(mtu: int) -> bool:
        """Validate MTU size (68-9000)"""
        return 68 <= mtu <= 9000
    
    @staticmethod
    def validate_bandwidth(bandwidth: int) -> bool:
        """Validate bandwidth value (positive integer)"""
        return bandwidth > 0
    
    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """Validate hostname format"""
        # Basic hostname validation
        if not hostname or len(hostname) > 63:
            return False
        
        # Check for valid characters
        valid_chars = re.compile(r'^[a-zA-Z0-9\-]+$')
        return bool(valid_chars.match(hostname))

class NetworkAnalysis:
    """Network analysis utilities"""
    
    @staticmethod
    def analyze_subnet_overlap(subnets: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Analyze subnet configurations for overlaps"""
        overlaps = []
        
        for i, subnet1 in enumerate(subnets):
            for j, subnet2 in enumerate(subnets[i+1:], i+1):
                try:
                    net1 = ipaddress.IPv4Network(f"{subnet1['ip']}/{subnet1['mask']}", strict=False)
                    net2 = ipaddress.IPv4Network(f"{subnet2['ip']}/{subnet2['mask']}", strict=False)
                    
                    if net1.overlaps(net2):
                        overlaps.append({
                            'subnet1': subnet1,
                            'subnet2': subnet2,
                            'overlap_type': 'full' if net1 == net2 else 'partial'
                        })
                except ValueError:
                    continue
        
        return overlaps
    
    @staticmethod
    def calculate_network_efficiency(devices: int, links: int) -> float:
        """Calculate network efficiency based on devices and links"""
        if devices <= 1:
            return 0.0
        
        # Optimal number of links for a fully connected network
        optimal_links = (devices * (devices - 1)) / 2
        
        # Efficiency is actual links / optimal links
        efficiency = links / optimal_links if optimal_links > 0 else 0.0
        
        return min(efficiency, 1.0)  # Cap at 100%
    
    @staticmethod
    def identify_bottlenecks(links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potential network bottlenecks"""
        bottlenecks = []
        
        # Sort links by bandwidth
        sorted_links = sorted(links, key=lambda x: x.get('bandwidth', 0))
        
        # Identify low bandwidth links
        for link in sorted_links[:3]:  # Top 3 lowest bandwidth
            if link.get('bandwidth', 0) < 100:  # Less than 100 Mbps
                bottlenecks.append({
                    'type': 'low_bandwidth',
                    'link': link,
                    'severity': 'high' if link.get('bandwidth', 0) < 10 else 'medium'
                })
        
        # Check for asymmetric links
        for link in links:
            if 'source_bandwidth' in link and 'target_bandwidth' in link:
                if link['source_bandwidth'] != link['target_bandwidth']:
                    bottlenecks.append({
                        'type': 'asymmetric_bandwidth',
                        'link': link,
                        'severity': 'medium'
                    })
        
        return bottlenecks

class TimeUtils:
    """Utility functions for time operations"""
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()
    
    @staticmethod
    def parse_timestamp(timestamp: str) -> Optional[datetime]:
        """Parse ISO timestamp string"""
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            return None

# Example usage and testing
if __name__ == "__main__":
    # Test NetworkUtils
    print("Testing NetworkUtils...")
    print(f"Valid IP: {NetworkUtils.is_valid_ip('192.168.1.1')}")
    print(f"Valid subnet mask: {NetworkUtils.is_valid_subnet_mask('255.255.255.0')}")
    print(f"Network address: {NetworkUtils.get_network_address('192.168.1.100', '255.255.255.0')}")
    
    # Test ValidationUtils
    print("\nTesting ValidationUtils...")
    print(f"Valid VLAN: {ValidationUtils.validate_vlan_id(100)}")
    print(f"Valid MTU: {ValidationUtils.validate_mtu(1500)}")
    print(f"Valid hostname: {ValidationUtils.validate_hostname('router-01')}")
    
    # Test NetworkAnalysis
    print("\nTesting NetworkAnalysis...")
    subnets = [
        {'ip': '192.168.1.0', 'mask': '255.255.255.0'},
        {'ip': '192.168.1.128', 'mask': '255.255.255.128'}
    ]
    overlaps = NetworkAnalysis.analyze_subnet_overlap(subnets)
    print(f"Subnet overlaps: {overlaps}")
    
    print("\nUtils module loaded successfully!") 