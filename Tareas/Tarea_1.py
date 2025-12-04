"""
conversions_tools.py

Programa educativo para:
 - conversion entre bases (binario, octal, decimal, hexadecimal) con pasos.
 - conversion a BCD, Gray y representacion alfanumerica (ASCII).
 - ejemplos de deteccion/correccion de errores: paridad simple y Hamming(7,4).

Ejecutar: python conversions_tools.py
"""

from typing import Tuple, List

HEX_DIGITS = "0123456789ABCDEF"

# ------------------------
# UTIL: limpieza / normalizacion
# ------------------------
def normalize_input(s: str) -> str:
    return s.strip().upper()

# ------------------------
# CONVERSIONES DECIMALES <-> BASES (con pasos)
# ------------------------
def decimal_to_base_steps(n: int, base: int) -> Tuple[str, List[str]]:
    """Convierte entero decimal n a base y devuelve (resultado_str, pasos)."""
    if n == 0:
        return "0", ["El número es 0 -> resultado '0'"]
    steps = []
    res_digits = []
    numero = n
    while numero > 0:
        q, r = divmod(numero, base)
        digit = HEX_DIGITS[r]
        steps.append(f"{numero} ÷ {base} = {q} restante {r} -> dígito '{digit}'")
        res_digits.append(digit)
        numero = q
    result = ''.join(reversed(res_digits))
    steps.append(f"Lectura de restos de abajo hacia arriba -> {result}")
    return result, steps

def base_to_decimal_steps(s: str, base: int) -> Tuple[int, List[str]]:
    """Convierte representación en base a decimal, mostrando pasos."""
    s = normalize_input(s)
    steps = []
    total = 0
    power = len(s) - 1
    for ch in s:
        val = HEX_DIGITS.index(ch)
        steps.append(f"Posición 10^{power}: {ch} -> {val} * ({base}^{power}) = {val * (base ** power)}")
        total += val * (base ** power)
        power -= 1
    steps.append(f"Suma total = {total}")
    return total, steps

# Frontend simple para convertir entre cualquier par de bases
def convert_between_bases(value: str, from_base: int, to_base: int) -> Tuple[str, List[str]]:
    """Convierte value (en from_base) a to_base devolviendo pasos combinados."""
    # primero a decimal
    dec, steps1 = base_to_decimal_steps(value, from_base)
    result, steps2 = decimal_to_base_steps(dec, to_base)
    steps = [f"--- Convertir {value} (base {from_base}) a decimal ---"] + steps1 + \
            [f"--- Convertir {dec} decimal a base {to_base} ---"] + steps2
    return result, steps

# ------------------------
# BCD (Binary-Coded Decimal)
# ------------------------
def decimal_to_bcd_steps(n: int) -> Tuple[str, List[str]]:
    """Convierte cada cifra decimal a BCD (4 bits) y detalla pasos."""
    s = str(n)
    steps = []
    bcd_parts = []
    for ch in s:
        d = int(ch)
        bin4 = format(d, '04b')
        steps.append(f"Cifra {ch} -> BCD 4 bits: {bin4}")
        bcd_parts.append(bin4)
    result = ' '.join(bcd_parts)
    steps.append(f"BCD final (grupos de 4 bits por cifra): {result}")
    return result, steps

# ------------------------
# GRAY code
# ------------------------
def binary_to_gray_steps(bin_str: str) -> Tuple[str, List[str]]:
    """Convierte binario a Gray mostrando pasos bit a bit."""
    bs = normalize_input(bin_str)
    steps = []
    # asegurar solo 0/1
    if any(c not in '01' for c in bs):
        raise ValueError("binary_to_gray_steps: entrada debe contener solo 0 y 1")
    # formula: G = B xor (B>>1)
    b_int = int(bs, 2)
    g_int = b_int ^ (b_int >> 1)
    g_str = format(g_int, '0{}b'.format(len(bs)))
    for i in range(len(bs)):
        b = int(bs[i])
        b_prev = int(bs[i-1]) if i > 0 else 0
        g = b ^ b_prev
        steps.append(f"Bit {i}: B[i]={b} XOR B[i-1]={b_prev} -> G[i]={g}")
    steps.append(f"Resultado Gray: {g_str}")
    return g_str, steps

