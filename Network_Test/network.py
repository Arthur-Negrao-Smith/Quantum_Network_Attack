# Basic imports
from matplotlib import pyplot as plt
import time

# Importing sequence structures
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QuantumRouter, BSMNode
from sequence.components.optical_channel import (QuantumChannel,
                                             ClassicalChannel)

def mili_per_pico(miliseconds: float) -> float:
    picoseconds = miliseconds * 1e9
    return picoseconds

def kilo_per_meter(kilometers: float) -> float:
    meters = kilometers * 1e3
    return meters

def simulation(sim_time: int, classical_channel_delay: int, classical_channel_distance: float,
 quantum_channel_attenuation: float, quantum_channel_distance: float):
    """
    sim_time: duration of simulation time (ms)
    classical_channel_delay: delay on classical channels (ms)
    quantum_channel_attenuation: attenuation on quantum channels (dB/m) 
    quantum_channel_distance: distance of quantum channels (km)
    """

    # Convert units
    cc_delay = mili_per_pico(classical_channel_delay)
    qc_distance = kilo_per_meter(quantum_channel_distance)
    
    raw_fidelity = 0.85

    # Construct the simulation timeline; the constructor argument is the simulation time (ps)
    tl = Timeline(mili_per_pico(sim_time))

    ## Create our quantum network

    # Quantum routers
    # Args: name, timeline, number of quantum memories
    r0 = QuantumRouter('r0', tl, 50)
    r1 = QuantumRouter('r1', tl, 50)
    r2 = QuantumRouter('r2', tl, 50)
    r3 = QuantumRouter('r3', tl, 50)

    # Create BSM nodes
    m0 = BSMNode('m0', tl, ['r0', 'r1'])
    m1 = BSMNode('m1', tl, ['r1', 'r2'])
    m2 = BSMNode('m2', tl, ['r2', 'r3'])
    m3 = BSMNode('m3', tl, ['r3', 'r0'])

    # Create connection among router and BSM
    r0.add_bsm_node(m0.name, r1.name)
    r1.add_bsm_node(m1.name, r2.name)
    r2.add_bsm_node(m2.name, r3.name)
    r3.add_bsm_node(m3.name, r0.name)

    # set seeds for random generators
    nodes = [r0, r1, r2, r3, m0, m1, m2, m3]
    for i, node in enumerate(nodes):
        node.set_seed(i)

    nodes = [r0, r1, r2, r3]
    for node in nodes:
        memory_array = node.get_components_by_type("MemoryArray")[0]
        # Update the coherence time (measured in seconds)
        memory_array.update_memory_params("coherence_time", 10)
        # Similarly update the fidelity of entanglement of the memories
        memory_array.update_memory_params("raw_fidelity", raw_fidelity)

    # create all-to-all classical connections
    for node1 in nodes:
        for node2 in nodes:
            if node1 == node2:
                continue
            # construct a classical communication channel
            # Args: name, timeline, length (in m), delay (in ps)
            cc = ClassicalChannel("cc_%s_%s"%(node1.name, node2.name), 
                tl, classical_channel_distance, delay=cc_delay)
            cc.set_ends(node1, node2.name)

    # Create quantum channels linking r0 and r1 to m0
    qc0 = QuantumChannel('qc_r0_m0', tl, quantum_channel_attenuation, quantum_channel_distance)
    qc1 = QuantumChannel('qc_r1_m0', tl, quantum_channel_attenuation, quantum_channel_distance)
    qc0.set_ends(r0, m0.name)
    qc1.set_ends(r1, m0.name)
    # Create quantum channels linking r1 and r2 to m1
    qc2 = QuantumChannel('qc_r1_m1', tl, quantum_channel_attenuation, quantum_channel_distance)
    qc3 = QuantumChannel('qc_r2_m1', tl, quantum_channel_attenuation, quantum_channel_distance)
    qc2.set_ends(r1, m1.name)
    qc3.set_ends(r2, m1.name)
    # Create quantum channels linking r2 and r3 to m2
    qc4 = QuantumChannel('qc_r2_m2', tl, quantum_channel_attenuation, quantum_channel_distance)
    qc5 = QuantumChannel('qc_r3_m2', tl, quantum_channel_attenuation, quantum_channel_distance)
    qc4.set_ends(r2, m2.name)
    qc5.set_ends(r3, m2.name)
    # Create quantum channels linking r3 and r0 to m3
    qc2 = QuantumChannel('qc_r3_m3', tl, quantum_channel_attenuation, quantum_channel_distance)
    qc3 = QuantumChannel('qc_r0_m3', tl, quantum_channel_attenuation, quantum_channel_distance)
    qc2.set_ends(r1, m3.name)
    qc3.set_ends(r2, m3.name)

    # Create routing table manually
    # This table is based on quantum links
    # Args: name of destination node and the next node
    # Router0 routes
    r0.network_manager.protocol_stack[0].add_forwarding_rule("r1", "r1")
    r0.network_manager.protocol_stack[0].add_forwarding_rule("r2", "r1")
    r0.network_manager.protocol_stack[0].add_forwarding_rule("r3", "r3")
    # Router1 routes
    r1.network_manager.protocol_stack[0].add_forwarding_rule("r2", "r2")
    r1.network_manager.protocol_stack[0].add_forwarding_rule("r3", "r2")
    r1.network_manager.protocol_stack[0].add_forwarding_rule("r0", "r0")
    # Router2 routes
    r2.network_manager.protocol_stack[0].add_forwarding_rule("r3", "r3")
    r2.network_manager.protocol_stack[0].add_forwarding_rule("r0", "r3")
    r2.network_manager.protocol_stack[0].add_forwarding_rule("r1", "r1")
    # Router3 routes
    r3.network_manager.protocol_stack[0].add_forwarding_rule("r0", "r0")
    r3.network_manager.protocol_stack[0].add_forwarding_rule("r1", "r0")
    r3.network_manager.protocol_stack[0].add_forwarding_rule("r2", "r2")

    ## Run simulation
    tl.init()
    
    # We use the network manager of an end router to make our entanglement request
    # Args: 
    # destination node, 
    # start time (ps) of entanglement, 
    # end time (ps) of entanglement, 
    # number of memories to entangle,
    # desired fidelity of entanglement
    