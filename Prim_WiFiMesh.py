import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import heapq
import textwrap

# ─── PALETA DE COLORES (Tema: Ciberespacio / Red de Señal) ───────────────────
BG        = '#0D1117'   # Fondo principal oscuro
PANEL_BG  = '#161B22'   # Fondo del panel
BORDER    = '#2F81F7'   # Azul eléctrico claro
GREEN_N   = '#3EE1A1'   # Verde neón (Mesh activo)
YELLOW    = '#F2CC60'   # Amarillo (Evaluando)
PINK      = '#FF7B72'   # Rosa/Rojo coral (Descartado/Error)
GRAY_E    = '#30363D'   # Arista inactiva
GRAY_N    = '#21262D'   # Nodo inactivo
WHITE     = '#E6EDF3'   # Texto principal
DIM       = '#8B949E'   # Texto secundario
ROUTER_C  = '#A371F7'   # Violeta brillante (Router)
ACTIVE_C  = '#2F81F7'   # Azul brillante (Conectado)

class PrimWiFiMesh:
    def __init__(self, graph, start):
        self.graph = graph
        self.start = start
        self.steps = []
        self.current_step = 0
        self.short_labels = {n: str(i) for i, n in enumerate(graph.nodes())}
        self.idx_to_name = {v: k for k, v in self.short_labels.items()}

    def prim_with_steps(self):
        visited, mst_edges, total_weight, pq = set(), [], 0, []
        visited.add(self.start)
        for nb in self.graph.neighbors(self.start):
            w = self.graph[self.start][nb]['weight']
            heapq.heappush(pq, (w, self.start, nb))

        self.steps.append({'visited': visited.copy(), 'mst_edges': [],
                           'total_weight': 0, 'current': self.start,
                           'message': f'Arrancando sistema desde el nodo matriz: {self.start}'})

        while pq and len(visited) < len(self.graph.nodes()):
            w, frm, to = heapq.heappop(pq)
            if to in visited:
                self.steps.append({'visited': visited.copy(), 'mst_edges': mst_edges.copy(),
                                   'total_weight': total_weight, 'current': frm,
                                   'rejected_edge': (frm, to),
                                   'message': f'Se detecta bucle ineficiente hacia {to}. Descartando enlace.'})
                continue
            visited.add(to)
            mst_edges.append((frm, to, w))
            total_weight += w
            self.steps.append({'visited': visited.copy(), 'mst_edges': mst_edges.copy(),
                                'total_weight': total_weight, 'current': to,
                                'new_edge': (frm, to),
                                'message': f'Enlace exitoso. {to} ahora es parte de la red Mesh (-{w} dB)'})
            for nb in self.graph.neighbors(to):
                if nb not in visited:
                    ew = self.graph[to][nb]['weight']
                    heapq.heappush(pq, (ew, to, nb))
                    self.steps.append({'visited': visited.copy(), 'mst_edges': mst_edges.copy(),
                                       'total_weight': total_weight, 'current': to,
                                       'exploring_edge': (to, nb),
                                       'message': f'Midiendo intensidad de señal desde {to} hasta {nb}...'})

        self.steps.append({'visited': visited.copy(), 'mst_edges': mst_edges.copy(),
                           'total_weight': total_weight, 'current': None,
                           'final_mst': True,
                           'message': 'Inicialización perimetral completada. La red Wi-Fi Mesh opera a máxima eficiencia.'})
        return mst_edges, total_weight

    def visualize(self):
        self.prim_with_steps()
        plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
        self.fig = plt.figure(figsize=(18, 10), facecolor=BG)
        self.gs  = self.fig.add_gridspec(1, 2, width_ratios=[2.2, 1],
                                          left=0.03, right=0.97,
                                          top=0.92, bottom=0.04, wspace=0.05)
        self.ax_g = self.fig.add_subplot(self.gs[0])
        self.ax_p = self.fig.add_subplot(self.gs[1])
        
        # Glow Effect Title (Sin emoticones)
        self.fig.suptitle('RED WI-FI MESH MULTINODO (PRIM)',
                           fontsize=18, fontweight='bold', color=WHITE,
                           x=0.5, y=0.97, ha='center')
        
        self.pos = nx.spring_layout(self.graph, seed=42, k=3.5, iterations=100)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.draw_step()
        plt.show()

    def draw_step(self):
        self.ax_g.clear(); self.ax_p.clear()
        self.ax_g.set_facecolor(BG); self.ax_p.set_facecolor(PANEL_BG)
        self.ax_p.set_xlim(0, 1); self.ax_p.set_ylim(0, 1)
        self.ax_p.axis('off'); self.ax_g.axis('off')

        if self.current_step >= len(self.steps):
            self.current_step = len(self.steps) - 1
        step = self.steps[self.current_step]

        # ── SEPARACIÓN DE ARISTAS PARA LOGRAR EFECTO GLOW (NEÓN) ──
        normal_edges = []
        glow_green_edges = []
        glow_yellow_edges = []
        glow_pink_edges = []
        glow_red_edges = []

        for edge in self.graph.edges():
            a, b = edge
            in_mst = any((a == m[0] and b == m[1]) or (a == m[1] and b == m[0]) for m in step['mst_edges'])
            is_new = 'new_edge' in step and set(edge) == set(step['new_edge'])
            is_exp = 'exploring_edge' in step and set(edge) == set(step['exploring_edge'])
            is_rej = 'rejected_edge' in step and set(edge) == set(step['rejected_edge'])

            if in_mst and not is_new:
                glow_green_edges.append(edge)
            elif is_new:
                glow_yellow_edges.append(edge)
            elif is_exp:
                glow_pink_edges.append(edge)
            elif is_rej:
                glow_red_edges.append(edge)
            else:
                normal_edges.append(edge)

        # 1. Dibujar el fondo "Halo" difuminado para el neón
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_green_edges, ax=self.ax_g, width=12, edge_color=GREEN_N, alpha=0.15)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_yellow_edges, ax=self.ax_g, width=14, edge_color=YELLOW, alpha=0.20)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_pink_edges, ax=self.ax_g, width=10, edge_color=YELLOW, alpha=0.10)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_red_edges, ax=self.ax_g, width=10, edge_color=PINK, alpha=0.15)
        
        # 2. Dibujar la línea sólida principal
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_green_edges, ax=self.ax_g, width=3.5, edge_color=GREEN_N, alpha=1.0)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_yellow_edges, ax=self.ax_g, width=4.5, edge_color=YELLOW, alpha=1.0)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_pink_edges, ax=self.ax_g, width=2.5, edge_color=YELLOW, alpha=0.7, style='dashed')
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_red_edges, ax=self.ax_g, width=2.5, edge_color=PINK, alpha=0.8)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=normal_edges, ax=self.ax_g, width=1.0, edge_color=GRAY_E, alpha=0.6)

        # ── SEPARACIÓN DE NODOS PARA EFECTO GLOW ──
        for node in self.graph.nodes():
            x, y = self.pos[node]
            is_start = (node == self.start)
            is_cur   = (step['current'] == node)
            is_vis   = (node in step['visited'])

            if is_start:   
                c, bg = ROUTER_C, ROUTER_C; s = 800
            elif is_cur:   
                c, bg = YELLOW, YELLOW; s = 700
            elif is_vis:   
                c, bg = GREEN_N, ACTIVE_C; s = 500
            else:          
                c, bg = GRAY_N, GRAY_E; s = 400

            # Halo del nodo
            if is_start or is_cur or is_vis:
                self.ax_g.scatter(x, y, s=s*3.5, color=c, alpha=0.15, zorder=1, edgecolors='none')

            # Centro del nodo
            self.ax_g.scatter(x, y, s=s, color=bg, zorder=2, edgecolors=c, linewidths=2.5 if (is_start or is_cur) else 1.5)
            
            # Número interior
            self.ax_g.text(x, y, self.short_labels[node], color=BG if is_cur else WHITE, 
                           fontsize=10, fontweight='bold', ha='center', va='center', zorder=3)
            
            # Nombre exterior en una cápsula estilizada. Se redujo el espaciado y a -0.075
            self.ax_g.text(x, y - 0.075, node, ha='center', va='top', fontsize=9, color=WHITE, fontweight='bold' if is_start else 'normal',
                           bbox=dict(boxstyle='round,pad=0.25', facecolor=PANEL_BG, edgecolor=c, linewidth=1, alpha=0.9), zorder=4)

        # ── ETIQUETAS DE PESO DE ARISTAS CON ESTILO REDUCIDO ──
        edge_labels = {(u, v): f"{d['weight']} dB" for u, v, d in self.graph.edges(data=True)}
        nx.draw_networkx_edge_labels(self.graph, self.pos, edge_labels=edge_labels, ax=self.ax_g,
                                     font_size=8, font_color=WHITE,
                                     bbox=dict(boxstyle='round,pad=0.2', facecolor=BG, edgecolor=GRAY_E, alpha=0.85))

        self._draw_panel(step)
        self.fig.canvas.draw_idle()

    def _draw_panel(self, step):
        ax = self.ax_p
        
        # Marco exterior del panel
        ax.add_patch(mpatches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle='round,pad=0.01',
            linewidth=2, edgecolor=BORDER, facecolor=PANEL_BG, alpha=0.8))

        y = 0.94 # Cursor vertical
        x_m = 0.08 # Margen izquierdo
        
        def draw_head(text):
            nonlocal y
            ax.text(x_m, y, text, color=BORDER, fontsize=11, fontweight='black', va='top')
            y -= 0.025
            ax.axhline(y, xmin=0.06, xmax=0.94, color=BORDER, alpha=0.4, linewidth=1)
            y -= 0.035

        def draw_text(text, color=WHITE, bold=False, size=9.5):
            nonlocal y
            lines = textwrap.wrap(text, width=38)
            for ln in lines:
                ax.text(x_m, y, ln, color=color, fontsize=size, va='top', fontweight='bold' if bold else 'normal')
                y -= 0.027
            y -= 0.005

        def draw_badge(text, color_bg, color_fg=BG):
            nonlocal y
            ax.text(0.5, y - 0.02, text, color=color_fg, fontsize=11, fontweight='bold', ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=color_bg, edgecolor='none', alpha=0.95))
            y -= 0.065

        # --- OBJETIVO ---
        draw_head('SINOPSIS DEL SISTEMA')
        draw_text("Operativo: Algoritmo de Prim\nObjetivo: Enlazar nodos buscando el vector con menor pérdida electromagnética acumulada.", DIM, size=9)
        y -= 0.03
        
        # --- ESTADO DE SIMULACIÓN ---
        draw_head('TELEMETRÍA EN TIEMPO REAL')
        draw_badge(f"PASO {self.current_step + 1} / {len(self.steps)}", BORDER, WHITE)
        draw_text(step['message'], WHITE, bold=True)
        y -= 0.03

        # --- MÉTRICAS ---
        draw_head('MÉTRICAS ACUMULATIVAS')
        if step.get('final_mst'):
            draw_badge(f"SEÑAL PÉRDIDA: {step['total_weight']} dB", GREEN_N, BG)
        else:
            draw_badge(f"SEÑAL PÉRDIDA: {step['total_weight']} dB", YELLOW, BG)
        
        enlaces = len(step['mst_edges']); nodos = len(step['visited'])
        draw_text(f"► Nodos enlazados: {nodos} de {len(self.graph.nodes())}", WHITE)
        draw_text(f"► Ramas generadas: {enlaces}", WHITE)
        y -= 0.03

        # --- LEYENDA VISUAL ---
        draw_head('CLASIFICACIÓN VISUAL')
        items = [
            ('●', ROUTER_C, 'Origen de la red'),
            ('●', GREEN_N,  'Nodo enlazado con éxito'),
            ('━', GREEN_N,  'Señal anclada y verificada'),
            ('━', YELLOW,   'Proyectando enlace futuro'),
            ('━', PINK,     'Conexión descartada / Bucle')
        ]
        
        for sym, col, txt in items:
            ax.text(x_m, y, sym, color=col, fontsize=14, va='center', fontweight='bold')
            ax.text(x_m + 0.08, y, txt, color=DIM, fontsize=9.5, va='center')
            y -= 0.035

        # Controles
        ax.text(0.5, 0.04, "[→] Siguiente Fase    [Q] Abortar Misión",
                color=DIM, fontsize=9, ha='center', va='center', fontweight='bold')

    def on_key(self, event):
        if event.key == 'right' and self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.draw_step()
        elif event.key == 'q':
            plt.close()

if __name__ == '__main__':
    G = nx.Graph()
    edges = [('Router Principal','Sala',12),('Router Principal','Cocina',25),('Sala','Cocina',30),
             ('Sala','Baño Visitas',15),('Cocina','Baño Visitas',10),('Cocina','Jardín',40),
             ('Baño Visitas','Jardín',35),('Baño Visitas','Recámara 1',20),('Recámara 1','Recámara General',18),
             ('Recámara General','Patio Trasero',22),('Jardín','Patio Trasero',28)]
    for u, v, w in edges: G.add_edge(u, v, weight=w)
    print("Controles:\n  -> (flecha derecha): Avanzar al siguiente paso\n  q: Cerrar visualización")
    PrimWiFiMesh(G, start='Router Principal').visualize()
