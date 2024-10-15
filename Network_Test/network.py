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

def test(sim_time: int, classical_channel_delay: int,
 quantum_channel_attenuation: float, quantum_channel_distance: int):
    """
    sim_time: duration of simulation time (ms)
    classical_channel_delay: delay on classical channels (ms)
    quantum_channel_attenuation: attenuation on quantum channels (dB/m) 
    quantum_channel_distance: distance of quantum channels (km)
    """

    pass