def gray_to_binary_steps(gray_str: str) -> Tuple[str, List[str]]:
    """Convierte Gray a binario mostrando pasos."""
    gs = normalize_input(gray_str)
    if any(c not in '01' for c in gs):
        raise ValueError("gray_to_binary_steps: entrada debe contener solo 0 y 1")
    steps = []
    b = []
    for i, ch in enumerate(gs):
        g = int(ch)
        if i == 0:
            b.append(g)
            steps.append(f"B[0] = G[0] = {g}")
        else:
            bi = b[i-1] ^ g
            b.append(bi)
            steps.append(f"B[{i}] = B[{i-1}] xor G[{i}] = {b[i-1]} xor {g} -> {bi}")
    b_str = ''.join(str(x) for x in b)
    steps.append(f"Binario resultante: {b_str}")
    return b_str, steps

# ------------------------
# Representación alfanumérica (ASCII)
# ------------------------
def text_to_ascii_steps(text: str) -> Tuple[List[Tuple[str,str,str]], List[str]]:
    """Devuelve por cada caracter su (char, ASCII decimal, binario8) y pasos."""
    steps = []
    table = []
    for ch in text:
        code = ord(ch)
        b8 = format(code, '08b')
        h = format(code, '02X')
        steps.append(f"'{ch}' -> ASCII dec: {code}, bin8: {b8}, hex: {h}")
        table.append((ch, str(code), b8))
    return table, steps

# ------------------------
# Paridad simple
# ------------------------
def add_parity_bit(data_bits: str, parity: str = 'even') -> Tuple[str, str]:
    """Agrega bit de paridad ('even' o 'odd') al final y devuelve (con_paridad, explicación)."""
    if any(c not in '01' for c in data_bits):
        raise ValueError("add_parity_bit: data_bits must be '0'/'1' string")
    ones = data_bits.count('1')
    if parity == 'even':
        bit = '0' if ones % 2 == 0 else '1'
    else:
        bit = '1' if ones % 2 == 0 else '0'
    explanation = f"ones={ones} -> parity='{parity}' -> parity bit={bit}"
    return data_bits + bit, explanation

def check_parity_bit(bits_with_parity: str, parity: str = 'even') -> Tuple[bool, str]:
    if any(c not in '01' for c in bits_with_parity):
        raise ValueError("check_parity_bit: bits must be 0/1 string")
    ones = bits_with_parity.count('1')
    ok = (ones % 2 == 0) if parity == 'even' else (ones % 2 == 1)
    return ok, f"ones={ones} -> parity '{parity}' -> OK={ok}"

# ------------------------
# Hamming (7,4) - codificacion y correccion simple
# ------------------------
def hamming74_encode(data4: str) -> Tuple[str, List[str]]:
    """Codifica 4 bits de datos en Hamming(7,4). data4 debe ser string de 4 bits 'd3d2d1d0'."""
    if len(data4) != 4 or any(c not in '01' for c in data4):
        raise ValueError("hamming74_encode: data4 debe ser 4 bits")
    d = [int(b) for b in data4]  # d0..d3 (usaremos index 0..3)
    # Ubicación: bits [p1, p2, d1, p3, d2, d3, d4] si usamos 1-indexed positions:
    # Vamos a construir en orden positions 1..7 (index 0..6)
    bits = [0]*7
    # colocar datos en posiciones 3,5,6,7 (1-indexed)
    bits[2] = d[0]  # pos3
    bits[4] = d[1]  # pos5
    bits[5] = d[2]  # pos6
    bits[6] = d[3]  # pos7
    steps = [f"Datos colocados: pos3={d[0]}, pos5={d[1]}, pos6={d[2]}, pos7={d[3]}"]
    # paridades:
    # p1 (pos1) cubre bits 1,3,5,7 -> pos1, pos3, pos5, pos7 (index 0,2,4,6)
    p1 = (bits[2] + bits[4] + bits[6]) % 2
    bits[0] = p1
    # p2 (pos2) cubre 2,3,6,7 -> index 1,2,5,6
    p2 = (bits[2] + bits[5] + bits[6]) % 2
    bits[1] = p2
    # p3 (pos4) cubre 4,5,6,7 -> index 3,4,5,6
    p3 = (bits[4] + bits[5] + bits[6]) % 2
    bits[3] = p3
    steps.append(f"Calculo paridades: p1={p1}, p2={p2}, p3={p3}")
    encoded = ''.join(str(b) for b in bits)
    steps.append(f"Codigo Hamming(7,4) -> {encoded} (pos 1..7)")
    return encoded, steps

