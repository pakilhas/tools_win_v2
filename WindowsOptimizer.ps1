# Script de Otimização e Rede para Windows
# Compatível com Windows 7, 8, 10 e 11
# Requer execução como administrador

# Verificar se está sendo executado como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Este script requer privilegios de administrador. Executando como administrador..." -ForegroundColor Yellow
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# Configurar política de execução para esta sessão
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force -ErrorAction SilentlyContinue

# Funções de compatibilidade para versões mais antigas do Windows
function Test-CommandExists {
    param($command)
    return (Get-Command $command -ErrorAction SilentlyContinue) -ne $null
}

function Get-NetIPConfigurationCompat {
    try {
        if (Test-CommandExists "Get-NetIPConfiguration") {
            return Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway -ne $null}
        } else {
            return Get-WmiObject -Class Win32_NetworkAdapterConfiguration -Filter "IPEnabled = 'True'"
        }
    } catch { return $null }
}

function Get-DnsClientServerAddressCompat {
    param($AddressFamily)
    try {
        if (Test-CommandExists "Get-DnsClientServerAddress") {
            return Get-DnsClientServerAddress -AddressFamily $AddressFamily | Where-Object {$_.ServerAddresses -ne $null}
        } else {
            return Get-WmiObject -Class Win32_NetworkAdapterConfiguration -Filter "IPEnabled = 'True'" | Select-Object InterfaceIndex, DNSDomainSuffixSearchOrder, DNSServerSearchOrder
        }
    } catch { return $null }
}

function Get-NetAdapterCompat {
    try {
        if (Test-CommandExists "Get-NetAdapter") {
            return Get-NetAdapter | Where-Object {$_.Status -eq 'Up'}
        } else {
            return Get-WmiObject -Class Win32_NetworkAdapter | Where-Object {$_.NetConnectionStatus -eq 2}
        }
    } catch { return $null }
}

function Get-NetFirewallProfileCompat {
    try {
        if (Test-CommandExists "Get-NetFirewallProfile") {
            return Get-NetFirewallProfile
        } else {
            # Alternativa para versões mais antigas
            $firewall = New-Object -ComObject HNetCfg.FwPolicy2
            return $firewall.CurrentProfileTypes
        }
    } catch { return $null }
}

function Set-NetFirewallProfileCompat {
    param($Name, $Enabled)
    try {
        if (Test-CommandExists "Set-NetFirewallProfile") {
            Set-NetFirewallProfile -Name $Name -Enabled $Enabled
        } else {
            # Alternativa para versões mais antigas
            $firewall = New-Object -ComObject HNetCfg.FwPolicy2
            $profile = $firewall.GetProfileByName($Name)
            $profile.FirewallEnabled = $Enabled
        }
    } catch { throw }
}

# Menus e funções principais
function Show-MainMenu {
    Clear-Host
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host "           OTIMIZADOR WINDOWS               " -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host "1. Manutencao do Sistema" -ForegroundColor Yellow
    Write-Host "2. Configuracoes de Rede" -ForegroundColor Yellow
    Write-Host "3. Personalizacao" -ForegroundColor Yellow
    Write-Host "4. Seguranca e Firewall" -ForegroundColor Yellow
    Write-Host "5. Informacoes do Sistema" -ForegroundColor Yellow
    Write-Host "0. Sair" -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Cyan
}

function Show-MaintenanceMenu {
    Clear-Host
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "           MANUTENCAO DO SISTEMA             " -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "1. Limpeza de Memoria (Desativar WinSat)" -ForegroundColor White
    Write-Host "2. Limpeza de Disco" -ForegroundColor White
    Write-Host "3. Opcoes de Pasta" -ForegroundColor White
    Write-Host "4. Fontes do Sistema" -ForegroundColor White
    Write-Host "5. Propriedades de Internet" -ForegroundColor White
    Write-Host "6. Pasta de Programas na Inicializacao" -ForegroundColor White
    Write-Host "7. Corrigir erros do SO (DISM)" -ForegroundColor White
    Write-Host "8. Corrigir erros do SO (SFC)" -ForegroundColor White
    Write-Host "9. Corrigir erros do SO (CHKDSK)" -ForegroundColor White
    Write-Host "10. Obter Serial do PC" -ForegroundColor White
    Write-Host "11. Desativar Servicos Desnecessarios" -ForegroundColor White
    Write-Host "12. Desativar Telemetria e Diagnosticos" -ForegroundColor White
    Write-Host "13. Desativar Efeitos Visuais para Desempenho" -ForegroundColor White
    Write-Host "14. Otimizar Power Plan" -ForegroundColor White
    Write-Host "15. Desfragmentar Disco" -ForegroundColor White
    Write-Host "16. Limpar Temp e Cache" -ForegroundColor White
    Write-Host "17. Ver Logs do Sistema" -ForegroundColor White
    Write-Host "18. Desativar Inicializacao Rapida" -ForegroundColor White
    Write-Host "19. Otimizacoes Avançadas de Desempenho" -ForegroundColor White
    Write-Host "20. Desativar Servicos de Background" -ForegroundColor White
    Write-Host "0. Voltar ao Menu Principal" -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Green
}

