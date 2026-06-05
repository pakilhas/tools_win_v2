import os
import subprocess
import sys

def main():
    print("=== Iniciando Processo de Compilacao do Executavel (Tools Win V2) ===")
    
    # 1. Verificar se o PyInstaller esta instalado, se nao, instalar
    try:
        import PyInstaller
        print("[*] PyInstaller ja esta instalado.")
    except ImportError:
        print("[!] PyInstaller nao encontrado. Instalando via pip...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("[+] PyInstaller instalado com sucesso!")
        except Exception as e:
            print(f"[-] Erro ao instalar PyInstaller: {e}")
            sys.exit(1)

    # 2. Converter logo.jpg para logo.ico usando Pillow
    logo_ico_exists = False
    if os.path.exists("logo.jpg"):
        print("[*] Encontrado logo.jpg. Convertendo para formato .ico...")
        try:
            from PIL import Image
            img = Image.open("logo.jpg")
            # Salvar como arquivo .ico contendo multiplos tamanhos recomendados para Windows
            img.save("logo.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print("[+] logo.ico gerado com sucesso!")
            logo_ico_exists = True
        except Exception as e:
            print(f"[!] Erro ao converter logo.jpg para .ico: {e}")
            print("[*] A compilaçao continuara sem icone personalizado.")

    # 3. Configurar o comando do PyInstaller
    # --onefile: Empacota em um unico executavel
    # --noconsole: Oculta a janela de comando do console (já que temos interface grafica)
    # --uac-admin: Solicita privilegios de Administrador automaticamente ao executar
    # --add-data: Inclui o logo.jpg dentro do executavel
    # --name: Nome do arquivo final gerado (Tools Win V2)
    # --icon: Icone do arquivo executavel (.ico)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--uac-admin",
        "--add-data=logo.jpg;.",
        "--name=Tools Win V2",
        "app.py"
    ]
    
    # Se o arquivo .ico foi gerado com sucesso, adiciona ao comando do PyInstaller
    if logo_ico_exists and os.path.exists("logo.ico"):
        command.append("--icon=logo.ico")

    print(f"[*] Executando comando: {' '.join(command)}")
    
    try:
        # Executar a compilacao
        subprocess.run(command, check=True)
        print("\n[+] Compilacao concluida com sucesso!")
        print("[+] O executavel 'Tools Win V2.exe' esta localizado na pasta 'dist/'.")
    except subprocess.CalledProcessError as e:
        print(f"\n[-] Erro durante a compilacao com PyInstaller: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
