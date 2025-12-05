# ============================
#   SIMULACIÓN CPU BÁSICA
# ============================

class Memory:
	def __init__(self, size=256):
		self.data = [0] * size

	def read(self, addr):
		if not (0 <= addr < len(self.data)):
			raise IndexError(f"Memory.read: dirección fuera de rango: {addr}")
		return self.data[addr]

	def write(self, addr, value):
		if not (0 <= addr < len(self.data)):
			raise IndexError(f"Memory.write: dirección fuera de rango: {addr}")
		self.data[addr] = value


class ALU:
	def execute(self, op, a, b):
		if op == "ADD": return a + b
		if op == "SUB": return a - b
		# soporte simple para operaciones adicionales
		if op == "AND": return a & b
		if op == "OR": return a | b
		return 0


class CPU:
	def __init__(self, memory, verbose: bool = True):
		self.mem = memory
		self.registers = {"PC": 0, "MAR": 0, "MDR": 0, "IR": 0,
						  "R0": 0, "R1": 0, "R2": 0, "R3": 0}
		self.alu = ALU()
		self.running = True
		self.verbose = verbose

	# -------- FETCH --------
	def fetch(self):
		self.registers["MAR"] = self.registers["PC"]
		self.registers["MDR"] = self.mem.read(self.registers["MAR"])
		self.registers["IR"] = self.registers["MDR"]
		self.registers["PC"] += 1

	# -------- DECODE & EXECUTE --------
	def execute(self):
		ir = self.registers["IR"]
		# validación rápida del formato de instrucción
		if not isinstance(ir, tuple) or len(ir) == 0:
			if self.verbose:
				print(f"Instrucción inválida o dato en PC-1: {ir}, ignorando.")
			return

		op = ir[0]

		if op == "LOAD":
			reg, addr = ir[1], ir[2]
			self.registers["MAR"] = addr
			self.registers["MDR"] = self.mem.read(addr)
			self.registers[reg] = self.registers["MDR"]

		elif op == "STORE":
			reg, addr = ir[1], ir[2]
			self.mem.write(addr, self.registers[reg])

		elif op == "ADD":
			regA, regB = ir[1], ir[2]
			result = self.alu.execute("ADD", self.registers[regA], self.registers[regB])
			self.registers[regA] = result

		elif op == "ADDI":  # soporte inmediato: ("ADDI","R1",5)
			reg, imm = ir[1], ir[2]
			result = self.alu.execute("ADD", self.registers[reg], imm)
			self.registers[reg] = result

		elif op == "HALT":
			self.running = False

		else:
			# instrucción desconocida -> detener y reportar
			if self.verbose:
				print(f"INSTRUCCIÓN DESCONOCIDA: {op} -> deteniendo CPU.")
			self.running = False

	# -------- CICLO COMPLETO --------
	def step(self):
		self.fetch()
		self.execute()
		if self.verbose:
			self.print_state()

	def print_state(self):
		print("----- CICLO -----")
		# imprimir PC/IR primero y luego registros ordenados
		print(f"PC: {self.registers['PC']}  IR: {self.registers['IR']}")
		for r in sorted(k for k in self.registers.keys() if k not in ("PC","IR")):
			print(f"{r}: {self.registers[r]}")
		print("-----------------\n")


def load_program(memory, program, start=0):
	"""Carga lista de instrucciones/datos en memoria desde 'start'."""
	for i, instr in enumerate(program):
		memory.write(start + i, instr)

# ============================================
#   PROGRAMA DE PRUEBA: R1 = A + B (actualizado)
# ============================================

memory = Memory()

# Datos en memoria
memory.write(100, 5)   # A
memory.write(101, 7)   # B

# Programa en memoria
program = [
	("LOAD", "R1", 100),   # R1 ← A
	("LOAD", "R2", 101),   # R2 ← B
	("ADD",  "R1", "R2"),  # R1 = R1 + R2
	("STORE", "R1", 120),  # MEM[120] = R1
	("HALT",)              # Detener CPU
]

# Cargar programa en memoria (usando utilidad)
load_program(memory, program, start=0)

# Ejecutar CPU (verbose True para traza)
cpu = CPU(memory, verbose=True)

while cpu.running:
	cpu.step()

print("Resultado final en memoria[120]:", memory.read(120))