import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import heapq
import textwrap

# ─── PALETA DE COLORES (Tema: GPS / Dark Mode Map) ────────────────────────────
BG        = '#1E1E2E'   # Fondo asfalto asfalto / Catppuccin Mocha
PANEL_BG  = '#181825'   # Contenedor modo noche
BORDER    = '#89B4FA'   # Azul GPS
ROUTE_C   = '#89B4FA'   # Azul neón (Ruta maestra)
START_C   = '#A6E3A1'   # Verde (Partida)
END_C     = '#F38BA8'   # Rojo (Llegada)
VISITED_C = '#CBA6F7'   # Morado pastel (Calles exploradas)
EVAL_C    = '#F9E2AF'   # Amarillo (Calculando tráfico)
GRAY_E    = '#45475A'   # Gris calle paralela
WHITE     = '#CDD6F4'   # Texto principal
DIM       = '#A6ADC8'   # Texto desvanecido


class DijkstraTrafico:
    def __init__(self, graph, start, end):
        self.graph = graph
        self.start = start
        self.end = end
        self.steps = []
        self.current_step = 0
        self.short_labels = {n: str(i) for i, n in enumerate(graph.nodes())}

    def dijkstra_with_steps(self):
        dist = {n: float('inf') for n in self.graph.nodes()}; dist[self.start] = 0
        prev = {n: None for n in self.graph.nodes()}
        pq = [(0, self.start)]; visited = set()

        self.steps.append({'current': None, 'visited': set(), 'distances': dict(dist), 'previous': dict(prev),
                           'message': f'Estableciendo enlace GPS desde {self.start} hacia {self.end}. Buscando mejor ruta...'})

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited: continue
            visited.add(u)
            self.steps.append({'current': u, 'visited': visited.copy(), 'distances': dict(dist), 'previous': dict(prev),
                                'message': f'Punto de control: {u} (Tiempo de manejo local: {d} min)'})
            if u == self.end: break
            
            for v in self.graph.neighbors(u):
                if v in visited: continue
                w, nd = self.graph[u][v]['weight'], d + self.graph[u][v]['weight']
                
                if nd < dist[v]:
                    dist[v], prev[v] = nd, u
                    heapq.heappush(pq, (nd, v))
                    self.steps.append({'current': u, 'visited': visited.copy(), 'distances': dict(dist), 'previous': dict(prev),
                                        'edge_highlight': (u, v),
                                        'message': f'Tráfico de {u} ➡ {v}... Estimando un total de {nd} minutos desde el origen.'})

        path, node = [], self.end
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()

        self.steps.append({'current': None, 'visited': visited.copy(), 'distances': dict(dist), 'previous': dict(prev),
                            'final_path': path, 'message': f'Algoritmo completado. Diríjase por la ruta resaltada. Llegará en {dist[self.end]} minutos sin tráfico severo.'})

    def visualize(self):
        self.dijkstra_with_steps()
        plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
        self.fig = plt.figure(figsize=(18, 10), facecolor=BG)
        self.gs  = self.fig.add_gridspec(1, 2, width_ratios=[2.2, 1], left=0.03, right=0.97, top=0.92, bottom=0.04, wspace=0.05)
        self.ax_g = self.fig.add_subplot(self.gs[0]); self.ax_p = self.fig.add_subplot(self.gs[1])
        
        self.fig.suptitle('SISTEMA DE NAVEGACIÓN SATELITAL (DIJKSTRA)', fontsize=18, fontweight='bold', color=WHITE, x=0.5, y=0.97, ha='center')
        self.pos = nx.spring_layout(self.graph, seed=42, k=3.5, iterations=100)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.draw_step()
        plt.show()

    def draw_step(self):
        self.ax_g.clear(); self.ax_p.clear()
        self.ax_g.set_facecolor(BG); self.ax_p.set_facecolor(PANEL_BG)
        self.ax_p.set_xlim(0, 1); self.ax_p.set_ylim(0, 1)
        self.ax_p.axis('off'); self.ax_g.axis('off')

        if self.current_step >= len(self.steps): self.current_step = len(self.steps) - 1
        step = self.steps[self.current_step]

        # ── MAPA / Trazado Glow GPS ──
        normal, eval_e, path_e = [], [], []
        fp = step.get('final_path', [])
        
        for edge in self.graph.edges():
            a, b = edge
            on_path  = any((fp[i] == a and fp[i+1] == b) or (fp[i] == b and fp[i+1] == a) for i in range(len(fp)-1))
            is_eval  = 'edge_highlight' in step and set(edge) == set(step['edge_highlight'])

            if on_path: path_e.append(edge)
            elif is_eval: eval_e.append(edge)
            else: normal.append(edge)

        # 1. Glow y contorno
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=path_e, ax=self.ax_g, width=15, edge_color=ROUTE_C, alpha=0.15)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=path_e, ax=self.ax_g, width=22, edge_color=ROUTE_C, alpha=0.08)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=eval_e, ax=self.ax_g, width=12, edge_color=EVAL_C, alpha=0.20)
        
        # 2. Rutas sólidas
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=path_e, ax=self.ax_g, width=5.5, edge_color=ROUTE_C, alpha=1.0)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=eval_e, ax=self.ax_g, width=3.5, edge_color=EVAL_C, alpha=1.0)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=normal, ax=self.ax_g, width=1.5, edge_color=GRAY_E, alpha=0.7)

        # ── UBICACIONES (Puntos de ancla en el mapa) ──
        for node in self.graph.nodes():
            x, y = self.pos[node]
            on_f = fp and node in fp
            is_s = (node == self.start); is_e = (node == self.end)
            is_c = (step['current'] == node); is_v = (node in step['visited'])
            
            # Determinando prioridades visuales
            if is_s: c, bg, s = START_C, START_C, 800
            elif is_e: c, bg, s = END_C, END_C, 800
            elif on_f: c, bg, s = ROUTE_C, ROUTE_C, 600
            elif is_c: c, bg, s = EVAL_C, EVAL_C, 750
            elif is_v: c, bg, s = VISITED_C, PANEL_BG, 500
            else: c, bg, s = GRAY_E, GRAY_E, 400

            # Halo luminoso en marcadores GPS importantes
            if is_s or is_e or (is_c and not on_f):
                self.ax_g.scatter(x, y, s=s*4, color=c, alpha=0.15, zorder=1, edgecolors='none')

            self.ax_g.scatter(x, y, s=s, color=bg, zorder=2, edgecolors=c, linewidths=2.5)
            self.ax_g.text(x, y, self.short_labels[node], color=BG if bg != PANEL_BG else WHITE, fontsize=10, fontweight='bold', ha='center', va='center', zorder=3)
            
            # Nombres (Etiquetas tipo Maps)
            self.ax_g.text(x, y - 0.12, node, ha='center', va='top', fontsize=9, color=WHITE,
                           bbox=dict(boxstyle='round,pad=0.25', facecolor=PANEL_BG, edgecolor=c, linewidth=1, alpha=0.9), zorder=4)

        edge_labels = {(u, v): f"{d['weight']} min" for u, v, d in self.graph.edges(data=True)}
        nx.draw_networkx_edge_labels(self.graph, self.pos, edge_labels=edge_labels, ax=self.ax_g, font_size=8, font_color=WHITE,
                                     bbox=dict(boxstyle='round,pad=0.2', facecolor=BG, edgecolor=GRAY_E, alpha=0.85))

        self._draw_panel(step)
        self.fig.canvas.draw_idle()

    def _draw_panel(self, step):
        ax = self.ax_p
        ax.add_patch(mpatches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle='round,pad=0.01',
            linewidth=2, edgecolor=BORDER, facecolor=PANEL_BG, alpha=0.9))

        y, x_m = 0.94, 0.08
        
        def draw_head(text):
            nonlocal y
            ax.text(x_m, y, text, color=BORDER, fontsize=11, fontweight='black', va='top')
            y -= 0.025
            ax.axhline(y, xmin=0.06, xmax=0.94, color=BORDER, alpha=0.4, linewidth=1)
            y -= 0.04

        def draw_text(text, color=WHITE, bold=False, size=9.5):
            nonlocal y
            for ln in textwrap.wrap(text, width=38):
                ax.text(x_m, y, ln, color=color, fontsize=size, va='top', fontweight='bold' if bold else 'normal')
                y -= 0.032
            y -= 0.01

        def draw_badge(text, color_bg, color_fg=BG):
            nonlocal y
            ax.text(0.5, y - 0.02, text, color=color_fg, fontsize=11, fontweight='bold', ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=color_bg, edgecolor='none', alpha=0.95))
            y -= 0.08

        # --- NAVEGACIÓN ---
        draw_head('RUTA PROGRAMADA')
        draw_text(f"■ LEYENDA ORIGEN: {self.start}", START_C, bold=True)
        draw_text(f"■ PUNTO LLEGADA: {self.end}", END_C, bold=True)
        y -= 0.01
        
        # --- ORDENADOR Y TRÁFICO ---
        draw_head('PANEL DE CONDUCCIÓN')
        draw_badge(f"KILÓMETRO ACTUAL: PASO {self.current_step + 1} DE {len(self.steps)}", BORDER, WHITE)
        draw_text(step['message'], WHITE, bold=True)
        y -= 0.02

        # --- TIEMPO ---
        draw_head('TIEMPO AL DESTINO ETA')
        cur = step['current']
        if step.get('final_path'): draw_badge(f"HORA ESTIMADA: EN {step['distances'][self.end]} MIN", START_C, BG)
        elif cur: draw_badge(f"A {step['distances'][cur]} MIN DE LA POSICIÓN", EVAL_C, BG)
        else: draw_badge('CALCULANDO RUTAS...', GRAY_E, WHITE)
        y -= 0.02

        # --- LEYENDA MAPA ---
        draw_head('REFERENCIAS MAPA')
        items = [
            ('━', ROUTE_C, 'Ruta Expresa Garantizada'),
            ('━', EVAL_C,  'Cálculo de Trafico Alterno'),
            ('●', START_C, 'Punto cero de Partida'),
            ('●', END_C,   'Bandera a Cuadros (Meta)'),
        ]
        
        for sym, col, txt in items:
            ax.text(x_m, y, sym, color=col, fontsize=14, va='center', fontweight='bold')
            ax.text(x_m + 0.08, y, txt, color=DIM, fontsize=9.5, va='center')
            y -= 0.04

        ax.text(0.5, 0.04, "[→] Conducir un Tramo    [Q] Apagar Motor GPS", color=DIM, fontsize=9, ha='center', va='center', fontweight='bold')

    def on_key(self, event):
        if event.key == 'right' and self.current_step < len(self.steps) - 1: self.current_step += 1; self.draw_step()
        elif event.key == 'q': plt.close()


if __name__ == '__main__':
    G = nx.Graph()
    edges = [('Casa','Parque',5),('Casa','Taller',12),('Parque','Taller',8),('Parque','Centro',15),
             ('Taller','Centro',10),('Taller','Escuela',20),('Centro','Escuela',6),('Centro','Gimnasio',18),
             ('Escuela','Gimnasio',5),('Escuela','Trabajo',25),('Gimnasio','Trabajo',12)]
    for u, v, w in edges: G.add_edge(u, v, weight=w)
    print("Controles:\n  -> (flecha derecha): Avanzar al siguiente paso\n  q: Cerrar visualización")
    DijkstraTrafico(G, start='Casa', end='Trabajo').visualize()