function Show-NetworkMenu {
    Clear-Host
    Write-Host "=============================================" -ForegroundColor Blue
    Write-Host "           CONFIGURACOES DE REDE             " -ForegroundColor Blue
    Write-Host "=============================================" -ForegroundColor Blue
    Write-Host "1. Mapeamento de Rede" -ForegroundColor White
    Write-Host "2. Visualizar IPs na Rede e Exportar" -ForegroundColor White
    Write-Host "3. Testar Ping para um IP" -ForegroundColor White
    Write-Host "4. Ver Portas Abertas no PC" -ForegroundColor White
    Write-Host "5. Ver Portas Abertas na Rede" -ForegroundColor White
    Write-Host "6. Configuracao IP Atual" -ForegroundColor White
    Write-Host "7. Liberar e Renovar IP" -ForegroundColor White
    Write-Host "8. Flush de DNS" -ForegroundColor White
    Write-Host "9. Testar Velocidade de Rede" -ForegroundColor White
    Write-Host "10. Ver Rota para um Host (Tracert)" -ForegroundColor White
    Write-Host "11. Ver Informacoes de DNS" -ForegroundColor White
    Write-Host "12. Testar Conexao with Site" -ForegroundColor White
    Write-Host "13. Ver Adaptadores de Rede" -ForegroundColor White
    Write-Host "14. Configurar DNS Manualmente" -ForegroundColor White
    Write-Host "0. Voltar ao Menu Principal" -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Blue
}

function Show-PersonalizationMenu {
    Clear-Host
    Write-Host "=============================================" -ForegroundColor Magenta
    Write-Host "           PERSONALIZACAO                    " -ForegroundColor Magenta
    Write-Host "=============================================" -ForegroundColor Magenta
    Write-Host "1. Alterar Tema (Claro/Escuro)" -ForegroundColor White
    Write-Host "2. Alterar Papel de Parede" -ForegroundColor White
    Write-Host "3. Desativar Efeitos Transparencia" -ForegroundColor White
    Write-Host "4. Desativar Animoes" -ForegroundColor White
    Write-Host "5. Mostrar/Ocultar Extensoes de Arquivo" -ForegroundColor White
    Write-Host "6. Alterar Resolucao da Tela" -ForegroundColor White
    Write-Host "7. Personalizar Menu Iniciar" -ForegroundColor White
    Write-Host "8. Personalizar Barra de Tarefas" -ForegroundColor White
    Write-Host "0. Voltar ao Menu Principal" -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Magenta
}

function Show-SecurityMenu {
    Clear-Host
    Write-Host "=============================================" -ForegroundColor Red
    Write-Host "           SEGURANCA E FIREWALL              " -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Red
    Write-Host "1. Ver Status do Firewall" -ForegroundColor White
    Write-Host "2. Habilitar/Desabilitar Firewall" -ForegroundColor White
    Write-Host "3. Ver Regras do Firewall" -ForegroundColor White
    Write-Host "4. Adicionar Regra ao Firewall" -ForegroundColor White
    Write-Host "5. Ver Antivirus Instalado" -ForegroundColor White
    Write-Host "6. Ver Atualizacoes de Seguranca" -ForegroundColor White
    Write-Host "7. Ver Processos em Execucao" -ForegroundColor White
    Write-Host "8. Ver Conexoes de Rede Ativas" -ForegroundColor White
    Write-Host "0. Voltar ao Menu Principal" -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Red
}

function Show-SystemInfoMenu {
    Clear-Host
    Write-Host "=============================================" -ForegroundColor Yellow
    Write-Host "           INFORMACOES DO SISTEMA            " -ForegroundColor Yellow
    Write-Host "=============================================" -ForegroundColor Yellow
    Write-Host "1. Informacoes de Hardware" -ForegroundColor White
    Write-Host "2. Informacoes de Software" -ForegroundColor White
    Write-Host "3. Informacoes de Rede" -ForegroundColor White
    Write-Host "4. Informacoes de Armazenamento" -ForegroundColor White
    Write-Host "5. Informacoes de Processos" -ForegroundColor White
    Write-Host "6. Informacoes de Servicos" -ForegroundColor White
    Write-Host "7. Ver Eventos do Sistema" -ForegroundColor White
    Write-Host "8. Ver Uso de Recursos" -ForegroundColor White
    Write-Host "0. Voltar ao Menu Principal" -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Yellow
}

# Novas funções de otimização
function Disable-FastStartup {
    Write-Host "Desativando inicializacao rapida..." -ForegroundColor Yellow
    try {
        powercfg /hibernate off
        reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power" /v HiberbootEnabled /t REG_DWORD /d 0 /f
        Write-Host "Inicializacao rapida desativada com sucesso!" -ForegroundColor Green
    } catch {
        Write-Host "Erro ao desativar inicializacao rapida: $_" -ForegroundColor Red
    }
}

function Optimize-Performance {
    Write-Host "Aplicando otimizacoes avançadas de desempenho..." -ForegroundColor Yellow
    try {
        # Desativar serviços desnecessários
        $services = @(
            "SysMain",           # SuperFetch
            "TrkWks",            # Rastreador de links distribuídos
            "RemoteRegistry",    # Registro remoto
            "WalletService",     # Serviço de carteira
            "WMPNetworkSvc",     # Serviço de compartilhamento de rede do Windows Media Player
            "WSearch",           # Windows Search
            "XblAuthManager",    # Gerenciador de autenticação Xbox Live
            "XblGameSave",       # Salvamento de jogos do Xbox Live
            "XboxNetApiSvc"      # Serviço de API de rede Xbox
        )
        
        foreach ($service in $services) {
            try {
                Stop-Service $service -Force -ErrorAction SilentlyContinue
                Set-Service $service -StartupType Disabled -ErrorAction SilentlyContinue
                Write-Host "Servico $service desativado" -ForegroundColor Green
            } catch {
                Write-Host "Nao foi possivel desativar $service" -ForegroundColor Yellow
            }
        }

        # Otimizar configurações de energia
        powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c # Alto desempenho
        powercfg -h off

        # Desativar tarefas agendadas desnecessárias
        $tasks = @(
            "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
            "\Microsoft\Windows\Application Experience\ProgramDataUpdater",
            "\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
            "\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip"
        )

        foreach ($task in $tasks) {
            try {
                Disable-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
            } catch {}
        }

        # Otimizar configurações do sistema
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "NtfsDisableLastAccessUpdate" -Value 1
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" -Name "ClearPageFileAtShutdown" -Value 0
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" -Name "LargeSystemCache" -Value 1
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" -Name "IoPageLockLimit" -Value 0

        Write-Host "Otimizacoes de desempenho aplicadas com sucesso!" -ForegroundColor Green
    } catch {
        Write-Host "Erro ao aplicar otimizacoes: $_" -ForegroundColor Red
    }
}

