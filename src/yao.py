import pickle
import random
from cryptography.fernet import Fernet


def encrypt(key, data):
    """Encrypt a message.

    Args:
        key: The encryption key.
        data: The message to encrypt.

    Returns:
        The encrypted message as a byte stream.
    """
    f = Fernet(key)
    return f.encrypt(data)


def decrypt(key, data):
    """Decrypt a message.

    Args:
        key: The decryption key.
        data: The message to decrypt.

    Returns:
        The decrypted message as a byte stream.
    """
    f = Fernet(key)
    return f.decrypt(data)


def evaluate(circuit, g_tables, pbits_out, a_inputs, b_inputs):
    """Evaluate yao circuit with given inputs.

    Args:
        circuit: A dict containing circuit spec.
        g_tables: The yao circuit garbled tables.
        pbits_out: The pbits of outputs.
        a_inputs: A dict mapping Alice's wires to (key, encr_bit) inputs.
        b_inputs: A dict mapping Bob's wires to (key, encr_bit) inputs.

    Returns:
        A dict mapping output wires with their result bit.
    """
    gates = circuit["gates"]  # dict containing circuit gates
    wire_outputs = circuit["out"]  # list of output wires
    wire_inputs = {}  # dict containing Alice and Bob inputs
    evaluation = {}  # dict containing result of evaluation

    wire_inputs.update(a_inputs)
    wire_inputs.update(b_inputs)

    # Iterate over all gates
    for gate in sorted(gates, key=lambda g: g["id"]):
        gate_id, gate_in, msg = gate["id"], gate["in"], None
        # Special case if it's a NOT gate
        if (len(gate_in) < 2) and (gate_in[0] in wire_inputs):
            # Fetch input key associated with the gate's input wire
            key_in, encr_bit_in = wire_inputs[gate_in[0]]
            # Fetch the encrypted message in the gate's garbled table
            encr_msg = g_tables[gate_id][(encr_bit_in, )]
            # Decrypt message
            msg = decrypt(key_in, encr_msg)
        # Else the gate has two input wires (same model)
        elif (gate_in[0] in wire_inputs) and (gate_in[1] in wire_inputs):
            key_a, encr_bit_a = wire_inputs[gate_in[0]]
            key_b, encr_bit_b = wire_inputs[gate_in[1]]
            encr_msg = g_tables[gate_id][(encr_bit_a, encr_bit_b)]
            msg = decrypt(key_b, decrypt(key_a, encr_msg))
        if msg:
            wire_inputs[gate_id] = pickle.loads(msg)

    # After all gates have been evaluated, we populate the dict of results
    for out in wire_outputs:
        evaluation[out] = wire_inputs[out][1] ^ pbits_out[out]

    return evaluation


