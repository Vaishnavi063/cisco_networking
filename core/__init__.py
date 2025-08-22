"""
Network Simulator Core Package

This package contains the core functionality for the network simulator:
- Device management and simulation
- Configuration parsing
- Topology generation
- Network validation
- Simulation engine
- Utility functions
"""

from .device import NetworkDevice, DeviceType, InterfaceState, Interface
from .config_parser import ConfigParser, ParsedConfig, ParsedInterface
from .topology_generator import TopologyGenerator, NetworkTopology, NetworkLink
from .validator import NetworkValidator, ValidationIssue, OptimizationRecommendation
from .simulator import NetworkSimulator, SimulationEvent, FaultInjection
from .utils import (
    NetworkUtils, FileUtils, LogUtils, ValidationUtils, 
    NetworkAnalysis, TimeUtils
)

__version__ = "1.0.0"
__author__ = "Network Simulator Team"

__all__ = [
    # Device classes
    'NetworkDevice',
    'DeviceType', 
    'InterfaceState',
    'Interface',
    
    # Configuration classes
    'ConfigParser',
    'ParsedConfig',
    'ParsedInterface',
    
    # Topology classes
    'TopologyGenerator',
    'NetworkTopology',
    'NetworkLink',
    
    # Validation classes
    'NetworkValidator',
    'ValidationIssue',
    'OptimizationRecommendation',
    
    # Simulation classes
    'NetworkSimulator',
    'SimulationEvent',
    'FaultInjection',
    
    # Utility classes
    'NetworkUtils',
    'FileUtils',
    'LogUtils',
    'ValidationUtils',
    'NetworkAnalysis',
    'TimeUtils'
] 