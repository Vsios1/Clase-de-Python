class Proceso:
    def __init__(self, pid, tiempo_llegada, tiempo_cpu, tiempo_memoria=0, prioridad=0):
        self.pid = pid
        self.tiempo_llegada = tiempo_llegada
        self.tiempo_cpu = tiempo_cpu
        self.tiempo_memoria = tiempo_memoria
        self.prioridad = prioridad
        self.tiempo_restante = tiempo_cpu
        self.estado = "Nuevo"
        self.tiempo_inicio = -1
        self.tiempo_fin = -1
        self.tiempo_espera = 0
        self.tiempo_respuesta = -1
    
    def __str__(self):
        return f"P{self.pid} (L:{self.tiempo_llegada}, CPU:{self.tiempo_cpu}, E:{self.estado})"
    
    def __repr__(self):
        return self.__str__()