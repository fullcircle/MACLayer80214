import simpy

# Parameters
NUM_NODES = 2
SIM_TIME = 10000  # simulation time in seconds
PACKET_SIZE = 128  # packet size in bytes
TX_RATE = 250000  # transmission rate in bits per second
ACK_SIZE = 32  # ACK packet size in bytes
BACKOFF_MIN = 20  # minimum backoff time in symbols
BACKOFF_MAX = 1023  # maximum backoff time in symbols
CSMA_CA_ATTEMPTS = 3  # maximum number of CSMA/CA attempts

class Node:
    def __init__(self, env, node_id):
        self.env = env
        self.id = node_id
        self.channel_busy = False
        self.packet_queue = []
        self.packets_sent = 0
        self.packets_received = 0
        self.collisions = 0
        self.waiting_for_ack = False

    def transmit_packet(self, dest_node):
        if self.channel_busy:
            # channel is busy, backoff
            backoff_time = self.env.random.randint(BACKOFF_MIN, BACKOFF_MAX)
            yield self.env.timeout(backoff_time * 20e-6)  # convert symbols to seconds
            yield from self.transmit_packet(dest_node)
        else:
            # channel is idle, send packet
            self.channel_busy = True
            packet_duration = (PACKET_SIZE + ACK_SIZE) * 8 / TX_RATE  # convert bytes to bits
            yield self.env.timeout(packet_duration)
            if dest_node.channel_busy:
                # destination node is also transmitting, collision occurs
                self.collisions += 1
                dest_node.collisions += 1
            else:
                # destination node receives packet
                dest_node.receive_packet(self.id)
                self.packets_sent += 1
                self.waiting_for_ack = True
                yield self.env.timeout(packet_duration)
                if self.waiting_for_ack:
                    # ACK not received, packet was lost
                    self.waiting_for_ack = False
                    dest_node.packets_received -= 1
                else:
                    # ACK received, packet was successfully transmitted
                    self.waiting_for_ack = False

            self.channel_busy = False

    def receive_packet(self, src_node_id):
        self.packets_received += 1
        ack_packet_duration = ACK_SIZE * 8 / TX_RATE  # convert bytes to bits
        yield self.env.timeout(ack_packet_duration)
        if self.channel_busy:
            # sender is also transmitting, collision occurs
            self.collisions += 1
        else:
            # sender receives ACK
            sender = nodes[src_node_id]
            sender.packets_received += 1
            sender.waiting_for_ack = False
            self.channel_busy = True
            yield self.env.timeout(ack_packet_duration)
            self.channel_busy = False

def csma_ca(env, node, dest_node):
    for i in range(CSMA_CA_ATTEMPTS):
        yield from node.transmit_packet(dest_node)
        if not node.waiting_for_ack:
            # packet was successfully transmitted
            break

# Initialize simulation environment
env = simpy.Environment()

# Create nodes
nodes = []
for i in range(NUM_NODES):
    node = Node(env, i)
    nodes.append(node)

# Start sending packets
env.process(csma_ca(env, nodes[0], nodes[1]))

# Run simulation
env.run(until=SIM_TIME)

# Print statistics
print("Node 0 sent", nodes[0].packets_sent, "packets")
print("Node 0 received", nodes[0].packets_received, "packets")
