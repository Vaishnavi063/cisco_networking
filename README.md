# Network Simulator

A comprehensive network simulation and analysis tool that automatically generates network topology from router configuration files, validates configurations, and simulates network behavior with fault injection capabilities.

## 🎯 Problem Statement

Currently, there is no existing solution to automatically generate a network topology from the configuration files of individual routers. This tool addresses this gap by providing:

- **Automatic Topology Generation**: Creates hierarchical network topology from router configuration files
- **Network Validation**: Detects configuration issues like duplicate IPs, VLAN problems, and routing conflicts
- **Performance Analysis**: Analyzes bandwidth, latency, and identifies bottlenecks
- **Network Simulation**: Simulates Day-1 scenarios and fault injection for testing
- **Optimization Recommendations**: Suggests improvements for network efficiency and security

## 🏗️ Architecture

The network simulator is built with a modular architecture:

```
network_simulator/
├── core/                     # Core simulation engine
│   ├── device.py            # Network device representation
│   ├── config_parser.py     # Configuration file parser
│   ├── topology_generator.py # Topology generation logic
│   ├── validator.py         # Network validation engine
│   ├── simulator.py         # Main simulation engine
│   └── utils.py             # Utility functions
├── ui/                      # User interfaces
│   └── cli.py              # Command-line interface
├── web_app.py               # Simple Streamlit web UI
├── conf/                    # Configuration files
│   ├── R1/config.dump      # Router 1 configuration
│   ├── R2/config.dump      # Router 2 configuration
│   └── R3/config.dump      # Router 3 configuration
├── tests/                   # Unit and integration tests
├── logs/                    # Simulation logs
├── output/                  # Generated reports
└── main.py                  # Main application entry point
```

## 🌐 Web UI (Streamlit) — Simple and Ready
A minimal browser UI is available via Streamlit to run the full workflow without CLI.

### Run the web app
```bash
cd network_simulator
pip install -r requirements.txt
python3 -m streamlit run web_app.py --server.port 8501
```
Then open: `http://localhost:8501` (network/external URLs are shown in the terminal too).

### Workflow in the UI
- Set Config directory: `conf`, Output directory: `output`
- Click, in order: 1) Parse configs → 2) Generate topology → 3) Validate → 4) Run simulation (10s)
- Tabs:
  - Overview: metrics (devices, links, subnets, avg bandwidth) and connectivity
  - Topology: quick NetworkX graph and compact JSON summary
  - Validation: first 20 issues and recommendations
  - Downloads: buttons for `ui_topology.json`, `ui_validation.json`, `ui_simulation.json`

### Screenshots to capture
- UI Overview tab after Generate Topology (metrics + connectivity)
- Topology tab (graph)
- Validation tab (issues + recommendations)
- Downloads tab showing generated files

## 🚀 Features

### Core Functionality
- **Configuration Parsing**: Parses Cisco IOS-style router configurations
- **Topology Generation**: Automatically discovers network topology from IP addressing
- **Network Validation**: Comprehensive validation of network configurations
- **Performance Analysis**: Bandwidth and latency analysis
- **Security Assessment**: Access list and routing protocol analysis

### Simulation Capabilities
- **Day-1 Scenarios**: Simulates network discovery (ARP, OSPF, neighbor discovery)
- **Fault Injection**: Simulates link failures, interface failures, and device issues
- **Real-time Monitoring**: Live statistics and event tracking
- **Pause/Resume**: Control simulation execution
- **Event Logging**: Comprehensive logging of all network events

### Analysis & Reporting
- **Topology Analysis**: Network efficiency and connectivity analysis
- **Validation Reports**: Detailed issue identification and recommendations
- **Performance Metrics**: Bandwidth utilization and bottleneck identification
- **Export Capabilities**: JSON export for further analysis

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 1GB free disk space

### Python Dependencies
```
networkx==3.2.1          # Network graph analysis
pytest==7.4.3            # Testing framework
colorama==0.4.6          # Terminal colors
rich==13.7.0             # Rich terminal output
psutil==5.9.6            # System monitoring
scapy==2.5.0             # Network packet manipulation
ipaddress==1.0.23        # IP address handling
pyyaml==6.0.1            # YAML configuration support
jsonschema==4.20.0       # JSON validation
streamlit==1.37.1        # Simple web UI
```

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd network_simulator
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -c "from core import NetworkSimulator; print('Installation successful!')"
```

## 🎮 Usage

### Command Line Interface

#### Basic Analysis
```bash
# Parse and validate configurations
python ui/cli.py --config-dir conf --validate

