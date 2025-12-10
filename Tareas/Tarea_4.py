import sys

def normalize_bin(s: str) -> str:
    s = s.strip().replace(" ", "")
    if s.startswith("0b") or s.startswith("0B"):
        s = s[2:]
    if s == "":
        raise ValueError("Cadena vacía")
    if any(c not in "01" for c in s):
        raise ValueError("Entrada debe contener solo 0 y 1")
    return s

def align_bins(a: str, b: str) -> tuple:
    L = max(len(a), len(b))
    return a.zfill(L), b.zfill(L)

def bitwise_steps(op: str, a: str, b: str) -> tuple:
    a, b = align_bins(a, b)
    L = len(a)
    steps = [f"Alineado: A={a}, B={b} (MSB ... LSB)"]
    res_bits = []
    # recorrer desde MSB a LSB pero mostrar índice relativo a LSB para claridad
    for idx, (ba, bb) in enumerate(zip(a, b)):
        msb_index = idx
        lsb_index = L - 1 - idx
        if op == "AND":
            r = str(int(ba) & int(bb))
        elif op == "OR":
            r = str(int(ba) | int(bb))
        elif op == "XOR":
            r = str(int(ba) ^ int(bb))
        else:
            raise ValueError("Operador bitwise desconocido")
        steps.append(f"Bit (MSB idx {msb_index}, LSB idx {lsb_index}): {ba} {op} {bb} -> {r}")
        res_bits.append(r)
    result = ''.join(res_bits)
    steps.append(f"Resultado (MSB ... LSB): {result}")
    steps.append(f"Interpretación decimal: {int(result,2)}")
    return result, steps

def not_steps(a: str) -> tuple:
    a = normalize_bin(a)
    steps = [f"Entrada (MSB ... LSB): {a}"]
    res = ''.join('1' if c == '0' else '0' for c in a)
    L = len(a)
    for idx, c in enumerate(a):
        msb_index = idx
        lsb_index = L - 1 - idx
        steps.append(f"Bit (MSB idx {msb_index}, LSB idx {lsb_index}): NOT {c} -> {res[idx]}")
    steps.append(f"Resultado NOT (MSB ... LSB): {res}  -> decimal {int(res,2)}")
    return res, steps

def shift_steps(a: str, n: int, direction: str) -> tuple:
    a = normalize_bin(a)
    steps = [f"Entrada: {a}  desplazamiento: {n} ({direction})"]
    if n < 0:
        raise ValueError("Desplazamiento debe ser >= 0")
    if direction == "L":
        res = a[n:] + "0" * n if n < len(a) else "0" * len(a)
        steps.append(f"Desplazar izquierda: quitar {n} bits más significativos, añadir {n} ceros a la derecha -> {res}")
    else:
        # R logical shift right
        res = "0" * n + a[:len(a)-n] if n < len(a) else "0" * len(a)
        steps.append(f"Desplazar derecha lógico: añadir {n} ceros a la izquierda, quitar {n} bits al final -> {res}")
    steps.append(f"Resultado: {res}")
    return res, steps

def add_steps(a: str, b: str) -> tuple:
    a, b = align_bins(a, b)
    L = len(a)
    steps = [f"Alineado: A={a}, B={b} (MSB ... LSB)"]
    carry = 0
    res_bits = []
    # recorrer de LSB a MSB para sumar correctamente y describir cada paso
    for i in range(L-1, -1, -1):
        sa = int(a[i]); sb = int(b[i])
        carry_in = carry
        s = sa + sb + carry_in
        bit = s % 2
        carry = s // 2
        bit_pos_lsb = L-1 - i
        steps.append(f"Bit LSB idx {bit_pos_lsb} (pos {i} MSB idx): {sa} + {sb} + carry_in({carry_in}) = {s} -> bit={bit}, carry_out={carry}")
        res_bits.append(str(bit))
    if carry:
        res_bits.append('1')
        steps.append(f"Acarreo final = 1 -> se añade bit extra al MSB")
    result = ''.join(reversed(res_bits))
    steps.append(f"Resultado final (MSB ... LSB): {result} -> decimal {int(result,2)}")
    return result, steps

