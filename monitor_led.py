
#!/usr/bin/env python3
"""
================================================================================
APLICAÇÃO ESCOLHIDA:
Sistema de Sinalização de Boot (Blink LED) e Monitoramento de Hardware via GPIO.

FUNCIONAMENTO DO PROGRAMA:
1. Este script é inicializado diretamente pelo interpretador Python chamado
   pelo unit file do systemd durante o boot da Raspberry Pi.
2. Utiliza a biblioteca 'gpiozero' para controlar dois LEDs e um botão físico:
   - LED Verde (GPIO 17): executa um blink contínuo a cada 1 segundo, provando
     visualmente que o serviço iniciou automaticamente no boot.
   - LED Vermelho (GPIO 27): acende quando o botão físico (GPIO 22) é
     pressionado ou quando a temperatura da CPU (lida via sysfs do kernel Linux)
     ultrapassa o limite configurado.
3. Ao receber o sinal SIGTERM (gerado pelo comando 'sudo systemctl stop'),
   encerra o laço principal e libera os pinos GPIO no bloco 'finally',
   permitindo que o programa configurado em 'ExecStop=' assuma o controle
   dos LEDs sem conflito de hardware.
================================================================================
"""

import signal
import time
from pathlib import Path
from gpiozero import Button, LED

# Mapeamento de pinos (numeração BCM)
PINO_LED_VERDE = 17     # Pino físico 11 - Blink de operação contínua
PINO_LED_VERMELHO = 27  # Pino físico 13 - Alerta / Botão pressionado
PINO_BOTAO = 22         # Pino físico 15 - Entrada digital com pull-up interno

TEMP_LIMITE_C = 60.0
SYSFS_TEMP_CPU = Path("/sys/class/thermal/thermal_zone0/temp")

executando = True


def tratar_sinal_parada(signum: int, _frame) -> None:
    """Intercepta SIGTERM (systemctl stop) e SIGINT (Ctrl+C) para saída limpa."""
    global executando
    print(f"[MONITOR] Sinal {signum} recebido. Liberando hardware...", flush=True)
    executando = False


def ler_temperatura_cpu() -> float:
    """Lê a temperatura do SoC exposta pelo kernel Linux em graus Celsius."""
    try:
        if SYSFS_TEMP_CPU.exists():
            return int(SYSFS_TEMP_CPU.read_text().strip()) / 1000.0
    except (OSError, ValueError):
        pass
    return 0.0


def atualizar_sinalizacao(led_verde: LED, led_vermelho: LED, botao: Button) -> None:
    """Executa um ciclo de blink no LED Verde e verifica alertas no LED Vermelho."""
    led_verde.toggle()
    temp_cpu = ler_temperatura_cpu()

    if botao.is_pressed or temp_cpu >= TEMP_LIMITE_C:
        led_vermelho.on()
        origem = "BOTAO" if botao.is_pressed else "TEMPERATURA"
        print(f"[ALERTA - {origem}] Temp CPU: {temp_cpu:.1f} C", flush=True)
    else:
        led_vermelho.off()
        print(f"[ATIVO] Blink LED OK | Temp CPU: {temp_cpu:.1f} C", flush=True)


def liberar_hardware(led_verde: LED, led_vermelho: LED, botao: Button) -> None:
    """Desliga os atuadores e libera os recursos GPIO para o processo ExecStop."""
    led_verde.off()
    led_vermelho.off()
    led_verde.close()
    led_vermelho.close()
    botao.close()
    print("[MONITOR] Pinos GPIO liberados com sucesso.", flush=True)


def main() -> None:
    """Inicializa sinais do SO, configura periféricos e mantém o loop principal."""
    signal.signal(signal.SIGTERM, tratar_sinal_parada)
    signal.signal(signal.SIGINT, tratar_sinal_parada)

    led_verde = LED(PINO_LED_VERDE)
    led_vermelho = LED(PINO_LED_VERMELHO)
    botao = Button(PINO_BOTAO, pull_up=True)

    print("[MONITOR] Servico iniciado via Python/systemd.", flush=True)

    try:
        while executando:
            atualizar_sinalizacao(led_verde, led_vermelho, botao)
            time.sleep(1.0)
    finally:
        liberar_hardware(led_verde, led_vermelho, botao)


if __name__ == "__main__":
    main()
