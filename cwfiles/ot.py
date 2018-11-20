"""
Emmanuelle Risson : ear
Olivier Roques    : or518
"""

import util
import yao

# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

OBLIVIOUS_TRANSFERS = True

def send_yao_circuit(socket, circuit, g_tables, pbits_out):
    socket.send_wait(circuit)
    socket.send_wait(g_tables)
    socket.send_wait(pbits_out)

def receive_yao_circuit(socket):
    circuit   = socket.receive()
    socket.send(True)
    g_tables  = socket.receive()
    socket.send(True)
    pbits_out = socket.receive()
    socket.send(True)
    return (circuit, g_tables, pbits_out)

if OBLIVIOUS_TRANSFERS: # __________________________________________________

    def get_result(socket, a_inputs, b_keys):
        socket.send(a_inputs)

        nb_bob_inputs = len([w for (w, b) in b_keys if b])
        for _ in range(nb_bob_inputs):
            w = socket.receive()
            util.log('OT Request received')
            pair = (b_keys[w, 0], b_keys[w, 1])
            ot_alice(socket, pair)

        result = socket.receive()
        return result

    # bellare-micali OT with naor and pinkas optimisations, see smart p423
    def ot_alice(socket, msgs):
        """Oblivious transfer, Alice's side.

        Keyword argument:
        socket -- socket for exchanges between A and B
        msgs   -- a pair (msg1, msg2) to offer to Bob
        """
        pass

    def send_result(socket, circuit, g_tables, pbits_out, b_inputs):
        a_inputs      = socket.receive()
        b_inputs_encr = {}

        for w, b_input in b_inputs.items():
            socket.send(w)
            util.log('OT Request sent')
            ot_bob(socket, b_input)
            b_inputs_encr[w] = socket.receive()

        result = yao.evaluate(circuit, g_tables, pbits_out, \
                              a_inputs, b_inputs_encr)
        socket.send(result)

    # bellare-micali OT with naor and pinkas optimisations, see smart p423
    def ot_bob(socket, b):
        """Oblivious transfer, Bob's side.

        Keyword argument:
        socket -- socket for exchanges between A and B
        b      -- Bob's input bit used to select one of Alice's messages
        """
        pass


else: # ____________________________________________________________________

    def get_result(socket, a_inputs, b_keys):
        socket.send(a_inputs)

        nb_bob_inputs = len([w for (w, b) in b_keys if b])
        for _ in range(nb_bob_inputs):
            w = socket.receive()
            pair = (b_keys[w, 0], b_keys[w, 1])
            socket.send(pair)

        result = socket.receive()
        return result

    def send_result(socket, circuit, g_tables, pbits_out, b_inputs):
        a_inputs      = socket.receive()
        b_inputs_encr = {}

        for w, b_input in b_inputs.items():
            socket.send(w)
            pair = socket.receive()
            b_inputs_encr[w] = pair[b_input]

        result = yao.evaluate(circuit, g_tables, pbits_out, \
                              a_inputs, b_inputs_encr)
        socket.send(result)

# __________________________________________________________________________