class GarbledGate:
    """A representation of a garbled gate.

    Args:
        gate: A dict containing gate spec.
        keys: A dict mapping each wire to a pair of keys.
        pbits: A dict mapping each wire to its p-bit.
    """
    def __init__(self, gate, keys, pbits):
        self.keys = keys  # dict of yao circuit keys
        self.pbits = pbits  # dict of p-bits
        self.input = gate["in"]  # list of inputs'ID
        self.output = gate["id"]  # ID of output
        self.gate_type = gate["type"]  # Gate type: OR, AND, ...
        self.garbled_table = {}  # The garbled table of the gate
        # A clear representation of the garbled table for debugging purposes
        self.clear_garbled_table = {}

        # Create the garbled table according to the gate type
        switch = {
            "OR": lambda b1, b2: b1 or b2,
            "AND": lambda b1, b2: b1 and b2,
            "XOR": lambda b1, b2: b1 ^ b2,
            "NOR": lambda b1, b2: not (b1 or b2),
            "NAND": lambda b1, b2: not (b1 and b2),
            "XNOR": lambda b1, b2: not (b1 ^ b2)
        }

        # NOT gate is a special case since it has only one input
        if (self.gate_type == "NOT"):
            self._gen_garbled_table_not()
        else:
            operator = switch[self.gate_type]
            self._gen_garbled_table(operator)

    def _gen_garbled_table_not(self):
        """Create the garbled table of a NOT gate."""
        inp, out = self.input[0], self.output

        # For each entry in the garbled table
        for encr_bit_in in (0, 1):
            # Retrieve original bit
            bit_in = encr_bit_in ^ self.pbits[inp]
            # Compute output bit according to the gate type
            bit_out = int(not (bit_in))
            # Compute encrypted bit with the p-bit table
            encr_bit_out = bit_out ^ self.pbits[out]
            # Retrieve related keys
            key_in = self.keys[inp][bit_in]
            key_out = self.keys[out][bit_out]

            # Serialize the output key along with the encrypted bit
            msg = pickle.dumps((key_out, encr_bit_out))
            # Encrypt message and add it to the garbled table
            self.garbled_table[(encr_bit_in, )] = encrypt(key_in, msg)
            # Add to the clear table indexes of each keys
            self.clear_garbled_table[(encr_bit_in, )] = [(inp, bit_in),
                                                         (out, bit_out),
                                                         encr_bit_out]

    def _gen_garbled_table(self, operator):
        """Create the garbled table of a 2-input gate.

        Args:
            operator: The logical function of to the 2-input gate type.
        """
        in_a, in_b, out = self.input[0], self.input[1], self.output

        # Same model as for the NOT gate except for 2 inputs instead of 1
        for encr_bit_a in (0, 1):
            for encr_bit_b in (0, 1):
                bit_a = encr_bit_a ^ self.pbits[in_a]
                bit_b = encr_bit_b ^ self.pbits[in_b]
                bit_out = int(operator(bit_a, bit_b))
                encr_bit_out = bit_out ^ self.pbits[out]
                key_a = self.keys[in_a][bit_a]
                key_b = self.keys[in_b][bit_b]
                key_out = self.keys[out][bit_out]

                msg = pickle.dumps((key_out, encr_bit_out))
                self.garbled_table[(encr_bit_a, encr_bit_b)] = encrypt(
                    key_a, encrypt(key_b, msg))
                self.clear_garbled_table[(encr_bit_a, encr_bit_b)] = [
                    (in_a, bit_a), (in_b, bit_b), (out, bit_out), encr_bit_out
                ]

    def print_garbled_table(self):
        """Print a clear representation of the garbled table."""
        print(f"GATE: {self.output}, TYPE: {self.gate_type}")
        for k, v in self.clear_garbled_table.items():
            # If it's a 2-input gate
            if len(k) > 1:
                key_a, key_b, key_out = v[0], v[1], v[2]
                encr_bit_out = v[3]
                print(f"[{k[0]}, {k[1]}]: "
                      f"[{key_a[0]}, {key_a[1]}][{key_b[0]}, {key_b[1]}]"
                      f"([{key_out[0]}, {key_out[1]}], {encr_bit_out})")
            # Else it's a NOT gate
            else:
                key_in, key_out = v[0], v[1]
                encr_bit_out = v[2]
                print(f"[{k[0]}]: "
                      f"[{key_in[0]}, {key_in[1]}]"
                      f"([{key_out[0]}, {key_out[1]}], {encr_bit_out})")

    def get_garbled_table(self):
        """Return the garbled table of the gate."""
        return self.garbled_table


class GarbledCircuit:
    """A representation of a garbled circuit.

    Args:
        circuit: A dict containing circuit spec.
        pbits: Optional; a dict of p-bits for the given circuit.
    """
    def __init__(self, circuit, pbits={}):
        self.circuit = circuit
        self.gates = circuit["gates"]  # list of gates
        self.wires = set()  # list of circuit wires

        self.pbits = {}  # dict of p-bits
        self.keys = {}  # dict of keys
        self.garbled_tables = {}  # dict of garbled tables

        # Retrieve all wire IDs from the circuit
        for gate in self.gates:
            self.wires.add(gate["id"])
            self.wires.update(set(gate["in"]))
        self.wires = list(self.wires)

        self._gen_pbits(pbits)
        self._gen_keys()
        self._gen_garbled_tables()

    def _gen_pbits(self, pbits):
        """Create a dict mapping each wire to a random p-bit."""
        if pbits:
            self.pbits = pbits
        else:
            self.pbits = {wire: random.randint(0, 1) for wire in self.wires}

    def _gen_keys(self):
        """Create pair of keys for each wire."""
        for wire in self.wires:
            self.keys[wire] = (Fernet.generate_key(), Fernet.generate_key())

    def _gen_garbled_tables(self):
        """Create the garbled table of each gate."""
        for gate in self.gates:
            garbled_gate = GarbledGate(gate, self.keys, self.pbits)
            self.garbled_tables[gate["id"]] = garbled_gate.get_garbled_table()

    def print_garbled_tables(self):
        """Print p-bits and a clear representation of all garbled tables."""
        print(f"======== {self.circuit['id']} ========")
        print(f"P-BITS: {self.pbits}")
        for gate in self.gates:
            garbled_table = GarbledGate(gate, self.keys, self.pbits)
            garbled_table.print_garbled_table()
        print()

    def get_pbits(self):
        """Return dict mapping each wire to its p-bit."""
        return self.pbits

    def get_garbled_tables(self):
        """Return dict mapping each gate to its garbled table."""
        return self.garbled_tables

    def get_keys(self):
        """Return dict mapping each wire to its pair of keys."""
        return self.keys