function Disable-BackgroundServices {
    Write-Host "Desativando servicos de background..." -ForegroundColor Yellow
    try {
        # Desativar aplicativos em segundo plano
        Get-AppxPackage -AllUsers | ForEach-Object {
            $package = $_
            try {
                $package.ProvisionedPackage | ForEach-Object {
                    Remove-AppxProvisionedPackage -Online -PackageName $_.PackageName -ErrorAction SilentlyContinue
                }
                Remove-AppxPackage -Package $package.PackageFullName -AllUsers -ErrorAction SilentlyContinue
            } catch {}
        }

        # Desativar serviços de telemetria
        $services = @(
            "DiagTrack",        # Rastreamento de diagnóstico
            "dmwappushservice", # Serviço de push de WAP de gerenciamento de dispositivo
            "DPS",              # Serviço de Política de Diagnóstico
            "lfsvc",            # Serviço de Localização Geográfica
            "MapsBroker",       # Serviço de Download de Mapas
            "WdiServiceHost"    # Host de serviço de diagnóstico
        )

        foreach ($service in $services) {
            try {
                Stop-Service $service -Force -ErrorAction SilentlyContinue
                Set-Service $service -StartupType Disabled -ErrorAction SilentlyContinue
                Write-Host "Servico $service desativado" -ForegroundColor Green
            } catch {
                Write-Host "Nao foi possivel desativar $service" -ForegroundColor Yellow
            }
        }

        # Desativar telemetria via registro
        $telemetryKeys = @(
            "HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection",
            "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Policies\DataCollection"
        )

        foreach ($key in $telemetryKeys) {
            try {
                if (!(Test-Path $key)) { New-Item -Path $key -Force | Out-Null }
                Set-ItemProperty -Path $key -Name "AllowTelemetry" -Value 0 -ErrorAction SilentlyContinue
            } catch {}
        }

        Write-Host "Servicos de background desativados com sucesso!" -ForegroundColor Green
    } catch {
        Write-Host "Erro ao desativar servicos de background: $_" -ForegroundColor Red
    }
}

# Funções existentes (mantidas do código anterior)
function Export-IPsToFile {
    param([array]$IPList)
    $filePath = "ips_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    $IPList | Out-File -FilePath $filePath -Encoding UTF8
    Write-Host "IPs exportados para $filePath" -ForegroundColor Green
}

