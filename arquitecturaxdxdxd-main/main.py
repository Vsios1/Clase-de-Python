from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.metrics import dp
import ctypes
import subprocess
import json

from planificador import Planificador
from proceso import Proceso

class ProcesoInput(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(260)

        def fila_etiqueta(texto, input_ref, ayuda):
            fila = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
            lbl = Label(text=texto, size_hint_x=0.35, color=(0,0,0,1))
            cont = BoxLayout(orientation='horizontal', size_hint_x=0.65)
            input_ref.size_hint = (0.92, 1)
            info = InfoIcon(message=ayuda, size_hint=(None, None), size=(dp(24), dp(24)))
            cont.add_widget(input_ref)
            cont.add_widget(info)
            fila.add_widget(lbl)
            fila.add_widget(cont)
            return fila

        self.pid_input = TextInput(hint_text='PID (entero)', multiline=False, foreground_color=(0,0,0,1), background_normal='', background_color=(1,1,1,1))
        self.llegada_input = TextInput(hint_text='Llegada (entero, vacío=0)', multiline=False, foreground_color=(0,0,0,1), background_normal='', background_color=(1,1,1,1))
        self.cpu_input = TextInput(hint_text='CPU (entero, vacío=1)', multiline=False, foreground_color=(0,0,0,1), background_normal='', background_color=(1,1,1,1))
        self.memoria_input = TextInput(hint_text='Memoria (entero, vacío=0)', multiline=False, foreground_color=(0,0,0,1), background_normal='', background_color=(1,1,1,1))
        self.prioridad_input = TextInput(hint_text='Prioridad (entero, vacío=0)', multiline=False, foreground_color=(0,0,0,1), background_normal='', background_color=(1,1,1,1))

        self.add_widget(fila_etiqueta('PID:', self.pid_input, 'Identificador único del proceso'))
        self.add_widget(fila_etiqueta('Llegada:', self.llegada_input, 'Tiempo en que el proceso entra al sistema'))
        self.add_widget(fila_etiqueta('CPU:', self.cpu_input, 'Ráfaga de CPU requerida por el proceso'))
        self.add_widget(fila_etiqueta('Memoria:', self.memoria_input, 'Memoria estimada que necesita el proceso'))
        self.add_widget(fila_etiqueta('Prioridad:', self.prioridad_input, 'Valor de prioridad, mayor es más prioritario'))
    
    def obtener_datos(self):
        try:
            pid_txt = self.pid_input.text.strip()
            if not pid_txt or not pid_txt.isdigit():
                return None
            lleg_txt = self.llegada_input.text.strip()
            cpu_txt = self.cpu_input.text.strip()
            mem_txt = self.memoria_input.text.strip()
            pri_txt = self.prioridad_input.text.strip()
            llegada_val = int(lleg_txt) if lleg_txt.isdigit() else 0
            cpu_val = int(cpu_txt) if cpu_txt.isdigit() else 1
            mem_val = int(mem_txt) if mem_txt.isdigit() else 0
            pri_val = int(pri_txt) if pri_txt.isdigit() else 0
            return {
                'pid': int(pid_txt),
                'llegada': llegada_val,
                'cpu': cpu_val,
                'memoria': mem_val,
                'prioridad': pri_val
            }
        except ValueError:
            return None
    
    def _with_info(self, widget, message):
        fl = FloatLayout(size_hint_x=widget.size_hint_x)
        widget.size_hint = (1, 1)
        fl.add_widget(widget)
        fl.add_widget(InfoIcon(message=message, size_hint=(None, None), size=(dp(16), dp(16)), pos_hint={'right': 1, 'top': 1}))
        return fl

class Card(BoxLayout):
    def __init__(self, title=None, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('padding', dp(10))
        kwargs.setdefault('spacing', dp(8))
        super().__init__(**kwargs)
        self.title = title
        with self.canvas.before:
            Color(0.96, 0.97, 0.98, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            Color(0.80, 0.84, 0.89, 1)
            self.border = Line(rectangle=(self.x, self.y, self.width, self.height), width=1.0)
        self.bind(size=self._update_rect, pos=self._update_rect)
        if self.title:
            self.header = Label(text=f"[b]{self.title}[/b]", markup=True,
                                size_hint_y=None, height=dp(28), color=(0.15,0.18,0.22,1))
            self.add_widget(self.header)

    def _update_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos
        try:
            self.border.rectangle = (self.x, self.y, self.width, self.height)
        except Exception:
            pass

class ColorAssigner:
    """Asigna colores únicos a cada PID"""
    def __init__(self):
        self.colores = [
            (0.2, 0.6, 0.86, 1),    # Azul
            (0.18, 0.72, 0.48, 1),  # Verde
            (0.95, 0.73, 0.25, 1),  # Naranja
            (0.68, 0.53, 0.95, 1),  # Púrpura
            (0.85, 0.30, 0.30, 1),  # Rojo
            (0.30, 0.85, 0.85, 1),  # Cian
            (0.85, 0.85, 0.30, 1),  # Amarillo
            (0.60, 0.40, 0.85, 1),  # Lavanda
            (0.85, 0.60, 0.40, 1),  # Coral
            (0.40, 0.85, 0.60, 1),  # Verde menta
        ]
        self.mapa_colores = {}
        self.contador = 0
    
    def obtener_color(self, pid):
        if pid not in self.mapa_colores:
            self.mapa_colores[pid] = self.colores[self.contador % len(self.colores)]
            self.contador += 1
        return self.mapa_colores[pid]
    
    def reset(self):
        self.mapa_colores.clear()
        self.contador = 0

class GanttChart(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(100)
        self.bind(size=self._update_rect)
        self.color_assigner = ColorAssigner()
        
        self.title = Label(text='Diagrama de Gantt', size_hint_y=None, height=dp(30))
        self.add_widget(self.title)
        
        self.chart_container = BoxLayout(size_hint_y=None, height=dp(70), orientation='vertical')
        self.add_widget(self.chart_container)
        
        with self.canvas.before:
            Color(0.9, 0.9, 0.9, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
    
    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos
    
    def actualizar_gantt(self, gantt_data):
        self.chart_container.clear_widgets()

        if not gantt_data:
            return

        # Soporta tanto lista [(t, pid)] como dict {core: [(t, pid)]}
        if isinstance(gantt_data, dict):
            # Calcular tiempo máximo global
            all_events = [t for core_events in gantt_data.values() for t in core_events]
            tiempo_max = max([t[0] for t in all_events]) + 1 if all_events else 1

            # Escala de tiempo
            escala = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20))
            for i in range(0, tiempo_max + 1, max(1, tiempo_max // 10)):
                label = Label(text=str(i), size_hint_x=None, width=dp(30), color=(0,0,0,1))
                escala.add_widget(label)
            self.chart_container.add_widget(escala)

            # Una fila por núcleo
            for core_id in sorted(gantt_data.keys()):
                fila = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(2))
                fila.add_widget(Label(text=f"Core {core_id}", size_hint_x=None, width=dp(60), color=(0,0,0,1)))
                
                # Crear bloques de color para cada evento
                bloques = BoxLayout(orientation='horizontal', size_hint_x=1, spacing=dp(1))
                eventos = gantt_data[core_id]
                
                for t, pid in eventos:
                    if pid is not None:
                        color = self.color_assigner.obtener_color(pid)
                        bloque = BoxLayout(size_hint_x=1)
                        with bloque.canvas.before:
                            Color(*color)
                            bloque.bg_rect = Rectangle(size=bloque.size, pos=bloque.pos)
                        bloque.bind(size=self._update_bloque_rect, pos=self._update_bloque_rect)
                        label_bloque = Label(text=f'P{pid}', color=(1,1,1,1), bold=True)
                        bloque.add_widget(label_bloque)
                        bloques.add_widget(bloque)
                    else:
                        bloque = BoxLayout(size_hint_x=1)
                        with bloque.canvas.before:
                            Color(0.7, 0.7, 0.7, 1)
                            bloque.bg_rect = Rectangle(size=bloque.size, pos=bloque.pos)
                        bloque.bind(size=self._update_bloque_rect, pos=self._update_bloque_rect)
                        bloques.add_widget(bloque)
                
                fila.add_widget(bloques)
                self.chart_container.add_widget(fila)
        else:
            # Si viene como lista de triples (t, core, pid), agrupamos
            if gantt_data and isinstance(gantt_data[0], tuple) and len(gantt_data[0]) == 3:
                por_core = {}
                for t, core, pid in gantt_data:
                    por_core.setdefault(core, []).append((t, pid))
                # Reusar rama dict
                return self.actualizar_gantt(por_core)

            tiempo_max = max([t[0] for t in gantt_data]) + 1 if gantt_data else 1

            escala = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20))
            for i in range(0, tiempo_max + 1, max(1, tiempo_max // 10)):
                label = Label(text=str(i), size_hint_x=None, width=dp(30), color=(0,0,0,1))
                escala.add_widget(label)
            self.chart_container.add_widget(escala)

            barras = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(1))
            procesos_vistos = set()
            for tiempo, pid in gantt_data:
                if pid not in procesos_vistos:
                    color = self.color_assigner.obtener_color(pid)
                    barra = BoxLayout()
                    with barra.canvas.before:
                        Color(*color)
                        barra.bg_rect = Rectangle(size=barra.size, pos=barra.pos)
                    barra.bind(size=self._update_bloque_rect, pos=self._update_bloque_rect)
                    label_barra = Label(text=f'P{pid}', color=(1,1,1,1), bold=True)
                    barra.add_widget(label_barra)
                    barras.add_widget(barra)
                    procesos_vistos.add(pid)
            self.chart_container.add_widget(barras)
    
    def _update_bloque_rect(self, instance, value):
        if hasattr(instance, 'bg_rect'):
            instance.bg_rect.size = instance.size
            instance.bg_rect.pos = instance.pos

class InfoIcon(Button):
    def __init__(self, message='', **kwargs):
        super().__init__(**kwargs)
        self.text = 'ⓘ'
        self.font_size = '14sp'
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (0.6, 0.6, 0.6, 0.85)
        self.message = message
        self.bind(on_press=self._show)

    def _show(self, instance):
        Popup(title='Ayuda', content=Label(text=self.message), size_hint=(0.6, 0.4)).open()

class PlanificadorApp(App):
    def build(self):
        self.planificador = Planificador()
        self.simulando = False
        self.evento_simulacion = None
        
        # Layout principal
        layout_principal = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        with layout_principal.canvas.before:
            Color(0.94, 0.95, 0.96, 1)
            bg = Rectangle(size=layout_principal.size, pos=layout_principal.pos)
        layout_principal.bind(size=lambda i,v: setattr(bg,'size',i.size), pos=lambda i,v: setattr(bg,'pos',i.pos))

        header = BoxLayout(size_hint_y=None, height=dp(56), padding=[dp(12),0,dp(12),0], spacing=dp(10))
        with header.canvas.before:
            Color(0.12, 0.16, 0.24, 1)
            hr = Rectangle(size=header.size, pos=header.pos)
        header.bind(size=lambda i,v: setattr(hr,'size',i.size), pos=lambda i,v: setattr(hr,'pos',i.pos))
        titulo = Label(text='Sistema de Planificación de Procesos', color=(1,1,1,1), font_size='20sp')
        header.add_widget(titulo)
        layout_principal.add_widget(header)
        
        # Sección de entrada de datos
        seccion_entrada = Card(title='Configuración', size_hint_y=None, height=dp(360))
        
        # Controles de algoritmo
        controles_algoritmo = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        controles_algoritmo.add_widget(Label(text='Algoritmo:', size_hint_x=0.18, color=(0,0,0,1)))
        
        self.spinner_algoritmo = Spinner(
            text='FCFS',
            values=('FCFS', 'SJF', 'SRTF', 'Round Robin', 'Prioridades No Apropiativo', 'Prioridades Apropiativo', 'MLFQ'),
            size_hint_x=0.32,
            color=(0,0,0,1),
            background_normal='',
            background_color=(1,1,1,1)
        )
        self.spinner_algoritmo.bind(text=self.on_algoritmo_change)
        controles_algoritmo.add_widget(self._with_info(self.spinner_algoritmo, 'Selecciona la estrategia de planificación'))
        
        controles_algoritmo.add_widget(Label(text='Quantum:', size_hint_x=0.15, color=(0,0,0,1)))
        self.quantum_input = TextInput(text='2', multiline=False, size_hint_x=0.15, foreground_color=(0,0,0,1), background_normal='', background_color=(1,1,1,1))
        controles_algoritmo.add_widget(self._with_info(self.quantum_input, 'Tiempo fijo por turno en Round Robin'))
        controles_algoritmo.add_widget(Label(text='Núcleos:', size_hint_x=0.1, color=(0,0,0,1)))
        self.cores_input = TextInput(text='1', multiline=False, size_hint_x=0.1, foreground_color=(0,0,0,1), background_normal='', background_color=(1,1,1,1))
        controles_algoritmo.add_widget(self._with_info(self.cores_input, 'Número de CPUs simuladas simultáneamente'))
        
        seccion_entrada.add_widget(controles_algoritmo)
        seccion_entrada.add_widget(Label(text='Agregar Proceso', size_hint_y=None, height=dp(24), color=(0,0,0,1)))
        
        # Entrada de proceso
        self.entrada_proceso = ProcesoInput()
        seccion_entrada.add_widget(self.entrada_proceso)
        
        # Botones de control
        botones_control = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        self.btn_agregar = Button(text='Agregar Proceso', background_normal='', background_color=(0.20,0.60,0.86,1))
        self.btn_agregar.bind(on_press=self.agregar_proceso)
        
        self.btn_iniciar = Button(text='Iniciar Simulación', background_normal='', background_color=(0.18,0.72,0.48,1))
        self.btn_iniciar.bind(on_press=self.iniciar_simulacion)
        
        self.btn_pausar = Button(text='Pausar', background_normal='', background_color=(0.95,0.73,0.25,1))
        self.btn_pausar.bind(on_press=self.pausar_simulacion)
        
        self.btn_reiniciar = Button(text='Reiniciar', background_normal='', background_color=(0.68,0.53,0.95,1))
        self.btn_reiniciar.bind(on_press=self.reiniciar_simulacion)
        
        self.btn_limpiar = Button(text='Limpiar Todo', background_normal='', background_color=(0.85,0.30,0.30,1))
        self.btn_limpiar.bind(on_press=self.limpiar_todo)

        self.btn_ejemplo = Button(text='Cargar ejemplo', background_normal='', background_color=(0.30,0.30,0.85,1))
        self.btn_ejemplo.bind(on_press=self.cargar_ejemplo)

        self.btn_simular_ejemplo = Button(text='Simular ejemplo', background_normal='', background_color=(0.20,0.50,0.75,1))
        self.btn_simular_ejemplo.bind(on_press=self.simular_ejemplo)
        
        botones_control.add_widget(self.btn_agregar)
        botones_control.add_widget(self.btn_iniciar)
        botones_control.add_widget(self.btn_pausar)
        botones_control.add_widget(self.btn_reiniciar)
        botones_control.add_widget(self.btn_limpiar)
        botones_control.add_widget(self.btn_ejemplo)
        botones_control.add_widget(self.btn_simular_ejemplo)
        
        seccion_entrada.add_widget(botones_control)
        
        layout_principal.add_widget(seccion_entrada)
        
        # Sección de visualización
        seccion_visualizacion = BoxLayout(orientation='horizontal', spacing=10)
        
        # Columna izquierda - Lista de procesos
        columna_izquierda = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=dp(10))
        
        procesos_card = Card(title='Procesos Ingresados')
        self.lista_procesos = GridLayout(cols=6, size_hint_y=None, padding=[0,dp(6),0,0], spacing=dp(6))
        self.lista_procesos.add_widget(Label(text='PID', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='Llegada', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='CPU', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='Memoria', size_hint_x=0.15))
        self.lista_procesos.add_widget(Label(text='Prioridad', size_hint_x=0.2))
        self.lista_procesos.add_widget(Label(text='Estado', size_hint_x=0.2))
        self.lista_procesos.height = dp(40)
        
        scroll_lista = ScrollView(size_hint_y=1)
        scroll_lista.add_widget(self.lista_procesos)
        procesos_card.add_widget(scroll_lista)
        columna_izquierda.add_widget(procesos_card)
        
        # Diagrama de Gantt
        self.gantt_chart = GanttChart()
        gantt_card = Card(title='Diagrama de Gantt')
        gantt_card.add_widget(self.gantt_chart)
        columna_izquierda.add_widget(gantt_card)
        
        seccion_visualizacion.add_widget(columna_izquierda)
        
        # Columna derecha - Estado del sistema
        columna_derecha = BoxLayout(orientation='vertical', size_hint_x=0.6, spacing=dp(10))
        
        # Información en tiempo real
        info_card = Card(title='Estado de simulación', size_hint_y=None, height=dp(120))
        info_tiempo_real = GridLayout(cols=2)
        info_tiempo_real.add_widget(Label(text='Tiempo Actual:', color=(0,0,0,1)))
        self.label_tiempo = Label(text='0')
        info_tiempo_real.add_widget(self.label_tiempo)
        
        info_tiempo_real.add_widget(Label(text='Proceso Ejecutando:', color=(0,0,0,1)))
        self.label_ejecutando = Label(text='Ninguno')
        info_tiempo_real.add_widget(self.label_ejecutando)
        
        info_card.add_widget(info_tiempo_real)
        columna_derecha.add_widget(info_card)
        
        # Colas del sistema
        colas_card = Card(title='Colas del sistema')
        colas_sistema = GridLayout(cols=3, spacing=10)
        
        # Cola Ready
        cola_ready = BoxLayout(orientation='vertical')
        cola_ready.add_widget(Label(text='Cola Ready', size_hint_y=None, height=dp(30), color=(0,0,0,1)))
        self.lista_ready = Label(text='Vacía', size_hint_y=1)
        scroll_ready = ScrollView()
        scroll_ready.add_widget(self.lista_ready)
        cola_ready.add_widget(scroll_ready)
        colas_sistema.add_widget(cola_ready)
        
        # Cola Espera
        cola_espera = BoxLayout(orientation='vertical')
        cola_espera.add_widget(Label(text='Cola Espera', size_hint_y=None, height=dp(30), color=(0,0,0,1)))
        self.lista_espera = Label(text='Vacía', size_hint_y=1)
        scroll_espera = ScrollView()
        scroll_espera.add_widget(self.lista_espera)
        cola_espera.add_widget(scroll_espera)
        colas_sistema.add_widget(cola_espera)
        
        # Procesos Terminados
        cola_terminados = BoxLayout(orientation='vertical')
        cola_terminados.add_widget(Label(text='Terminados', size_hint_y=None, height=dp(30), color=(0,0,0,1)))
        self.lista_terminados = Label(text='Vacía', size_hint_y=1)
        scroll_terminados = ScrollView()
        scroll_terminados.add_widget(self.lista_terminados)
        cola_terminados.add_widget(scroll_terminados)
        colas_sistema.add_widget(cola_terminados)
        
        colas_card.add_widget(colas_sistema)
        columna_derecha.add_widget(colas_card)
        
        controles_sistema = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        btn_detalles = Button(text='Ver detalles del sistema', background_normal='', background_color=(0.20,0.60,0.86,1))
        btn_cpu_graph = Button(text='Ver gráfico CPU', background_normal='', background_color=(0.18,0.72,0.48,1))
        btn_ram_graph = Button(text='Ver gráfico RAM', background_normal='', background_color=(0.95,0.73,0.25,1))
        btn_detalles.bind(on_press=self.abrir_detalles_sistema)
        btn_cpu_graph.bind(on_press=self.abrir_grafico_cpu)
        btn_ram_graph.bind(on_press=self.abrir_grafico_ram)
        controles_sistema.add_widget(btn_detalles)
        controles_sistema.add_widget(btn_cpu_graph)
        controles_sistema.add_widget(btn_ram_graph)
        columna_derecha.add_widget(controles_sistema)
        
        seccion_visualizacion.add_widget(columna_derecha)
        layout_principal.add_widget(seccion_visualizacion)
        
        self._cpu_last_times = None
        return layout_principal
    
    def on_algoritmo_change(self, spinner, text):
        self.planificador.algoritmo = text
    
    def agregar_proceso(self, instance):
        datos = self.entrada_proceso.obtener_datos()
        if datos is None:
            # Resaltar campos inválidos
            def _mk_ok(inp): inp.background_color = (1,1,1,1)
            def _mk_err(inp): inp.background_color = (1,0.9,0.9,1)
            pid_ok = self.entrada_proceso.pid_input.text.strip().isdigit()
            llegada_ok = self.entrada_proceso.llegada_input.text.strip().isdigit() or self.entrada_proceso.llegada_input.text.strip() == ''
            cpu_ok = self.entrada_proceso.cpu_input.text.strip().isdigit() or self.entrada_proceso.cpu_input.text.strip() == ''
            _mk_ok(self.entrada_proceso.memoria_input if self.entrada_proceso.memoria_input.text.strip().isdigit() or self.entrada_proceso.memoria_input.text.strip() == '' else self.entrada_proceso.memoria_input)
            _mk_ok(self.entrada_proceso.prioridad_input if self.entrada_proceso.prioridad_input.text.strip().isdigit() or self.entrada_proceso.prioridad_input.text.strip() == '' else self.entrada_proceso.prioridad_input)
            _mk_ok(self.entrada_proceso.llegada_input) if llegada_ok else _mk_err(self.entrada_proceso.llegada_input)
            _mk_ok(self.entrada_proceso.cpu_input) if cpu_ok else _mk_err(self.entrada_proceso.cpu_input)
            _mk_ok(self.entrada_proceso.pid_input) if pid_ok else _mk_err(self.entrada_proceso.pid_input)
            self.mostrar_error("Ingresa números. PID es obligatorio; Llegada vacía=0, CPU vacía=1.")
            return
        
        # Verificar si el PID ya existe
        for proceso in self.planificador.procesos:
            if proceso.pid == datos['pid']:
                self.mostrar_error(f"El PID {datos['pid']} ya existe.")
                return
        
        proceso = Proceso(
            datos['pid'], datos['llegada'], datos['cpu'],
            datos['memoria'], datos['prioridad']
        )
        self.planificador.agregar_proceso(proceso)
        self.actualizar_lista_procesos()
        
        # Limpiar campos de entrada
        self.entrada_proceso.pid_input.text = ''
        self.entrada_proceso.llegada_input.text = ''
        self.entrada_proceso.cpu_input.text = ''
        self.entrada_proceso.memoria_input.text = ''
        self.entrada_proceso.prioridad_input.text = ''
        # Reset de colores
        for inp in [
            self.entrada_proceso.pid_input,
            self.entrada_proceso.llegada_input,
            self.entrada_proceso.cpu_input,
            self.entrada_proceso.memoria_input,
            self.entrada_proceso.prioridad_input,
        ]:
            inp.background_color = (1,1,1,1)

    def cargar_ejemplo(self, instance):
        ejemplos = [
            {'pid': 1, 'llegada': 0, 'cpu': 5, 'memoria': 10, 'prioridad': 2},
            {'pid': 2, 'llegada': 1, 'cpu': 3, 'memoria': 8, 'prioridad': 1},
            {'pid': 3, 'llegada': 2, 'cpu': 7, 'memoria': 6, 'prioridad': 3},
            {'pid': 4, 'llegada': 3, 'cpu': 4, 'memoria': 4, 'prioridad': 2},
            {'pid': 5, 'llegada': 4, 'cpu': 2, 'memoria': 2, 'prioridad': 1},
        ]
        existentes = {p.pid for p in self.planificador.procesos}
        for d in ejemplos:
            if d['pid'] in existentes:
                continue
            p = Proceso(d['pid'], d['llegada'], d['cpu'], d['memoria'], d['prioridad'])
            self.planificador.agregar_proceso(p)
        self.actualizar_lista_procesos()

    def simular_ejemplo(self, instance):
        self.cargar_ejemplo(instance)
        self.iniciar_simulacion(instance)
    
    def actualizar_lista_procesos(self):
        self.lista_procesos.clear_widgets()
        
        # Encabezados
        self.lista_procesos.add_widget(Label(text='PID', size_hint_x=0.15, color=(0,0,0,1)))
        self.lista_procesos.add_widget(Label(text='Llegada', size_hint_x=0.15, color=(0,0,0,1)))
        self.lista_procesos.add_widget(Label(text='CPU', size_hint_x=0.15, color=(0,0,0,1)))
        self.lista_procesos.add_widget(Label(text='Memoria', size_hint_x=0.15, color=(0,0,0,1)))
        self.lista_procesos.add_widget(Label(text='Prioridad', size_hint_x=0.2, color=(0,0,0,1)))
        self.lista_procesos.add_widget(Label(text='Estado', size_hint_x=0.2, color=(0,0,0,1)))
        
        for proceso in self.planificador.procesos:
            self.lista_procesos.add_widget(Label(text=str(proceso.pid), size_hint_x=0.15))
            self.lista_procesos.add_widget(Label(text=str(proceso.tiempo_llegada), size_hint_x=0.15))
            self.lista_procesos.add_widget(Label(text=str(proceso.tiempo_cpu), size_hint_x=0.15))
            self.lista_procesos.add_widget(Label(text=str(proceso.tiempo_memoria), size_hint_x=0.15))
            self.lista_procesos.add_widget(Label(text=str(proceso.prioridad), size_hint_x=0.2))
            self.lista_procesos.add_widget(Label(text=proceso.estado, size_hint_x=0.2))
        
        self.lista_procesos.height = dp(40 + len(self.planificador.procesos) * 30)
    
    def iniciar_simulacion(self, instance):
        if not self.planificador.procesos:
            self.mostrar_error("No hay procesos para simular.")
            return
        
        try:
            if self.spinner_algoritmo.text == "Round Robin":
                self.planificador.quantum = int(self.quantum_input.text)
            # Configurar núcleos
            if hasattr(self, 'cores_input') and self.cores_input.text.strip():
                self.planificador.set_cores(int(self.cores_input.text))
        except ValueError:
            self.mostrar_error("Quantum debe ser un número entero.")
            return
        
        self.planificador.algoritmo = self.spinner_algoritmo.text
        self.planificador.inicializar_simulacion()
        self.simulando = True
        
        # Programar la simulación paso a paso
        self.evento_simulacion = Clock.schedule_interval(self.ejecutar_paso_simulacion, 1.0)
    
    def ejecutar_paso_simulacion(self, dt):
        if self.simulando:
            estado_antes = len(self.planificador.procesos_terminados)
            self.planificador.ejecutar_paso()
            estado_despues = len(self.planificador.procesos_terminados)
            
            self.actualizar_interfaz()
            
            # Si terminó la simulación
            if estado_despues == len(self.planificador.procesos):
                self.simulando = False
                if self.evento_simulacion:
                    self.evento_simulacion.cancel()
                self.mostrar_estadisticas_finales()
    
    def pausar_simulacion(self, instance):
        self.simulando = False
        if self.evento_simulacion:
            self.evento_simulacion.cancel()
    
    def reiniciar_simulacion(self, instance):
        self.simulando = False
        if self.evento_simulacion:
            self.evento_simulacion.cancel()
        
        # Mantener los procesos pero reiniciar la simulación
        for proceso in self.planificador.procesos:
            proceso.estado = "Nuevo"
            proceso.tiempo_restante = proceso.tiempo_cpu
            proceso.tiempo_espera = 0
            proceso.tiempo_respuesta = -1
        
        self.planificador.tiempo_actual = 0
        self.planificador.proceso_ejecutando = None
        self.planificador.cola_ready.clear()
        self.planificador.cola_espera.clear()
        self.planificador.procesos_terminados.clear()
        self.planificador.gantt.clear()
        
        self.gantt_chart.color_assigner.reset()
        self.actualizar_interfaz()
    
    def limpiar_todo(self, instance):
        self.simulando = False
        if self.evento_simulacion:
            self.evento_simulacion.cancel()
        
        self.planificador.reset()
        self.gantt_chart.color_assigner.reset()
        self.actualizar_interfaz()
    
    def _with_info(self, widget, message):
        fl = FloatLayout(size_hint_x=widget.size_hint_x)
        widget.size_hint = (1, 1)
        fl.add_widget(widget)
        fl.add_widget(InfoIcon(message=message, size_hint=(None, None), size=(dp(16), dp(16)), pos_hint={'right': 1, 'top': 1}))
        return fl
    
    def actualizar_interfaz(self):
        # Actualizar tiempo actual
        self.label_tiempo.text = str(self.planificador.tiempo_actual)
        
        # Actualizar proceso ejecutando
        if self.planificador.proceso_ejecutando:
            self.label_ejecutando.text = f"P{self.planificador.proceso_ejecutando.pid}"
        else:
            self.label_ejecutando.text = "Ninguno"
        
        # Actualizar colas
        self.lista_ready.text = "\n".join([f"P{p.pid} (CPU:{p.tiempo_restante})" 
                                          for p in self.planificador.cola_ready])
        self.lista_espera.text = "\n".join([f"P{p.pid}" for p in self.planificador.cola_espera])
        self.lista_terminados.text = "\n".join([f"P{p.pid} (Fin:{p.tiempo_fin})" 
                                               for p in self.planificador.procesos_terminados])
        
        # Actualizar diagrama de Gantt
        self.gantt_chart.actualizar_gantt(self.planificador.gantt)
        
        # Actualizar lista de procesos
        self.actualizar_lista_procesos()
        
        
    def mostrar_error(self, mensaje):
        popup = Popup(title='Error',
                     content=Label(text=mensaje),
                     size_hint=(0.6, 0.3))
        popup.open()
    
    def mostrar_estadisticas_finales(self):
        if not self.planificador.estadisticas:
            self.planificador.calcular_estadisticas()
        stats = self.planificador.estadisticas
        contenido = BoxLayout(orientation='vertical', spacing=10)
        contenido.add_widget(Label(text=f"Procesos ejecutados: {stats['total_procesos']}"))
        contenido.add_widget(Label(text=f"Tiempo espera promedio: {stats['promedio_espera']:.2f}"))
        contenido.add_widget(Label(text=f"Tiempo retorno promedio: {stats['promedio_retorno']:.2f}"))
        contenido.add_widget(Label(text=f"Tiempo respuesta promedio: {stats['promedio_respuesta']:.2f}"))
        contenido.add_widget(Label(text=f"Uso de CPU: {stats['uso_cpu']*100:.1f}%"))
        btn_cerrar = Button(text='Cerrar', size_hint_y=None, height=dp(40))
        popup = Popup(title='Estadísticas Finales', content=contenido, size_hint=(0.7, 0.5))
        btn_cerrar.bind(on_press=popup.dismiss)
        contenido.add_widget(btn_cerrar)
        popup.open()
    
    def _fmt_bytes(self, b):
        u = ['B','KB','MB','GB','TB']
        v = float(b)
        i = 0
        while v >= 1024 and i < len(u) - 1:
            v /= 1024.0
            i += 1
        return f"{v:.1f} {u[i]}"

    def _get_cpu_times(self):
        class FILETIME(ctypes.Structure):
            _fields_ = [("dwLowDateTime", ctypes.c_uint32), ("dwHighDateTime", ctypes.c_uint32)]
        idle = FILETIME()
        kernel = FILETIME()
        user = FILETIME()
        ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user))
        def to_int(ft):
            return (ft.dwHighDateTime << 32) + ft.dwLowDateTime
        return to_int(idle), to_int(kernel), to_int(user)

    def _get_cpu_usage_percent(self):
        t = self._cpu_last_times
        idle, kernel, user = self._get_cpu_times()
        if t is None:
            self._cpu_last_times = (idle, kernel, user)
            return None
        last_idle, last_kernel, last_user = t
        idle_delta = idle - last_idle
        kernel_delta = kernel - last_kernel
        user_delta = user - last_user
        total = kernel_delta + user_delta
        busy = (kernel_delta - idle_delta) + user_delta
        self._cpu_last_times = (idle, kernel, user)
        if total <= 0:
            return None
        return max(0.0, min(100.0, (busy * 100.0) / total))

    def _get_cpu_speed(self):
        try:
            cmd = [
                "powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_Processor | Select-Object CurrentClockSpeed, MaxClockSpeed | ConvertTo-Json"
            ]
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=2)
            data = json.loads(out.decode('utf-8'))
            if isinstance(data, list) and data:
                cur = data[0].get('CurrentClockSpeed')
                mx = data[0].get('MaxClockSpeed')
            elif isinstance(data, dict):
                cur = data.get('CurrentClockSpeed')
                mx = data.get('MaxClockSpeed')
            else:
                return None, None
            if cur is None:
                return None, None
            return cur, mx
        except Exception:
            return None, None

    def _win_perf_info(self):
        class PERFORMANCE_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("CommitTotal", ctypes.c_size_t),
                ("CommitLimit", ctypes.c_size_t),
                ("CommitPeak", ctypes.c_size_t),
                ("PhysicalTotal", ctypes.c_size_t),
                ("PhysicalAvailable", ctypes.c_size_t),
                ("SystemCache", ctypes.c_size_t),
                ("KernelTotal", ctypes.c_size_t),
                ("KernelPaged", ctypes.c_size_t),
                ("KernelNonpaged", ctypes.c_size_t),
                ("PageSize", ctypes.c_size_t),
                ("HandleCount", ctypes.c_ulong),
                ("ProcessCount", ctypes.c_ulong),
                ("ThreadCount", ctypes.c_ulong),
            ]
        perf = PERFORMANCE_INFORMATION()
        perf.cb = ctypes.sizeof(PERFORMANCE_INFORMATION)
        ok = ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(perf), perf.cb)
        if not ok:
            return None
        return perf

    def actualizar_sistema_real(self, dt):
        pass

    def abrir_grafico_cpu(self, instance):
        popup = CpuGraphPopup(self)
        popup.open()

    def abrir_grafico_ram(self, instance):
        popup = RamGraphPopup(self)
        popup.open()

    def abrir_detalles_sistema(self, instance):
        popup = SystemDetailsPopup(self)
        popup.open()

