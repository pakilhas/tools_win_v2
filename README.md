# Tools Win V2 (v2.0.1)

**Tools Win V2** é uma ferramenta de desktop moderna em Python desenvolvida especificamente para otimização, privacidade, manutenção do Windows (com foco no Windows 11) e gerenciamento completo de contas de usuário locais.

Desenvolvido por: **Pablo Carvalho**  
Ano: **2026**  
Versão do App: **2.0.1**

---

## 🚀 Funcionalidades Principais

1. **📊 Painel & Status**:
   * Monitoramento de hardware em tempo real (Uso de CPU, RAM e Disco C:).
   * Limpeza de arquivos temporários e caches de sistema de forma rápida.
   * Ativação automática do perfil de energia de "Alto Desempenho".
   * Desativação do agendador `WinSat` (reduz uso de disco em segundo plano) e da Inicialização Rápida.

2. **🛠️ Correção & Reparos (Execução Assíncrona)**:
   * **DISM Restore Health**: Reparo da imagem do Windows.
   * **SFC Scannow**: Verificação e correção de arquivos corrompidos.
   * **CHKDSK Scheduler**: Agendamento de varredura física do disco no boot.
   * **Reset do Windows Update**: Parada de serviços, limpeza de cache (`SoftwareDistribution` e `catroot2`) e reinicialização automática do agente.
   * **Flush DNS**: Limpeza rápida do cache de rede.

3. **🤖 Desativar IA & Privacidade (Debloat)**:
   * Desativação do **Windows Copilot** via registro.
   * Desativação do **AI Recall** (Windows 11) via registro.
   * Desativação completa da **Cortana**.
   * Bloqueio da busca Web do Bing dentro do Menu Iniciar.
   * Parada e desativação de serviços de **Telemetria e Diagnósticos** (DiagTrack e dmwappushservice).
   * Desativação de serviços raramente usados para acelerar o sistema (Xbox, Fax, Carteira, Registro Remoto).
   * Remoção automatizada do **Microsoft Edge** do sistema.
   * Bloqueio corporativo de novos perfis e Modo Convidado no **Google Chrome** via políticas de registro.

4. **👥 Contas de Usuários (Agnóstico de Idioma)**:
   * Listagem de todas as contas locais.
   * Identificação de contas Administradoras usando SIDs universais (`S-1-5-32-544`).
   * **Alterar senha de qualquer usuário selecionado**.
   * Alternar privilégios administrativos (Adicionar ou remover do grupo de administradores).
   * Ativar ou Desativar contas locais.
   * Criar novos usuários ou Excluir permanentemente contas locais.

5. **🌐 Ferramentas de Rede**:
   * Alterar DNS de adaptadores de rede ativos para **Cloudflare (1.1.1.1)** ou **Google (8.8.8.8)**, ou restaurar para DHCP padrão.
   * Teste integrado de latência (Ping) com feedback visual.

---

## 📦 Como Executar e Compilar

O arquivo **[ExecuteScript.bat](ExecuteScript.bat)** localizado na raiz é o inicializador unificado da ferramenta.

1. **Executar em modo desenvolvimento (Interface Python)**:
   * Abra o `ExecuteScript.bat` com duplo clique (ele solicitará elevação de Administrador automaticamente).
   * Selecione a opção **`1`**.

2. **Compilar para Executável (.exe independente)**:
   * Abra o `ExecuteScript.bat`.
   * Selecione a opção **`2`**.
   * O script irá converter automaticamente o arquivo `logo.jpg` em `logo.ico` utilizando a biblioteca `Pillow`, e em seguida compilará a aplicação por meio do `PyInstaller`.
   * O executável final estará pronto e disponível na pasta **`dist/Tools Win V2.exe`** com UAC de administrador e ícone personalizado.

---

## 🛠️ Requisitos e Tecnologias
* **Linguagem**: Python 3.x
* **Bibliotecas nativas**: `tkinter` (para a GUI escura moderna), `winreg`, `subprocess`, `ctypes`.
* **Dependências externas** (instaladas automaticamente na primeira compilação):
  * `psutil` (monitoramento de recursos)
  * `Pillow` (conversão e exibição de imagem da logo)
  * `PyInstaller` (gerador do executável `.exe`)
