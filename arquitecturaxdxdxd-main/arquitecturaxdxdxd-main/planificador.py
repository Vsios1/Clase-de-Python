from proceso import Proceso
from collections import deque
import heapq
from kernel import Kernel
from dispatcher import Dispatcher

class Planificador:
    def __init__(self):
        # Extensiones: multicore y memoria/MLFQ
        self.num_cores = 1
        self.kernel = Kernel(num_niveles=3, quanta=(1, 2, 4), aging_interval=5, num_cores=self.num_cores)
        self.dispatcher = Dispatcher(num_cores=self.num_cores)
        self.reset()
    
    def reset(self):
        self.procesos = []
        self.tiempo_actual = 0
        self.proceso_ejecutando = None
        self.cola_ready = deque()
        self.cola_espera = deque()
        self.procesos_terminados = []
        self.gantt = []
        self.quantum = 2
        self.algoritmo = "FCFS"
        self.estadisticas = {}
        # Reiniciar dispatcher según núcleos
        if hasattr(self, 'dispatcher'):
            self.dispatcher.set_cores(self.num_cores)
    
    def agregar_proceso(self, proceso):
        self.procesos.append(proceso)
        # Registrar en kernel para MLFQ/memoria
        self.kernel.agregar_proceso(proceso)
    
    def ordenar_procesos_llegada(self):
        self.procesos.sort(key=lambda x: x.tiempo_llegada)
    
    def inicializar_simulacion(self):
        self.ordenar_procesos_llegada()
        self.tiempo_actual = 0
        self.proceso_ejecutando = None
        self.cola_ready.clear()
        self.cola_espera.clear()
        self.procesos_terminados.clear()
        self.gantt = []

        # Resetear estados de procesos
        for proceso in self.procesos:
            proceso.estado = "Nuevo"
            proceso.tiempo_restante = proceso.tiempo_cpu
            proceso.tiempo_espera = 0
            proceso.tiempo_respuesta = -1
            proceso.tiempo_inicio = -1
            proceso.tiempo_fin = -1

        # Reiniciar kernel
        self.kernel.inicializar()
        self.kernel.set_cores(self.num_cores)
        self.dispatcher.set_cores(self.num_cores)
    
    def llegada_procesos(self):
        """Agrega procesos que llegan en el tiempo actual a la cola ready"""
        for proceso in self.procesos:
            if proceso.tiempo_llegada == self.tiempo_actual and proceso.estado == "Nuevo":
                proceso.estado = "Listo"
                self.cola_ready.append(proceso)
    
    def fcfs(self):
        if not self.proceso_ejecutando and self.cola_ready:
            self.proceso_ejecutando = self.cola_ready.popleft()
            self.proceso_ejecutando.estado = "Ejecutando"
            if self.proceso_ejecutando.tiempo_respuesta == -1:
                self.proceso_ejecutando.tiempo_respuesta = self.tiempo_actual - self.proceso_ejecutando.tiempo_llegada
    
    def sjf(self):
        if not self.proceso_ejecutando and self.cola_ready:
            # Ordenar por tiempo de CPU más corto
            self.cola_ready = deque(sorted(self.cola_ready, key=lambda x: x.tiempo_cpu))
            self.proceso_ejecutando = self.cola_ready.popleft()
            self.proceso_ejecutando.estado = "Ejecutando"
            if self.proceso_ejecutando.tiempo_respuesta == -1:
                self.proceso_ejecutando.tiempo_respuesta = self.tiempo_actual - self.proceso_ejecutando.tiempo_llegada
    
    def srtf(self):
        if self.proceso_ejecutando:
            # Siempre revisar si hay un proceso más corto
            proceso_mas_corto = self.proceso_ejecutando
            for proceso in self.cola_ready:
                if proceso.tiempo_restante < proceso_mas_corto.tiempo_restante:
                    # Interrumpir proceso actual
                    self.cola_ready.append(self.proceso_ejecutando)
                    self.proceso_ejecutando.estado = "Listo"
                    proceso_mas_corto = proceso
                    self.cola_ready.remove(proceso)
            
            if proceso_mas_corto != self.proceso_ejecutando:
                self.proceso_ejecutando = proceso_mas_corto
                self.proceso_ejecutando.estado = "Ejecutando"
        
        elif self.cola_ready:
            # Elegir el proceso con menor tiempo restante
            self.cola_ready = deque(sorted(self.cola_ready, key=lambda x: x.tiempo_restante))
            self.proceso_ejecutando = self.cola_ready.popleft()
            self.proceso_ejecutando.estado = "Ejecutando"
            if self.proceso_ejecutando.tiempo_respuesta == -1:
                self.proceso_ejecutando.tiempo_respuesta = self.tiempo_actual - self.proceso_ejecutando.tiempo_llegada
    
    def round_robin(self):
        if not self.proceso_ejecutando and self.cola_ready:
            self.proceso_ejecutando = self.cola_ready.popleft()
            self.proceso_ejecutando.estado = "Ejecutando"
            if self.proceso_ejecutando.tiempo_respuesta == -1:
                self.proceso_ejecutando.tiempo_respuesta = self.tiempo_actual - self.proceso_ejecutando.tiempo_llegada
    
    def prioridades(self, apropiativo=False):
        if apropiativo and self.proceso_ejecutando:
            # Buscar proceso con mayor prioridad (número menor = mayor prioridad)
            proceso_mayor_prioridad = self.proceso_ejecutando
            for proceso in self.cola_ready:
                if proceso.prioridad < proceso_mayor_prioridad.prioridad:
                    # Interrumpir proceso actual
                    self.cola_ready.append(self.proceso_ejecutando)
                    self.proceso_ejecutando.estado = "Listo"
                    proceso_mayor_prioridad = proceso
                    self.cola_ready.remove(proceso)
            
            if proceso_mayor_prioridad != self.proceso_ejecutando:
                self.proceso_ejecutando = proceso_mayor_prioridad
                self.proceso_ejecutando.estado = "Ejecutando"
        
        elif not self.proceso_ejecutando and self.cola_ready:
            # Ordenar por prioridad (menor número = mayor prioridad)
            self.cola_ready = deque(sorted(self.cola_ready, key=lambda x: x.prioridad))
            self.proceso_ejecutando = self.cola_ready.popleft()
            self.proceso_ejecutando.estado = "Ejecutando"
            if self.proceso_ejecutando.tiempo_respuesta == -1:
                self.proceso_ejecutando.tiempo_respuesta = self.tiempo_actual - self.proceso_ejecutando.tiempo_llegada
    
    def ejecutar_paso(self):
        if self.algoritmo == "MLFQ":
            # Ejecutar un paso del kernel MLFQ
            self.kernel.step()
            # Construir Gantt multicore para el tick que acaba de correr
            time_ran = self.kernel.tiempo_actual - 1
            for core_id, p in enumerate(self.kernel.en_ejecucion):
                if p is not None:
                    self.gantt.append((time_ran, core_id, p.pid))

            # Reflejar estado en campos compatibles
            self.tiempo_actual = self.kernel.tiempo_actual
            self.procesos_terminados = list(self.kernel.procesos_terminados)
            # Flatten ready queues
            ready = []
            for q in self.kernel.colas:
                ready.extend(list(q))
            self.cola_ready = deque(ready)
            # Proceso ejecutando (primero)
            self.proceso_ejecutando = self.kernel.en_ejecucion[0] if self.kernel.en_ejecucion else None
        else:
            # Lógica anterior de algoritmos clásicos
            self.llegada_procesos()

            if self.algoritmo == "FCFS":
                self.fcfs()
            elif self.algoritmo == "SJF":
                self.sjf()
            elif self.algoritmo == "SRTF":
                self.srtf()
            elif self.algoritmo == "Round Robin":
                self.round_robin()
            elif self.algoritmo == "Prioridades No Apropiativo":
                self.prioridades(apropiativo=False)
            elif self.algoritmo == "Prioridades Apropiativo":
                self.prioridades(apropiativo=True)

            if self.proceso_ejecutando:
                if self.proceso_ejecutando.tiempo_inicio == -1:
                    self.proceso_ejecutando.tiempo_inicio = self.tiempo_actual
                self.gantt.append((self.tiempo_actual, self.proceso_ejecutando.pid))
                self.proceso_ejecutando.tiempo_restante -= 1
                if self.proceso_ejecutando.tiempo_restante <= 0:
                    self.proceso_ejecutando.estado = "Terminado"
                    self.proceso_ejecutando.tiempo_fin = self.tiempo_actual + 1
                    self.procesos_terminados.append(self.proceso_ejecutando)
                    self.proceso_ejecutando = None
                elif self.algoritmo == "Round Robin" and (self.tiempo_actual + 1) % self.quantum == 0:
                    self.proceso_ejecutando.estado = "Listo"
                    self.cola_ready.append(self.proceso_ejecutando)
                    self.proceso_ejecutando = None

            for proceso in self.cola_ready:
                proceso.tiempo_espera += 1

            self.tiempo_actual += 1
    
    def simulacion_completa(self):
        self.inicializar_simulacion()
        while len(self.procesos_terminados) < len(self.procesos):
            self.ejecutar_paso()
        self.calcular_estadisticas()
    
    def calcular_estadisticas(self):
        if self.algoritmo == "MLFQ":
            self.estadisticas = self.kernel.estadisticas()
        else:
            tiempos_espera = []
            tiempos_retorno = []
            tiempos_respuesta = []
            for proceso in self.procesos_terminados:
                tiempo_retorno = proceso.tiempo_fin - proceso.tiempo_llegada
                tiempos_retorno.append(tiempo_retorno)
                tiempos_espera.append(proceso.tiempo_espera)
                tiempos_respuesta.append(proceso.tiempo_respuesta)
            self.estadisticas = {
                'promedio_espera': sum(tiempos_espera) / len(tiempos_espera) if tiempos_espera else 0,
                'promedio_retorno': sum(tiempos_retorno) / len(tiempos_retorno) if tiempos_retorno else 0,
                'promedio_respuesta': sum(tiempos_respuesta) / len(tiempos_respuesta) if tiempos_respuesta else 0,
                'total_procesos': len(self.procesos_terminados),
                'uso_cpu': (self.tiempo_actual - sum(tiempos_espera)) / self.tiempo_actual if self.tiempo_actual > 0 else 0
            }
    
    def obtener_estado_actual(self):
        estado = {
            'tiempo_actual': self.tiempo_actual,
            'proceso_ejecutando': self.proceso_ejecutando,
            'cola_ready': list(self.cola_ready),
            'procesos_terminados': self.procesos_terminados,
            'gantt': self.gantt
        }
        if self.algoritmo == "MLFQ":
            estado['memoria'] = self.kernel.memoria.stats()
        return estado

    # Configuración externa
    def set_cores(self, n):
        self.num_cores = max(1, int(n))
        self.kernel.set_cores(self.num_cores)
        self.dispatcher.set_cores(self.num_cores)