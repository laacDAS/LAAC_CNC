# Verifica se o Python está disponível
$pythonExists = $false
try {
    $ver = python --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $ver -match "Python") {
        $pythonExists = $true
    }
} catch {
    $pythonExists = $false
}
if (-not $pythonExists) {
    Write-Host "Python não foi encontrado no sistema. Instale o Python e adicione ao PATH antes de continuar."
    exit 1
}
# Script PowerShell para criar e instalar dependências do projeto Python
# Execute este script na raiz do projeto

# Verifica se a venv existe
$venvPath = ".venv"
$venvActive = $env:VIRTUAL_ENV -ne $null -and $env:VIRTUAL_ENV -ne ""


# Criação e ativação da venv
$activate = $false
if (!(Test-Path $venvPath)) {
    $resp = Read-Host "A venv não existe. Deseja criá-la? (s/n)"
    if ($resp -eq 's' -or $resp -eq 'S') {
        python -m venv $venvPath
        if (!(Test-Path "$venvPath/Scripts/Activate.ps1")) {
            Write-Host "Falha ao criar a venv."
            exit 1
        }
        Write-Host "Venv criada."
        $activate = $true
    } else {
        Write-Host "Operação cancelada pelo usuário."
        exit
    }
} elseif (-not $venvActive) {
    $resp = Read-Host "A venv já existe, mas não está ativa. Deseja ativá-la? (s/n)"
    if ($resp -eq 's' -or $resp -eq 'S') {
        $activate = $true
    } else {
        Write-Host "Operação cancelada pelo usuário."
        exit
    }
} else {
    Write-Host "A venv já está ativa."
}

if ($activate) {
    . .\.venv\Scripts\Activate.ps1
    if ($env:VIRTUAL_ENV -eq $null -or $env:VIRTUAL_ENV -eq "") {
        Write-Host "Falha ao ativar a venv."
        exit 1
    }
    Write-Host "Venv ativada."
}

# Lê dependências do requirements.txt e verifica/instala usando o Python selecionado
if (!(Test-Path "requirements.txt")) {
    Write-Host "Arquivo requirements.txt não encontrado na raiz do projeto. Crie-o e rode novamente."
    exit 1
}

$raw = Get-Content -Path "requirements.txt" | ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not ($_.StartsWith('#')) }
$reqs = @()
foreach ($line in $raw) {
    # Remove comentários inline e espaços
    $pkg = $line -split '\\s*#' | Select-Object -First 1
    $pkg = $pkg.Trim()
    if ($pkg) { $reqs += $pkg }
}

if ($reqs.Count -eq 0) {
    Write-Host "Nenhuma dependência válida encontrada em requirements.txt"
    exit 0
}

# Detecta venv e escolhe python a ser usado para instalação
$venvPath = ".venv"
$useVenv = $false
$chosenPython = "python"
if (Test-Path $venvPath) {
    $resp = Read-Host "Existe a venv '.venv'. Deseja usar a venv para instalar as dependências? (s/n)"
    if ($resp -eq 's' -or $resp -eq 'S') { $useVenv = $true }
}

if ($useVenv) {
    # Procura executável python na venv (Windows/Unix)
    $winPython = Join-Path $venvPath "Scripts\python.exe"
    $unixPython = Join-Path $venvPath "bin/python"
    if (Test-Path $winPython) { $chosenPython = $winPython }
    elseif (Test-Path $unixPython) { $chosenPython = $unixPython }
    else {
        Write-Host "Executável Python não encontrado dentro de .venv. Usando 'python' do sistema."
        $chosenPython = "python"
    }
    Write-Host "Usando Python: $chosenPython"
} else {
    Write-Host "Usando o Python do sistema (comando 'python')."
}

# Função para verificar se pacote está instalado (pip show)
function Test-PackageInstalled($pkg) {
    $proc = Start-Process -FilePath $chosenPython -ArgumentList "-m","pip","show","$pkg" -NoNewWindow -PassThru -Wait -ErrorAction SilentlyContinue
    return ($proc.ExitCode -eq 0)
}

$table = @()
foreach ($req in $reqs) {
    # Extrai o nome do pacote sem especificadores de versão
    $name = $req -split '[=<>~]' | Select-Object -First 1
    $installed = Test-PackageInstalled $name
    $status = if ($installed) { 'INSTALADO' } else { 'NÃO INSTALADO' }
    $table += [PSCustomObject]@{ Pacote = $req; Nome = $name; Status = $status }
}

Write-Host "\nSTATUS DAS DEPENDÊNCIAS (baseado em requirements.txt):"
$table | Format-Table -AutoSize | Out-String | Write-Host

