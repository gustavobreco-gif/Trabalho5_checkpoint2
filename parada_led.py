
#!/usr/bin/env python3
"""
================================================================================
PROGRAMA DE PARADA DO SERVIÇO (ExecStop):
Rotina em Python executada automaticamente pelo systemd quando o serviço é
pausado/interrompido com o comando 'sudo systemctl stop monitor_led.service'.

FUNCIONAMENTO DO PROGRAMA:
1. É invocado pelo interpretador Python definido na diretiva 'ExecStop=' do
   unit file logo após o encerramento do processo principal (monitor_led.py).
2. Pisca o LED Vermelho (GPIO 27) 3 vezes rapidamente para fornecer uma
   confirmação física de que o serviço foi parado pelo operador.
3. Garante que ambos os LEDs permaneçam apagados e registra a mensagem de
   encerramento no log do systemd (journalctl).
================================================================================
"""

import time
from gpiozero import LED

PINO_LED_VERDE = 17
PINO_LED_VERMELHO = 27


def sinalizar_parada(led_verde: LED, led_vermelho: LED, repeticoes: int = 3) -> None:
    """Apaga o LED Verde e pisca o LED Vermelho para confirmar a parada."""
    led_verde.off()
    for _ in range(repeticoes):
        led_vermelho.on()
        time.sleep(0.2)
        led_vermelho.off()
        time.sleep(0.2)


def liberar_hardware(led_verde: LED, led_vermelho: LED) -> None:
    """Garante estado desligado e libera os pinos GPIO ao finalizar."""
    led_verde.off()
    led_vermelho.off()
    led_verde.close()
    led_vermelho.close()
    print("[EXECSTOP] Servico finalizado e LEDs desligados.", flush=True)


def main() -> None:
    """Ponto de entrada da rotina de encerramento do serviço."""
    print("[EXECSTOP] Executando rotina de parada do servico...", flush=True)

    led_verde = LED(PINO_LED_VERDE)
    led_vermelho = LED(PINO_LED_VERMELHO)

    try:
        sinalizar_parada(led_verde, led_vermelho)
    finally:
        liberar_hardware(led_verde, led_vermelho)


if __name__ == "__main__":
    main()
