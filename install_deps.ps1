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
    $resp = Read-Host "Deseja instalar as dependências não instaladas usando $chosenPython? (s/n)"
    if ($resp -eq 's' -or $resp -eq 'S') {
        Write-Host "Instalando..."
        & $chosenPython -m pip install --upgrade pip
        & $chosenPython -m pip install -r requirements.txt
    } else {
        Write-Host "Instalação cancelada pelo usuário."
    }
} else {
    Write-Host "Todas as dependências já estão instaladas."
}

Write-Host "\nProcesso finalizado."

Write-Host "`nPressione Enter para sair..."
[void][System.Console]::ReadLine()