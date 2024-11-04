from matplotlib import pyplot as plt
import time
from random import randint

# Importing sequence structures
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QuantumRouter, BSMNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel

# Importing sequence network attack
from sequence.network_management.network_manager import NetworkManager
from sequence.network_management.routing import StaticRoutingProtocol
from sequence.network_management.reservation import ResourceReservationProtocol

def mili_to_pico(miliseconds: float) -> float:
    picoseconds = miliseconds * 1e9
    return picoseconds

def kilo_to_meter(kilometers: float) -> float:
    meters = kilometers * 1e3
    return meters

def plotEntangleMemories(router: QuantumRouter, label: str, ax_type: str, ax: 'Axes') -> None:
    data = []
    for info in router.resource_manager.memory_manager:
        if info.entangle_time > 0:
            data.append(info.entangle_time / 1e12)
    data.sort()
    ax.plot(data, range(1, len(data) + 1), marker="o")
    ax.set_title(router.name)
    if label:
        if ax_type == 'x':
            ax.set_xlabel(label)
        else:
            ax.set_ylabel(label)

def displayMemoryFidelity(router: QuantumRouter, label: str, ax_type: str, ax: 'Axes', raw_fidelity: float) -> None:
    data = []
    for info in router.resource_manager.memory_manager:
        data.append(info.fidelity)
    ax.bar(range(len(data)), data)
    ax.plot([0, len(data)], [raw_fidelity, raw_fidelity], "k--")
    ax.plot([0, len(data)], [0.9, 0.9], "k--")
    ax.set_ylim(0.7,1)
    ax.set_title(router.name)
    if label:
        if ax_type == 'x':
            ax.set_xlabel(label)
        else:
            ax.set_ylabel(label)

def choiceNode(nodes: list, choice_node: int = None) -> list:
    """
        It will choose one of the network nodes according to the
        chosen and random number if it does not determine a node
    """
    choice_node = choice_node
    if choice_node == None:
        from random import randint
        choice_node = randint(0, len(nodes) - 1)

    if len(nodes) - choice_node == 2:
        aux = [nodes[choice_node], nodes[choice_node + 1], nodes[0]]
        print(f"Caso == 2: {aux}")
        return aux
    elif len(nodes) - choice_node == 1:
        aux = [nodes[choice_node], nodes[0], nodes[1]]
        print(f"Caso == 1: {aux}")
        return aux
    else:
        aux = [nodes[choice_node], nodes[choice_node+1], nodes[choice_node+2]]
        print(f"Caso genérico: {aux}")
        return aux

def NewNetworkManager(owner: "QuantumRouter", memory_array_name: str, swapping_success_rate: float = 0.5) -> "NetworkManager":
    """Function to create a new network manager.

    Will create a network manager with default protocol stack.
    This stack inclused a reservation and routing protocol.

    Args:
        owner (QuantumRouter): node to attach network manager to.
        memory_array_name (str): name of the memory array component on owner.
        swapping_success_rate (float): probability of swapping success

    Returns:
        NetworkManager: network manager object created.
    """
    swapping_success_rate = swapping_success_rate
    manager = NetworkManager(owner, [])
    routing = StaticRoutingProtocol(owner, owner.name + ".StaticRoutingProtocol", {})
    rsvp = ResourceReservationProtocol(owner, owner.name + ".RSVP", memory_array_name)
    rsvp.set_swapping_success_rate(swapping_success_rate)
    routing.upper_protocols.append(rsvp)
    rsvp.lower_protocols.append(routing)
    manager.load_stack([routing, rsvp])
    return manager