function Show-NetworkIPs {
    Write-Host "Escaneando dispositivos na rede..." -ForegroundColor Yellow
    Write-Host "Este processo pode demorar alguns minutos..." -ForegroundColor Yellow
    
    try {
        $ipconfig = Get-NetIPConfigurationCompat
        if (-not $ipconfig) {
            Write-Host "Nenhuma conexao de rede ativa encontrada!" -ForegroundColor Red
            Pause
            return
        }
        
        # Obter o endereço IPv4 de maneira compatível
        if ($ipconfig.GetType().Name -eq "Win32_NetworkAdapterConfiguration") {
            $ipv4 = $ipconfig.IPAddress | Where-Object { $_ -match '^(\d{1,3}\.){3}\d{1,3}$' } | Select-Object -First 1
        } else {
            $ipv4 = $ipconfig.IPv4Address.IPAddress
        }
        
        if (-not ($ipv4 -match '^(\d{1,3}\.){3}\d{1,3}$')) {
            Write-Host "Endereco IP invalido: $ipv4" -ForegroundColor Red
            Pause
            return
        }
        
        $subnet = $ipv4 -replace '\.\d{1,3}$', ''
        
        Write-Host "Varrendo rede: $subnet.0/24" -ForegroundColor Yellow
        
        $activeIPs = @()
        $count = 0
        
        # Verificar hosts ativos na rede (1 a 254)
        foreach ($i in 1..254) {
            $ip = "$subnet.$i"
            Write-Progress -Activity "Escaneando rede" -Status "Verificando $ip" -PercentComplete (($i / 254) * 100)
            
            $ping = Test-Connection -ComputerName $ip -Count 1 -Quiet -ErrorAction SilentlyContinue
            if ($ping) {
                try {
                    $hostname = [System.Net.Dns]::GetHostEntry($ip).HostName
                    Write-Host "IP: $ip - Hostname: $hostname" -ForegroundColor Green
                    $activeIPs += "$ip - $hostname"
                    $count++
                } catch {
                    Write-Host "IP: $ip - Hostname: Não identificado" -ForegroundColor Green
                    $activeIPs += "$ip - Não identificado"
                    $count++
                }
            }
        }
        
        Write-Progress -Activity "Escaneando rede" -Completed
        
        # Exportar IPs para arquivo
        if ($activeIPs.Count -gt 0) {
            Export-IPsToFile -IPList $activeIPs
            Write-Host "`nEscaneamento concluído! $count dispositivos encontrados." -ForegroundColor Green
            Write-Host "Resultados exportados para $filePath" -ForegroundColor Green
        } else {
            Write-Host "Nenhum dispositivo encontrado na rede!" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Erro ao escanear rede: $_" -ForegroundColor Red
    }
    Pause
}

# ... (restante das funções existentes permanecem iguais)

# Loop principal do programa
do {
    Show-MainMenu
    $mainChoice = Read-Host "Escolha uma opcao"
    
    switch ($mainChoice) {
        '1' {
            do {
                Show-MaintenanceMenu
                $maintenanceChoice = Read-Host "Escolha uma opcao"
                
                switch ($maintenanceChoice) {
                    '1' {
                        try {
                            if (Test-CommandExists "Disable-ScheduledTask") {
                                Disable-ScheduledTask -TaskName "WinSat" -TaskPath "\Microsoft\Windows\Maintenance" -ErrorAction Stop
                                Write-Host "Tarefa WinSat desativada com sucesso!" -ForegroundColor Green
                            } else {
                                schtasks /Change /TN "\Microsoft\Windows\Maintenance\WinSat" /DISABLE
                                Write-Host "Tarefa WinSat desativada com sucesso!" -ForegroundColor Green
                            }
                        } catch {
                            Write-Host "Erro ao desativar tarefa: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '2' { 
                        try {
                            Start-Process cleanmgr
                        } catch {
                            Write-Host "Erro ao executar Limpeza de Disco: $_" -ForegroundColor Red
                        }
                    }
                    '3' { 
                        try {
                            Start-Process control -ArgumentList "folders"
                        } catch {
                            Write-Host "Erro ao abrir Opcoes de Pasta: $_" -ForegroundColor Red
                        }
                    }
                    '4' { 
                        try {
                            Start-Process control -ArgumentList "fonts"
                        } catch {
                            Write-Host "Erro ao abrir Fontes do Sistema: $_" -ForegroundColor Red
                        }
                    }
                    '5' { 
                        try {
                            Start-Process inetcpl.cpl
                        } catch {
                            Write-Host "Erro ao abrir Propriedades de Internet: $_" -ForegroundColor Red
                        }
                    }
                    '6' { 
                        try {
                            Start-Process shell:startup
                        } catch {
                            Write-Host "Erro ao abrir Pasta de Inicializacao: $_" -ForegroundColor Red
                        }
                    }
                    '7' {
                        Write-Host "Executando DISM..." -ForegroundColor Yellow
                        try {
                            DISM /Online /Cleanup-Image /RestoreHealth
                        } catch {
                            Write-Host "Erro ao executar DISM: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '8' {
                        Write-Host "Executando SFC..." -ForegroundColor Yellow
                        try {
                            sfc /scannow
                        } catch {
                            Write-Host "Erro ao executar SFC: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '9' {
                        Write-Host "Agendando CHKDSK..." -ForegroundColor Yellow
                        try {
                            chkdsk /r /x
                            Write-Host "Reinicie o computador para executar o CHKDSK" -ForegroundColor Cyan
                        } catch {
                            Write-Host "Erro ao agendar CHKDSK: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '10' {
                        try {
                            $serial = (Get-CimInstance -ClassName Win32_BIOS).SerialNumber
                            Write-Host "Serial do PC: $serial" -ForegroundColor Cyan
                        } catch {
                            Write-Host "Erro ao obter serial: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '11' {
                        $services = @("DiagTrack", "dmwappushservice", "WMPNetworkSvc", "WerSvc", "Fax")
                        foreach ($service in $services) {
                            try {
                                Stop-Service $service -Force -ErrorAction SilentlyContinue
                                Set-Service $service -StartupType Disabled -ErrorAction Stop
                                Write-Host "Servico $service desativado" -ForegroundColor Green
                            } catch {
                                Write-Host "Falha ao desativar $service" -ForegroundColor Yellow
                            }
                        }
                        Pause
                    }
                    '12' {
                        $keys = @(
                            "HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                            "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\SQMClient"
                        )
                        foreach ($key in $keys) {
                            try {
                                if (!(Test-Path $key)) { New-Item -Path $key -Force | Out-Null }
                                Set-ItemProperty -Path $key -Name "AllowTelemetry" -Value 0 -ErrorAction Stop
                            } catch {}
                        }
                        Write-Host "Telemetria desativada!" -ForegroundColor Green
                        Pause
                    }
                    '13' {
                        try {
                            Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" -Name "VisualFXSetting" -Value 2
                            Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" -Name "DisableThumbnailCache" -Value 1
                            Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "NtfsDisable8dot3NameCreation" -Value 1
                            Write-Host "Otimizacoes de desempenho aplicadas!" -ForegroundColor Green
                        } catch {
                            Write-Host "Erro ao aplicar otimizacoes: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '14' {
                        try {
                            powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
                            powercfg -h off
                            Write-Host "Power plan otimizado!" -ForegroundColor Green
                        } catch {
                            Write-Host "Erro ao configurar power plan: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '15' { 
                        Write-Host "Desfragmentando disco..." -ForegroundColor Yellow
                        try {
                            if (Test-CommandExists "Optimize-Volume") {
                                Optimize-Volume -DriveLetter C -Defrag -Verbose
                            } else {
                                defrag C: /O
                            }
                            Write-Host "Desfragmentacao concluida!" -ForegroundColor Green
                        } catch {
                            Write-Host "Erro ao desfragmentar disco: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '16' { 
                        Write-Host "Limpando arquivos temporarios..." -ForegroundColor Yellow
                        try {
                            Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
                            Remove-Item -Path "$env:WINDIR\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
                            Remove-Item -Path "$env:LOCALAPPDATA\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
                            Write-Host "Arquivos temporarios limpos com sucesso!" -ForegroundColor Green
                        } catch {
                            Write-Host "Erro ao limpar arquivos temporarios: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '17' { 
                        Write-Host "Visualizando logs do sistema..." -ForegroundColor Yellow
                        try {
                            Get-EventLog -LogName System -Newest 10 | Format-Table TimeGenerated, EntryType, Source, Message -AutoSize -Wrap
                        } catch {
                            Write-Host "Erro ao visualizar logs: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '18' { 
                        Disable-FastStartup
                        Pause
                    }
                    '19' { 
                        Optimize-Performance
                        Pause
                    }
                    '20' { 
                        Disable-BackgroundServices
                        Pause
                    }
                    '0' { break }
                    default { Write-Host "Opcao invalida!" -ForegroundColor Red; Pause }
                }
            } while ($maintenanceChoice -ne '0')
        }
        '2' {
            do {
                Show-NetworkMenu
                $networkChoice = Read-Host "Escolha uma opcao"
                
                switch ($networkChoice) {
                    '1' {
                        try {
                            Get-WmiObject -Class Win32_MappedLogicalDisk | Format-Table DeviceID, ProviderName, VolumeName
                        } catch {
                            Write-Host "Erro ao obter mapeamentos de rede: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '2' { Show-NetworkIPs }
                    '3' { 
                        $ip = Read-Host "Digite o IP ou hostname para testar ping"
                        if ($ip) {
                            Write-Host "Testando ping para $ip..." -ForegroundColor Yellow
                            try {
                                Test-Connection -ComputerName $ip -Count 4
                            } catch {
                                Write-Host "Erro ao testar ping: $_" -ForegroundColor Red
                            }
                        } else {
                            Write-Host "Nenhum IP informado!" -ForegroundColor Red
                        }
                        Pause
                    }
                    '4' {
                        try {
                            if (Test-CommandExists "Get-NetTCPConnection") {
                                Get-NetTCPConnection | Where-Object {$_.State -eq "Listen"} | 
                                    Select-Object LocalAddress, LocalPort, State, OwningProcess | 
                                    Sort-Object LocalPort | Format-Table -AutoSize
                            } else {
                                netstat -ano | findstr "LISTENING"
                            }
                        } catch {
                            Write-Host "Erro ao ver portas abertas: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '5' {
                        $ip = Read-Host "Digite o IP para verificar portas abertas"
                        if (-not $ip) {
                            Write-Host "Nenhum IP informado!" -ForegroundColor Red
                            Pause
                            break
                        }
                        
                        Write-Host "Verificando portas abertas em $ip..." -ForegroundColor Yellow
                        $commonPorts = @(21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080)
                        
                        foreach ($port in $commonPorts) {
                            try {
                                $tcp = New-Object System.Net.Sockets.TcpClient
                                $result = $tcp.BeginConnect($ip, $port, $null, $null)
                                $success = $result.AsyncWaitHandle.WaitOne(500, $false)
                                if ($success) {
                                    Write-Host "Porta $port aberta" -ForegroundColor Green
                                    $tcp.EndConnect($result)
                                }
                                $tcp.Close()
                            } catch {}
                        }
                        Pause
                    }
                    '6' {
                        try {
                            ipconfig /all
                        } catch {
                            Write-Host "Erro ao obter configuracao IP: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '7' {
                        try {
                            ipconfig /release
                            ipconfig /renew
                            Write-Host "IP liberado e renovado!" -ForegroundColor Green
                        } catch {
                            Write-Host "Erro ao liberar/renovar IP: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '8' {
                        try {
                            ipconfig /flushdns
                            Write-Host "Cache DNS limpo!" -ForegroundColor Green
                        } catch {
                            Write-Host "Erro ao limpar cache DNS: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '9' { 
                        Write-Host "Testando velocidade de rede..." -ForegroundColor Yellow
                        try {
                            $testFileUrl = "http://ipv4.download.thinkbroadband.com/10MB.zip"
                            $outputFile = "$env:TEMP\speedtest.zip"
                            
                            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
                            Invoke-WebRequest -Uri $testFileUrl -OutFile $outputFile
                            $stopwatch.Stop()
                            
                            $fileSize = (Get-Item $outputFile).Length
                            $speedMbps = ($fileSize * 8 / 1MB) / $stopwatch.Elapsed.TotalSeconds
                            
                            Remove-Item $outputFile -Force -ErrorAction SilentlyContinue
                            
                            Write-Host "Velocidade aproximada: $($speedMbps.ToString('N2')) Mbps" -ForegroundColor Green
                            Write-Host "Tempo de download: $($stopwatch.Elapsed.TotalSeconds.ToString('N2')) segundos" -ForegroundColor Green
                        } catch {
                            Write-Host "Erro ao testar velocidade: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '10' {
                        $hostname = Read-Host "Digite o hostname para tracar rota"
                        if ($hostname) {
                            try {
                                tracert $hostname
                            } catch {
                                Write-Host "Erro ao executar tracert: $_" -ForegroundColor Red
                            }
                        } else {
                            Write-Host "Nenhum hostname informado!" -ForegroundColor Red
                        }
                        Pause
                    }
                    '11' { 
                        Write-Host "Informacoes de DNS:" -ForegroundColor Yellow
                        try {
                            $dnsInfo = Get-DnsClientServerAddressCompat -AddressFamily IPv4
                            if ($dnsInfo -ne $null) {
                                if ($dnsInfo -is [array]) {
                                    $dnsInfo | Format-Table InterfaceAlias, ServerAddresses -AutoSize
                                } else {
                                    $dnsInfo | Format-List DNSDomainSuffixSearchOrder, DNSServerSearchOrder
                                }
                            } else {
                                Write-Host "Nao foi possivel obter informacoes DNS." -ForegroundColor Red
                            }
                        } catch {
                            Write-Host "Erro ao obter informacoes DNS: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '12' { 
                        $url = Read-Host "Digite a URL do site para testar"
                        if ($url) {
                            Write-Host "Testando conexao com $url..." -ForegroundColor Yellow
                            try {
                                $request = [System.Net.WebRequest]::Create($url)
                                $request.Timeout = 5000
                                $response = $request.GetResponse()
                                Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
                                $response.Close()
                            } catch {
                                Write-Host "Erro ao testar site: $_" -ForegroundColor Red
                            }
                        } else {
                            Write-Host "Nenhuma URL informada!" -ForegroundColor Red
                        }
                        Pause
                    }
                    '13' {
                        try {
                            $adapters = Get-NetAdapterCompat
                            if ($adapters -is [array]) {
                                $adapters | Format-Table Name, InterfaceDescription, Status -AutoSize
                            } else {
                                Write-Host "Adaptador: $($adapters.Name)" -ForegroundColor Green
                            }
                        } catch {
                            Write-Host "Erro ao obter adaptadores de rede: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '14' { 
                        Write-Host "Configuracao de DNS Manual" -ForegroundColor Yellow
                        try {
                            $adapters = Get-NetAdapterCompat
                            if (-not $adapters) {
                                Write-Host "Nenhum adaptador de rede ativo encontrado!" -ForegroundColor Red
                                Pause
                                return
                            }
                            
                            Write-Host "Adaptadores de rede disponiveis:" -ForegroundColor Yellow
                            if ($adapters -is [array]) {
                                $adapters | Format-Table Name, InterfaceDescription -AutoSize
                                $adapterName = Read-Host "Digite o nome do adaptador"
                            } else {
                                $adapterName = $adapters.Name
                                Write-Host "Adaptador: $adapterName" -ForegroundColor Green
                            }
                            
                            $dnsPrimary = Read-Host "Digite o DNS primario (ex: 8.8.8.8)"
                            $dnsSecondary = Read-Host "Digite o DNS secundario (ex: 8.8.4.4)"
                            
                            if ($dnsPrimary -and $dnsSecondary) {
                                if (Test-CommandExists "Set-DnsClientServerAddress") {
                                    Set-DnsClientServerAddress -InterfaceAlias $adapterName -ServerAddresses @($dnsPrimary, $dnsSecondary)
                                } else {
                                    $interface = Get-WmiObject -Class Win32_NetworkAdapterConfiguration -Filter "IPEnabled = 'True'" | Where-Object { $_.Description -like "*$adapterName*" }
                                    $interface.SetDNSServerSearchOrder(@($dnsPrimary, $dnsSecondary))
                                }
                                Write-Host "DNS configurado com sucesso!" -ForegroundColor Green
                            } else {
                                Write-Host "DNS invalido!" -ForegroundColor Red
                            }
                        } catch {
                            Write-Host "Erro ao configurar DNS: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '0' { break }
                    default { Write-Host "Opcao invalida!" -ForegroundColor Red; Pause }
                }
            } while ($networkChoice -ne '0')
        }
        '3' {
            do {
                Show-PersonalizationMenu
                $personalizationChoice = Read-Host "Escolha uma opcao"
                
                switch ($personalizationChoice) {
                    '1' {
                        $choice = Read-Host "1. Tema Escuro`n2. Tema Claro`nEscolha uma opcao"
                        try {
                            if ($choice -eq "1") {
                                Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "AppsUseLightTheme" -Value 0
                                Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "SystemUsesLightTheme" -Value 0
                                Write-Host "Tema alterado para Escuro!" -ForegroundColor Green
                            } elseif ($choice -eq "2") {
                                Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "AppsUseLightTheme" -Value 1
                                Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "SystemUsesLightTheme" -Value 1
                                Write-Host "Tema alterado para Claro!" -ForegroundColor Green
                            } else {
                                Write-Host "Opcao invalida!" -ForegroundColor Red
                            }
                        } catch {
                            Write-Host "Erro ao alterar tema: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '2' {
                        $wallpaperPath = Read-Host "Digite o caminho completo para a imagem de papel de parede"
                        if (Test-Path $wallpaperPath) {
                            try {
                                Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name "Wallpaper" -Value $wallpaperPath
                                rundll32.exe user32.dll, UpdatePerUserSystemParameters
                                Write-Host "Papel de parede alterado com sucesso!" -ForegroundColor Green
                            } catch {
                                Write-Host "Erro ao alterar papel de parede: $_" -ForegroundColor Red
                            }
                        } else {
                            Write-Host "Arquivo nao encontrado!" -ForegroundColor Red
                        }
                        Pause
                    }
                    '3' {
                        try {
                            Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "EnableTransparency" -Value 0
                            Write-Host "Efeitos de transparencia desativados!" -ForegroundColor Green
                        } catch {
                            Write-Host "Erro ao desativar efeitos de transparencia: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '4' {
                        try {
                            Set-ItemProperty -Path "HKCU:\Control Panel\Desktop\WindowMetrics" -Name "MinAnimate" -Value 0
                            Write-Host "Animacoes desativadas!" -ForegroundColor Green
                        } catch {
                            Write-Host "Erro ao desativar animacoes: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '5' {
                        try {
                            $current = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" -Name "HideFileExt" -ErrorAction SilentlyContinue
                            if ($current.HideFileExt -eq 1) {
                                Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" -Name "HideFileExt" -Value 0
                                Write-Host "Extensoes de arquivo agora estao VISIVEIS" -ForegroundColor Green
                            } else {
                                Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" -Name "HideFileExt" -Value 1
                                Write-Host "Extensoes de arquivo agora estao OCULTAS" -ForegroundColor Green
                            }
                        } catch {
                            Write-Host "Erro ao alterar configuracao de extensoes: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '6' {
                        try {
                            Write-Host "Resolucoes disponiveis:" -ForegroundColor Yellow
                            (Get-WmiObject -Class Win32_VideoController).VideoModeDescription
                        } catch {
                            Write-Host "Erro ao obter resolucoes: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '7' {
                        Write-Host "Personalizando Menu Iniciar..." -ForegroundColor Yellow
                        try {
                            Start-Process "shell:::{05d7b0f4-2121-4eff-bf6b-ed3f69b894d9}"
                        } catch {
                            Write-Host "Erro ao personalizar Menu Iniciar: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '8' {
                        Write-Host "Personalizando Barra de Tarefas..." -ForegroundColor Yellow
                        try {
                            Start-Process "shell:::{0df44eaa-ff21-4412-828e-260a8728e7f1}"
                        } catch {
                            Write-Host "Erro ao personalizar Barra de Tarefas: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '0' { break }
                    default { Write-Host "Opcao invalida!" -ForegroundColor Red; Pause }
                }
            } while ($personalizationChoice -ne '0')
        }
        '4' {
            do {
                Show-SecurityMenu
                $securityChoice = Read-Host "Escolha uma opcao"
                
                switch ($securityChoice) {
                    '1' { 
                        Write-Host "Status do Firewall:" -ForegroundColor Yellow
                        try {
                            $status = Get-NetFirewallProfileCompat
                            if ($status -ne $null) {
                                if ($status -is [array]) {
                                    $status | Format-Table Name, Enabled -AutoSize
                                } else {
                                    Write-Host "Perfil atual: $status" -ForegroundColor Green
                                }
                            } else {
                                Write-Host "Nao foi possivel obter status do firewall." -ForegroundColor Red
                            }
                        } catch {
                            Write-Host "Erro ao ver status do firewall: $_" -ForegroundColor Red
                            Pause
                        }
                    }
                    '2' { 
                        Write-Host "Alternar Status do Firewall" -ForegroundColor Yellow
                        try {
                            $profile = Read-Host "Digite o perfil (Domain, Private, Public)"
                            $currentStatus = (Get-NetFirewallProfileCompat | Where-Object {$_.Name -eq $profile}).Enabled
                            
                            if ($currentStatus -eq $true) {
                                Set-NetFirewallProfileCompat -Name $profile -Enabled $false
                                Write-Host "Firewall $profile desativado!" -ForegroundColor Green
                            } else {
                                Set-NetFirewallProfileCompat -Name $profile -Enabled $true
                                Write-Host "Firewall $profile ativado!" -ForegroundColor Green
                            }
                        } catch {
                            Write-Host "Erro ao alternar firewall: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '3' {
                        try {
                            if (Test-CommandExists "Get-NetFirewallRule") {
                                Get-NetFirewallRule | Select-Object -First 10 | Format-Table DisplayName, Enabled, Direction -AutoSize
                            } else {
                                Write-Host "Comando nao disponivel nesta versao do Windows" -ForegroundColor Yellow
                            }
                        } catch {
                            Write-Host "Erro ao ver regras do firewall: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '4' {
                        Write-Host "Criar nova regra de firewall..." -ForegroundColor Yellow
                        try {
                            if (Test-CommandExists "New-NetFirewallRule") {
                                $name = Read-Host "Nome da regra"
                                $direction = Read-Host "Direcao (Inbound/Outbound)"
                                $action = Read-Host "Acao (Allow/Block)"
                                $protocol = Read-Host "Protocolo (TCP/UDP)"
                                $port = Read-Host "Porta"
                                
                                New-NetFirewallRule -DisplayName $name -Direction $direction -Action $action -Protocol $protocol -LocalPort $port
                                Write-Host "Regra criada com sucesso!" -ForegroundColor Green
                            } else {
                                Write-Host "Comando nao disponivel nesta versao do Windows" -ForegroundColor Yellow
                            }
                        } catch {
                            Write-Host "Erro ao criar regra: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '5' {
                        try {
                            if (Test-CommandExists "Get-CimInstance") {
                                Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct | Format-Table displayName, productState
                            } else {
                                Get-WmiObject -Namespace root/SecurityCenter2 -Class AntiVirusProduct | Format-Table displayName, productState
                            }
                        } catch {
                            Write-Host "Erro ao ver informacoes do antivirus: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '6' {
                        try {
                            Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10 | Format-Table HotFixID, InstalledOn
                        } catch {
                            Write-Host "Erro ao ver atualizacoes de seguranca: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '7' {
                        try {
                            Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 | Format-Table Name, CPU, WorkingSet -AutoSize
                        } catch {
                            Write-Host "Erro ao ver processos: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '8' {
                        try {
                            if (Test-CommandExists "Get-NetTCPConnection") {
                                Get-NetTCPConnection | Where-Object {$_.State -eq 'Established'} | Select-Object -First 10 | Format-Table LocalAddress, LocalPort, RemoteAddress, RemotePort -AutoSize
                            } else {
                                netstat -ano | findstr "ESTABLISHED" | Select-Object -First 10
                            }
                        } catch {
                            Write-Host "Erro ao ver conexoes de rede: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '0' { break }
                    default { Write-Host "Opcao invalida!" -ForegroundColor Red; Pause }
                }
            } while ($securityChoice -ne '0')
        }
        '5' {
            do {
                Show-SystemInfoMenu
                $systemInfoChoice = Read-Host "Escolha uma opcao"
                
                switch ($systemInfoChoice) {
                    '1' { 
                        Write-Host "Informacoes de Hardware:" -ForegroundColor Yellow
                        try {
                            $cpu = Get-WmiObject -Class Win32_Processor
                            Write-Host "Processador: $($cpu.Name)" -ForegroundColor Green
                            Write-Host "  Núcleos: $($cpu.NumberOfCores)" -ForegroundColor White
                            Write-Host "  Threads: $($cpu.NumberOfLogicalProcessors)" -ForegroundColor White
                            Write-Host "  Clock: $([math]::Round($cpu.MaxClockSpeed / 1000, 2)) GHz" -ForegroundColor White
                            Write-Host ""
                            
                            $memory = Get-WmiObject -Class Win32_PhysicalMemory
                            $totalMemory = 0
                            foreach ($mem in $memory) {
                                $size = [math]::Round($mem.Capacity / 1GB, 2)
                                $totalMemory += $size
                                Write-Host "Memoria: $size GB" -ForegroundColor White
                            }
                            Write-Host "Memoria Total: $totalMemory GB" -ForegroundColor Cyan
                            
                            $disks = Get-WmiObject -Class Win32_DiskDrive
                            foreach ($disk in $disks) {
                                $size = [math]::Round($disk.Size / 1GB, 2)
                                Write-Host "Disco: $($disk.Model) - $size GB" -ForegroundColor White
                            }
                        } catch {
                            Write-Host "Erro ao obter informacoes de hardware: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '2' { 
                        Write-Host "Informacoes de Software:" -ForegroundColor Yellow
                        try {
                            $os = Get-WmiObject -Class Win32_OperatingSystem
                            Write-Host "Sistema Operacional: $($os.Caption)" -ForegroundColor Green
                            Write-Host "  Versao: $($os.Version)" -ForegroundColor White
                            Write-Host "  Build: $($os.BuildNumber)" -ForegroundColor White
                            
                            $bios = Get-WmiObject -Class Win32_BIOS
                            Write-Host "BIOS: $($bios.Name)" -ForegroundColor Green
                            Write-Host "  Versao: $($bios.SMBIOSBIOSVersion)" -ForegroundColor White
                        } catch {
                            Write-Host "Erro ao obter informacoes de software: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '3' { 
                        try {
                            $ipconfig = Get-NetIPConfigurationCompat
                            if ($ipconfig -is [array]) {
                                $ipconfig | Format-Table InterfaceAlias, IPv4Address, IPv4DefaultGateway -AutoSize
                            } else {
                                $ipconfig | Format-List IPAddress, IPSubnet, DefaultIPGateway
                            }
                        } catch {
                            Write-Host "Erro ao obter informacoes de rede: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '4' { 
                        Write-Host "Informacoes de Armazenamento:" -ForegroundColor Yellow
                        try {
                            $drives = Get-WmiObject -Class Win32_LogicalDisk
                            foreach ($drive in $drives) {
                                if ($drive.Size -gt 0) {
                                    $size = [math]::Round($drive.Size / 1GB, 2)
                                    $free = [math]::Round($drive.FreeSpace / 1GB, 2)
                                    Write-Host "Unidade $($drive.DeviceID): $free GB livres de $size GB" -ForegroundColor White
                                }
                            }
                        } catch {
                            Write-Host "Erro ao obter informacoes de armazenamento: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '5' {
                        try {
                            Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 | Format-Table Name, CPU, PM -AutoSize
                        } catch {
                            Write-Host "Erro ao obter informacoes de processos: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '6' {
                        try {
                            Get-Service | Where-Object {$_.Status -eq 'Running'} | Sort-Object DisplayName | Select-Object -First 10 | Format-Table DisplayName, Status -AutoSize
                        } catch {
                            Write-Host "Erro ao obter informacoes de servicos: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '7' {
                        try {
                            Get-EventLog -LogName Application -Newest 5 | Format-Table TimeGenerated, EntryType, Source, Message -AutoSize -Wrap
                        } catch {
                            Write-Host "Erro ao ver eventos do sistema: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '8' {
                        try {
                            if (Test-CommandExists "Get-Counter") {
                                Get-Counter '\Processor(_Total)\% Processor Time' | Format-Table -AutoSize
                                Get-Counter '\Memory\Available MBytes' | Format-Table -AutoSize
                            } else {
                                Write-Host "Uso da CPU: $((Get-WmiObject -Class Win32_Processor).LoadPercentage)%" -ForegroundColor Green
                                Write-Host "Memoria disponivel: $([math]::Round((Get-WmiObject -Class Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)) GB" -ForegroundColor Green
                            }
                        } catch {
                            Write-Host "Erro ao ver uso de recursos: $_" -ForegroundColor Red
                        }
                        Pause
                    }
                    '0' { break }
                    default { Write-Host "Opcao invalida!" -ForegroundColor Red; Pause }
                }
            } while ($systemInfoChoice -ne '0')
        }
        '0' {
            Write-Host "Saindo..." -ForegroundColor Yellow
            exit
        }
        default {
            Write-Host "Opcao invalida!" -ForegroundColor Red
            Pause
        }
    }
} while ($true)