def sub_steps(a: str, b: str) -> tuple:
    a = normalize_bin(a); b = normalize_bin(b)
    L = max(len(a), len(b))
    az, bz = a.zfill(L), b.zfill(L)
    ai = int(az, 2); bi = int(bz, 2)
    steps = [f"Alineado: A={az} (dec {ai}), B={bz} (dec {bi})"]
    diff = ai - bi
    steps.append(f"Resta decimal: {ai} - {bi} = {diff}")
    if diff >= 0:
        res = format(diff, 'b').zfill(L)
        steps.append(f"Resultado binario (no negativo): {res}")
    else:
        # mostrar complemento a dos de la magnitud (representación en L bits)
        mod = 1 << L
        two_comp = (diff + mod) & (mod - 1)
        res = format(two_comp, 'b').zfill(L)
        steps.append(f"Resultado negativo -> representación en complemento a dos con {L} bits: {res}")
    steps.append(f"Resultado final: {res}")
    return res, steps

def conversion_menu():
    while True:
        print("\n--- Conversión ---")
        print("1) Binario -> Decimal/Hex")
        print("2) Decimal -> Binario")
        print("0) Volver")
        opt = input("Opción: ").strip()
        if opt == "0":
            return
        if opt == "1":
            s = input("Ingrese binario: ").strip()
            try:
                s = normalize_bin(s)
                dec = int(s, 2)
                print(f"{s} -> decimal {dec} -> hex 0x{dec:X}")
            except Exception as e:
                print("Error:", e)
        elif opt == "2":
            try:
                n = int(input("Ingrese decimal: ").strip())
                if n < 0:
                    print("Solo soporta decimales no negativos")
                    continue
                print(f"{n} -> binario {format(n,'b')}")
            except Exception as e:
                print("Error:", e)
        else:
            print("Opción inválida")

def main_menu():
    while True:
        print("\n=== MICRO-SIMULADOR BINARIO ===")
        print("Operaciones disponibles:")
        print("1) AND")
        print("2) OR")
        print("3) XOR")
        print("4) NOT")
        print("5) SHIFT LEFT")
        print("6) SHIFT RIGHT")
        print("7) ADD")
        print("8) SUBTRACT")
        print("9) Conversiones")
        print("0) Salir")
        choice = input("Seleccione operación: ").strip()
        try:
            if choice == "0":
                print("Saliendo.")
                break
            if choice in ("1","2","3"):
                a = normalize_bin(input("Operando A (binario): "))
                b = normalize_bin(input("Operando B (binario): "))
                op = {"1":"AND","2":"OR","3":"XOR"}[choice]
                res, steps = bitwise_steps(op, a, b)
            elif choice == "4":
                a = input("Operando A (binario): ")
                res, steps = not_steps(a)
            elif choice in ("5","6"):
                a = normalize_bin(input("Operando A (binario): "))
                n = int(input("Desplazamiento (entero >=0): ").strip())
                dirc = "L" if choice=="5" else "R"
                res, steps = shift_steps(a, n, dirc)
            elif choice == "7":
                a = normalize_bin(input("Operando A (binario): "))
                b = normalize_bin(input("Operando B (binario): "))
                res, steps = add_steps(a, b)
            elif choice == "8":
                a = normalize_bin(input("Operando A (binario): "))
                b = normalize_bin(input("Operando B (binario): "))
                res, steps = sub_steps(a, b)
            elif choice == "9":
                conversion_menu()
                continue
            else:
                print("Opción inválida")
                continue
        except Exception as e:
            print("Error:", e)
            continue

        print("\n--- PASOS ---")
        for line in steps:
            print(line)
        print(f"-> Resultado final: {res}")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nInterrupción por usuario. Adiós.")
        sys.exit(0)