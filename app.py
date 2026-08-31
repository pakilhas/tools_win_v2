import sys
import os
os.makedirs(r'C:\ProgramData\ToolsWin', exist_ok=True)
import ctypes

def get_resource_path(relative_path):
    import sys, os
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

import subprocess
import threading
import json
import inventory_module
import tkinter as tk
import sv_ttk
from tkinter import ttk, messagebox, simpledialog
import psutil

# Cores do Tema (Glary Utilities Palette)
COLOR_BG = "#1c1c1c"           # Honeydew
COLOR_SIDEBAR = "#1c1c1c"      # Oxford Navy
COLOR_CARD = "#2d2d2d"         # White for contrast
COLOR_TEXT = "#ffffff"         # Dark Navy text for readability
COLOR_SIDEBAR_TEXT = "#ffffff" # Light text for sidebar
COLOR_MUTED = "#457b9d"        # Cerulean
COLOR_ACCENT = "#457b9d"       # Cerulean
COLOR_SUCCESS = "#a8dadc"      # Frosted Blue / Esmeralda fallback
COLOR_WARNING = "#f59e0b"      # Mantém
COLOR_DANGER = "#e63946"       # Punch Red
COLOR_BTN_HOVER = "#a8dadc"    # Frosted Blue
COLOR_BTN_BG = "#457b9d"       # Cerulean

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WindowsOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tools Win V2")
        self.root.geometry("1000x650")
        self.root.resizable(True, True)

        # Configurar ícone da janela
        try:
            from PIL import Image, ImageTk
            logo_path = resource_path("favicon.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                self.win_icon = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self.win_icon)
        except Exception as e:
            print(f"Erro ao carregar ícone da janela: {e}")

        # Configurar estilos do TTK
                # Estilos removidos para usar sv_ttk nativamente
        self.running_thread = None
        self.admin_group_name = None

        # Detectar nome do grupo de administradores (idioma-independente)
        self.detect_admin_group_name()

        # Layout Principal
        sv_ttk.set_theme('dark')
        self.create_layout()

        # Iniciar monitoramento de recursos
        self.update_system_stats()

        # Iniciar verificação de IA de saúde após 3 segundos
        self.root.after(3000, self.start_ai_health_check)

    def detect_admin_group_name(self):
        try:
            # Pega o nome localizado do grupo Administrators pelo SID S-1-5-32-544
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "(Get-LocalGroup -SID S-1-5-32-544).Name"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            name = res.stdout.strip()
            self.admin_group_name = name if name else "Administrators"
        except Exception:
            self.admin_group_name = "Administrators"

    
    def show_sobre(self):
        messagebox.showinfo("Sobre", "Aplicativo de Otimização e Agentes\nDesenvolvido por Pablo Carvalho, funcionário da Fred Souza.")

    def create_layout(self):
        # Top Bar (Toolbar Rápida e Título)
        self.topbar = ttk.Frame(self.root, style='Sidebar.TFrame', height=40)
        self.topbar.pack(side='top', fill='x')
        self.topbar.pack_propagate(False)
        
        lbl_top_title = ttk.Label(
            self.topbar, text="Glary Utilities Clone - Tools Win V2",
            font=('Segoe UI Semibold', 12)
        )
        lbl_top_title.pack(side='left', padx=15, pady=5)
        
        # Botões da Barra Superior
        top_btn_frame = ttk.Frame(self.topbar, style='Sidebar.TFrame')
        top_btn_frame.pack(side='right', padx=10)
        
        for t_label in ["Sobre", "Ajuda", "Opções", "Agendar", "Atualizar"]:
            b = ttk.Button(top_btn_frame, text=t_label)
            if t_label == "Sobre":
                b.configure(command=self.show_sobre)
            b.pack(side='right', padx=5, pady=5)

        # Status Bar (Base)
        self.statusbar = ttk.Frame(self.root, height=30)
        self.statusbar.pack(side='bottom', fill='x')
        self.statusbar.pack_propagate(False)
        
        lbl_status_ver = ttk.Label(self.statusbar, text="Versão 2.0.5")
        lbl_status_ver.pack(side='left', padx=10)
        
        lbl_status_prot = ttk.Label(self.statusbar, text="Status da proteção: Ativada")
        lbl_status_prot.pack(side='right', padx=10)

        # Sidebar (Esquerda) - Navegação
        self.sidebar = ttk.Frame(self.root, style='Sidebar.TFrame', width=200)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        # Logo da Sidebar
        try:
            from PIL import Image, ImageTk
            logo_path = resource_path("favicon.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                img = img.resize((70, 70), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                lbl_logo = ttk.Label(self.sidebar, image=self.logo_img)
                lbl_logo.pack(pady=(20, 5))
        except Exception as e:
            pass

        # Botões de Navegação da Sidebar
        self.nav_buttons = {}
        tabs = [
            ("dashboard", "Visão Geral", self.show_dashboard_tab),
            
            ("repair", "Limpeza e Reparo", self.show_repair_tab),
            
            ("debloat", "Privacidade e Segurança", self.show_debloat_tab),
            
            ("system", "Ferramentas do Sistema", self.show_network_tab),
            ("agents", "Agentes", self.show_agents_tab),
        ]

        for tab_id, label, func in tabs:
            btn = ttk.Button(
                self.sidebar, text=label, 
                command=lambda f=func, t_id=tab_id: self.select_tab(t_id, f)
            )
            btn.pack(fill='x', padx=5, pady=2)
            self.nav_buttons[tab_id] = btn

        # Rodapé da Sidebar (Informa se está como Admin)
        is_adm = is_admin() if 'is_admin' in globals() else False
        adm_text = "🟢 ADMIN" if is_adm else "🔴 USUÁRIO COMUM"
        adm_color = COLOR_SUCCESS if is_adm else COLOR_WARNING
        
        lbl_adm = ttk.Label(
            self.sidebar, text=adm_text
        )
        lbl_adm.pack(side='bottom', fill='x')
        lbl_copy = ttk.Label(self.sidebar, text='© Fred Souza')
        lbl_copy.pack(side='bottom', pady=5)

        # Conteúdo Principal (Direita)
        self.content_area = ttk.Frame(self.root)
        self.content_area.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        # Inicializar a aba do Dashboard
        self.active_tab_id = None
        self.select_tab("dashboard", self.show_dashboard_tab)


    
    def show_agents_tab(self):
        lbl = ttk.Label(self.content_area, text="Gerenciador de Agentes", font=('Segoe UI', 16, 'bold'))
        lbl.pack(anchor='w', pady=(0, 20))

        # Canvas for scroll
        canvas = tk.Canvas(self.content_area, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_area, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", configure_canvas)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        def draw_agent_card(parent, title, desc, icon_char, install_cmd, uninstall_cmd, is_inventory=False):
            card = ttk.Frame(parent, style='Card.TFrame', padding=15)
            card.pack(fill='x', pady=10, padx=5)
            
            header = ttk.Frame(card)
            header.pack(fill='x')
            ttk.Label(header, text=icon_char, font=('Segoe UI', 20)).pack(side='left', padx=(0, 10))
            ttk.Label(header, text=title, font=('Segoe UI', 12, 'bold')).pack(side='left')

            ttk.Label(card, text=desc, wraplength=500).pack(anchor='w', pady=(5, 10))
            
            btn_frame = ttk.Frame(card)
            btn_frame.pack(anchor='w')

            if is_inventory:
                config_path = r"C:\ProgramData\ToolsWin\inventory_config.json"
                saved_config = {}
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r") as f:
                            saved_config = json.load(f)
                    except:
                        pass

                conf_frame = ttk.Frame(card)
                conf_frame.pack(fill='x', pady=5)
                
                ttk.Label(conf_frame, text="ID Empresa:").grid(row=0, column=0, sticky='w')
                ent_id = ttk.Entry(conf_frame, width=10)
                ent_id.grid(row=0, column=1, padx=5)
                ent_id.insert(0, saved_config.get("EMPRESA_ID", "4"))

                def save_and_install():
                    with open(config_path, "w") as f:
                        json.dump({
                            "API_URL": "http://31.97.251.77:8090", 
                            "EMPRESA_ID": ent_id.get(), 
                            "AGENT_API_KEY": "kisjanbrh1245ta568ha1"
                        }, f)
                    self.run_raw_cmd(install_cmd)
                    subprocess.Popen([sys.executable, "--run-inventory"], creationflags=subprocess.CREATE_NO_WINDOW)
                    messagebox.showinfo("Ação Concluída", "Inventário configurado, executado e agendado com sucesso!")

                ttk.Button(btn_frame, text="Instalar Inventário", command=save_and_install).pack(side='left', padx=(0, 5))
                ttk.Button(btn_frame, text="Desinstalar", command=lambda c=uninstall_cmd: [self.run_raw_cmd(c), messagebox.showinfo("Ação Concluída", "O comando de desinstalação foi enviado ao sistema em segundo plano.")]).pack(side='left')
            else:
                
                def run_and_trigger(c, is_cs):
                    self.run_raw_cmd(c)
                    if is_cs:
                        subprocess.Popen([sys.executable, "--run-clearsite"], creationflags=subprocess.CREATE_NO_WINDOW)
                    elif "--run-wallpulse-install" in str(c):
                        pass # Wallpulse runs on install via ps1 logic
                    messagebox.showinfo("Ação Concluída", "O comando de instalação foi enviado ao sistema em segundo plano.")
                    
                ttk.Button(btn_frame, text=f"Instalar {title}", command=lambda c=install_cmd, is_cs=(title=="Clear Site"): run_and_trigger(c, is_cs)).pack(side='left', padx=(0, 5))
                ttk.Button(btn_frame, text="Desinstalar", command=lambda c=uninstall_cmd: [self.run_raw_cmd(c), messagebox.showinfo("Ação Concluída", "O comando de desinstalação foi enviado ao sistema em segundo plano.")]).pack(side='left')

        draw_agent_card(
            scrollable_frame, "Inventário", 
            "Coleta informações de hardware e software e envia para o servidor.", 
            "⚙", 
            ['schtasks', '/create', '/tn', 'ToolsWin_Inventory', '/tr', '\"{}\" --run-inventory'.format(sys.executable), '/sc', 'onlogon', '/ru', 'SYSTEM', '/f'], 
            ['schtasks', '/delete', '/tn', 'ToolsWin_Inventory', '/f'],
            is_inventory=True
        )
        
        draw_agent_card(
            scrollable_frame, "Wallpulse", 
            "Monitoramento ativo e comunicação em tempo real.", 
            "💠", 
            [sys.executable, '--run-wallpulse-install'], 
            [sys.executable, '--run-wallpulse-uninstall']
        )
        
        draw_agent_card(
            scrollable_frame, "Clear Site", 
            "Ferramenta de limpeza automática de navegação.", 
            "🧹", 
            ['schtasks', '/create', '/tn', 'ToolsWin_ClearSite', '/tr', '\"{}\" --run-clearsite'.format(sys.executable), '/sc', 'daily', '/st', '12:00', '/ru', 'SYSTEM', '/f'], 
            ['schtasks', '/delete', '/tn', 'ToolsWin_ClearSite', '/f']
        )
    def select_tab(self, tab_id, show_func):
        if self.active_tab_id == tab_id:
            return

        # Limpar área de conteúdo
        for child in self.content_area.winfo_children():
            child.destroy()

        # Resetar botões de navegação
        for tid, btn in self.nav_buttons.items():
            btn

        # Destacar o botão ativo
        self.nav_buttons[tab_id]
        self.active_tab_id = tab_id

        # Carregar a nova aba
        show_func()

    def on_btn_hover(self, btn):
        # Apenas muda cor se não for o botão selecionado
        for tid, b in self.nav_buttons.items():
            if b == btn and tid == self.active_tab_id:
                return
        btn

    def on_btn_leave(self, btn):
        for tid, b in self.nav_buttons.items():
            if b == btn and tid == self.active_tab_id:
                return
        btn

    # ----------------------------------------------------
    # ABA 1: DASHBOARD
    # ----------------------------------------------------
    def show_dashboard_tab(self):
        # Container com Canvas para Scroll
        canvas = tk.Canvas(self.content_area, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_area, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", configure_canvas)

        # Scrolling com mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side="left", fill="both", expand=True)

        # --- Injection for Inventory Indicator ---
        import json
        config_path = r"C:\ProgramData\ToolsWin\inventory_config.json"
        emp_id = "N/A"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    emp_id = json.load(f).get("EMPRESA_ID", "N/A")
            except:
                pass
        res_check = subprocess.run('schtasks /query /tn "ToolsWin_Inventory"', shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        is_inventoriada = (res_check.returncode == 0)
        
        status_text = f"✅ MÁQUINA INVENTARIADA (Empresa ID: {emp_id})" if is_inventoriada else "❌ MÁQUINA NÃO INVENTARIADA"
        
        lbl_dash_inv_status = ttk.Label(scrollable_frame, text=status_text)
        lbl_dash_inv_status.pack(anchor='w', padx=20, pady=(20, 10))
        # ----------------------------------------

        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Título
        lbl_title = ttk.Label(
            scrollable_frame, text="Painel do Sistema", anchor='w'
        )
        lbl_title.pack(fill='x', pady=(0, 15))

        # Grid de Status de Recursos (CPU, RAM, Disco)
        stats_frame = ttk.Frame(scrollable_frame)
        stats_frame.pack(fill='x', pady=5)
        stats_frame.columnconfigure((0, 1, 2), weight=1, uniform="equal")

        # Card CPU
        card_cpu = ttk.Frame(stats_frame, style='Card.TFrame', padding=15)
        card_cpu.grid(row=0, column=0, padx=(0, 10), sticky='nsew')
        ttk.Label(card_cpu, text="Processador (CPU)").pack(anchor='w')
        self.lbl_cpu_val = ttk.Label(card_cpu, text="0%")
        self.lbl_cpu_val.pack(anchor='w', pady=5)
        self.canvas_cpu = tk.Canvas(card_cpu, height=8, bg="#2d2d35", highlightthickness=0, bd=0)
        self.canvas_cpu.pack(fill='x', pady=5)

        # Card RAM
        card_ram = ttk.Frame(stats_frame, style='Card.TFrame', padding=15)
        card_ram.grid(row=0, column=1, padx=5, sticky='nsew')
        ttk.Label(card_ram, text="Memória RAM").pack(anchor='w')
        self.lbl_ram_val = ttk.Label(card_ram, text="0 / 0 GB (0%)")
        self.lbl_ram_val.pack(anchor='w', pady=10)
        self.canvas_ram = tk.Canvas(card_ram, height=8, bg="#2d2d35", highlightthickness=0, bd=0)
        self.canvas_ram.pack(fill='x', pady=5)

        # Card Disco
        card_disk = ttk.Frame(stats_frame, style='Card.TFrame', padding=15)
        card_disk.grid(row=0, column=2, padx=(10, 0), sticky='nsew')
        ttk.Label(card_disk, text="Disco Principal (C:)").pack(anchor='w')
        self.lbl_disk_val = ttk.Label(card_disk, text="0 / 0 GB (0%)")
        self.lbl_disk_val.pack(anchor='w', pady=10)
        self.canvas_disk = tk.Canvas(card_disk, height=8, bg="#2d2d35", highlightthickness=0, bd=0)
        self.canvas_disk.pack(fill='x', pady=5)

        # Seção de Ações Rápidas de Otimização
        quick_frame = ttk.Frame(scrollable_frame, style='Card.TFrame', padding=20)
        quick_frame.pack(fill='both', expand=True, pady=(20, 0))

        ttk.Label(
            quick_frame, text="Ações Rápidas de Otimização",
            font=('Segoe UI Semibold', 13)
        ).pack(anchor='w', pady=(0, 15))

        btn_container = ttk.Frame(quick_frame, style='Card.TFrame')
        btn_container.pack(fill='both', expand=True)
        btn_container.columnconfigure((0, 1), weight=1)

        # Botões de Otimização
        actions = [
            ("🧹 Limpar Arquivos Temporários", "Limpa cache de atualizações, pasta temp de usuários, logs e arquivos de despejo do Windows.", self.action_clean_temp),
            ("🚀 Liberar Memória RAM", "Libera a memória RAM do sistema forçando processos a liberarem memória física.", self.action_free_ram),
            ("❌ Remover Microsoft Edge", "Remove completamente o Edge do Windows 11 e bloqueia a sua reinstalação automática.", self.action_remove_edge),
            ("➕ Restaurar Microsoft Edge", "Baixa e reinstala o Microsoft Edge no sistema e remove bloqueios de atualização.", self.action_restore_edge),
            ("⚡ Plano de Alto Desempenho", "Configura e ativa o perfil de energia de Alto Desempenho do Windows.", self.action_high_performance),
            ("🔇 Desativar WinSat", "Desativa o agendamento do WinSat (avaliação do sistema) que roda em segundo plano e consome disco/CPU.", self.action_disable_winsat),
            ("🚀 Otimizar Inicialização Rápida", "Desativa a hibernação híbrida que pode acumular lixo na inicialização e causar travamentos.", self.action_disable_fast_startup),
            ("🌐 Flush DNS (Limpar Cache)", "Limpa o cache de DNS do resolvedor local para corrigir problemas de conexão de internet.", self.action_flush_dns),
        ]

        for i, (title, desc, func) in enumerate(actions):
            row = i // 2
            col = i % 2
            
            frame_act = ttk.Frame(btn_container)
            frame_act.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            lbl_title = ttk.Label(frame_act, text=title)
            lbl_title.pack(anchor='w', padx=15, pady=(10, 2))
            
            lbl_desc = ttk.Label(frame_act, text=desc, wraplength=300)
            lbl_desc.pack(anchor='w', padx=15, pady=(0, 10))
            
            btn_act = ttk.Button(
                frame_act, text="Executar",
                command=func
            )
            btn_act.pack(anchor='e', padx=15, pady=(0, 15))
            btn_act.bind("<Enter>", lambda e, b=btn_act: b)
            btn_act.bind("<Leave>", lambda e, b=btn_act: b)

    def update_system_stats(self):
        if self.active_tab_id == "dashboard":
            try:
                # CPU
                cpu_p = psutil.cpu_percent()
                self.lbl_cpu_val.configure(text=f"{cpu_p}%")
                self.draw_progress_bar(self.canvas_cpu, cpu_p, COLOR_ACCENT)

                # RAM
                ram = psutil.virtual_memory()
                ram_used = ram.used / (1024**3)
                ram_total = ram.total / (1024**3)
                self.lbl_ram_val.configure(text=f"{ram_used:.1f} / {ram_total:.1f} GB ({ram.percent}%)")
                self.draw_progress_bar(self.canvas_ram, ram.percent, COLOR_SUCCESS)

                # DISCO
                disk = psutil.disk_usage('C:')
                disk_used = disk.used / (1024**3)
                disk_total = disk.total / (1024**3)
                self.lbl_disk_val.configure(text=f"{disk_used:.1f} / {disk_total:.1f} GB ({disk.percent}%)")
                self.draw_progress_bar(self.canvas_disk, disk.percent, COLOR_WARNING if disk.percent < 90 else COLOR_DANGER)
            except Exception:
                pass
        
        # Agendar próxima atualização em 2 segundos
        self.root.after(2000, self.update_system_stats)

    def draw_progress_bar(self, canvas, percentage, color):
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1:
            width = 200 # Fallback
        fill_width = (percentage / 100) * width
        
        # Fundo
        canvas.create_rectangle(0, 0, width, height, fill="#2d2d35", outline="")
        # Barra preenchida
        canvas.create_rectangle(0, 0, fill_width, height, fill=color, outline="")

    def start_ai_health_check(self):
        # Roda em thread separada para não travar a GUI
        threading.Thread(target=self.run_ai_health_check, daemon=True).start()

    def run_ai_health_check(self):
        alerts = []
        
        # 1. Bateria (se for laptop)
        try:
            battery = psutil.sensors_battery()
            if battery is not None:
                if battery.percent <= 20 and not battery.power_plugged:
                    alerts.append({
                        "level": "MÉDIO",
                        "title": "Bateria Fraca",
                        "desc": f"Bateria está em {battery.percent}% e não está conectada à tomada.",
                        "color": COLOR_WARNING
                    })
        except Exception:
            pass

        # 2. Espaço em Disco
        try:
            disk = psutil.disk_usage('C:')
            # Menos de 10% livre ou menos de 5GB livre
            free_gb = disk.free / (1024**3)
            if disk.percent >= 90 or free_gb < 5:
                alerts.append({
                    "level": "MÉDIO",
                    "title": "Espaço em Disco Crítico",
                    "desc": f"Seu disco C: está {disk.percent}% cheio. Restam apenas {free_gb:.1f} GB livres.",
                    "color": COLOR_WARNING
                })
        except Exception:
            pass

        # 3. CPU / RAM (Aviso Informativo)
        try:
            cpu_p = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            if cpu_p > 90:
                alerts.append({
                    "level": "INFORMATIVO",
                    "title": "Uso de CPU Elevado",
                    "desc": f"O uso do processador está em {cpu_p}%. O sistema pode apresentar lentidão.",
                    "color": COLOR_MUTED
                })
            if ram.percent > 90:
                alerts.append({
                    "level": "INFORMATIVO",
                    "title": "Uso de RAM Elevado",
                    "desc": f"A memória RAM está {ram.percent}% ocupada. Feche alguns programas.",
                    "color": COLOR_MUTED
                })
        except Exception:
            pass

        # 4. Saúde do Disco (S.M.A.R.T. via WMI)
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-WmiObject -Class Win32_DiskDrive | Select-Object Status | ConvertTo-Json"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            out = res.stdout.strip()
            if out:
                data = json.loads(out)
                if isinstance(data, dict):
                    data = [data]
                
                bad_disks = False
                for d in data:
                    if d.get("Status", "OK").upper() != "OK":
                        bad_disks = True
                        break
                
                if bad_disks:
                    alerts.append({
                        "level": "CRÍTICO",
                        "title": "Saúde do Disco Comprometida",
                        "desc": "Foi detectado um problema S.M.A.R.T. no seu HD/SSD. Risco de falha de hardware e perda de dados. Faça backup urgente!",
                        "color": COLOR_DANGER
                    })
        except Exception:
            pass
            
        # Se houver alertas, exibe o pop-up na thread principal
        if alerts:
            self.root.after(0, lambda: self.show_ai_report(alerts))

    def show_ai_report(self, alerts):
        # Cria janela de relatório
        top = tk.Toplevel(self.root)
        top.title("Relatório de Saúde por IA")
        top.geometry("550x450")
        top
        top.transient(self.root)
        top.grab_set()
        
        # Centralizar
        top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - top.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - top.winfo_height()) // 2
        top.geometry(f"+{x}+{y}")
        
        lbl_title = ttk.Label(top, text="🤖 Relatório de Saúde do Sistema")
        lbl_title.pack(pady=(20, 5))
        
        lbl_sub = ttk.Label(top, text="A inteligência artificial detectou os seguintes pontos de atenção:")
        lbl_sub.pack(pady=(0, 15))
        
        # Canvas para scroll se houver muitos alertas
        frame_canvas = ttk.Frame(top)
        frame_canvas.pack(fill='both', expand=True, padx=20, pady=5)
        
        canvas = tk.Canvas(frame_canvas, bg=COLOR_BG, highlightthickness=0)
        scroll = ttk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        # Configurar para que o frame interno se expanda
        canvas_window = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        
        def configure_scrollable(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=e.width)

        canvas.bind("<Configure>", configure_scrollable)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        canvas.configure(yscrollcommand=scroll.set)
        
        canvas.pack(side="left", fill="both", expand=True)


        scroll.pack(side="right", fill="y")
        
        if not alerts:
            alerts.append({"level": "OK", "title": "Sistema Saudável", "desc": "A IA não encontrou nenhum problema crítico no seu sistema neste momento."})
        
        for alert in alerts:
            card = ttk.Frame(scrollable)
            card.pack(fill='x', pady=5, ipadx=10, ipady=10)
            
            header = ttk.Frame(card)
            header.pack(fill='x')
            
            lbl_level = ttk.Label(header, text=alert["level"])
            lbl_level.pack(side='left')
            
            lbl_t = ttk.Label(header, text=alert["title"])
            lbl_t.pack(side='left', padx=10)
            
            lbl_d = ttk.Label(card, text=alert["desc"], wraplength=450)
            lbl_d.pack(anchor='w', pady=(8, 0))
            
        btn_close = ttk.Button(
            top, text="Entendi",
            command=top.destroy
        )
        btn_close.pack(pady=20)

    # ----------------------------------------------------
    # ABA 2: CORREÇÃO & REPAROS
    # ----------------------------------------------------
    def show_repair_tab(self):
        lbl_title = ttk.Label(
            self.content_area, text="Ferramentas de Correção do Windows", anchor='w'
        )
        lbl_title.pack(fill='x', pady=(0, 15))

        # Container dos Botões
        buttons_frame = ttk.Frame(self.content_area, style='Card.TFrame', padding=15)
        buttons_frame.pack(fill='x', pady=5)
        
        rep_tools = [
            ("Corrigir Erros DISM", "Restaura a imagem de saúde do Windows via Windows Update.", "dism /online /cleanup-image /restorehealth"),
            ("Verificação SFC", "Examina arquivos de sistema corrompidos e os substitui.", "sfc /scannow"),
            ("Agendar CHKDSK", "Examina o disco principal na próxima reinicialização por setores defeituosos.", "chkdsk C: /f /r /x"),
            ("Resetar Windows Update", "Limpa cache, para serviços de update e reinicia o agente.", "reset_update"),
            ("Flush DNS", "Limpa o cache do resolvedor de DNS.", "ipconfig /flushdns")
            ,
            ("Limpeza de Disco Avançada", "Aciona a limpeza profunda nativa do sistema.", "cleanmgr /sagerun:1"),
            ("Otimização de SSD/HDD", "Força o TRIM e a desfragmentação no disco principal.", "defrag C: /O"),
            ("Limpeza da Pasta Temp", "Apagamento forçado de todo o lixo da pasta Temp local.", r'del /q /f /s "%TEMP%\\*"'),
            ("Limpar Cache Windows Store", "Resolve problemas de aplicativos travados na loja.", "wsreset.exe"),
            ("Escanear Malware Rápido", "Aciona o Windows Defender via terminal.", "MpCmdRun.exe -Scan -ScanType 1")
        ]

        for i, (name, desc, cmd) in enumerate(rep_tools):
            btn_tool = ttk.Button(
                buttons_frame, text=name,
                command=lambda c=cmd, n=name: self.run_system_tool(c, n)
            )
            btn_tool.pack(fill='x', pady=4)
            btn_tool.bind("<Enter>", lambda e, b=btn_tool: b)
            btn_tool.bind("<Leave>", lambda e, b=btn_tool: b)

        # Console Log
        log_frame = ttk.Frame(self.content_area, style='Card.TFrame', padding=15)
        log_frame.pack(fill='both', expand=True, pady=(15, 0))

        ttk.Label(log_frame, text="Log de Execução").pack(anchor='w', pady=(0, 5))
        
        # Scrolled Text Box
        self.text_log = tk.Text(
            log_frame, bg="#18181b", fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
            font=('Consolas', 10), borderwidth=0, highlightthickness=1, highlightbackground="#2d2d35"
        )
        self.text_log.pack(fill='both', expand=True)
        self.text_log.configure(state='disabled')


        self.text_log.see(tk.END)
        self.text_log.configure(state='disabled')


    def log(self, text):
        if hasattr(self, "text_log"):
            self.text_log.configure(state="normal")
            self.text_log.insert("end", text)
            self.text_log.see("end")
            self.text_log.configure(state="disabled")

    def run_system_tool(self, cmd_key, tool_name):
        if self.running_thread and self.running_thread.is_alive():
            messagebox.showwarning("Aviso", "Já existe um processo em execução. Por favor, aguarde.")
            return

        if not is_admin():
            messagebox.showerror("Erro", "Esta operação requer privilégios de Administrador.")
            return

        self.log(f"\n--- Iniciando: {tool_name} ---\n")

        if cmd_key == "reset_update":
            # Comando especial que executa múltiplas etapas
            threading.Thread(target=self.reset_windows_update_flow, daemon=True).start()
        elif cmd_key.startswith("chkdsk"):
            # CHKDSK precisa de entrada manual do usuário
            confirm = messagebox.askyesno(
                "Confirmar CHKDSK", 
                "Para agendar a verificação de disco (chkdsk C: /f /r /x), é necessário reiniciar a máquina. Deseja agendar?"
            )
            if confirm:
                threading.Thread(target=self.run_raw_cmd, args=("echo Y | chkdsk C: /f /r /x",), daemon=True).start()
            else:
                self.log("Operação cancelada pelo usuário.\n")
        else:
            self.running_thread = threading.Thread(target=self.run_logged_cmd, args=(cmd_key,), daemon=True)
            self.running_thread.start()


    def run_logged_cmd(self, command):
        import subprocess
        try:
            p = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in p.stdout:
                self.root.after(0, self.log, line)
            p.wait()
            self.root.after(0, self.log, f"\n--- Concluido com codigo {p.returncode} ---\n")
        except Exception as e:
            self.root.after(0, self.log, f"\nErro fatal: {e}\n")

    def run_raw_cmd(self, command):
        import subprocess
        try:
            if isinstance(command, str):
                subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(command, shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

    def reset_windows_update_flow(self):
        commands = [
            ("Parando serviço Windows Update...", "net stop wuauserv"),
            ("Parando serviço de Criptografia...", "net stop cryptSvc"),
            ("Parando serviço de Transferência Inteligente...", "net stop bits"),
            ("Parando Windows Installer...", "net stop msiserver"),
            ("Renomeando pasta SoftwareDistribution...", 'powershell -NoProfile -Command "Rename-Item -Path C:\\Windows\\SoftwareDistribution -NewName SoftwareDistribution.old -ErrorAction SilentlyContinue"'),
            ("Renomeando pasta catroot2...", 'powershell -NoProfile -Command "Rename-Item -Path C:\\Windows\\System32\\catroot2 -NewName catroot2.old -ErrorAction SilentlyContinue"'),
            ("Iniciando serviço Windows Update...", "net start wuauserv"),
            ("Iniciando serviço de Criptografia...", "net start cryptSvc"),
            ("Iniciando serviço de Transferência...", "net start bits"),
            ("Iniciando Windows Installer...", "net start msiserver")
        ]
        
        for msg, cmd in commands:
            self.root.after(0, self.log, f"\n{msg}\n")
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if res.stdout:
                    self.root.after(0, self.log, res.stdout)
                if res.stderr:
                    self.root.after(0, self.log, f"Aviso/Erro: {res.stderr}\n")
            except Exception as e:
                self.root.after(0, self.log, f"Erro: {e}\n")
        
        self.root.after(0, self.log, "\nReset do Windows Update finalizado!\n")

    # ----------------------------------------------------
    # ABA 3: DESATIVAR IA & PRIVACIDADE
    # ----------------------------------------------------
    def show_debloat_tab(self):
        lbl_title = ttk.Label(
            self.content_area, text="Gerenciador de IA, Privacidade & Debloat", anchor='w'
        )
        lbl_title.pack(fill='x', pady=(0, 15))

        container = ttk.Frame(self.content_area, style='Card.TFrame', padding=15)
        container.pack(fill='both', expand=True)

        ttk.Label(
            container, text="Gerencie individualmente as opções de telemetria, IA e navegadores. Use os botões 'Desativar' ou 'Ativar' correspondentes.", wraplength=700
        ).pack(anchor='w', pady=(0, 15))

        canvas = tk.Canvas(container, bg=COLOR_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", configure_canvas)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side="left", fill="both", expand=True)


        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        opts = [
            ("copilot", "🤖 Windows Copilot", "Desativa ou ativa o assistente de inteligência artificial Copilot.", self.debloat_copilot, self.restore_copilot),
            ("recall", "🧠 AI Recall", "Impede ou permite o Windows 11 de rastrear atividades via Recall.", self.debloat_recall, self.restore_recall),
            ("cortana", "🎙 Assistente Cortana", "Desativa ou ativa a assistente virtual Cortana.", self.debloat_cortana, self.restore_cortana),
            ("web_search", "🔍 Busca Web no Iniciar", "Bloqueia ou permite pesquisas do Bing no Menu Iniciar.", self.debloat_web_search, self.restore_web_search),
            ("telemetry", "📊 Telemetria & Diagnósticos", "Desativa ou ativa o DiagTrack e envio de telemetria para a Microsoft.", self.debloat_telemetry, self.restore_telemetry),
            ("useless_services", "⚙ Serviços Inúteis", "Desativa ou ativa serviços do sistema raramente usados (Fax, Xbox, etc.).", self.debloat_useless_services, self.restore_useless_services),
            ("edge", "🌐 Microsoft Edge", "Remove ou reinstala/restaura o navegador Microsoft Edge no sistema.", self.debloat_edge, self.restore_edge_action),
            ("chrome_policies", "🌐 Restrições do Chrome (Login)", "Bloqueia ou permite fazer login e usar múltiplos perfis no Google Chrome.", self.debloat_chrome_policies, self.restore_chrome_policies),
        ]

        self.status_labels = {}

        for i, (key, title, desc, df_func, rf_func) in enumerate(opts):
            row_frame = ttk.Frame(scroll_frame)
            row_frame.pack(fill='x', pady=4, ipady=4)
            
            text_frame = ttk.Frame(row_frame)
            text_frame.pack(side='left', fill='x', expand=True, padx=15, pady=5)
            
            lbl_title = ttk.Label(text_frame, text=title, anchor='w')
            lbl_title.pack(fill='x')
            lbl_desc = ttk.Label(text_frame, text=desc, anchor='w')
            lbl_desc.pack(fill='x')
            
            lbl_status = ttk.Label(row_frame, text="Carregando...", width=15, anchor='center')
            lbl_status.pack(side='left', padx=10)
            self.status_labels[key] = lbl_status
            
            btn_frame = ttk.Frame(row_frame)
            btn_frame.pack(side='right', padx=15)
            
            btn_disable = ttk.Button(
                btn_frame, text="Desativar", width=10,
                command=lambda f=df_func, k=key, n=title: self.execute_single_action(f, k, f"Desativar {n}")
            )
            btn_disable.pack(side='left', padx=3)
            
            btn_enable = ttk.Button(
                btn_frame, text="Ativar", width=10,
                command=lambda f=rf_func, k=key, n=title: self.execute_single_action(f, k, f"Ativar {n}")
            )
            btn_enable.pack(side='left', padx=3)

        self.refresh_debloat_statuses()

    def get_status_text(self, key):
        if key == "copilot":
            disabled = self.check_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot", 1)
            return "Desativado" if disabled else "Ativo"
        elif key == "recall":
            disabled = self.check_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI", "AllowRecallEnablement", 0)
            return "Desativado" if disabled else "Ativo"
        elif key == "cortana":
            disabled = self.check_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search", "AllowCortana", 0)
            return "Desativado" if disabled else "Ativo"
        elif key == "web_search":
            disabled = self.check_reg_value("HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer", "DisableSearchBoxSuggestions", 1)
            return "Desativado" if disabled else "Ativo"
        elif key == "telemetry":
            disabled = self.check_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection", "AllowTelemetry", 0)
            return "Desativado" if disabled else "Ativo"
        elif key == "useless_services":
            disabled = self.check_service_disabled("Fax")
            return "Desativados" if disabled else "Ativos"
        elif key == "edge":
            pf_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            installed = os.path.exists(os.path.join(pf_x86, "Microsoft", "Edge", "Application", "msedge.exe"))
            return "Instalado" if installed else "Removido"
        elif key == "chrome_policies":
            blocked = self.check_reg_value("HKLM\\SOFTWARE\\Policies\\Google\\Chrome", "BrowserAddPersonEnabled", 0)
            return "Restrito" if blocked else "Liberado"
        return "Desconhecido"

    def refresh_debloat_statuses(self):
        for key, lbl in self.status_labels.items():
            txt = self.get_status_text(key)
            color = COLOR_SUCCESS if txt in ["Ativo", "Ativos", "Instalado", "Liberado"] else COLOR_DANGER
            lbl.config(text=txt, foreground=color)

    def execute_single_action(self, action_func, key, action_name):
        if not is_admin():
            messagebox.showerror("Erro", "Esta operação requer privilégios de Administrador.")
            return

        def run():
            try:
                action_func()
                self.root.after(0, self.refresh_debloat_statuses)
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"Operação '{action_name}' concluída com sucesso!"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha ao executar '{action_name}':\n{e}"))

        threading.Thread(target=run, daemon=True).start()

    def debloat_copilot(self):
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg add "HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def restore_copilot(self):
        subprocess.run('reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot" /v TurnOffWindowsCopilot /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg delete "HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsCopilot" /v TurnOffWindowsCopilot /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def debloat_recall(self):
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI" /v AllowRecallEnablement /t REG_DWORD /d 0 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg add "HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsAI" /v AllowRecallEnablement /t REG_DWORD /d 0 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def restore_recall(self):
        subprocess.run('reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI" /v AllowRecallEnablement /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg delete "HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsAI" /v AllowRecallEnablement /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def debloat_cortana(self):
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def restore_cortana(self):
        subprocess.run('reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def debloat_web_search(self):
        subprocess.run('reg add "HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer" /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def restore_web_search(self):
        subprocess.run('reg delete "HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer" /v DisableSearchBoxSuggestions /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def debloat_telemetry(self):
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('sc config DiagTrack start=disabled', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('sc stop DiagTrack', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('sc config dmwappushservice start=disabled', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('sc stop dmwappushservice', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def restore_telemetry(self):
        subprocess.run('reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('sc config DiagTrack start=auto', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('sc start DiagTrack', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('sc config dmwappushservice start=auto', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('sc start dmwappushservice', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def debloat_useless_services(self):
        services = ["Fax", "RemoteRegistry", "WalletService", "WMPNetworkSvc", "XblAuthManager", "XblGameSave", "XboxNetApiSvc"]
        for srv in services:
            subprocess.run(f'sc config {srv} start=disabled', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(f'sc stop {srv}', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def restore_useless_services(self):
        services = ["Fax", "RemoteRegistry", "WalletService", "WMPNetworkSvc", "XblAuthManager", "XblGameSave", "XboxNetApiSvc"]
        for srv in services:
            subprocess.run(f'sc config {srv} start=demand', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def debloat_edge(self):
        return self._execute_edge_removal()

    def restore_edge_action(self):
        return self._execute_edge_restoration()

    def debloat_chrome_policies(self):
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserAddPersonEnabled /t REG_DWORD /d 0 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserGuestModeEnabled /t REG_DWORD /d 0 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserSignin /t REG_DWORD /d 2 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v AccountsRestriction /t REG_SZ /d "primary_account_only" /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        subprocess.run('reg add "HKCU\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserAddPersonEnabled /t REG_DWORD /d 0 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg add "HKCU\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserGuestModeEnabled /t REG_DWORD /d 0 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg add "HKCU\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserSignin /t REG_DWORD /d 2 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg add "HKCU\\SOFTWARE\\Policies\\Google\\Chrome" /v AccountsRestriction /t REG_SZ /d "primary_account_only" /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def restore_chrome_policies(self):
        subprocess.run('reg delete "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserAddPersonEnabled /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg delete "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserGuestModeEnabled /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg delete "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserSignin /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg delete "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v AccountsRestriction /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        subprocess.run('reg delete "HKCU\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserAddPersonEnabled /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg delete "HKCU\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserGuestModeEnabled /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg delete "HKCU\\SOFTWARE\\Policies\\Google\\Chrome" /v BrowserSignin /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run('reg delete "HKCU\\SOFTWARE\\Policies\\Google\\Chrome" /v AccountsRestriction /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    # ----------------------------------------------------
    # ABA 4: GERENCIADOR DE USUÁRIOS
    # ----------------------------------------------------
    def show_users_tab(self):
        lbl_title = ttk.Label(
            self.content_area, text="Gerenciador de Usuários do Windows", anchor='w'
        )
        lbl_title.pack(fill='x', pady=(0, 15))

        # Container Principal
        container = ttk.Frame(self.content_area)
        container.pack(fill='both', expand=True)

        # Esquerda: Lista de Usuários (Tabela Treeview)
        table_frame = ttk.Frame(container, style='Card.TFrame', padding=10)
        table_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Colunas da tabela
        columns = ('username', 'enabled', 'admin')
        self.tree_users = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')
        
        self.tree_users.heading('username', text='Nome de Usuário')
        self.tree_users.heading('enabled', text='Status da Conta')
        self.tree_users.heading('admin', text='Administrador')

        self.tree_users.column('username', anchor='w', width=180)
        self.tree_users.column('enabled', anchor='center', width=100)
        self.tree_users.column('admin', anchor='center', width=100)

        self.tree_users.pack(fill='both', expand=True)

        # Direita: Painel de Controle de Usuários (Ações)
        actions_frame = ttk.Frame(container, style='Card.TFrame', padding=15, width=220)
        actions_frame.pack(side='right', fill='y')
        actions_frame.pack_propagate(False)

        ttk.Label(actions_frame, text="Ações do Usuário").pack(anchor='w', pady=(0, 15))

        btn_pass = ttk.Button(
            actions_frame, text="🔑 Trocar Senha",
            command=self.user_change_password
        )
        btn_pass.pack(fill='x', pady=4)

        self.btn_toggle_admin = ttk.Button(
            actions_frame, text="🛡️ Alternar Admin",
            command=self.user_toggle_admin
        )
        self.btn_toggle_admin.pack(fill='x', pady=4)

        self.btn_toggle_status = ttk.Button(
            actions_frame, text="🔌 Ativar/Desativar",
            command=self.user_toggle_status
        )
        self.btn_toggle_status.pack(fill='x', pady=4)

        # Separador de Ações Globais
        ttk.Frame(actions_frame, height=1).pack(fill='x', pady=15)

        btn_create = ttk.Button(
            actions_frame, text="➕ Novo Usuário",
            command=self.user_create
        )
        btn_create.pack(fill='x', pady=4)

        btn_delete = ttk.Button(
            actions_frame, text="❌ Excluir Usuário",
            command=self.user_delete
        )
        btn_delete.pack(fill='x', pady=4)

        # Carregar lista inicial de usuários
        self.load_users_list()

    def load_users_list(self):
        # Limpar tabela
        for item in self.tree_users.get_children():
            self.tree_users.delete(item)

        if not is_admin():
            self.tree_users.insert('', 'end', values=("Erro: Execute como Administrador", "-", "-"))
            return

        try:
            # Pegar usuários via PowerShell convertendo para JSON
            res_users = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-LocalUser | Select-Object Name, Enabled | ConvertTo-Json"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            users_data = json.loads(res_users.stdout.strip())
            if isinstance(users_data, dict):
                users_data = [users_data]

            # Pegar administradores pelo SID do grupo Administradores (independente de idioma)
            res_admins = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-LocalGroupMember -SID S-1-5-32-544 | Select-Object Name | ConvertTo-Json"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            admins_raw = res_admins.stdout.strip()
            admin_users = []
            if admins_raw:
                admins_data = json.loads(admins_raw)
                if isinstance(admins_data, dict):
                    admins_data = [admins_data]
                # Pegar apenas o nome do usuário sem o nome do computador (ex: PC\Nome -> Nome)
                for item in admins_data:
                    full_name = item.get("Name", "")
                    if "\\" in full_name:
                        admin_users.append(full_name.split("\\")[-1])
                    else:
                        admin_users.append(full_name)

            for user in users_data:
                name = user.get("Name", "")
                enabled = "Ativo" if user.get("Enabled") else "Inativo"
                is_adm = "Sim" if name in admin_users else "Não"
                self.tree_users.insert('', 'end', values=(name, enabled, is_adm))

        except Exception as e:
            messagebox.showerror("Erro ao carregar usuários", f"Erro crítico: {e}")

    def get_selected_user(self):
        selected = self.tree_users.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Por favor, selecione um usuário na lista primeiro.")
            return None
        values = self.tree_users.item(selected[0], 'values')
        return values[0] if values else None

    def user_change_password(self):
        user = self.get_selected_user()
        if not user: return
        
        new_pass = simpledialog.askstring("Alterar Senha", f"Digite a nova senha para o usuário '{user}':", show='*')
        if new_pass is not None:
            # Comando: net user username password
            res = subprocess.run(f'net user "{user}" "{new_pass}"', shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                messagebox.showinfo("Sucesso", f"Senha do usuário '{user}' alterada com sucesso!")
            else:
                messagebox.showerror("Erro", f"Não foi possível alterar a senha:\n{res.stderr}")

    def user_toggle_admin(self):
        user = self.get_selected_user()
        if not user: return

        selected_item = self.tree_users.selection()[0]
        values = self.tree_users.item(selected_item, 'values')
        current_admin = values[2] # "Sim" ou "Não"

        # Usar o nome do grupo de administradores detectado
        group = self.admin_group_name

        if current_admin == "Sim":
            # Remover Admin
            cmd = f'net localgroup "{group}" "{user}" /delete'
            action = "remover"
        else:
            # Adicionar Admin
            cmd = f'net localgroup "{group}" "{user}" /add'
            action = "adicionar"

        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if res.returncode == 0:
            messagebox.showinfo("Sucesso", f"Privilégios de Administrador atualizados para o usuário '{user}'!")
            self.load_users_list()
        else:
            messagebox.showerror("Erro", f"Falha ao {action} privilégios:\n{res.stderr}")

    def user_toggle_status(self):
        user = self.get_selected_user()
        if not user: return

        selected_item = self.tree_users.selection()[0]
        values = self.tree_users.item(selected_item, 'values')
        current_status = values[1] # "Ativo" ou "Inativo"

        new_status_cmd = "/active:no" if current_status == "Ativo" else "/active:yes"
        cmd = f'net user "{user}" {new_status_cmd}'

        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if res.returncode == 0:
            messagebox.showinfo("Sucesso", f"Status da conta '{user}' atualizado com sucesso!")
            self.load_users_list()
        else:
            messagebox.showerror("Erro", f"Falha ao alterar status da conta:\n{res.stderr}")

    def user_create(self):
        username = simpledialog.askstring("Novo Usuário", "Digite o nome do novo usuário:")
        if not username: return
        
        password = simpledialog.askstring("Novo Usuário", f"Digite a senha para o usuário '{username}':", show='*')
        if password is None: return

        # Executar comando para criar
        cmd = f'net user "{username}" "{password}" /add'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if res.returncode == 0:
            # Perguntar se deseja adicionar ao grupo administradores
            add_admin = messagebox.askyesno("Adicionar Administrador?", f"Deseja adicionar o usuário '{username}' ao grupo de Administradores?")
            if add_admin:
                group = self.admin_group_name
                subprocess.run(f'net localgroup "{group}" "{username}" /add', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            messagebox.showinfo("Sucesso", f"Usuário '{username}' criado com sucesso!")
            self.load_users_list()
        else:
            messagebox.showerror("Erro", f"Não foi possível criar o usuário:\n{res.stderr}")

    def user_delete(self):
        user = self.get_selected_user()
        if not user: return

        # Verificar se tenta deletar o usuário logado
        try:
            current_user = os.getlogin()
        except Exception:
            current_user = ""
        
        if current_user and user.lower() == current_user.lower():
            messagebox.showerror("Erro", "Você não pode excluir a conta de usuário que está conectada no momento.")
            return

        # Lista de contas do sistema protegidas
        system_accounts = ["administrator", "administrador", "guest", "convidado", "defaultaccount", "wdagutilityaccount"]
        if user.lower() in system_accounts:
            messagebox.showerror("Erro", f"A conta '{user}' é uma conta protegida do sistema e não pode ser excluída.")
            return

        # Confirmar exclusão da conta
        confirm = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza de que deseja excluir permanentemente o usuário '{user}'?")
        if not confirm: return

        # Perguntar se deseja remover os arquivos/perfil
        delete_files = messagebox.askyesnocancel(
            "Excluir Arquivos e Perfil?",
            f"Deseja excluir também a pasta de perfil (C:\\Users\\{user}) e todos os arquivos associados a este usuário?\n\n"
            "Clique em 'Sim' para excluir a Conta e Todos os Arquivos.\n"
            "Clique em 'Não' para excluir Apenas a Conta (arquivos serão mantidos).\n"
            "Clique em 'Cancelar' para abortar."
        )

        if delete_files is None:
            return

        # Executar a exclusão
        def run():
            # Excluir a conta de usuário primeiro
            cmd_del_user = f'net user "{user}" /delete'
            res = subprocess.run(cmd_del_user, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if res.returncode != 0:
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Não foi possível excluir a conta de usuário:\n{res.stderr}"))
                return

            if delete_files:
                # Excluir o perfil de usuário (pastas e registro) via PowerShell
                cmd_del_profile = f'powershell -NoProfile -Command "Get-CimInstance -ClassName Win32_UserProfile | Where-Object {{ $_.LocalPath -like \'*\\\\{user}\' }} | Remove-CimInstance"'
                res_profile = subprocess.run(cmd_del_profile, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                if res_profile.returncode == 0:
                    self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"Usuário '{user}' e todas as suas pastas de perfil foram excluídos com sucesso!"))
                else:
                    self.root.after(0, lambda: messagebox.showwarning("Aviso", f"A conta do usuário foi excluída, mas ocorreu um erro ao remover a pasta de perfil:\n{res_profile.stderr}"))
            else:
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"Conta do usuário '{user}' excluída com sucesso (os arquivos foram mantidos)."))
            
            self.root.after(0, self.load_users_list)

        threading.Thread(target=run, daemon=True).start()

    # ----------------------------------------------------
    # ABA 5: FERRAMENTAS DE REDE
    # ----------------------------------------------------
    def show_network_tab(self):
        lbl_title = ttk.Label(
            self.content_area, text="Ferramentas de Rede", anchor='w'
        )
        lbl_title.pack(fill='x', pady=(0, 15))

        container = ttk.Frame(self.content_area)
        container.pack(fill='both', expand=True)

        # Card de DNS Changer (Esquerda)
        dns_frame = ttk.Frame(container, style='Card.TFrame', padding=15)
        dns_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        ttk.Label(dns_frame, text="⚡ Alterar DNS do Adaptador").pack(anchor='w', pady=(0, 10))
        
        ttk.Label(dns_frame, text="Selecione o Adaptador de Rede:").pack(anchor='w')
        self.combo_adapters = ttk.Combobox(dns_frame, state='readonly', font=('Segoe UI', 10))
        self.combo_adapters.pack(fill='x', pady=5)

        ttk.Label(dns_frame, text="Selecione o Servidor DNS:").pack(anchor='w', pady=(10, 0))
        self.combo_dns = ttk.Combobox(
            dns_frame, state='readonly', font=('Segoe UI', 10),
            values=["Cloudflare DNS (1.1.1.1 / 1.0.0.1)", "Google DNS (8.8.8.8 / 8.8.4.4)", "Restaurar Padrão (Obter DHCP)"]
        )
        self.combo_dns.set("Cloudflare DNS (1.1.1.1 / 1.0.0.1)")
        self.combo_dns.pack(fill='x', pady=5)

        btn_apply_dns = ttk.Button(
            dns_frame, text="Aplicar DNS",
            command=self.network_apply_dns
        )
        btn_apply_dns.pack(fill='x', pady=(20, 0))

        # Card de Ping Test (Direita)
        ping_frame = ttk.Frame(container, style='Card.TFrame', padding=15, width=350)
        ping_frame.pack(side='right', fill='both')
        ping_frame.pack_propagate(False)

        ttk.Label(ping_frame, text="📡 Testar Latência (Ping)").pack(anchor='w', pady=(0, 10))

        ttk.Label(ping_frame, text="Endereço de Destino (Ex: google.com):").pack(anchor='w')
        self.entry_ping = ttk.Entry(
            ping_frame, insertbackground=COLOR_TEXT, borderwidth=0
        )
        self.entry_ping.insert(0, "1.1.1.1")
        self.entry_ping.pack(fill='x', pady=5, ipady=5)

        btn_ping = ttk.Button(
            ping_frame, text="Iniciar Teste",
            command=self.network_run_ping
        )
        btn_ping.pack(fill='x', pady=10)

        self.text_ping_log = tk.Text(
            ping_frame, bg="#18181b", fg=COLOR_TEXT, font=('Consolas', 9),
            borderwidth=0, highlightthickness=1, highlightbackground="#2d2d35"
        )
        self.text_ping_log.pack(fill='both', expand=True)
        self.text_ping_log.configure(state='disabled')

        # Carregar lista de adaptadores de rede
        self.load_network_adapters()

    def load_network_adapters(self):
        try:
            # Listar adaptadores de rede via PowerShell
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name | ConvertTo-Json"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            raw = res.stdout.strip()
            adapters = []
            if raw:
                data = json.loads(raw)
                if isinstance(data, dict):
                    data = [data]
                adapters = [item.get("Name") for item in data if item.get("Name")]
            
            if adapters:
                self.combo_adapters.configure(values=adapters)
                self.combo_adapters.set(adapters[0])
            else:
                self.combo_adapters.configure(values=["Nenhum adaptador ativo"])
                self.combo_adapters.set("Nenhum adaptador ativo")
        except Exception:
            self.combo_adapters.configure(values=["Erro ao listar adaptadores"])
            self.combo_adapters.set("Erro ao listar adaptadores")

    def network_apply_dns(self):
        adapter = self.combo_adapters.get()
        if not adapter or adapter in ["Nenhum adaptador ativo", "Erro ao listar adaptadores"]:
            messagebox.showwarning("Aviso", "Por favor, selecione um adaptador válido.")
            return

        if not is_admin():
            messagebox.showerror("Erro", "Esta operação requer privilégios de Administrador.")
            return

        dns_type = self.combo_dns.get()
        if "Cloudflare" in dns_type:
            dns_servers = "('1.1.1.1', '1.0.0.1')"
            cmd = f'powershell -NoProfile -Command "Set-DnsClientServerAddress -InterfaceAlias \'{adapter}\' -ServerAddresses {dns_servers}"'
        elif "Google" in dns_type:
            dns_servers = "('8.8.8.8', '8.8.4.4')"
            cmd = f'powershell -NoProfile -Command "Set-DnsClientServerAddress -InterfaceAlias \'{adapter}\' -ServerAddresses {dns_servers}"'
        else:
            # DHCP / Restaurar
            cmd = f'powershell -NoProfile -Command "Set-DnsClientServerAddress -InterfaceAlias \'{adapter}\' -ResetServerAddresses"'

        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                messagebox.showinfo("Sucesso", "Configurações de DNS atualizadas com sucesso!")
            else:
                messagebox.showerror("Erro", f"Não foi possível alterar o DNS:\n{res.stderr}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro de execução: {e}")

    def network_run_ping(self):
        host = self.entry_ping.get().strip()
        if not host:
            messagebox.showwarning("Aviso", "Digite um endereço de destino.")
            return

        self.text_ping_log.configure(state='normal')
        self.text_ping_log.delete('1.0', tk.END)
        self.text_ping_log.insert(tk.END, f"Disparando ping para {host}...\n\n")
        self.text_ping_log.configure(state='disabled')

        def run():
            try:
                # Disparar 4 pings
                process = subprocess.Popen(
                    f"ping -n 4 {host}", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    shell=True, text=True, encoding='cp850', errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in process.stdout:
                    self.root.after(0, self.append_ping_log, line)
                process.communicate()
            except Exception as e:
                self.root.after(0, self.append_ping_log, f"\nErro ao pingar: {e}\n")

        threading.Thread(target=run, daemon=True).start()

    def append_ping_log(self, text):
        self.text_ping_log.configure(state='normal')
        self.text_ping_log.insert(tk.END, text)
        self.text_ping_log.see(tk.END)
        self.text_ping_log.configure(state='disabled')

    # ----------------------------------------------------
    # OPERAÇÕES DE LIMPEZA DO DASHBOARD
    # ----------------------------------------------------
    def _execute_edge_removal(self):
        # 1. Matar processos do Edge e do updater de forma exaustiva
        subprocess.run("taskkill /f /im msedge.exe", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run("taskkill /f /im MicrosoftEdgeUpdate.exe", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run("taskkill /f /im edgeupdate.exe", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run("taskkill /f /im msedgewebview2.exe", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # 2. Desinstalador oficial por setup.exe se existir
        import glob
        pf_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        pf = os.environ.get("ProgramFiles", "C:\\Program Files")
        installers = glob.glob(os.path.join(pf_x86, "Microsoft", "Edge", "Application", "*", "Installer", "setup.exe"))
        if not installers:
            installers = glob.glob(os.path.join(pf, "Microsoft", "Edge", "Application", "*", "Installer", "setup.exe"))
        
        if installers:
            for setup_exe in installers:
                cmd = f'"{setup_exe}" --uninstall --system-level --verbose-logging --force-uninstall'
                subprocess.run(cmd, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # 3. Remover pacotes Appx do Edge
        appx_commands = [
            'powershell -NoProfile -Command "Get-AppxPackage -AllUsers -Name *MicrosoftEdge* | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue"',
            'powershell -NoProfile -Command "Get-AppxProvisionedPackage -Online | Where-Object {$_.DisplayName -like \'*MicrosoftEdge*\'} | Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue"'
        ]
        for cmd in appx_commands:
            subprocess.run(cmd, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # 4. Deletar Serviços do Edge do Registro/Sistema
        services = ["edgeupdate", "edgeupdatem"]
        for srv in services:
            subprocess.run(f'sc stop {srv}', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(f'sc delete {srv}', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
        # 5. Deletar Tarefas Agendadas
        tasks = [
            "MicrosoftEdgeUpdateTaskMachineCore",
            "MicrosoftEdgeUpdateTaskMachineUA",
            "MicrosoftEdgeUpdateTaskMachineCoreGlobal",
            "MicrosoftEdgeUpdateTaskMachineUAGlobal"
        ]
        for t in tasks:
            subprocess.run(f'schtasks /delete /tn "{t}" /f', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
        # 6. Remover App Paths do Registro para que o Windows não consiga chamar "msedge"
        reg_commands = [
            'reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\msedge.exe" /f',
            'reg delete "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\msedge.exe" /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\EdgeUpdate" /v DoNotUpdateToEdgeWithChromium /t REG_DWORD /d 1 /f',
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\EdgeUpdate" /v InstallDefault /t REG_DWORD /d 0 /f',
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\EdgeUpdate" /v Install{56EB18C8-B163-40A0-8940-34185C667824} /t REG_DWORD /d 0 /f'
        ]
        for cmd in reg_commands:
            subprocess.run(cmd, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
        # 7. Remover atalhos do Edge da Área de Trabalho e Menu Iniciar
        shortcuts = [
            "C:\\Users\\Public\\Desktop\\Microsoft Edge.lnk",
            "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Microsoft Edge.lnk"
        ]
        user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Default")
        shortcuts.append(os.path.join(user_profile, "Desktop", "Microsoft Edge.lnk"))
        shortcuts.append(os.path.join(user_profile, "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Microsoft Edge.lnk"))
        
        for shortcut in shortcuts:
            if os.path.exists(shortcut):
                try:
                    os.remove(shortcut)
                except Exception:
                    pass
                    
        # 8. Tomar posse e conceder acesso total recursivamente para deletar/renomear pastas
        local_appdata = os.environ.get("LOCALAPPDATA", "C:\\Users\\Default\\AppData\\Local")
        edge_dirs = [
            os.path.join(pf_x86, "Microsoft", "Edge"),
            os.path.join(pf_x86, "Microsoft", "EdgeUpdate"),
            os.path.join(pf_x86, "Microsoft", "EdgeCore"),
            os.path.join(pf_x86, "Microsoft", "EdgeWebView"),
            os.path.join(pf, "Microsoft", "Edge"),
            os.path.join(pf, "Microsoft", "EdgeUpdate"),
            os.path.join(pf, "Microsoft", "EdgeCore"),
            os.path.join(local_appdata, "Microsoft", "Edge"),
            os.path.join(local_appdata, "Microsoft", "EdgeUpdate"),
            os.path.join(local_appdata, "Microsoft", "EdgeSxS")
        ]
        
        for d in edge_dirs:
            if os.path.exists(d):
                # Executar takeown e icacls para liberar permissões travadas por TrustedInstaller
                subprocess.run(f'takeown /f "{d}" /r /d y', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(f'icacls "{d}" /grant *S-1-5-32-544:F /t /c /q', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Tenta deletar fisicamente
                import shutil
                try:
                    shutil.rmtree(d, ignore_errors=True)
                except Exception:
                    pass
                
                # Se ainda sobrar algum arquivo em uso, renomeia a pasta para invalidar o caminho
                if os.path.exists(d):
                    try:
                        import time
                        os.rename(d, d + f"_removed_{int(time.time())}")
                    except Exception:
                        pass
        return True

    def action_remove_edge(self):
        confirm = messagebox.askyesno(
            "Confirmar Remoção do Edge",
            "Deseja realmente remover o Microsoft Edge do Windows 11?\n\n"
            "Isso encerrará o Edge, executará o desinstalador oficial, "
            "removerá os pacotes Appx e bloqueará futuras reinstalações via Windows Update."
        )
        if not confirm: return

        if not is_admin():
            messagebox.showerror("Erro", "Esta operação requer privilégios de Administrador.")
            return

        def run():
            self.root.after(0, lambda: messagebox.showinfo("Remoção em Andamento", "A remoção do Edge foi iniciada em segundo plano. Por favor, aguarde."))
            try:
                self._execute_edge_removal()
                messagebox.showinfo("Sucesso", "O Microsoft Edge foi desinstalado e as políticas de bloqueio de reinstalação foram aplicadas com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro durante a remoção: {e}")

        threading.Thread(target=run, daemon=True).start()

    def action_free_ram(self):
        if not is_admin():
            messagebox.showerror("Erro", "Esta operação requer privilégios de Administrador.")
            return

        def run():
            ram_before = psutil.virtual_memory().available
            import ctypes
            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi
            
            count_cleaned = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pid = proc.info['pid']
                    if pid <= 4:
                        continue
                    handle = kernel32.OpenProcess(0x0400 | 0x0100, False, pid)
                    if handle:
                        if psapi.EmptyWorkingSet(handle):
                            count_cleaned += 1
                        kernel32.CloseHandle(handle)
                except Exception:
                    pass
            
            ram_after = psutil.virtual_memory().available
            freed = (ram_after - ram_before) / (1024 * 1024)
            if freed < 0:
                freed = 0
                
            self.root.after(0, self.update_system_stats)
            self.root.after(0, lambda: messagebox.showinfo("Memória Liberada", f"Memória RAM otimizada com sucesso!\nProcessos limpos: {count_cleaned}\nMemória liberada: ~{freed:.2f} MB."))

        threading.Thread(target=run, daemon=True).start()

    def action_clean_temp(self):
        confirm = messagebox.askyesno("Confirmar Limpeza", "Deseja limpar os arquivos temporários, caches do Windows Update, logs e lixeira agora?")
        if not confirm: return

        if not is_admin():
            messagebox.showerror("Erro", "Esta operação requer privilégios de Administrador.")
            return

        def run():
            subprocess.run("net stop wuauserv", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run("net stop bits", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            clean_paths = [
                os.environ.get("TEMP", ""),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Temp"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Prefetch"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "SoftwareDistribution\\Download"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Logs"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Minidump")
            ]
            
            cleaned_size = 0
            for p in clean_paths:
                if not p or not os.path.exists(p):
                    continue
                for root_dir, dirs, files in os.walk(p):
                    for file in files:
                        fp = os.path.join(root_dir, file)
                        try:
                            cleaned_size += os.path.getsize(fp)
                            os.remove(fp)
                        except Exception:
                            pass
                    for d in dirs:
                        dp = os.path.join(root_dir, d)
                        try:
                            import shutil
                            shutil.rmtree(dp, ignore_errors=True)
                        except Exception:
                            pass

            try:
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            except Exception:
                pass
                
            subprocess.run("net start wuauserv", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run("net start bits", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            size_mb = cleaned_size / (1024 * 1024)
            messagebox.showinfo("Limpeza Concluída", f"Limpeza de temporários concluída!\nForam liberados aproximadamente {size_mb:.2f} MB.")

        threading.Thread(target=run, daemon=True).start()

    def action_high_performance(self):
        if not is_admin():
            messagebox.showerror("Erro", "Esta operação requer privilégios de Administrador.")
            return
        
        try:
            # Habilitar plano de Alto Desempenho
            subprocess.run("powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            messagebox.showinfo("Sucesso", "Plano de energia de Alto Desempenho ativado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível aplicar o plano de energia:\n{e}")

    def action_disable_winsat(self):
        if not is_admin():
            messagebox.showerror("Erro", "Esta operação requer privilégios de Administrador.")
            return
        
        try:
            # Desativar WinSat na Agenda do Windows
            subprocess.run("schtasks /Change /TN \"\\Microsoft\\Windows\\Maintenance\\WinSat\" /DISABLE", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            messagebox.showinfo("Sucesso", "Tarefa WinSat (Avaliação do Sistema) desativada com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível desativar a tarefa:\n{e}")

    def action_disable_fast_startup(self):
        if not is_admin():
            messagebox.showerror("Erro", "Esta operação requer privilégios de Administrador.")
            return
        
        try:
            # Desativar hibernação e inicialização rápida
            subprocess.run("powercfg /hibernate off", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" /v HiberbootEnabled /t REG_DWORD /d 0 /f', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            messagebox.showinfo("Sucesso", "Inicialização Rápida e Hibernação desativadas com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao desativar Inicialização Rápida:\n{e}")

    def _execute_edge_restoration(self):
        # 1. Remover registros de bloqueio
        reg_commands = [
            'reg delete "HKLM\\SOFTWARE\\Microsoft\\EdgeUpdate" /v DoNotUpdateToEdgeWithChromium /f',
            'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\EdgeUpdate" /v InstallDefault /f',
            'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\EdgeUpdate" /v Install{56EB18C8-B163-40A0-8940-34185C667824} /f'
        ]
        for cmd in reg_commands:
            subprocess.run(cmd, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
        # 2. Executar winget para baixar e instalar o Edge
        cmd_winget = 'winget install --id Microsoft.Edge --silent --accept-source-agreements --accept-package-agreements'
        res = subprocess.run(cmd_winget, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if res.returncode != 0:
            # Fallback download MSI
            cmd_ps = 'powershell -NoProfile -Command "Invoke-WebRequest -Uri \'https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/b498f395-5cb3-4876-b633-8a033c467a84/MicrosoftEdgeEnterpriseX64.msi\' -OutFile \'$env:TEMP\\MicrosoftEdge.msi\'; Start-Process msiexec.exe -ArgumentList \'/i $env:TEMP\\MicrosoftEdge.msi /qn /norestart\' -Wait"'
            subprocess.run(cmd_ps, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True

    def action_restore_edge(self):
        confirm = messagebox.askyesno(
            "Confirmar Restauração do Edge",
            "Deseja realmente reinstalar o Microsoft Edge e remover os bloqueios de atualização?"
        )
        if not confirm: return

        if not is_admin():
            messagebox.showerror("Erro", "Esta operação requer privilégios de Administrador.")
            return

        def run():
            self.root.after(0, lambda: messagebox.showinfo("Instalação em Andamento", "A instalação do Edge foi iniciada em segundo plano. Por favor, aguarde."))
            try:
                self._execute_edge_restoration()
                messagebox.showinfo("Sucesso", "O Microsoft Edge foi reinstalado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro durante a reinstalação: {e}")

        threading.Thread(target=run, daemon=True).start()

    def action_flush_dns(self):
        try:
            res = subprocess.run("ipconfig /flushdns", shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                messagebox.showinfo("Sucesso", "Cache do resolvedor DNS limpo com sucesso!")
            else:
                messagebox.showerror("Erro", "Falha ao limpar cache DNS.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar: {e}")

    def check_reg_value(self, path, value_name, expected_val):
        try:
            res = subprocess.run(f'reg query "{path}" /v "{value_name}"', shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if value_name in line:
                        parts = line.split()
                        val = int(parts[-1], 16) if parts[-1].startswith("0x") else int(parts[-1])
                        return val == expected_val
            return False
        except Exception:
            return False

    def check_service_disabled(self, service_name):
        try:
            res = subprocess.run(f'sc qc {service_name}', shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                return "DISABLED" in res.stdout.upper()
            return False
        except Exception:
            return False




def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def elevate():
    # Roda o script de novo solicitando privilégios de administrador
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


if __name__ == "__main__":
    import sys
    import subprocess
    import os

    if "--run-wallpulse-install" in sys.argv:
        try:
            import os
            import subprocess
            base_dir = r"C:\ProgramData\Empresa\WallpaperAgent"
            os.makedirs(base_dir, exist_ok=True)

            ps1_content = r"""$ImageUrl = "http://31.97.251.77:8085/wallpaper.jpg"

$BaseDir = "C:\ProgramData\Empresa\WallpaperAgent"
$DateFile = "$BaseDir\last_hash.txt"
$LogFile = "$BaseDir\agent.log"
$WallpaperCache = "$BaseDir\wallpaper.jpg"
$TempFile = "$BaseDir\temp_wallpaper.jpg"

if (!(Test-Path $BaseDir)) { New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null }

function Write-Log { param($m) "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $m" | Out-File -Append $LogFile }

function Set-Wallpaper {
    param($ImagePath)
    if (!(Test-Path $ImagePath)) { Write-Log "ERRO: Imagem em cache no encontrada!"; return }
    Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name Wallpaper -Value $ImagePath
    Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name WallpaperStyle -Value "2"
    Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name TileWallpaper -Value "0"
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Wallpaper {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
}
"@
    [Wallpaper]::SystemParametersInfo(0x0014, 0, $ImagePath, 0x0001 -bor 0x0002)
    Write-Log ">>> Wallpaper aplicado: $ImagePath"
}

while ($true) {
    try {
        Write-Log "=== INCIO ==="
        Write-Log "Baixando imagem de: $ImageUrl"

        Invoke-WebRequest -Uri $ImageUrl -OutFile $TempFile -UseBasicParsing -ErrorAction Stop

        if (!(Test-Path $TempFile)) {
            Write-Log "ERRO: Falha ao baixar a imagem!"
        } else {
            $CurrentHash = (Get-FileHash -Path $TempFile -Algorithm MD5).Hash
            Write-Log "Hash da imagem baixada: $CurrentHash"

            $SavedHash = if (Test-Path $DateFile) { Get-Content $DateFile -Raw } else { $null }
            Write-Log "Hash salvo: $SavedHash"

            if ($CurrentHash -ne $SavedHash -or !(Test-Path $WallpaperCache)) {
                Write-Log ">>> Nova imagem detectada! Copiando..."
                Move-Item -Path $TempFile -Destination $WallpaperCache -Force
                $CurrentHash | Out-File $DateFile -Encoding UTF8 -Force
                Set-Wallpaper -ImagePath $WallpaperCache
            } else {
                Write-Log "Sem alteraes (hash idntico)."
                Remove-Item -Path $TempFile -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {
        Write-Log "ERRO CRTICO: $($_.Exception.Message)"
        if (Test-Path $TempFile) { Remove-Item -Path $TempFile -Force -ErrorAction SilentlyContinue }
    }
    Write-Log "=== FIM DO CICLO ==="
    Start-Sleep -Seconds 600
}"""
            
            with open(os.path.join(base_dir, "WallpaperAgent.ps1"), "w", encoding="utf-8") as f_ps1:
                f_ps1.write(ps1_content)
                
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", "Unregister-ScheduledTask -TaskName 'WallpaperAgent' -Confirm:$false -ErrorAction SilentlyContinue"], creationflags=subprocess.CREATE_NO_WINDOW)
            
            startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
            vbs_path = os.path.join(startup_folder, "WallpaperAgent.vbs")
            
            vbs_content = 'Set objShell = CreateObject("WScript.Shell")\n'
            vbs_content += 'objShell.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File ""' + base_dir + '\\WallpaperAgent.ps1""", 0, False\n'
            
            with open(vbs_path, "w", encoding="ascii") as f_vbs:
                f_vbs.write(vbs_content)
                
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", "Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match 'WallpaperAgent.ps1' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"], creationflags=subprocess.CREATE_NO_WINDOW)
            
            subprocess.Popen(["wscript.exe", vbs_path], creationflags=subprocess.CREATE_NO_WINDOW)
            
        except Exception as e:
            pass
        sys.exit(0)

    if "--run-wallpulse-uninstall" in sys.argv:
        try:
            import os
            import subprocess
            import shutil
            
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", "Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match 'WallpaperAgent.ps1' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"], creationflags=subprocess.CREATE_NO_WINDOW)
            
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", "Unregister-ScheduledTask -TaskName 'WallpaperAgent' -Confirm:$false -ErrorAction SilentlyContinue"], creationflags=subprocess.CREATE_NO_WINDOW)
            
            startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
            vbs_path = os.path.join(startup_folder, "WallpaperAgent.vbs")
            if os.path.exists(vbs_path):
                os.remove(vbs_path)
                
            base_dir = r"C:\ProgramData\Empresa\WallpaperAgent"
            if os.path.exists(base_dir):
                shutil.rmtree(base_dir, ignore_errors=True)
                
        except Exception as e:
            pass
        sys.exit(0)

    if "--run-inventory" in sys.argv:
        try:
            import inventory_module
            import json
            config_path = r"C:\ProgramData\ToolsWin\inventory_config.json"
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    cfg = json.load(f)
                inventory_module.send_heartbeat(cfg.get("API_URL"), cfg.get("AGENT_API_KEY"), cfg.get("EMPRESA_ID"))
        except Exception as e:
            pass
        sys.exit(0)
        
    if "--run-clearsite" in sys.argv:
        try:
            sys.path.append(get_resource_path("clear_site"))
            import clear_skychart
            clear_skychart.main()
        except Exception as e:
            pass
        sys.exit(0)

    # Garantir codificação UTF-8 para saídas em lote
    sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None

    # Tenta obter privilégios de admin se não tiver
    if not is_admin():
        elevate()
    else:
        root = tk.Tk()
        sv_ttk.set_theme("dark")
        app = WindowsOptimizerApp(root)
        root.mainloop()
