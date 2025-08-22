import os
import io
import time
import json
import networkx as nx
import matplotlib.pyplot as plt
import streamlit as st
from core import ConfigParser, TopologyGenerator, NetworkValidator, NetworkSimulator

st.set_page_config(page_title="Network Simulator", layout="wide")

# Sidebar
st.sidebar.title("Network Simulator")
st.sidebar.caption("Simple web UI")
config_dir = st.sidebar.text_input("Config directory", value="conf")
output_dir = st.sidebar.text_input("Output directory", value="output")
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

# Instances
parser = ConfigParser()
generator = TopologyGenerator()
validator = NetworkValidator()

# Session state
if "configs" not in st.session_state:
    st.session_state["configs"] = {}
if "topo" not in st.session_state:
    st.session_state["topo"] = None
if "analysis" not in st.session_state:
    st.session_state["analysis"] = {}
if "validation" not in st.session_state:
    st.session_state["validation"] = {"issues": [], "recs": []}

# Header
st.title("Network Simulator (Simple UI)")

# Step controls
col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    if st.button("1) Parse configs", use_container_width=True):
        try:
            configs = {}
            for root, _, files in os.walk(config_dir):
                for f in files:
                    if f == "config.dump":
                        hostname = os.path.basename(root)
                        configs[hostname] = parser.parse_config_file(os.path.join(root, f))
            st.session_state["configs"] = configs
            st.success(f"Loaded {len(configs)} device configs: {', '.join(configs.keys())}")
        except Exception as e:
            st.error(str(e))
with col_b:
    if st.button("2) Generate topology", use_container_width=True):
        try:
            topo = generator.generate_topology(st.session_state.get("configs", {}))
            st.session_state["topo"] = topo
            analysis = generator.analyze_topology()
            st.session_state["analysis"] = analysis
            generator.export_topology(os.path.join(output_dir, "ui_topology.json"))
            st.toast("Topology saved to output/ui_topology.json", icon="✅")
        except Exception as e:
            st.error(str(e))
with col_c:
    if st.button("3) Validate", use_container_width=True):
        try:
            topo = st.session_state.get("topo")
            issues, recs = validator.validate_network(topo)
            st.session_state["validation"] = {"issues": issues, "recs": recs}
            validator.export_validation_report(os.path.join(output_dir, "ui_validation.json"))
            st.toast("Validation saved to output/ui_validation.json", icon="✅")
        except Exception as e:
            st.error(str(e))
with col_d:
    if st.button("4) Run simulation (10s)", use_container_width=True):
        try:
            topo = st.session_state.get("topo")
            sim = NetworkSimulator(topo)
            sim.start_simulation()
            sim.run_day1_scenario()
            time.sleep(10)
            sim.stop_simulation()
            sim.export_simulation_log(os.path.join(output_dir, "ui_simulation.json"))
            st.toast("Simulation saved to output/ui_simulation.json", icon="✅")
        except Exception as e:
            st.error(str(e))

st.divider()

# Tabs for views
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Topology", "Validation", "Downloads"])

with tab1:
    a = st.session_state.get("analysis", {})
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Devices", a.get("total_devices", 0))
    m2.metric("Links", a.get("total_links", 0))
    m3.metric("Subnets", a.get("total_subnets", 0))
    m4.metric("VLANs", a.get("total_vlans", 0))
    m5.metric("Avg BW (Mbps)", f"{a.get('bandwidth_analysis', {}).get('average_bandwidth_mbps', 0):.1f}")
    st.write("Connectivity:", a.get("connectivity", {}).get("status", "-"))
    if a.get("potential_issues"):
        st.write("Potential Issues:")
        for i in a["potential_issues"]:
            st.write("-", i)

with tab2:
    topo = st.session_state.get("topo")
    if topo:
        # Draw a simple networkx graph
        fig, ax = plt.subplots(figsize=(6, 4))
        G = topo.graph if hasattr(topo, "graph") else nx.Graph()
        pos = nx.spring_layout(G, seed=42)
        nx.draw_networkx_nodes(G, pos, node_size=800, node_color="#87CEEB", ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color="#999999", width=1.5, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=10, font_color="#222222", ax=ax)
        ax.axis("off")
        st.pyplot(fig, use_container_width=True)
        # Also show a compact JSON summary
        st.caption("Topology summary (compact)")
        st.json({
            "devices": list(topo.devices.keys()),
            "links": [
                {
                    "src": l.source_device,
                    "dst": l.target_device,
                    "bw": l.bandwidth
                } for l in topo.links
            ]
        })
    else:
        st.info("Generate topology to view graph.")

with tab3:
    v = st.session_state.get("validation", {"issues": [], "recs": []})
    issues = v.get("issues", [])
    recs = v.get("recs", [])
    c1, c2 = st.columns(2)
    c1.metric("Issues", len(issues))
    c2.metric("Recommendations", len(recs))
    st.subheader("Issues (first 20)")
    if issues:
        st.json([i.__dict__ for i in issues][:20])
    else:
        st.success("No issues found.")
    st.subheader("Recommendations (first 20)")
    if recs:
        st.json([r.__dict__ for r in recs][:20])
    else:
        st.info("No recommendations.")

with tab4:
    # Prepare downloads if files exist
    files = {
        "Topology JSON": os.path.join(output_dir, "ui_topology.json"),
        "Validation Report": os.path.join(output_dir, "ui_validation.json"),
        "Simulation Log": os.path.join(output_dir, "ui_simulation.json"),
    }
    for label, path in files.items():
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            st.download_button(label=f"Download {label}", data=data, file_name=os.path.basename(path), mime="application/json")
        else:
            st.caption(f"{label} will appear after you run the corresponding step.")

st.caption("Workflow: Parse → Topology → Validation → Simulation. Keep it simple.")