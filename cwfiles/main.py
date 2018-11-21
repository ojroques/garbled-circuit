"""
Emmanuelle Risson : ear3218
Olivier Roques    : or518

yao garbled circuit evaluation v1. simple version based on smart
naranker dulay, dept of computing, imperial college, october 2018
"""

import json         # load
import sys          # argv

import util         # ClientSocket, log, ServerSocket
import ot           # alice, bob
import yao          # Yao circuit

# Alice is the circuit generator (client) __________________________________

def alice(filename):
    """ALICE: create Yao circuit, send it and print circuit evaluation.

    Keyword argument:
    filename -- name of the json representation of the circuit
    """
    socket = util.ClientSocket()
    util.log('CLIENT STARTED')

    with open(filename) as json_file:
        json_circuits = json.load(json_file)

    for json_circuit in json_circuits['circuits']:
        # 1: CREATE YAO CIRCUIT
        g_circuit = yao.GarbledCircuit(json_circuit)
        g_tables  = g_circuit.get_garbled_tables()
        keys      = g_circuit.get_keys()
        pbits     = g_circuit.get_pbits()
        pbits_out = {w: pbits[w] for w in json_circuit["out"]}

        # 2: SEND YAO CIRCUIT TO BOB
        util.log('Sending yao circuit...')
        ot.send_yao_circuit(socket, json_circuit, g_tables, pbits_out)

        # 3: PRINT YAO CIRCUIT EVALUATION FOR ALL INPUTS
        util.log('Waiting for circuit evaluation...')
        print_evaluation(socket, json_circuit, keys, pbits)
        util.log('Done.\n')
    print()


def print_evaluation(socket, circuit, keys, pbits):
    """Print circuit evaluation for all Bob and Alice inputs.

    Keyword arguments:
    socket  -- socket for exchanges between A and B
    circuit -- dict containing circuit spec
    keys    -- dict mapping each wire to a pair of key
    pbits   -- dict mapping each wire with a p-bit
    """
    outputs   = circuit["out"]           # ID of outputs
    a_wires   = circuit.get("alice", []) # List of Alice's wires
    # dict mapping Alice's wires to (key, encr_bit) inputs
    a_inputs  = {}
    b_wires   = circuit.get("bob", [])   # List of Bob's wires
    # dict mapping each bob's wire to a pair (key, encr_bit)
    b_keys    = {w: ((key0, 0 ^ pbits[w]), (key1, 1 ^ pbits[w]))
                 for w, (key0, key1) in keys.items() if w in b_wires}

    print("\n======= {0} =======".format(circuit["name"]))

    len_a_wires, len_b_wires = len(a_wires), len(b_wires)
    N                        = len_a_wires + len_b_wires

    # Generate all possible inputs for both Alice and Bob
    for bits in [format(n, 'b').zfill(N) for n in range(2**N)]:
        bits_a = [int(b) for b in bits[:len_a_wires]]  # Alice's inputs

        # Map Alice's wires to (key, encr_bit)
        for i in range(len_a_wires):
            a_inputs[a_wires[i]] = \
                (keys[a_wires[i]][bits_a[i]], pbits[a_wires[i]] ^ bits_a[i])

        # Send Alice's encrypted inputs and keys to Bob and wait for results
        result = ot.get_result(socket, a_inputs, b_keys)

        # Last term is a little hack to respect the given output format
        str_bits_a = ' '.join(bits[:len_a_wires]) + ' '*bool(len_a_wires)
        str_bits_b = ' '.join(bits[len_a_wires:]) + ' '*bool(len_b_wires)
        str_result = ' '.join([str(result[w]) for w in outputs]) + ' '
        # Print one evaluation of the circuit
        line       = "  Alice{0} = {1} Bob{2} = {3}  Outputs{4} = {5}".\
            format(a_wires, str_bits_a, b_wires, str_bits_b, \
                   outputs, str_result)
        print(line)


# Bob is the circuit evaluator (server) ____________________________________

def bob():
    """BOB: Receive yao circuit and evaluate the circuit for all inputs."""
    socket = util.ServerSocket()
    util.log(f'SERVER STARTED')

    while True:
        # 1: RECEIVE YAO CIRCUIT
        util.log('Waiting for yao circuit...')
        circuit, g_tables, pbits_out = ot.receive_yao_circuit(socket)
        util.log('Sending circuit evaluation...')
        # 2: EVALUATE CIRCUIT AND SEND IT TO ALICE
        send_evaluation(socket, circuit, g_tables, pbits_out)
        util.log('Done.\n')