def simulation(sim_time: int, cc_delay: float, qc_atten: float, qc_dist: int, swapping_success_rate: int):
    """
    sim_time: duration of simulation time (ms)
    cc_delay: delay on classical channels (ms)
    qc_atten: attenuation on quantum channels (dB/m)
    qc_dist: distance of quantum channels (km)
    swapping_success_rate (float): probability of swapping success
    """

    # Convert units
    cc_delay = mili_to_pico(cc_delay)
    qc_distance = kilo_to_meter(qc_dist)

    raw_fidelity = 0.85

    # Construct the simulation timeline; the constructor argument is the simulation time (ps)
    tl = Timeline(mili_to_pico(sim_time))

    ## Create our quantum network

    # Quantum routers
    # Args: name, timeline, number of quantum memories
    r0 = QuantumRouter('r0', tl, 100)
    r1 = QuantumRouter('r1', tl, 100)
    r2 = QuantumRouter('r2', tl, 100)
    r3 = QuantumRouter('r3', tl, 100)

    # Create BSM nodes
    m0 = BSMNode('m0', tl, ['r0', 'r1'])
    m1 = BSMNode('m1', tl, ['r1', 'r2'])
    m2 = BSMNode('m2', tl, ['r2', 'r3'])
    m3 = BSMNode('m3', tl, ['r3', 'r0'])

    # Create connection between router and BSM
    r0.add_bsm_node(m3.name, r3.name)
    r0.add_bsm_node(m0.name, r1.name)
    r1.add_bsm_node(m0.name, r0.name)
    r1.add_bsm_node(m1.name, r2.name)
    r2.add_bsm_node(m1.name, r1.name)
    r2.add_bsm_node(m2.name, r3.name)
    r3.add_bsm_node(m2.name, r2.name)
    r3.add_bsm_node(m3.name, r0.name)

    # set seeds for random generators
    nodes = [r0, r1, r2, r3, m0, m1, m2, m3]
    for i, node in enumerate(nodes):
        node.set_seed(i)

    for node in [r0, r1, r2, r3]:
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
        cc = ClassicalChannel("cc_%s_%s"%(node1.name, node2.name), tl, 1e3, delay=cc_delay)
        cc.set_ends(node1, node2.name)

    # Create quantum channels linking r0 and r1 to m0
    qc0 = QuantumChannel("qc_r0_m0", tl, qc_atten, qc_dist)
    qc1 = QuantumChannel('qc_r1_m0', tl, qc_atten, qc_dist)
    qc0.set_ends(r0, m0.name)
    qc1.set_ends(r1, m0.name)
    # Create quantum channels linking r1 and r2 to m1
    qc2 = QuantumChannel('qc_r1_m1', tl, qc_atten, qc_dist)
    qc3 = QuantumChannel('qc_r2_m1', tl, qc_atten, qc_dist)
    qc2.set_ends(r1, m1.name)
    qc3.set_ends(r2, m1.name)
    # Create quantum channels linking r2 and r3 to m2
    qc4 = QuantumChannel('qc_r2_m2', tl, qc_atten, qc_dist)
    qc5 = QuantumChannel('qc_r3_m2', tl, qc_atten, qc_dist)
    qc4.set_ends(r2, m2.name)
    qc5.set_ends(r3, m2.name)
    # Create quantum channels linking r3 and r0 to m3
    qc6 = QuantumChannel('qc_r3_m3', tl, qc_atten, qc_dist)
    qc7 = QuantumChannel('qc_r0_m3', tl, qc_atten, qc_dist)
    qc6.set_ends(r3, m3.name)
    qc7.set_ends(r0, m3.name)

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

    nodes = [r0, r1, r2, r3]
    nodes_list = choiceNode(nodes)
    
    # We use the network manager of an end router to make our entanglement request
    # Args:
    # destination node,
    # start time (ps) of entanglement,
    # end time (ps) of entanglement,
    # number of memories to entangle,
    # desired fidelity of entanglement
    nodes_list[0].network_manager.request(f'{nodes_list[2].name}', 1e12, 1e14, 50, 0.9)

    tick = time.time()
    tl.run()
    print("execution time %.2f sec" % (time.time() - tick))

    ## Display metrics for entangled memories

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3)
    fig.set_size_inches(12, 5)

    # Entangled memories on r0
    # Plot number of entangled memories versus time for r0
    plotEntangleMemories(nodes_list[0], "Number of Entangled Memories", 'y', ax1)
    plotEntangleMemories(nodes_list[1], "Simulation Time (s)", 'x', ax2)
    plotEntangleMemories(nodes_list[2], None, None, ax3)

    fig.tight_layout()

    ## Display metrics for memory fidelities
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3)
    fig.set_size_inches(12, 5)

    # display collected metric for memory fidelities on r1
    # in this case, a bar chart of memory fidelity at each index
    displayMemoryFidelity(nodes_list[0], 'Fidelity', 'y', ax1, raw_fidelity)
    displayMemoryFidelity(nodes_list[1], 'Memory Number', 'x', ax2, raw_fidelity)
    displayMemoryFidelity(nodes_list[2], None, None, ax3, raw_fidelity)

    fig.tight_layout()

simulation(sim_time=3000, cc_delay=0.1, qc_atten=3e-5, qc_dist=1, swapping_success_rate=0.05)
plt.show()