# Generate topology
python ui/cli.py --config-dir conf --topology

# Run full analysis with export
python ui/cli.py --config-dir conf --validate --export-topology --export-validation
```

#### Simulation
```bash
# Run network simulation for 5 minutes
python ui/cli.py --config-dir conf --simulate --duration 300

# Run Day-1 discovery scenario
python ui/cli.py --config-dir conf --day1-scenario

# Run fault injection scenario
python ui/cli.py --config-dir conf --fault-scenario link_failure

# Inject specific fault
python ui/cli.py --config-dir conf --fault-injection interface_down R1 GigabitEthernet0/1
```

#### Output Options
```bash
# Export results to JSON
python ui/cli.py --config-dir conf --validate --export-json

# Specify output directory
python ui/cli.py --config-dir conf --output-dir results --export-topology

# Verbose output
python ui/cli.py --config-dir conf --validate --verbose
```

### Python API

#### Basic Usage
```python
from core import ConfigParser, TopologyGenerator, NetworkValidator, NetworkSimulator

# Parse configurations
config_parser = ConfigParser()
configs = {}
for config_file in config_files:
    hostname = extract_hostname(config_file)
    configs[hostname] = config_parser.parse_config_file(config_file)

# Generate topology
topology_generator = TopologyGenerator()
topology = topology_generator.generate_topology(configs)

# Validate network
validator = NetworkValidator()
issues, recommendations = validator.validate_network(topology)

# Run simulation
simulator = NetworkSimulator(topology)
simulator.start_simulation()
simulator.run_day1_scenario()
time.sleep(60)
simulator.stop_simulation()
```

#### Advanced Features
```python
# Inject faults
simulator.inject_fault('interface_down', 'R1', 'GigabitEthernet0/1', duration=30)
simulator.inject_fault('link_failure', 'R1', duration=60)

# Monitor simulation
status = simulator.get_network_status()
events = simulator.get_simulation_events('packet_sent', limit=100)

# Export results
simulator.export_simulation_log('simulation_log.json')
topology.export_topology('topology.json')
validator.export_validation_report('validation_report.json')
```

## 📁 Configuration Files

### Router Configuration Format
The simulator parses Cisco IOS-style configuration files. Place your router configurations in the `conf/` directory:

```
conf/
├── R1/
│   └── config.dump      # Router 1 configuration
├── R2/
│   └── config.dump      # Router 2 configuration
└── R3/
    └── config.dump      # Router 3 configuration
```

### Supported Configuration Elements
- **Interfaces**: IP addresses, subnet masks, bandwidth, MTU, VLANs
- **Routing Protocols**: OSPF, BGP, EIGRP, RIP
- **Access Lists**: Standard and extended ACLs
- **Route Maps**: Policy-based routing
- **VLANs**: Switch port configurations

## 🔍 Validation Features

### IP Configuration Validation
- Duplicate IP address detection
- Invalid IP address format checking
- Subnet mask validation
- Network overlap detection

### VLAN Validation
- VLAN consistency checking
- Missing VLAN definitions
- Single-interface VLAN detection

### Routing Validation
- Protocol conflict detection
- OSPF area consistency
- BGP ASN validation
- Default gateway configuration

### Performance Validation
- MTU mismatch detection
- Bandwidth bottleneck identification
- Network redundancy analysis

### Security Validation
- Access list implementation
- Default gateway configuration
- Routing protocol security

## 🎯 Simulation Scenarios

### Day-1 Network Discovery
- **ARP Discovery**: Automatic IP-to-MAC address resolution
- **OSPF Hello**: Router neighbor discovery and area formation
- **Neighbor Discovery**: Link layer neighbor detection
- **Routing Convergence**: Automatic route table population

### Fault Injection Scenarios
- **Link Failures**: Simulate physical link failures
- **Interface Failures**: Bring down specific interfaces
- **Device Failures**: Simulate device crashes or high CPU
- **Network Partitions**: Test network resilience

### Performance Testing
- **Bandwidth Testing**: Measure link utilization
- **Latency Analysis**: End-to-end delay measurement
- **Packet Loss**: Simulate network congestion
- **Load Balancing**: Test redundant path utilization

## 📊 Output and Reports

### Topology Export
```json
{
  "devices": {
    "R1": {
      "hostname": "R1",
      "interfaces": [...],
      "routing_protocols": ["OSPF"]
    }
  },
  "links": [
    {
      "source_device": "R1",
      "target_device": "R2",
      "bandwidth": 1000,
      "latency": 0.1
    }
  ],
  "subnets": {...},
  "vlans": {...}
}
```

### Validation Report
```json
{
  "summary": {
    "total_issues": 5,
    "total_recommendations": 3
  },
  "issues": [
    {
      "severity": "warning",
      "category": "performance",
      "message": "Low bandwidth link detected",
      "recommendation": "Upgrade to higher bandwidth"
    }
  ],
  "recommendations": [...]
}
```

### Simulation Log
```json
{
  "simulation_info": {
    "start_time": 1234567890,
    "total_events": 150,
    "total_faults": 2
  },
  "events": [...],
  "faults": [...],
  "statistics": {...}
}
```

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Test configuration parsing
pytest tests/test_config_parser.py -v

# Test topology generation
pytest tests/test_topology_generator.py -v

# Test validation
pytest tests/test_validator.py -v

# Test simulation
pytest tests/test_simulator.py -v
```