def send_evaluation(socket, circuit, g_tables, pbits_out):
    """Evaluate yao circuit and send the result for all Bob and Alice's inputs.

    Keyword arguments:
    socket    -- socket for exchanges between A and B
    circuit   -- dict containing circuit spec
    g_tables  -- garbled tables of yao circuit
    pbits_out -- pbits of outputs
    """
    outputs   = circuit["out"]           # ID of outputs
    a_wires   = circuit.get("alice", []) # List of Alice's wires
    b_wires   = circuit.get("bob", [])   # List of Bob's wires

    len_a_wires, len_b_wires = len(a_wires), len(b_wires)
    N                        = len_a_wires + len_b_wires

    # Generate all possible inputs for both Alice and Bob
    for bits in [format(n, 'b').zfill(N) for n in range(2**N)]:
        bits_b = [int(b) for b in bits[N - len_b_wires:]]  # Bob's inputs
        # Create dict mapping each bob's wire to bob's input
        b_inputs_clear = {b_wires[i]: bits_b[i] for i in range(len_b_wires)}
        # Evaluate and send result to Alice
        ot.send_result(socket, circuit, g_tables, pbits_out, b_inputs_clear)


# local test of circuit generation and evaluation, no transfers_____________

def local_test(filename):
    """FOR LOCAL TESTS: Print circuit evaluation or garbled tables.

    Keyword argument:
    filename -- name of the json representation of the circuit
    """
    # 2 MODES:
    # 0 -> print yao circuit evaluation for all inputs
    # 1 -> print garbled tables of the yao circuit in a readable format
    PRINT_MODE = 0

    with open(filename) as json_file:
        json_circuits = json.load(json_file)

    for json_circuit in json_circuits['circuits']:
        # CREATE YAO CIRCUIT
        g_circuit = yao.GarbledCircuit(json_circuit)
        g_tables  = g_circuit.get_garbled_tables()
        keys      = g_circuit.get_keys()
        pbits     = g_circuit.get_pbits()

        # PRINT RESULTS ACCORDING TO SELECTED MODE
        if PRINT_MODE: g_circuit.print_garbled_tables()
        else: print_evaluation_local(json_circuit, g_tables, keys, pbits)
    print()


def print_evaluation_local(circuit, g_tables, keys, pbits):
    """Print circuit evaluation for all Bob and Alice inputs.

    Keyword arguments:
    circuit  -- dict containing circuit spec
    g_tables -- garbled tables of the yao circuit
    keys    -- dict mapping each wire to a pair of key
    pbits    -- dict mapping each wire with a p-bit
    """
    outputs   = circuit["out"]           # ID of outputs
    a_wires   = circuit.get("alice", []) # List of Alice's wires
    b_wires   = circuit.get("bob", [])   # List of Bob's wires
    # dict mapping Alice's wires to (key, encr_bit) inputs
    a_inputs  = {}
    # dict mapping Bob's wires to (key, encr_bit) inputs
    b_inputs  = {}
    # pbits of outputs
    pbits_out = {w: pbits[w] for w in outputs}

    print("\n======= {0} =======".format(circuit["name"]))

    len_a_wires, len_b_wires = len(a_wires), len(b_wires)
    N                        = len_a_wires + len_b_wires

    # Generate all possible inputs for both Alice and Bob
    for bits in [format(n, 'b').zfill(N) for n in range(2**N)]:
        bits_a = [int(b) for b in bits[:len_a_wires]]      # Alice's inputs
        bits_b = [int(b) for b in bits[N - len_b_wires:]]  # Bob's inputs

        # Map Alice's wires to (key, encr_bit)
        for i in range(len_a_wires):
            a_inputs[a_wires[i]] = \
                (keys[a_wires[i]][bits_a[i]], pbits[a_wires[i]] ^ bits_a[i])
        # Map Bob's wires to (key, encr_bit)
        for i in range(len_b_wires):
            b_inputs[b_wires[i]] = \
                (keys[b_wires[i]][bits_b[i]], pbits[b_wires[i]] ^ bits_b[i])

        # Send Alice's encrypted inputs and keys to Bob and wait for results
        result = yao.evaluate(circuit, g_tables, pbits_out, a_inputs, b_inputs)

        # Last term is a little hack to respect the given output format
        str_bits_a = ' '.join(bits[:len_a_wires]) + ' '*bool(len_a_wires)
        str_bits_b = ' '.join(bits[len_a_wires:]) + ' '*bool(len_b_wires)
        str_result = ' '.join([str(result[w]) for w in outputs]) + ' '
        # Print one evaluation of the circuit
        line       = "  Alice{0} = {1} Bob{2} = {3}  Outputs{4} = {5}".\
            format(a_wires, str_bits_a, b_wires, str_bits_b, \
                   outputs, str_result)
        print(line)

# main _____________________________________________________________________

def main():
    """MAIN: Redirect execution."""
    behaviour = sys.argv[1]
    if   behaviour == 'alice': alice(filename=sys.argv[2])
    elif behaviour == 'bob':   bob()
    elif behaviour == 'local': local_test(filename=sys.argv[2])

if __name__ == '__main__':
    main()

# __________________________________________________________________________
