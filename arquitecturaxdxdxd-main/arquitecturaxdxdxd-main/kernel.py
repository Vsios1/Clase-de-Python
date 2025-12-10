from collections import deque
from memoria import MemoryManager


class Kernel:
    """Kernel con MLFQ y prioridad dinámica, integrado con MemoryManager."""

    def __init__(self, num_niveles=3, quanta=(1, 2, 4), aging_interval=5,
                 ram_bytes=1024, page_size=64, cache_capacity=32, num_cores=1):
        self.num_niveles = num_niveles
        self.quanta = list(quanta)[:num_niveles]
        self.aging_interval = max(1, aging_interval)
        self.tiempo_actual = 0

        # Colas por nivel (0 = más alta prioridad)
        self.colas = [deque() for _ in range(self.num_niveles)]
        self.procesos = []
        self.procesos_terminados = []
        self.en_ejecucion = []  # procesos corriendo este tick

        # Estados por proceso
        self.prioridad_por_pid = {}
        self.quantum_consumido = {}  # pid -> ticks usados en su nivel actual
        self.espera_por_pid = {}  # pid -> ticks esperando en colas

        # Memoria
        self.memoria = MemoryManager(total_ram_bytes=ram_bytes,
                                     page_size_bytes=page_size,
                                     cache_capacity_pages=cache_capacity)

        # Núcleos
        self.num_cores = max(1, int(num_cores))

    def set_cores(self, n):
        self.num_cores = max(1, int(n))

    def agregar_proceso(self, proceso):
        self.procesos.append(proceso)
        self.prioridad_por_pid[proceso.pid] = 0
        self.quantum_consumido[proceso.pid] = 0
        self.espera_por_pid[proceso.pid] = 0

    def inicializar(self):
        self.tiempo_actual = 0
        self.procesos_terminados.clear()
        for p in self.procesos:
            p.estado = "Nuevo"
            p.tiempo_restante = p.tiempo_cpu
            p.tiempo_espera = 0
            p.tiempo_respuesta = -1
            p.tiempo_inicio = -1
            p.tiempo_fin = -1
        for q in self.colas:
            q.clear()
        # Reset memoria
        self.memoria.logs.clear()

    def _llegadas(self):
        for p in self.procesos:
            if p.estado == "Nuevo" and p.tiempo_llegada == self.tiempo_actual:
                # Intentar asignación de memoria
                ok = self.memoria.allocate(p.pid, max(1, p.tiempo_memoria) * self.memoria.page_size)
                if not ok:
                    # Si falla memoria, va a espera (simula bloqueo)
                    p.estado = "Espera"
                else:
                    p.estado = "Listo"
                    self.colas[0].append(p)

    def _aging(self):
        # Aumenta prioridad (subir nivel) de procesos que esperan demasiado
        for nivel in range(self.num_niveles):
            for p in list(self.colas[nivel]):
                self.espera_por_pid[p.pid] += 1
                if self.espera_por_pid[p.pid] % self.aging_interval == 0 and nivel > 0:
                    self.colas[nivel].remove(p)
                    self.prioridad_por_pid[p.pid] = nivel - 1
                    self.colas[nivel - 1].append(p)

    def _select_runnable(self):
        runnable = []
        # Seleccionar desde el nivel más alto hacia abajo
        for nivel in range(self.num_niveles):
            while len(runnable) < self.num_cores and self.colas[nivel]:
                p = self.colas[nivel].popleft()
                p.estado = "Ejecutando"
                if p.tiempo_inicio == -1:
                    p.tiempo_inicio = self.tiempo_actual
                    p.tiempo_respuesta = self.tiempo_actual - p.tiempo_llegada
                runnable.append((nivel, p))
        # Registrar espera para los que quedan en colas
        for nivel in range(self.num_niveles):
            for p in self.colas[nivel]:
                p.tiempo_espera += 1
        return runnable

    def _post_run(self, nivel, p):
        # Reducir CPU restante y manejar fin/quantum
        p.tiempo_restante -= 1
        self.quantum_consumido[p.pid] = self.quantum_consumido.get(p.pid, 0) + 1
        # Simular acceso de memoria
        self.memoria.access(p.pid, 0)

        if p.tiempo_restante <= 0:
            p.estado = "Terminado"
            p.tiempo_fin = self.tiempo_actual + 1
            self.procesos_terminados.append(p)
            self.memoria.free(p.pid)
            self.quantum_consumido[p.pid] = 0
            return

        # Quantum agotado -> bajar prioridad (si existe un nivel inferior)
        if self.quantum_consumido[p.pid] >= self.quanta[min(nivel, self.num_niveles - 1)]:
            self.quantum_consumido[p.pid] = 0
            nuevo_nivel = min(nivel + 1, self.num_niveles - 1)
            self.prioridad_por_pid[p.pid] = nuevo_nivel
            p.estado = "Listo"
            self.colas[nuevo_nivel].append(p)
        else:
            # Aún le queda quantum, continúa en el mismo nivel (Round Robin por nivel)
            p.estado = "Listo"
            self.colas[nivel].append(p)

    def step(self):
        self._llegadas()
        self._aging()

        runnable = self._select_runnable()
        self.en_ejecucion = [p for _, p in runnable]
        # Ejecutar un tick
        for nivel, p in runnable:
            self._post_run(nivel, p)

        self.tiempo_actual += 1

    def estadisticas(self):
        tiempos_espera = []
        tiempos_retorno = []
        tiempos_respuesta = []

        for p in self.procesos_terminados:
            tiempo_retorno = p.tiempo_fin - p.tiempo_llegada
            tiempos_retorno.append(tiempo_retorno)
            tiempos_espera.append(p.tiempo_espera)
            tiempos_respuesta.append(p.tiempo_respuesta)

        total_tiempo = max(1, self.tiempo_actual)
        uso_cpu = sum(1 for _ in range(total_tiempo))  # simplificación
        return {
            'promedio_espera': sum(tiempos_espera) / len(tiempos_espera) if tiempos_espera else 0,
            'promedio_retorno': sum(tiempos_retorno) / len(tiempos_retorno) if tiempos_retorno else 0,
            'promedio_respuesta': sum(tiempos_respuesta) / len(tiempos_respuesta) if tiempos_respuesta else 0,
            'total_procesos': len(self.procesos_terminados),
            'uso_cpu': uso_cpu / total_tiempo,
            'memoria': self.memoria.stats(),
        }