def hamming74_decode(received7: str) -> Tuple[str, List[str]]:
    """Decodifica Hamming(7,4), detecta y corrige 1-bit error si existe.
       Devuelve (decoded_data4, pasos)"""
    if len(received7) != 7 or any(c not in '01' for c in received7):
        raise ValueError("hamming74_decode: received7 debe ser 7 bits")
    r = [int(b) for b in received7]
    steps = [f"Recibido: {received7} (pos 1..7)"]
    # Syndrome bits (s1 s2 s3)
    s1 = (r[0] + r[2] + r[4] + r[6]) % 2
    s2 = (r[1] + r[2] + r[5] + r[6]) % 2
    s3 = (r[3] + r[4] + r[5] + r[6]) % 2
    steps.append(f"Calculo sindrome: s1={s1}, s2={s2}, s3={s3}")
    syndrome = s3*4 + s2*2 + s1  # posición en decimal
    if syndrome == 0:
        steps.append("Sindrome = 0 -> no se detectan errores.")
        corrected = r
    else:
        steps.append(f"Sindrome = {syndrome} -> error en posición {syndrome} (1-indexed). Se corrige invirtiendo ese bit.")
        pos = syndrome - 1
        corrected = r[:]
        corrected[pos] ^= 1
        steps.append(f"Bit en pos {syndrome} cambiado {r[pos]} -> {corrected[pos]}")
    # extraer datos de pos 3,5,6,7
    data = [corrected[2], corrected[4], corrected[5], corrected[6]]
    data_str = ''.join(str(x) for x in data)
    steps.append(f"Datos extraidos (pos3,pos5,pos6,pos7): {data_str}")
    return data_str, steps

# ------------------------
# EJEMPLO / DEMO (cuando se corre el script)
# ------------------------
def demo():
    print("=== DEMO CONVERSIONES ===")
    value = input("Ingrese un valor para convertir: ")
    from_base = int(input("Ingrese la base de origen: "))
    to_base = int(input("Ingrese la base de destino: "))
    val, steps = convert_between_bases(value, from_base, to_base)
    print("\n".join(steps))
    print(f"-> Resultado: {val}\n")

    print("=== DECIMAL A BCD ===")
    decimal_value = int(input("Ingrese un número decimal para convertir a BCD: "))
    bcd, steps = decimal_to_bcd_steps(decimal_value)
    print("\n".join(steps))
    print()

    print("=== BINARIO A GRAY ===")
    bin_value = input("Ingrese un número binario para convertir a Gray: ")
    g, steps = binary_to_gray_steps(bin_value)
    print("\n".join(steps))
    print()

    print("=== GRAY A BINARIO ===")
    gray_value = input("Ingrese un número Gray para convertir a binario: ")
    b, steps = gray_to_binary_steps(gray_value)
    print("\n".join(steps))
    print()

    print("=== TEXTO A ASCII ===")
    text_value = input("Ingrese un texto para convertir a ASCII: ")
    table, steps = text_to_ascii_steps(text_value)
    print("\n".join(steps))
    print()

    print("=== PARIDAD SIMPLE ===")
    data = input("Ingrese una cadena de bits para agregar paridad: ")
    with_par, expl = add_parity_bit(data, parity='even')
    print(f"Data: {data} -> Con paridad even: {with_par} ({expl})")
    ok, check = check_parity_bit(with_par, parity='even')
    print(f"Comprobacion: {check}")
    # simular error
    corrupted = with_par[:3] + ('1' if with_par[3]=='0' else '0') + with_par[4:]
    ok2, check2 = check_parity_bit(corrupted, parity='even')
    print(f"Corrupto: {corrupted} -> {check2}")
    print()

    print("=== HAMMING (7,4) ===")
    data4 = input("Ingrese 4 bits de datos para codificar en Hamming(7,4): ")
    encoded, steps = hamming74_encode(data4)
    print("\n".join(steps))
    # simular un error:
    rec_list = list(encoded)
    rec_list[4] = '1' if rec_list[4]=='0' else '0'  # flip pos5 (index 4)
    received = ''.join(rec_list)
    print(f"\nMensaje transmitido con error en pos5: {received}")
    decoded, dsteps = hamming74_decode(received)
    print("\n".join(dsteps))
    print()

if __name__ == "__main__":
    demo()
