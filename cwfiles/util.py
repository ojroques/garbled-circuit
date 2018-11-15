
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

import hashlib	# shake_256
import operator	# xor
import random	# randint
import secrets	# randbits
import sys	# argv, exit

import sympy	# nextprime, primefactors
import zmq	# Context


# logging __________________________________________________________________

VERBOSE = 0 				# 0=quiet, 1+=increasing verbosity

def log(message, verbose=1):
  if VERBOSE >= verbose: print(message)

def exit(message):			# for exiting after errors
  print(message)
  sys.exit(1)


# primes, bits and bytes ___________________________________________________

PRIME_BITS = 64			# order of magnitude of prime in base 2

"""
generate random prime approx 2 ** PRIME_BITS in size. 64 bits is
big enough for this course. generation of primes and primefactors will
start to slow past this. a fast multi-precision library like gmpy2 will
be more efficient but will slow also -- large primes problems tend to be
computationally hard
"""

def next_prime(num):			# next prime after num (skip 2)
  return 3 if num < 3 else sympy.nextprime(num)

def gen_prime(num_bits):		# random 'bits-sized' prime
  r = secrets.randbits(num_bits)
  log(f'  nextprime {r} ({r.bit_length()} bits)', verbose=3)
  return next_prime(r)
  # should really ensure that prime-1 has a large prime factor, 
  # see free handbook of applied cryptography p164 for a discussion

def xor_bytes(seq1, seq2):		# xor two byte sequences
  return bytes(map(operator.xor, seq1, seq2))

def ot_hash(pub_key, msg_length):	# hash function for OT keys
  # use shake256 to ensure hash length equals msg length
  key_length = (pub_key.bit_length() + 7) // 8	# key length in bytes
  bytes = pub_key.to_bytes(key_length, byteorder="big")
  return hashlib.shake_256(bytes).digest(msg_length)

def bits(num, width):			# convert number into a list of bits
  # example: bits(num=6, width=5) will return [0, 0, 1, 1, 0]
  # use [int(k) for k in format(num, 'b').zfill(width)] for older Pythons
  return [int(k) for k in f'{num:0{width}b}']

class PrimeGroup:
  # cyclic abelian group of prime order i.e. order totient(p)=p-1

  def __init__(self, prime=None):	# assert prime > 2
    self.prime   = prime or gen_prime(num_bits=PRIME_BITS)
    self.primeM1 = self.prime - 1
    self.primeM2 = self.prime - 2
    self.generator = self.find_generator()
    log(f'  Prime Group {self.prime} Generator {self.generator}', verbose=3)

  def mul(self, num1, num2):		# multiplication 
    return (num1 * num2) % self.prime

  def pow(self, base, exponent):	# exponentiation
    return pow(base, exponent, self.prime)

  def gen_pow(self, exponent):		# generator exponentiation
    return pow(self.generator, exponent, self.prime)

  def inv(self, num): 			# multiplicative inverse 
    return pow(num, self.primeM2, self.prime)

  def rand_int(self):  			# random int in [1, prime-1] 
    return random.randint(1, self.primeM1)
    # not 0 since gcd(int, prime)==1 for multiplicative group elements

  def find_generator(self):		# find random generator for group
    # see free handbook of applied cryptography p163 for a description
    factors = sympy.primefactors(self.primeM1)
    while True:				# there are numerous generators 
      candidate = self.rand_int()	# so we'll find in a few tries
      log(f'  candidate {candidate}', verbose=3)
      for factor in factors:
        if 1 == self.pow(candidate, self.primeM1 // factor): break
      else:
        return candidate

if sys.argv[1] == 'alice':		# one group is sufficient
  prime_group = PrimeGroup()		# singleton, simpler than metaclass
else:
  prime_group = None			# bob receives group from alice


# sockets __________________________________________________________________

LOCAL_PORT  = 4080			# change if port clashes
SERVER_PORT = 4080			# change if using port redirection 
SERVER_HOST = 'localhost'		# change if server on different host
# SERVER_HOST = '0.tcp.au.ngrok.io' 	# relay through amazonws in Sydney

class Socket:
  def send(self, msg):	self.socket.send_pyobj(msg)
  def receive(self): 	return self.socket.recv_pyobj()

  def send_wait(self, msg):
    self.send(msg)
    return self.receive()

class ServerSocket(Socket):
  def __init__(self, endpoint=f'tcp://*:{LOCAL_PORT}'):
    self.socket = zmq.Context().socket(zmq.REP)
    self.socket.bind(endpoint)

class ClientSocket(Socket):  # change local host for
  def __init__(self, endpoint=f'tcp://{SERVER_HOST}:{SERVER_PORT}'):
    self.socket = zmq.Context().socket(zmq.REQ)
    self.socket.connect(endpoint)

# __________________________________________________________________________
