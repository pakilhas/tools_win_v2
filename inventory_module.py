import os
import platform
import socket
import psutil
import requests
import uuid
import subprocess
import threading
import time

def get_or_create_uuid():
    uuid_file = ".machine_uuid"
    if os.path.exists(uuid_file):
        with open(uuid_file, 'r') as f:
            return f.read().strip()
    else:
        new_uuid = str(uuid.uuid4())
        with open(uuid_file, 'w') as f:
            f.write(new_uuid)
        return new_uuid

def get_system_info():
    os_info = f"{platform.system()} {platform.release()}"
    
    mem = psutil.virtual_memory()
    mem_total_gb = round(mem.total / (1024**3), 2)
    
    try:
        disk_path = '/' if platform.system() != 'Windows' else 'C:\\\\'
        disk = psutil.disk_usage(disk_path)
        disk_total_gb = round(disk.total / (1024**3), 2)
    except:
        disk_total_gb = 0

    cpu_info = f"{platform.processor()} - {psutil.cpu_count(logical=False)} Cores"
    if platform.system() == "Windows":
        cpu_out = ""
        try:
            cpu_out = subprocess.check_output(
                'powershell -Command "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name"',
                shell=True, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).decode().strip()
            if "Get-CimInstance" in cpu_out:
                cpu_out = ""
        except Exception:
            pass
            
        if not cpu_out:
            try:
                wmic_out = subprocess.check_output(
                    'wmic cpu get name', shell=True, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                ).decode().strip()
                if "Name" in wmic_out:
                    cpu_out = wmic_out.split('\\n')[1].strip()
            except Exception:
                pass
                
        if cpu_out:
            cpu_out = " ".join(cpu_out.split())
            cpu_info = f"{cpu_out} - {psutil.cpu_count(logical=False)} Cores"

    ip_address = socket.gethostbyname(socket.gethostname())
    mac_address = "Desconhecido"
    
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == psutil.AF_LINK:
                if snic.address and snic.address != '00:00:00:00:00:00':
                    mac_address = snic.address
                    break

    fabricante = "Desconhecido"
    serial = "Desconhecido"
    if platform.system() == "Windows":
        try:
            serial_out = subprocess.check_output(
                'powershell -Command "Get-CimInstance Win32_BIOS | Select-Object -ExpandProperty SerialNumber"', 
                shell=True, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).decode().strip()
            if serial_out:
                serial = serial_out
                
            vendor_out = subprocess.check_output(
                'powershell -Command "Get-CimInstance Win32_ComputerSystem | Select-Object -ExpandProperty Manufacturer"', 
                shell=True, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).decode().strip()
            if vendor_out:
                fabricante = vendor_out
        except Exception:
            pass

    return {
        "tipo": "Desktop/Notebook",
        "fabricante": fabricante, 
        "modelo": socket.gethostname(),
        "serial": serial,
        "sistema_operacional": os_info,
        "cpu": cpu_info,
        "memoria_total": f"{mem_total_gb} GB",
        "disco_total": f"{disk_total_gb} GB",
        "placa_rede": "Padrão",
        "mac_address": mac_address,
        "ip_address": ip_address
    }

def get_open_processes():
    processos = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info']):
        try:
            info = proc.info
            if info['name']:
                mem_mb = round(info['memory_info'].rss / (1024 * 1024), 2) if info['memory_info'] else 0
                processos.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "username": info['username'] or "N/A",
                    "mem_mb": mem_mb
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processos

def send_heartbeat(api_url, api_key, empresa_id):
    agente_uuid = get_or_create_uuid()
    info = get_system_info()
    processos = get_open_processes()
    
    payload = {
        "agente_uuid": agente_uuid,
        "empresa_id": int(empresa_id),
        "dados_adicionais": {
            "is_monitor": True,
            "processos": processos
        },
        **info
    }

    headers = {
        "Content-Type": "application/json",
        "x-agent-token": api_key
    }

    url = f"{api_url}/api/agente/heartbeat"
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
