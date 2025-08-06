# Script PowerShell para ativar a venv e rodar o main.py
# Execute este script na raiz do projeto

# Ativa a venv apenas se não estiver ativa
if (-not ($env:VIRTUAL_ENV -ne $null -and $env:VIRTUAL_ENV -ne "")) {
    . .venv\Scripts\Activate.ps1
}

# Executa o main.py
python main.py