class GraphWidget(Widget):
    def __init__(self, max_samples=120, max_value=100.0, **kwargs):
        super().__init__(**kwargs)
        self.max_samples = max_samples
        self.max_value = max_value
        self.samples = []
        self.bind(size=self.redraw, pos=self.redraw)

    def add_sample(self, value):
        self.samples.append(float(value))
        if len(self.samples) > self.max_samples:
            self.samples = self.samples[-self.max_samples:]
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.12, 0.12, 0.12, 1)
            Rectangle(pos=self.pos, size=self.size)
            if len(self.samples) > 1:
                Color(0.2, 0.7, 1.0, 1)
                w = float(self.width)
                h = float(self.height)
                n = len(self.samples)
                step = w / float(max(1, self.max_samples - 1))
                pts = []
                start = max(0, n - self.max_samples)
                for i, v in enumerate(self.samples[start:]):
                    x = self.x + i * step
                    y = self.y + max(0.0, min(h, (v / self.max_value) * h))
                    pts.extend([x, y])
                Line(points=pts, width=2)

class CpuGraphPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Gráfico CPU'
        self.size_hint = (0.8, 0.6)
        box = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.label_val = Label(text='CPU: -%')
        self.graph = GraphWidget(max_samples=180, max_value=100.0)
        btn_cerrar = Button(text='Cerrar', size_hint_y=None, height=dp(40))
        btn_cerrar.bind(on_press=self.dismiss)
        box.add_widget(self.label_val)
        box.add_widget(self.graph)
        box.add_widget(btn_cerrar)
        self.content = box
        self.app = app
        self._ev = Clock.schedule_interval(self._tick, 1.0)
        self.bind(on_dismiss=self._on_close)

    def _tick(self, dt):
        v = self.app._get_cpu_usage_percent()
        if v is None:
            return
        self.label_val.text = f'CPU: {v:.1f}%'
        self.graph.add_sample(v)

    def _on_close(self, *args):
        if self._ev:
            self._ev.cancel()

class RamGraphPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Gráfico RAM'
        self.size_hint = (0.8, 0.6)
        box = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.label_val = Label(text='RAM: -%')
        self.graph = GraphWidget(max_samples=180, max_value=100.0)
        btn_cerrar = Button(text='Cerrar', size_hint_y=None, height=dp(40))
        btn_cerrar.bind(on_press=self.dismiss)
        box.add_widget(self.label_val)
        box.add_widget(self.graph)
        box.add_widget(btn_cerrar)
        self.content = box
        self.app = app
        self._ev = Clock.schedule_interval(self._tick, 1.0)
        self.bind(on_dismiss=self._on_close)

    def _tick(self, dt):
        perf = self.app._win_perf_info()
        if not perf:
            return
        page = int(perf.PageSize)
        total = int(perf.PhysicalTotal) * page
        avail = int(perf.PhysicalAvailable) * page
        used = max(0, total - avail)
        if total <= 0:
            return
        pct = (used * 100.0) / float(total)
        self.label_val.text = f'RAM: {pct:.1f}%'
        self.graph.add_sample(pct)

    def _on_close(self, *args):
        if self._ev:
            self._ev.cancel()

class SystemDetailsPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Detalles del Sistema'
        self.size_hint = (0.9, 0.8)
        cont = BoxLayout(orientation='vertical', spacing=10, padding=10)
        grid_stats = GridLayout(cols=2, size_hint_y=None, height=dp(120))
        grid_stats.add_widget(Label(text='Tiempo espera promedio:'))
        self.l_espera = Label(text='-')
        grid_stats.add_widget(self.l_espera)
        grid_stats.add_widget(Label(text='Tiempo retorno promedio:'))
        self.l_retorno = Label(text='-')
        grid_stats.add_widget(self.l_retorno)
        grid_stats.add_widget(Label(text='Tiempo respuesta promedio:'))
        self.l_respuesta = Label(text='-')
        grid_stats.add_widget(self.l_respuesta)
        grid_stats.add_widget(Label(text='Uso CPU simulador:'))
        self.l_uso_cpu_sim = Label(text='-')
        grid_stats.add_widget(self.l_uso_cpu_sim)

        grid_mem_sim = GridLayout(cols=2, size_hint_y=None, height=dp(120))
        grid_mem_sim.add_widget(Label(text='RAM total (sim):'))
        self.l_ram_total_sim = Label(text='-')
        grid_mem_sim.add_widget(self.l_ram_total_sim)
        grid_mem_sim.add_widget(Label(text='RAM usada (sim):'))
        self.l_ram_usada_sim = Label(text='-')
        grid_mem_sim.add_widget(self.l_ram_usada_sim)
        grid_mem_sim.add_widget(Label(text='Swap usada (sim):'))
        self.l_swap_usada_sim = Label(text='-')
        grid_mem_sim.add_widget(self.l_swap_usada_sim)
        grid_mem_sim.add_widget(Label(text='Páginas en RAM (sim):'))
        self.l_paginas_ram_sim = Label(text='-')
        grid_mem_sim.add_widget(self.l_paginas_ram_sim)

        grid_sys = GridLayout(cols=2)
        grid_sys.add_widget(Label(text='Uso de CPU:'))
        self.l_cpu_uso = Label(text='-')
        grid_sys.add_widget(self.l_cpu_uso)
        grid_sys.add_widget(Label(text='Velocidad CPU:'))
        self.l_cpu_vel = Label(text='-')
        grid_sys.add_widget(self.l_proc)
        grid_sys.add_widget(Label(text='Subprocesos activos:'))
        self.l_threads = Label(text='-')
        grid_sys.add_widget(self.l_threads)
        grid_sys.add_widget(Label(text='RAM disponible:'))
        self.l_ram_disp = Label(text='-')
        grid_sys.add_widget(self.l_ram_disp)
        grid_sys.add_widget(Label(text='Memoria confirmada:'))
        self.l_mem_commit = Label(text='-')
        grid_sys.add_widget(self.l_mem_commit)
        grid_sys.add_widget(Label(text='Caché del sistema:'))
        self.l_cache = Label(text='-')
        grid_sys.add_widget(self.l_cache)
        grid_sys.add_widget(Label(text='Kernel paginado:'))
        self.l_kpag = Label(text='-')
        grid_sys.add_widget(self.l_kpag)
        grid_sys.add_widget(Label(text='Kernel no paginado:'))
        self.l_knp = Label(text='-')
        grid_sys.add_widget(self.l_knp)

        btn_cerrar = Button(text='Cerrar', size_hint_y=None, height=dp(40))
        btn_cerrar.bind(on_press=self.dismiss)
        cont.add_widget(grid_stats)
        cont.add_widget(grid_mem_sim)
        cont.add_widget(grid_sys)
        cont.add_widget(btn_cerrar)
        self.content = cont
        self.app = app
        self._ev = Clock.schedule_interval(self._tick, 1.0)
        self.bind(on_dismiss=self._on_close)

    def _tick(self, dt):
        stats = self.app.planificador.estadisticas
        if stats:
            self.l_espera.text = f"{stats['promedio_espera']:.2f}"
            self.l_retorno.text = f"{stats['promedio_retorno']:.2f}"
            self.l_respuesta.text = f"{stats['promedio_respuesta']:.2f}"
            self.l_uso_cpu_sim.text = f"{stats['uso_cpu']*100:.1f}%"
        try:
            if hasattr(self.app.planificador, 'kernel') and hasattr(self.app.planificador.kernel, 'memoria'):
                mem = self.app.planificador.kernel.memoria.stats()
                if 'total_ram' in mem:
                    self.l_ram_total_sim.text = f"{mem.get('total_ram', 0)}"
                    self.l_ram_usada_sim.text = f"{mem.get('ram_usada', 0)}"
                    self.l_swap_usada_sim.text = f"{mem.get('swap_usada', 0)}"
                    self.l_paginas_ram_sim.text = str(mem.get('paginas_en_ram', []))
                else:
                    self.l_ram_total_sim.text = str(mem.get('total_pages', '-'))
                    self.l_ram_usada_sim.text = str(mem.get('used_pages', '-'))
                    self.l_swap_usada_sim.text = str(mem.get('swap_pages', '-'))
                    self.l_paginas_ram_sim.text = str(mem.get('free_pages', '-'))
        except Exception:
            pass
        v = self.app._get_cpu_usage_percent()
        if v is not None:
            self.l_cpu_uso.text = f"{v:.1f}%"
        cur, mx = self.app._get_cpu_speed()
        if cur is not None:
            if mx:
                self.l_cpu_vel.text = f"{cur/1000:.2f} GHz / {mx/1000:.2f} GHz"
            else:
                self.l_cpu_vel.text = f"{cur/1000:.2f} GHz"
        perf = self.app._win_perf_info()
        if perf:
            page = int(perf.PageSize)
            disp = int(perf.PhysicalAvailable) * page
            commit = int(perf.CommitTotal) * page
            cache = int(perf.SystemCache) * page
            kpag = int(perf.KernelPaged) * page
            knp = int(perf.KernelNonpaged) * page
            self.l_proc.text = str(int(perf.ProcessCount))
            self.l_threads.text = str(int(perf.ThreadCount))
            self.l_ram_disp.text = self.app._fmt_bytes(disp)
            self.l_mem_commit.text = self.app._fmt_bytes(commit)
            self.l_cache.text = self.app._fmt_bytes(cache)
            self.l_kpag.text = self.app._fmt_bytes(kpag)
            self.l_knp.text = self.app._fmt_bytes(knp)

    def _on_close(self, *args):
        if self._ev:
            self._ev.cancel()

if __name__ == '__main__':
    PlanificadorApp().run()
