"""
Autor: Jardel M. Fialho
Data: 26/02/2025

Descrição: Implementação para possível solução para porta COM desabilitada 
após muito tempo de inatividade de hardware.

Dependências externas: devcom. É uma ferramenta de linha de comando da Microsoft para 
gerenciar dispositivos no Windows, que faz parte do Windows Driver Kit (WDK).

Instuções de instalação: https://learn.microsoft.com/pt-br/windows-hardware/drivers/download-the-wdk
"""


import subprocess
import os

# Caminho para o devcon.exe (ajuste conforme sua instalação)
DEVCON_PATH = r"C:\devcon\devcon.exe"


def list_usb_devices():
    """Lista todos os dispositivos USB conectados e retorna seus HWIDs."""
    try:
        result = subprocess.run(
            [DEVCON_PATH, "hwids", "=usb"], capture_output=True, text=True)
        output = result.stdout
        devices = []
        current_device = {}

        for line in output.splitlines():
            line = line.strip()
            if line.startswith("USB\\"):
                if current_device:
                    devices.append(current_device)
                current_device = {"HWID": line}
            elif line and current_device and "Name:" in line:
                current_device["Name"] = line.split("Name:")[1].strip()

        if current_device:
            devices.append(current_device)

        return devices
    except Exception as e:
        print(f"Erro ao listar dispositivos USB: {e}")
        return []


def enable_usb_port(hwid):
    """Habilita uma porta USB específica usando o HWID."""
    try:
        subprocess.run([DEVCON_PATH, "enable", hwid], check=True)
        print(f"Porta USB com HWID {hwid} habilitada.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao habilitar a porta: {e}")


def disable_usb_port(hwid):
    """Desabilita uma porta USB específica usando o HWID."""
    try:
        subprocess.run([DEVCON_PATH, "disable", hwid], check=True)
        print(f"Porta USB com HWID {hwid} desabilitada.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao desabilitar a porta: {e}")


def main():
    # Verifica se o devcon está disponível
    if not os.path.exists(DEVCON_PATH):
        print("Erro: devcon.exe não encontrado no caminho especificado.")
        return

    # Lista os dispositivos USB
    devices = list_usb_devices()
    if not devices:
        print("Nenhum dispositivo USB encontrado.")
        return

    # Exibe os dispositivos disponíveis
    print("Dispositivos USB conectados:")
    for i, device in enumerate(devices):
        print(
            f"{i}: {device.get('Name', 'Desconhecido')} - HWID: {device['HWID']}")

    # Solicita ao usuário o índice do dispositivo
    try:
        choice = int(
            input("Digite o número do dispositivo que deseja controlar (ex.: 0): "))
        if 0 <= choice < len(devices):
            hwid = devices[choice]["HWID"]
        else:
            print("Escolha inválida.")
            return
    except ValueError:
        print("Entrada inválida. Digite um número.")
        return

    # Solicita ação (habilitar/desabilitar)
    action = input(
        "Digite 'h' para habilitar ou 'd' para desabilitar: ").lower()
    if action == 'h':
        enable_usb_port(hwid)
    elif action == 'd':
        disable_usb_port(hwid)
    else:
        print("Ação inválida. Use 'h' ou 'd'.")


if __name__ == "__main__":
    main()