$toInstall = $table | Where-Object { $_.Status -eq 'NÃO INSTALADO' } | ForEach-Object { $_.Pacote }
if ($toInstall.Count -gt 0) {
    # Antes de instalar pacotes Python, tenta garantir que libexiv2/exiv2 esteja presente
    $exivCmd = Get-Command exiv2 -ErrorAction SilentlyContinue
    if (-not $exivCmd) {
        Write-Host "libexiv2/exiv2 não encontrado. Tentando instalar via gerenciador do sistema..."
        try {
            if ($IsWindows) {
                $choco = Get-Command choco -ErrorAction SilentlyContinue
                if ($choco) {
                    Write-Host "Usando Chocolatey para instalar exiv2..."
                    & choco install exiv2 -y
                } else {
                    $winget = Get-Command winget -ErrorAction SilentlyContinue
                    if ($winget) {
                        Write-Host "Usando winget para instalar exiv2..."
                        & winget install --id Exiv2.Exiv2 -e --accept-package-agreements --accept-source-agreements
                    } else {
                        Write-Host "Chocolatey/winget não encontrado. Instalação automática no Windows não é possível neste sistema."
                        Write-Host "Sugestão: instale Chocolatey (https://chocolatey.org/install) e rode: choco install exiv2 -y"
                        Write-Host "Ou baixe/instale exiv2 manualmente: https://www.exiv2.org/"
                    }
                }
            } elseif ($IsMacOS) {
                $brew = Get-Command brew -ErrorAction SilentlyContinue
                if ($brew) {
                    Write-Host "Usando Homebrew para instalar exiv2..."
                    & brew install exiv2
                } else {
                    Write-Host "Homebrew não encontrado. Instale Homebrew (https://brew.sh/) e rode: brew install exiv2"
                }
            } elseif ($IsLinux) {
                $osRelease = ""
                if (Test-Path "/etc/os-release") { $osRelease = Get-Content /etc/os-release -Raw }
                if ($osRelease -match "(ubuntu|debian)") {
                    Write-Host "Usando apt para instalar libexiv2-dev..."
                    & sudo apt-get update
                    & sudo apt-get install -y libexiv2-dev || & sudo apt-get install -y exiv2
                } elseif ($osRelease -match "(fedora|rhel|centos)") {
                    Write-Host "Usando dnf para instalar libexiv2-devel..."
                    & sudo dnf install -y libexiv2-devel || & sudo dnf install -y exiv2
                } else {
                    # Tenta apt e dnf como fallback
                    Write-Host "Distro não reconhecida. Tentando apt e dnf como fallback..."
                    try { & sudo apt-get update; & sudo apt-get install -y libexiv2-dev } catch { Write-Host "apt falhou" }
                    try { & sudo dnf install -y libexiv2-devel } catch { Write-Host "dnf falhou" }
                }
            } else {
                Write-Host "Sistema operacional não reconhecido. Instale libexiv2/exiv2 manualmente (https://www.exiv2.org/)."
            }
        } catch {
            Write-Host "Falha ao tentar instalar libexiv2 automaticamente: $($_.Exception.Message)"
        }
        # Re-check
        $exivCmd = Get-Command exiv2 -ErrorAction SilentlyContinue
        if ($exivCmd) { 
            Write-Host "libexiv2/exiv2 instalado ou já disponível." 
        } else { 
            Write-Host "Não foi possível instalar libexiv2 automaticamente. Por favor instale manualmente."
            if ($IsWindows) {
                Write-Host "Exemplo de ação manual (Windows): instale Chocolatey e rode: choco install exiv2 -y"
                Write-Host "Chocolatey: https://chocolatey.org/install"
            } elseif ($IsMacOS) {
                Write-Host "Exemplo de ação manual (macOS): brew install exiv2"
            } elseif ($IsLinux) {
                Write-Host "Exemplo de ação manual (Ubuntu/Debian): sudo apt-get update && sudo apt-get install -y libexiv2-dev"
                Write-Host "Exemplo de ação manual (Fedora): sudo dnf install -y libexiv2-devel"
            } else {
                Write-Host "Consulte https://www.exiv2.org/ para instruções específicas do seu sistema."
            }
        }
    }

    $resp = Read-Host "Deseja instalar as dependências não instaladas usando $chosenPython? (s/n)"
    if ($resp -eq 's' -or $resp -eq 'S') {
        Write-Host "Instalando..."
        & $chosenPython -m pip install --upgrade pip
        & $chosenPython -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERRO: 'pip install' retornou código de saída $LASTEXITCODE."
            Write-Host "Sugestões:"
            Write-Host " - Verifique sua conexão de rede e tente novamente: $chosenPython -m pip install -r requirements.txt"
            Write-Host " - Se estiver usando .venv, verifique se a venv está ativada antes de executar o script."
            Write-Host " - Verifique permissões (use --user ou rode em ambiente com privilégios adequados)."
            Write-Host " - Se o erro for relacionado ao 'pyexiv2', instale primeiro a dependência do sistema 'libexiv2' (veja instruções acima)."
            Write-Host "Depois de corrigir, execute novamente: $chosenPython -m pip install -r requirements.txt"
        } else {
            Write-Host "Pip instalou as dependências com sucesso."
        }
    } else {
        Write-Host "Instalação cancelada pelo usuário."
    }
} else {
    Write-Host "Todas as dependências já estão instaladas."
}

Write-Host "\nProcesso finalizado."

Write-Host "`nPressione Enter para sair..."
[void][System.Console]::ReadLine()