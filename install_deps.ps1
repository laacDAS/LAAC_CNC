# Script PowerShell para criar e instalar dependências do projeto Python
# Execute este script na raiz do projeto


# Pergunta ao usuário sobre criar e ativar a venv, mas só pergunta sobre ativar se não estiver ativa
$venvAction = $false
$venvActive = $env:VIRTUAL_ENV -ne $null -and $env:VIRTUAL_ENV -ne ""
if (!(Test-Path ".venv")) {
    $resp = Read-Host "A venv não existe. Deseja criá-la e ativar? (s/n)"
    if ($resp -eq 's' -or $resp -eq 'S') {
        python -m venv .venv
        $venvAction = $true
    } else {
        Write-Host "Operação cancelada pelo usuário."
        exit
    }
} elseif (-not $venvActive) {
    $resp = Read-Host "A venv já existe, mas não está ativa. Deseja ativá-la? (s/n)"
    if ($resp -eq 's' -or $resp -eq 'S') {
        $venvAction = $true
    } else {
        Write-Host "Operação cancelada pelo usuário."
        exit
    }
} else {
    Write-Host "A venv já está ativa."
}

if ($venvAction) {
    . .venv\Scripts\Activate.ps1
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
        pip install $($to_install -join ' ')
    } else {
        Write-Host "Instalação de dependências cancelada pelo usuário."
    }
} else {
    Write-Host "Todas as dependências já estão instaladas."
}

# Dependências opcionais/utilitários
pip install --upgrade pip

Write-Host "\nProcesso finalizado."
