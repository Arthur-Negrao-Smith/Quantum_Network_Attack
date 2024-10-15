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

def test(sim_time: int, classical_channel_delay: int, classical_channel_distance: float,
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