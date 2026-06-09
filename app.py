import sys
import os
import ctypes
import subprocess
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import psutil

# Cores do Tema Escuro Moderno
COLOR_BG = "#121214"
COLOR_SIDEBAR = "#1a1a1e"
COLOR_CARD = "#202024"
COLOR_TEXT = "#ffffff"
COLOR_MUTED = "#8a8a93"
COLOR_ACCENT = "#3b82f6"       # Azul moderno
COLOR_SUCCESS = "#10b981"      # Esmeralda
COLOR_WARNING = "#f59e0b"      # Âmbar
COLOR_DANGER = "#ef4444"       # Vermelho
COLOR_BTN_HOVER = "#2563eb"
COLOR_BTN_BG = "#2a2a30"

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
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(True, True)

        # Configurar ícone da janela
        try:
            from PIL import Image, ImageTk
            logo_path = resource_path("logo.jpg")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                self.win_icon = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self.win_icon)
        except Exception as e:
            print(f"Erro ao carregar ícone da janela: {e}")

        # Configurar estilos do TTK
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('.', background=COLOR_BG, foreground=COLOR_TEXT)
        self.style.configure('TFrame', background=COLOR_BG)
        self.style.configure('Card.TFrame', background=COLOR_CARD, relief='flat')
        self.style.configure('Sidebar.TFrame', background=COLOR_SIDEBAR)
        
        # Estilo customizado para Treeview (Tabela de Usuários)
        self.style.configure('Treeview',
            background=COLOR_CARD,
            foreground=COLOR_TEXT,
            rowheight=30,
            fieldbackground=COLOR_CARD,
            borderwidth=0
        )
        self.style.map('Treeview', background=[('selected', COLOR_ACCENT)])
        self.style.configure('Treeview.Heading',
            background=COLOR_SIDEBAR,
            foreground=COLOR_TEXT,
            borderwidth=1,
            font=('Segoe UI', 10, 'bold')
        )

        # Estado da aplicação
        self.running_thread = None
        self.admin_group_name = None

        # Detectar nome do grupo de administradores (idioma-independente)
        self.detect_admin_group_name()

        # Layout Principal
        self.create_layout()

        # Iniciar monitoramento de recursos
        self.update_system_stats()

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

    def create_layout(self):
        # Sidebar (Esquerda) - Navegação
        self.sidebar = ttk.Frame(self.root, style='Sidebar.TFrame', width=220)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        # Logo da Sidebar
        try:
            from PIL import Image, ImageTk
            logo_path = resource_path("logo.jpg")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                img = img.resize((70, 70), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                lbl_logo = tk.Label(self.sidebar, image=self.logo_img, bg=COLOR_SIDEBAR)
                lbl_logo.pack(pady=(20, 5))
        except Exception as e:
            print(f"Erro ao carregar logo na sidebar: {e}")

        # Título da Sidebar
        title_label = tk.Label(
            self.sidebar, text="Tools Win V2", fg=COLOR_TEXT, bg=COLOR_SIDEBAR,
            font=('Segoe UI Semibold', 16), pady=5
        )
        title_label.pack(fill='x')

        # Separador na Sidebar
        sep = tk.Frame(self.sidebar, height=1, bg="#2d2d35")
        sep.pack(fill='x', padx=15, pady=5)

        # Botões de Navegação da Sidebar
        self.nav_buttons = {}
        tabs = [
            ("dashboard", "📊 Painel & Status", self.show_dashboard_tab),
            ("repair", "🛠 Correção & Reparos", self.show_repair_tab),
            ("debloat", "🤖 Privacidade & IA", self.show_debloat_tab),
            ("users", "👥 Contas de Usuários", self.show_users_tab),
            ("network", "🌐 Ferramentas de Rede", self.show_network_tab),
        ]

        for tab_id, label, func in tabs:
            btn = tk.Button(
                self.sidebar, text=label, anchor='w', bg=COLOR_SIDEBAR, fg=COLOR_TEXT,
                activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT,
                relief='flat', bd=0, font=('Segoe UI', 11), padx=20, pady=10,
                command=lambda f=func, t_id=tab_id: self.select_tab(t_id, f)
            )
            btn.pack(fill='x', padx=10, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: self.on_btn_hover(b))
            btn.bind("<Leave>", lambda e, b=btn: self.on_btn_leave(b))
            self.nav_buttons[tab_id] = btn

        # Rodapé da Sidebar (Copyright e Versão)
        lbl_footer = tk.Label(
            self.sidebar, text="Desenvolvido por Pablo Carvalho\n© 2026 | Versão 2.0.1",
            fg=COLOR_MUTED, bg=COLOR_SIDEBAR, font=('Segoe UI', 8), justify='center'
        )
        lbl_footer.pack(side='bottom', pady=(5, 15))

        # Rodapé da Sidebar (Informa se está como Admin)
        is_adm = is_admin()
        adm_text = "🛡️ ADMIN" if is_adm else "⚠️ USUÁRIO COMUM"
        adm_color = COLOR_SUCCESS if is_adm else COLOR_WARNING
        
        lbl_adm = tk.Label(
            self.sidebar, text=adm_text, fg=adm_color, bg=COLOR_SIDEBAR,
            font=('Segoe UI Bold', 10), pady=10
        )
        lbl_adm.pack(side='bottom', fill='x')

        # Conteúdo Principal (Direita)
        self.content_area = ttk.Frame(self.root)
        self.content_area.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        # Inicializar a aba do Dashboard
        self.active_tab_id = None
        self.select_tab("dashboard", self.show_dashboard_tab)

    def select_tab(self, tab_id, show_func):
        if self.active_tab_id == tab_id:
            return

        # Limpar área de conteúdo
        for child in self.content_area.winfo_children():
            child.destroy()

        # Resetar botões de navegação
        for tid, btn in self.nav_buttons.items():
            btn.configure(bg=COLOR_SIDEBAR, fg=COLOR_TEXT)

        # Destacar o botão ativo
        self.nav_buttons[tab_id].configure(bg=COLOR_ACCENT, fg=COLOR_TEXT)
        self.active_tab_id = tab_id

        # Carregar a nova aba
        show_func()

    def on_btn_hover(self, btn):
        # Apenas muda cor se não for o botão selecionado
        for tid, b in self.nav_buttons.items():
            if b == btn and tid == self.active_tab_id:
                return
        btn.configure(bg="#2d2d35")

    def on_btn_leave(self, btn):
        for tid, b in self.nav_buttons.items():
            if b == btn and tid == self.active_tab_id:
                return
        btn.configure(bg=COLOR_SIDEBAR)

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
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Título
        lbl_title = tk.Label(
            scrollable_frame, text="Painel do Sistema", fg=COLOR_TEXT, bg=COLOR_BG,
            font=('Segoe UI Semibold', 18), anchor='w'
        )
        lbl_title.pack(fill='x', pady=(0, 15))

        # Grid de Status de Recursos (CPU, RAM, Disco)
        stats_frame = ttk.Frame(scrollable_frame)
        stats_frame.pack(fill='x', pady=5)
        stats_frame.columnconfigure((0, 1, 2), weight=1, uniform="equal")

        # Card CPU
        card_cpu = ttk.Frame(stats_frame, style='Card.TFrame', padding=15)
        card_cpu.grid(row=0, column=0, padx=(0, 10), sticky='nsew')
        tk.Label(card_cpu, text="Processador (CPU)", fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI', 10)).pack(anchor='w')
        self.lbl_cpu_val = tk.Label(card_cpu, text="0%", fg=COLOR_TEXT, bg=COLOR_CARD, font=('Segoe UI Semibold', 22))
        self.lbl_cpu_val.pack(anchor='w', pady=5)
        self.canvas_cpu = tk.Canvas(card_cpu, height=8, bg="#2d2d35", highlightthickness=0, bd=0)
        self.canvas_cpu.pack(fill='x', pady=5)

        # Card RAM
        card_ram = ttk.Frame(stats_frame, style='Card.TFrame', padding=15)
        card_ram.grid(row=0, column=1, padx=5, sticky='nsew')
        tk.Label(card_ram, text="Memória RAM", fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI', 10)).pack(anchor='w')
        self.lbl_ram_val = tk.Label(card_ram, text="0 / 0 GB (0%)", fg=COLOR_TEXT, bg=COLOR_CARD, font=('Segoe UI Semibold', 16))
        self.lbl_ram_val.pack(anchor='w', pady=10)
        self.canvas_ram = tk.Canvas(card_ram, height=8, bg="#2d2d35", highlightthickness=0, bd=0)
        self.canvas_ram.pack(fill='x', pady=5)

        # Card Disco
        card_disk = ttk.Frame(stats_frame, style='Card.TFrame', padding=15)
        card_disk.grid(row=0, column=2, padx=(10, 0), sticky='nsew')
        tk.Label(card_disk, text="Disco Principal (C:)", fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI', 10)).pack(anchor='w')
        self.lbl_disk_val = tk.Label(card_disk, text="0 / 0 GB (0%)", fg=COLOR_TEXT, bg=COLOR_CARD, font=('Segoe UI Semibold', 16))
        self.lbl_disk_val.pack(anchor='w', pady=10)
        self.canvas_disk = tk.Canvas(card_disk, height=8, bg="#2d2d35", highlightthickness=0, bd=0)
        self.canvas_disk.pack(fill='x', pady=5)

        # Seção de Ações Rápidas de Otimização
        quick_frame = ttk.Frame(scrollable_frame, style='Card.TFrame', padding=20)
        quick_frame.pack(fill='both', expand=True, pady=(20, 0))

        tk.Label(
            quick_frame, text="Ações Rápidas de Otimização", fg=COLOR_TEXT, bg=COLOR_CARD,
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
            
            frame_act = tk.Frame(btn_container, bg=COLOR_CARD, bd=1, highlightbackground="#2d2d35", highlightthickness=1)
            frame_act.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            lbl_title = tk.Label(frame_act, text=title, fg=COLOR_TEXT, bg=COLOR_CARD, font=('Segoe UI Bold', 11))
            lbl_title.pack(anchor='w', padx=15, pady=(10, 2))
            
            lbl_desc = tk.Label(frame_act, text=desc, fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI', 9), justify='left', wraplength=300)
            lbl_desc.pack(anchor='w', padx=15, pady=(0, 10))
            
            btn_act = tk.Button(
                frame_act, text="Executar", bg=COLOR_BTN_BG, fg=COLOR_TEXT, relief='flat', bd=0,
                font=('Segoe UI Semibold', 9), padx=15, pady=5, activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT,
                command=func
            )
            btn_act.pack(anchor='e', padx=15, pady=(0, 15))
            btn_act.bind("<Enter>", lambda e, b=btn_act: b.configure(bg=COLOR_ACCENT))
            btn_act.bind("<Leave>", lambda e, b=btn_act: b.configure(bg=COLOR_BTN_BG))

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

    # ----------------------------------------------------
    # ABA 2: CORREÇÃO & REPAROS
    # ----------------------------------------------------
    def show_repair_tab(self):
        lbl_title = tk.Label(
            self.content_area, text="Ferramentas de Correção do Windows", fg=COLOR_TEXT, bg=COLOR_BG,
            font=('Segoe UI Semibold', 18), anchor='w'
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
        ]

        for i, (name, desc, cmd) in enumerate(rep_tools):
            btn_tool = tk.Button(
                buttons_frame, text=name, bg=COLOR_BTN_BG, fg=COLOR_TEXT, relief='flat', bd=0,
                font=('Segoe UI Semibold', 10), pady=10, activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT,
                command=lambda c=cmd, n=name: self.run_system_tool(c, n)
            )
            btn_tool.pack(fill='x', pady=4)
            btn_tool.bind("<Enter>", lambda e, b=btn_tool: b.configure(bg=COLOR_ACCENT))
            btn_tool.bind("<Leave>", lambda e, b=btn_tool: b.configure(bg=COLOR_BTN_BG))

        # Console Log
        log_frame = ttk.Frame(self.content_area, style='Card.TFrame', padding=15)
        log_frame.pack(fill='both', expand=True, pady=(15, 0))

        tk.Label(log_frame, text="Log de Execução", fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI Semibold', 11)).pack(anchor='w', pady=(0, 5))
        
        # Scrolled Text Box
        self.text_log = tk.Text(
            log_frame, bg="#18181b", fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
            font=('Consolas', 10), borderwidth=0, highlightthickness=1, highlightbackground="#2d2d35"
        )
        self.text_log.pack(fill='both', expand=True)
        self.text_log.configure(state='disabled')

    def log(self, message):
        self.text_log.configure(state='normal')
        self.text_log.insert(tk.END, message)
        self.text_log.see(tk.END)
        self.text_log.configure(state='disabled')

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
            self.running_thread = threading.Thread(target=self.run_raw_cmd, args=(cmd_key,), daemon=True)
            self.running_thread.start()

    def run_raw_cmd(self, command):
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                shell=True, text=True, bufsize=1, encoding='utf-8', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in process.stdout:
                self.root.after(0, self.log, line)
            
            process.communicate()
            rc = process.returncode
            self.root.after(0, self.log, f"\nProcesso concluído com código: {rc}\n")
        except Exception as e:
            self.root.after(0, self.log, f"Erro na execução do comando: {e}\n")

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
        lbl_title = tk.Label(
            self.content_area, text="Gerenciador de IA, Privacidade & Debloat", fg=COLOR_TEXT, bg=COLOR_BG,
            font=('Segoe UI Semibold', 18), anchor='w'
        )
        lbl_title.pack(fill='x', pady=(0, 15))

        container = ttk.Frame(self.content_area, style='Card.TFrame', padding=15)
        container.pack(fill='both', expand=True)

        tk.Label(
            container, text="Gerencie individualmente as opções de telemetria, IA e navegadores. Use os botões 'Desativar' ou 'Ativar' correspondentes.", 
            fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI Semibold', 10), wraplength=700, justify='left'
        ).pack(anchor='w', pady=(0, 15))

        canvas = tk.Canvas(container, bg=COLOR_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLOR_CARD)

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
            row_frame = tk.Frame(scroll_frame, bg=COLOR_CARD, bd=0, highlightbackground="#2d2d35", highlightthickness=1)
            row_frame.pack(fill='x', pady=4, ipady=4)
            
            text_frame = tk.Frame(row_frame, bg=COLOR_CARD)
            text_frame.pack(side='left', fill='x', expand=True, padx=15, pady=5)
            
            lbl_title = tk.Label(text_frame, text=title, fg=COLOR_TEXT, bg=COLOR_CARD, font=('Segoe UI Bold', 11), anchor='w')
            lbl_title.pack(fill='x')
            lbl_desc = tk.Label(text_frame, text=desc, fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI', 9), anchor='w')
            lbl_desc.pack(fill='x')
            
            lbl_status = tk.Label(row_frame, text="Carregando...", fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI Bold', 10), width=15, anchor='center')
            lbl_status.pack(side='left', padx=10)
            self.status_labels[key] = lbl_status
            
            btn_frame = tk.Frame(row_frame, bg=COLOR_CARD)
            btn_frame.pack(side='right', padx=15)
            
            btn_disable = tk.Button(
                btn_frame, text="Desativar", bg="#ef4444", fg=COLOR_TEXT, relief='flat', bd=0,
                font=('Segoe UI Semibold', 9), width=10, activebackground="#dc2626", activeforeground=COLOR_TEXT,
                command=lambda f=df_func, k=key, n=title: self.execute_single_action(f, k, f"Desativar {n}")
            )
            btn_disable.pack(side='left', padx=3)
            
            btn_enable = tk.Button(
                btn_frame, text="Ativar", bg="#10b981", fg=COLOR_TEXT, relief='flat', bd=0,
                font=('Segoe UI Semibold', 9), width=10, activebackground="#059669", activeforeground=COLOR_TEXT,
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
            lbl.configure(text=txt, fg=color)

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
        lbl_title = tk.Label(
            self.content_area, text="Gerenciador de Usuários do Windows", fg=COLOR_TEXT, bg=COLOR_BG,
            font=('Segoe UI Semibold', 18), anchor='w'
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

        tk.Label(actions_frame, text="Ações do Usuário", fg=COLOR_TEXT, bg=COLOR_CARD, font=('Segoe UI Bold', 11)).pack(anchor='w', pady=(0, 15))

        btn_pass = tk.Button(
            actions_frame, text="🔑 Trocar Senha", bg=COLOR_BTN_BG, fg=COLOR_TEXT, relief='flat', bd=0,
            font=('Segoe UI Semibold', 10), pady=8, activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT,
            command=self.user_change_password
        )
        btn_pass.pack(fill='x', pady=4)

        self.btn_toggle_admin = tk.Button(
            actions_frame, text="🛡️ Alternar Admin", bg=COLOR_BTN_BG, fg=COLOR_TEXT, relief='flat', bd=0,
            font=('Segoe UI Semibold', 10), pady=8, activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT,
            command=self.user_toggle_admin
        )
        self.btn_toggle_admin.pack(fill='x', pady=4)

        self.btn_toggle_status = tk.Button(
            actions_frame, text="🔌 Ativar/Desativar", bg=COLOR_BTN_BG, fg=COLOR_TEXT, relief='flat', bd=0,
            font=('Segoe UI Semibold', 10), pady=8, activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT,
            command=self.user_toggle_status
        )
        self.btn_toggle_status.pack(fill='x', pady=4)

        # Separador de Ações Globais
        tk.Frame(actions_frame, height=1, bg="#2d2d35").pack(fill='x', pady=15)

        btn_create = tk.Button(
            actions_frame, text="➕ Novo Usuário", bg=COLOR_SUCCESS, fg=COLOR_TEXT, relief='flat', bd=0,
            font=('Segoe UI Semibold', 10), pady=8, activebackground=COLOR_SUCCESS, activeforeground=COLOR_TEXT,
            command=self.user_create
        )
        btn_create.pack(fill='x', pady=4)

        btn_delete = tk.Button(
            actions_frame, text="❌ Excluir Usuário", bg=COLOR_DANGER, fg=COLOR_TEXT, relief='flat', bd=0,
            font=('Segoe UI Semibold', 10), pady=8, activebackground=COLOR_DANGER, activeforeground=COLOR_TEXT,
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
        lbl_title = tk.Label(
            self.content_area, text="Ferramentas de Rede", fg=COLOR_TEXT, bg=COLOR_BG,
            font=('Segoe UI Semibold', 18), anchor='w'
        )
        lbl_title.pack(fill='x', pady=(0, 15))

        container = ttk.Frame(self.content_area)
        container.pack(fill='both', expand=True)

        # Card de DNS Changer (Esquerda)
        dns_frame = ttk.Frame(container, style='Card.TFrame', padding=15)
        dns_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        tk.Label(dns_frame, text="⚡ Alterar DNS do Adaptador", fg=COLOR_TEXT, bg=COLOR_CARD, font=('Segoe UI Bold', 12)).pack(anchor='w', pady=(0, 10))
        
        tk.Label(dns_frame, text="Selecione o Adaptador de Rede:", fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI', 9)).pack(anchor='w')
        self.combo_adapters = ttk.Combobox(dns_frame, state='readonly', font=('Segoe UI', 10))
        self.combo_adapters.pack(fill='x', pady=5)

        tk.Label(dns_frame, text="Selecione o Servidor DNS:", fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI', 9)).pack(anchor='w', pady=(10, 0))
        self.combo_dns = ttk.Combobox(
            dns_frame, state='readonly', font=('Segoe UI', 10),
            values=["Cloudflare DNS (1.1.1.1 / 1.0.0.1)", "Google DNS (8.8.8.8 / 8.8.4.4)", "Restaurar Padrão (Obter DHCP)"]
        )
        self.combo_dns.set("Cloudflare DNS (1.1.1.1 / 1.0.0.1)")
        self.combo_dns.pack(fill='x', pady=5)

        btn_apply_dns = tk.Button(
            dns_frame, text="Aplicar DNS", bg=COLOR_ACCENT, fg=COLOR_TEXT, relief='flat', bd=0,
            font=('Segoe UI Semibold', 10), pady=10, activebackground=COLOR_BTN_HOVER, activeforeground=COLOR_TEXT,
            command=self.network_apply_dns
        )
        btn_apply_dns.pack(fill='x', pady=(20, 0))

        # Card de Ping Test (Direita)
        ping_frame = ttk.Frame(container, style='Card.TFrame', padding=15, width=350)
        ping_frame.pack(side='right', fill='both')
        ping_frame.pack_propagate(False)

        tk.Label(ping_frame, text="📡 Testar Latência (Ping)", fg=COLOR_TEXT, bg=COLOR_CARD, font=('Segoe UI Bold', 12)).pack(anchor='w', pady=(0, 10))

        tk.Label(ping_frame, text="Endereço de Destino (Ex: google.com):", fg=COLOR_MUTED, bg=COLOR_CARD, font=('Segoe UI', 9)).pack(anchor='w')
        self.entry_ping = tk.Entry(
            ping_frame, bg="#18181b", fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
            font=('Segoe UI', 10), borderwidth=0, highlightthickness=1, highlightbackground="#2d2d35"
        )
        self.entry_ping.insert(0, "1.1.1.1")
        self.entry_ping.pack(fill='x', pady=5, ipady=5)

        btn_ping = tk.Button(
            ping_frame, text="Iniciar Teste", bg=COLOR_BTN_BG, fg=COLOR_TEXT, relief='flat', bd=0,
            font=('Segoe UI Semibold', 10), pady=8, activebackground=COLOR_ACCENT, activeforeground=COLOR_TEXT,
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
    # Garantir codificação UTF-8 para saídas em lote
    sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None

    # Tenta obter privilégios de admin se não tiver
    if not is_admin():
        elevate()
    else:
        root = tk.Tk()
        app = WindowsOptimizerApp(root)
        root.mainloop()
