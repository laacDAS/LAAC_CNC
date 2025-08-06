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

# Lê as dependências do cfg.json
$cfg = Get-Content -Raw -Path "cfg.json" | ConvertFrom-Json
$deps = $cfg.python_dependencies

# Verifica e mostra status das dependências
$table = @()
foreach ($dep in $deps) {
    $result = python -c "import $($dep.import)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $status = "INSTALADO"
    } else {
        $status = "NÃO INSTALADO"
    }
    $table += [PSCustomObject]@{
        Pacote = $dep.name
        Modulo = $dep.import
        Status = $status
    }
}

Write-Host "\nSTATUS DAS DEPENDÊNCIAS:"
$table | Format-Table -AutoSize | Out-String | Write-Host

# Instala apenas os que não estão instalados
$to_install = $table | Where-Object { $_.Status -eq "NÃO INSTALADO" } | ForEach-Object { $_.Pacote }
if ($to_install.Count -gt 0) {
    $resp = Read-Host "Deseja instalar as dependências faltantes? (s/n)"
    if ($resp -eq 's' -or $resp -eq 'S') {
        pip install $to_install
    } else {
        Write-Host "Instalação de dependências cancelada pelo usuário."
    }
} else {
    Write-Host "Todas as dependências já estão instaladas."
}

# Dependências opcionais/utilitários
pip install --upgrade pip

Write-Host "\nProcesso finalizado."

Write-Host "`nPressione Enter para sair..."
[void][System.Console]::ReadLine()