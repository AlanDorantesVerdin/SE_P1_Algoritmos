import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import textwrap

# ─── PALETA DE COLORES (Tema: Red de Agua) ─────────────────
BG        = '#0A1118'   # Azul marino nocturno
PANEL_BG  = '#111D2B'   # Panel asfalto
BORDER    = '#0EA5E9'   # Azul cielo (accento)
CYAN_MST  = '#22D3EE'   # Cyan brillante (Tubería PVC)
YELLOW    = '#FACC15'   # Amarillo (Tramos evaluados)
ORANGE    = '#FB923C'   # Naranja (Evaluación actual)
RED       = '#EF4444'   # Rojo (Bucle descartado)
GRAY_E    = '#1E3A4C'   # Gris tubería inactiva
WHITE     = '#F0F9FF'   # Texto principal
DIM       = '#64748B'   # Texto secundario
ISLANDS   = ['#7DD3FC', '#38BDF8', '#0EA5E9', '#0284C7', '#60E6E1', '#2DD4BF']


class KruskalTuberias:
    def __init__(self, graph):
        self.graph = graph
        self.steps = []
        self.current_step = 0
        self.short_labels = {n: str(i) for i, n in enumerate(graph.nodes())}

    def kruskal_with_steps(self):
        parent = {n: n for n in self.graph.nodes()}
        rank   = {n: 0 for n in self.graph.nodes()}

        def find(n):
            if parent[n] != n: parent[n] = find(parent[n])
            return parent[n]
        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb: return False
            if rank[ra] < rank[rb]: parent[ra] = rb
            elif rank[ra] > rank[rb]: parent[rb] = ra
            else: parent[rb] = ra; rank[ra] += 1
            return True

        sorted_edges = sorted([(d['weight'], u, v) for u, v, d in self.graph.edges(data=True)])
        mst_edges, total_weight = [], 0

        self.steps.append({'current_edge': None, 'mst_edges': [], 'total_weight': 0, 'parent': dict(parent),
                           'message': 'Bodega verificada. Tramos de PVC clasificados por longitud.'})

        for w, u, v in sorted_edges:
            self.steps.append({'current_edge': (u, v, w), 'mst_edges': mst_edges.copy(),
                'total_weight': total_weight, 'parent': dict(parent), 'message': f'Fase de evaluación en plano: {u} ↔ {v} ({w} m)'})
            
            if union(u, v):
                mst_edges.append((u, v, w))
                total_weight += w
                self.steps.append({'current_edge': (u, v, w), 'mst_edges': mst_edges.copy(),
                    'total_weight': total_weight, 'parent': dict(parent), 'accepted': True,
                    'message': f'Tramo {u} ─ {v} instalado satisfactoriamente. (+{w} m)'})
            else:
                self.steps.append({'current_edge': (u, v, w), 'mst_edges': mst_edges.copy(),
                    'total_weight': total_weight, 'parent': dict(parent), 'rejected': True,
                    'message': f'Tramo {u} ─ {v} ignorado (Zonas previamente enlazadas al acueducto).'})

        self.steps.append({'current_edge': None, 'mst_edges': mst_edges.copy(),
            'total_weight': total_weight, 'parent': dict(parent), 'final_mst': True,
            'message': 'Plano de obra hídrica certificado. Sistema distribuido correctamente.'})

    def visualize(self):
        self.kruskal_with_steps()
        plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
        self.fig = plt.figure(figsize=(18, 10), facecolor=BG)
        self.gs  = self.fig.add_gridspec(1, 2, width_ratios=[2.2, 1], left=0.03, right=0.97, top=0.92, bottom=0.04, wspace=0.05)
        self.ax_g = self.fig.add_subplot(self.gs[0]); self.ax_p = self.fig.add_subplot(self.gs[1])
        
        self.fig.suptitle('RED ACUEDUCTOS PVC (KRUSKAL)', fontsize=18, fontweight='bold', color=WHITE, x=0.5, y=0.97, ha='center')
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

        pm = step['parent']
        def get_root(n):
            r = n
            while pm.get(r, r) != r: r = pm[r]
            return r

        roots = {}
        for node in self.graph.nodes():
            r = get_root(node)
            if r not in roots: roots[r] = ISLANDS[len(roots) % len(ISLANDS)]

        # ── SEPARACIÓN DE ARISTAS (GLOW EFECTO FLUIDO DE AGUA) ──
        normal_edges = []
        glow_cyan_edges = []
        glow_cyan_thick = []
        glow_orange_edges = []
        glow_red_edges = []

        for edge in self.graph.edges():
            a, b = edge
            in_mst = any((a == m[0] and b == m[1]) or (a == m[1] and b == m[0]) for m in step['mst_edges'])
            ce = step.get('current_edge')
            is_cur = ce and set(edge) == {ce[0], ce[1]}

            if in_mst and not is_cur: glow_cyan_edges.append(edge)
            elif is_cur and step.get('accepted'): glow_cyan_thick.append(edge)
            elif is_cur and step.get('rejected'): glow_red_edges.append(edge)
            elif is_cur: glow_orange_edges.append(edge)
            else: normal_edges.append(edge)

        # 1. Halo Glow Fluido Transparente (Efecto Agua/Presión)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_cyan_edges, ax=self.ax_g, width=14, edge_color=CYAN_MST, alpha=0.15)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_cyan_thick, ax=self.ax_g, width=18, edge_color=CYAN_MST, alpha=0.25)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_orange_edges, ax=self.ax_g, width=12, edge_color=ORANGE, alpha=0.2)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_red_edges, ax=self.ax_g, width=12, edge_color=RED, alpha=0.15)
        
        # 2. Línea Sólida Primaria (La tubería central)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_cyan_edges, ax=self.ax_g, width=4.5, edge_color=CYAN_MST, alpha=1.0)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_cyan_thick, ax=self.ax_g, width=6.0, edge_color=CYAN_MST, alpha=1.0)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_orange_edges, ax=self.ax_g, width=3.5, edge_color=ORANGE, alpha=0.9, style='dashed')
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=glow_red_edges, ax=self.ax_g, width=3.5, edge_color=RED, alpha=0.9)
        nx.draw_networkx_edges(self.graph, self.pos, edgelist=normal_edges, ax=self.ax_g, width=1.5, edge_color=GRAY_E, alpha=0.5)

        # ── SEPARACIÓN DE NODOS (PUNTOS DE BOMBEO / REGISTROS) ──
        ce = step.get('current_edge')
        for node in self.graph.nodes():
            x, y = self.pos[node]
            checked = ce and node in [ce[0], ce[1]]
            
            if step.get('final_mst'): c, bg = CYAN_MST, CYAN_MST; s = 700
            elif checked: c, bg = ORANGE, YELLOW; s = 800
            else: c, bg = roots[get_root(node)], GRAY_E; s = 500

            # Halo de presión en nodo
            if step.get('final_mst') or checked:
                self.ax_g.scatter(x, y, s=s*4, color=c, alpha=0.15, zorder=1, edgecolors='none')

            # Render de la llave central
            self.ax_g.scatter(x, y, s=s, color=bg, zorder=2, edgecolors=c, linewidths=2.5)
            self.ax_g.text(x, y, self.short_labels[node], color=BG if checked else WHITE, fontsize=10, fontweight='bold', ha='center', va='center', zorder=3)
            
            # Nombre exterior en placa azul marina
            self.ax_g.text(x, y - 0.05, node, ha='center', va='top', fontsize=9, color=WHITE,
                           bbox=dict(boxstyle='round,pad=0.25', facecolor=PANEL_BG, edgecolor=c, linewidth=1, alpha=0.9), zorder=4)

        # ── ETIQUETAS DE METRAJE DE TUBERÍA ──
        edge_labels = {(u, v): f"{d['weight']} m" for u, v, d in self.graph.edges(data=True)}
        nx.draw_networkx_edge_labels(self.graph, self.pos, edge_labels=edge_labels, ax=self.ax_g,
                                     font_size=8, font_color=WHITE,
                                     bbox=dict(boxstyle='round,pad=0.2', facecolor=BG, edgecolor=GRAY_E, alpha=0.85))

        self._draw_panel(step)
        self.fig.canvas.draw_idle()

    def _draw_panel(self, step):
        ax = self.ax_p
        # Cuadro Arquitectónico
        ax.add_patch(mpatches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle='round,pad=0.01',
            linewidth=2, edgecolor=BORDER, facecolor=PANEL_BG, alpha=0.9))

        y = 0.94; x_m = 0.08
        
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
            y -= 0.0025

        def draw_badge(text, color_bg, color_fg=BG):
            nonlocal y
            ax.text(0.5, y - 0.02, text, color=color_fg, fontsize=11, fontweight='bold', ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=color_bg, edgecolor='none', alpha=0.95))
            y -= 0.06

        # --- OBJETIVO ---
        draw_head('PLANO MAESTRO DE AGUA')
        draw_text("Protocolo: Algoritmo de Kruskal (Árbol de Expansión Mínimo)\nMisión: Optimizar costos calculando la red hidráulica con la menor cantidad de tubería PVC empleada.", DIM, size=9)
        y -= 0.03
        
        # --- ESTADO DE SIMULACIÓN ---
        draw_head('BITÁCORA DE CONTROL')
        draw_badge(f"PASO {self.current_step + 1} / {len(self.steps)}", BORDER, WHITE)
        y -= 0.01
        draw_text(step['message'], WHITE, bold=True)
        y -= 0.03

        # --- METRAJE / MATERIALES ---
        draw_head('MATERIALES ADQUIRIDOS (PVC)')
        if step.get('final_mst'): draw_badge(f"METRAJE TOTAL: {step['total_weight']} M = COMPLETO", CYAN_MST, BG)
        else: draw_badge(f"METRAJE ACUMULADO: {step['total_weight']} M", YELLOW, BG)
        
        tramos = len(step['mst_edges'])
        y -= 0.01
        draw_text(f"► Tramos ensamblados: {tramos}", WHITE)
        y -= 0.03

        # --- LEYENDA VISUAL ---
        draw_head('SISTEMA HIDRÁULICO')
        items = [
            ('━', CYAN_MST, 'Tubería unificada principal'),
            ('━', ORANGE,   'Medición y excavación actual'),
            ('━', RED,      'Redundante/Se ignora el tramo'),
            ('●', CYAN_MST, 'Registro hídrico operando'),
            ('●', ORANGE,   'Inspección focalizada'),
        ]
        
        for sym, col, txt in items:
            ax.text(x_m, y, sym, color=col, fontsize=14, va='center', fontweight='bold')
            ax.text(x_m + 0.08, y, txt, color=DIM, fontsize=9.5, va='center')
            y -= 0.035

        # Controles
        ax.text(0.5, 0.04, "[→] Aprobar Siguiente Tramo    [Q] Cerrar Planos", color=DIM, fontsize=9, ha='center', va='center', fontweight='bold')

    def on_key(self, event):
        if event.key == 'right' and self.current_step < len(self.steps) - 1: self.current_step += 1; self.draw_step()
        elif event.key == 'q': plt.close()

if __name__ == '__main__':
    G = nx.Graph()
    edges = [('Fregadero','Lavadora',4),('Fregadero','Inodoro Principal',12),('Lavadora','Inodoro Principal',10),
             ('Lavadora','Ducha Principal',15),('Inodoro Principal','Ducha Principal',3),('Inodoro Principal','Registro Central',14),
             ('Ducha Principal','Registro Central',16),('Baño Medio','Registro Central',8),('Baño Medio','Conexión Exterior',18),
             ('Registro Central','Conexión Exterior',22)]
    for u, v, w in edges: G.add_edge(u, v, weight=w)
    print("Controles:\n  -> (flecha derecha): Avanzar al siguiente paso\n  q: Cerrar visualización")
    KruskalTuberias(G).visualize()