### Test Coverage
```bash
pytest --cov=core tests/ --cov-report=html
```

## 🔧 Configuration

### Logging Configuration
```python
from core.utils import LogUtils

# Setup logging with custom configuration
logger = LogUtils.setup_logging(
    log_file="custom.log",
    level="DEBUG",
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Output Directory Configuration
```python
# Customize output directories
app = NetworkSimulatorApp()
app.output_dir = "custom_output"
app.log_dir = "custom_logs"
```

## 🚨 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure you're in the correct directory
cd network_simulator

# Check Python path
python -c "import sys; print(sys.path)"

# Install missing dependencies
pip install -r requirements.txt
```

#### Configuration Parsing Issues
- Verify configuration file format (Cisco IOS style)
- Check file encoding (UTF-8 recommended)
- Ensure proper interface syntax

#### Simulation Issues
- Check available memory (simulation requires significant RAM)
- Verify network topology connectivity
- Check log files for detailed error messages

### Debug Mode
```bash
# Enable verbose logging
python ui/cli.py --config-dir conf --validate --verbose

# Check log files
tail -f logs/simulator.log
```

## 📈 Performance Considerations

### Memory Usage
- **Small Networks** (< 10 devices): 512MB RAM
- **Medium Networks** (10-50 devices): 2GB RAM
- **Large Networks** (> 50 devices): 8GB+ RAM

### CPU Usage
- **Idle**: 5-10% CPU
- **Active Simulation**: 20-50% CPU
- **Fault Injection**: 30-70% CPU

### Disk Space
- **Logs**: 10-100MB per simulation hour
- **Exports**: 1-10MB per topology
- **Temporary Files**: 50-500MB during simulation

## 🔮 Future Enhancements

### Planned Features
- **GUI Interface**: Web-based graphical user interface
- **Real-time Monitoring**: Live network status dashboard
- **Advanced Protocols**: Support for IPv6, MPLS, VXLAN
- **Cloud Integration**: AWS, Azure, GCP network simulation
- **API Server**: RESTful API for integration
- **Machine Learning**: Predictive network analysis

### Extension Points
- **Custom Protocols**: Plugin system for new protocols
- **External Tools**: Integration with network management tools
- **Reporting**: Custom report generation
- **Automation**: CI/CD pipeline integration

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Add docstrings for all classes and methods
- Maintain test coverage above 80%

### Testing Guidelines
- Write unit tests for all new functionality
- Ensure all tests pass before submitting
- Add integration tests for complex scenarios
- Update test documentation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Share questions and ideas
- **Docs**: See this README and inline code documentation

---

## 🚢 Publishing to GitHub (Quick Guide)
Initialize and push the project:
```bash
# from the project root (contains network_simulator/)
git init
git add .
git commit -m "feat: initial network simulator with Streamlit UI"

# create repo on GitHub (option A: using GitHub CLI)
# requires: https://cli.github.com/
gh repo create <your-username>/network-simulator --public --source . --remote origin --push

# option B: manual remote
# 1) create an empty repo on GitHub, then:
git remote add origin https://github.com/<your-username>/network-simulator.git
git branch -M main
git push -u origin main
```

Add a release tag (optional):
```bash
git tag -a v1.0.0 -m "Network Simulator v1.0 with Web UI"
git push origin v1.0.0
```

---

**Network Simulator** - Making network analysis and simulation accessible to everyone! 🚀 