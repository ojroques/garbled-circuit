"""
Emmanuelle Risson : ear
Olivier Roques    : or518
"""

import util
import yao

# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

OBLIVIOUS_TRANSFERS = True

if OBLIVIOUS_TRANSFERS: # __________________________________________________
    def send_yao_circuit(socket, circuit, g_tables, pbits_out):
        socket.send(circuit)
        socket.send(g_tables)
        socket.send(pbits_out)

    def get_bob_result(socket, a_inputs, b_keys):
        """
        a_inputs of the form:
            {wire: (key, encrypted_bit), ...}
        b_keys of the form:
            {(wire, 0): (key, 0^pbits[wire],
             (wire, 1): key, 1^pbits[wire]...}
        """
        socket.send(a_inputs)

        for i in range(len(b_keys) // 2):
            w = socket.receive()
            pair = (b_keys[w, 0], b_keys[w, 1])
            ot_alice(socket, pair)

        result = socket.receive()
        return result

    def ot_alice(socket, pair):
        """
            pair = (msg1, msg2)
        """
        pass

    def receive_yao_circuit(socket):
        circuit   = socket.receive()
        g_tables  = socket.receive()
        pbits_out = socket.receive()
        return (circuit, g_tables, pbits_out)

    def send_result(socket, circuit, g_tables, pbits_out, b_inputs):
        """
        b_inputs of the form:
            {wire: clear_bit, ...}
        """
        a_inputs      = socket.receive()
        b_inputs_encr = {}

        for w, b_input in b_inputs.items():
            socket.send(w)
            ot_bot(socket, b_input)
            b_inputs_encr[w] = socket.receive()

        result = yao.evaluate(circuit, g_tables, pbits_out, a_inputs, b_inputs_encr)
        socket.send(result)

    def ot_bob(socket, b_input):
        """
            b_input = 0 or 1
        """
        pass

  # bellare-micali OT with naor and pinkas optimisations, see smart p423

else: # ____________________________________________________________________

  # non oblivious transfers, not even a secure channel is used, for testing

# __________________________________________________________________________
