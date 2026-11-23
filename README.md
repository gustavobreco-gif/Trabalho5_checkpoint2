## ANTONIO ROSA GALINDO DE ANDRADE 15440868
## GUSTAVO BREDA COELHO 14746742

# SEL0337 – Prática 5: Sistema Embarcado Linux com `systemd` e Controle de Versão com Git/GitHub

Projeto prático de Sistemas Embarcados para **Raspberry Pi (Linux Embarcado)**, utilizando **Python (`gpiozero`)** e gerenciamento do ciclo de vida de processos via **`systemd`**. A documentação e o histórico do projeto são mantidos com **Git** e **GitHub**.

A aplicação foi pensada para executar automaticamente durante o boot do sistema operacional (sem login manual e sem scripts `.sh` intermediários), sinalizando seu estado por LEDs e executando uma rotina dedicada quando o serviço é interrompido via `systemctl stop`.

> **Aviso sobre o estado da entrega:** a prática **não foi concluída** em laboratório. Foi feita uma tentativa de execução com um comando de teste, mas não conseguimos finalizá-la. Por isso este relatório **não possui fotografias, prints ou vídeo** do funcionamento, e o comportamento descrito para o boot **não foi validado em hardware**. Os códigos e o procedimento de validação foram escritos conforme o roteiro e estão documentados abaixo.

---

## Estrutura do Repositório

```text
SEL0337---PRATICA5/
├── README.md            # Documentação (arquitetura, hardware, execução e Git/GitHub)
├── monitor_led.py       # Script principal executado no boot (ExecStart)
├── parada_led.py        # Script executado na parada do serviço (ExecStop)
├── monitor_led.service  # Arquivo de unidade (Unit File) do systemd
├── historico_git.txt    # Saída de `git log` (histórico de commits)
└── evidencias/          # Pasta reservada para evidências de execução
```

---

# Parte 1 – Configuração do `systemd` para serviços personalizados

## 1. Conceitos envolvidos

### 1.1 Processo de boot da Raspberry Pi
Na Raspberry Pi 3B+ (SoC Broadcom BCM2837B0), quem assume o controle ao ligar a placa não é a CPU ARM, e sim a **GPU** (VideoCore). O boot acontece em etapas:

1. **First-level bootloader:** código gravado na ROM do SoC (de acesso restrito) inicializa alguns clocks e procura uma mídia externa, em geral o cartão microSD.
2. **Second-level bootloader (`bootcode.bin`):** lido da partição `boot` (FAT32), inicializa a SDRAM.
3. **Third-level bootloader (`start.elf`):** firmware da GPU. Lê o `config.txt`, carrega os arquivos de *device tree* (`.dtb`) e a imagem do kernel Linux na RAM.
4. **Kernel Linux:** os núcleos da CPU ARM são inicializados e o controle passa ao kernel, conforme os parâmetros do `cmdline.txt`.
5. **Init system:** o kernel monta a partição `rootfs` (ext4) e o **`systemd`** inicia todos os serviços da distribuição.

É nesta última etapa que o serviço desenvolvido neste projeto entra em execução.

### 1.2 `systemd` e `systemctl`
O `systemd` é o *init system* moderno adotado por distribuições como Debian e Raspberry Pi OS. Os serviços são descritos por *unit files* com extensão `.service`, e o utilitário `systemctl` é usado para gerenciá-los (`start`, `stop`, `enable`, `disable`, `status`).

### 1.3 `systemd` vs. `SystemV`

| Característica | SystemV (`init`) | `systemd` (adotado neste projeto) |
| :--- | :--- | :--- |
| **Inicialização** | Sequencial por scripts shell em `/etc/init.d/` | Paralela, baseada em dependências e alvos (`targets`) |
| **Configuração** | Scripts Bash complexos com códigos de retorno manuais | Arquivos declarativos (*Unit Files* `.service`) |
| **Monitoramento** | Sem supervisão nativa de queda de processos | Supervisão nativa (`Restart=`) e logs centralizados (`journalctl`) |
| **Gerenciamento** | Comandos `service <nome> start/stop` | Utilitário unificado `systemctl` |

---

## 2. Arquitetura e funcionamento

### Chamada direta ao interpretador Python no Unit File
O unit file invoca explicitamente o interpretador **`/usr/bin/python3`**, tanto na inicialização (`ExecStart`) quanto na parada (`ExecStop`). Isso dispensa encapsulamentos em shell script e torna o ambiente de execução (interpretador e bibliotecas `gpiozero`/`lgpio`) explícito e previsível dentro do `systemd`, que não herda o ambiente de uma sessão de login.

* **`ExecStart=/usr/bin/python3 .../monitor_led.py`:** executa o programa principal, que faz o *blink* contínuo do LED Verde (serviço ativo) e monitora um botão físico e a temperatura da CPU via `sysfs` (`/sys/class/thermal/thermal_zone0/temp`).
* **`ExecStop=/usr/bin/python3 .../parada_led.py`:** programa executado pelo `systemd` quando o serviço é parado com `sudo systemctl stop monitor_led.service`. Pisca o LED Vermelho 3 vezes como sinalização visual e registra o evento no log (`journald`).

> **Observação técnica:** o `systemd` executa os comandos de `ExecStop=` *antes* de encerrar o processo principal. Se o `monitor_led.py` ainda estiver com os pinos GPIO reservados nesse momento, o `parada_led.py` pode não conseguir acessá-los. Nesse caso, a alternativa é usar `ExecStopPost=`, executado depois que o processo principal termina. Como a prática não foi concluída, esse comportamento **não foi validado**.

### Resumo dos programas
* **`monitor_led.py`:** usa `gpiozero` para controlar LED Verde (GPIO 17), LED Vermelho (GPIO 27) e botão (GPIO 22, com pull-up interno). O LED Vermelho acende quando o botão é pressionado ou quando a temperatura da CPU passa de 60 °C. Trata `SIGTERM`/`SIGINT` para encerrar de forma limpa e liberar os pinos.
* **`parada_led.py`:** apaga o LED Verde, pisca o LED Vermelho 3 vezes e libera os pinos, registrando `[EXECSTOP]` no log.
* **`monitor_led.service`:** descreve o serviço (`[Unit]`, `[Service]`, `[Install]`), com `Restart=on-failure` e `WantedBy=multi-user.target`.

---

## 3. Montagem do hardware (protoboard ou simulador)

### Lista de componentes
* **1x** Raspberry Pi (3B+, 4B, 5 ou Zero 2 W) com Raspberry Pi OS.
* **1x** Protoboard.
* **1x** LED Verde 5 mm (indicador de atividade / *blink* no boot).
* **1x** LED Vermelho 5 mm (alerta térmico, teste via botão e sinalização de parada).
* **2x** Resistores de 220 Ω ou 330 Ω.
* **1x** Push button (chave tátil).
* **Jumpers** macho-fêmea e macho-macho.

### Tabela de conexões (pinout)

| Componente | Terminal | Pino BCM | Pino físico (Header) | Função |
| :--- | :--- | :--- | :--- | :--- |
| **Barramento comum** | Negativo (`-`) | `GND` | **Pino 6** | Referência terra na protoboard |
| **LED Verde** | Ânodo (`+`) via 220 Ω | `GPIO 17` | **Pino 11** | *Blink* contínuo enquanto o serviço roda |
| **LED Vermelho** | Ânodo (`+`) via 220 Ω | `GPIO 27` | **Pino 13** | Alerta/botão e aviso visual no `ExecStop` |
| **Push button** | Terminal A (Term. B no `GND`) | `GPIO 22` | **Pino 15** | Acionamento manual para demonstração |

### Diagrama esquemático

```text
Raspberry Pi (Header 40 pinos)               Protoboard
─────────────────────────────────            ───────────────────────────────
Pino 6  (GND)     ─────────────────────────► Barramento Negativo (-)
Pino 11 (GPIO 17) ──► [ Resistor 220 Ω ] ──► (+) LED Verde (-)     ──► GND
Pino 13 (GPIO 27) ──► [ Resistor 220 Ω ] ──► (+) LED Vermelho (-)  ──► GND
Pino 15 (GPIO 22) ─────────────────────────► [ Push Button ]       ──► GND
```

> **Execução em simulador:** para validar apenas a lógica em terminal Linux, sem placa física, pode-se usar `GPIOZERO_PIN_FACTORY=mock /usr/bin/python3 monitor_led.py`.

---

## 4. Procedimento de instalação e validação previsto (`systemctl`)

> Procedimento escrito conforme o roteiro. **Não foi executado até o fim** por nossa dupla (ver aviso no início).

### Passo 1: Clonar o repositório e instalar dependências
```bash
sudo apt update && sudo apt install -y python3-gpiozero python3-lgpio
git clone https://github.com/art-ga/SEL0337---PRATICA5.git ~/projeto-embarcados
cd ~/projeto-embarcados
chmod +x monitor_led.py parada_led.py
```

### Passo 2: Ajustar usuário e diretório no `.service` e registrar no `systemd`
```bash
sed -i "s|User=pi|User=$USER|g" monitor_led.service
sed -i "s|/home/pi/projeto-embarcados|$PWD|g" monitor_led.service

sudo cp monitor_led.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### Passo 3: Habilitar no boot e validar
1. **Habilitar e iniciar:**
   ```bash
   sudo systemctl enable monitor_led.service
   sudo systemctl start monitor_led.service
   ```
2. **Verificar o status** (esperado: `active (running)` e LED Verde piscando):
   ```bash
   systemctl status monitor_led.service
   ```
3. **Testar o `ExecStop`:**
   ```bash
   sudo systemctl stop monitor_led.service
   journalctl -u monitor_led.service -n 15 --no-pager
   ```
   *(Esperado: LED Vermelho piscando 3 vezes e mensagens `[MONITOR]` seguidas de `[EXECSTOP]` no log.)*
4. **Testar persistência após reinicialização:**
   ```bash
   sudo systemctl start monitor_led.service
   sudo reboot
   ```
   *(Esperado: após o reinício, o LED Verde volta a piscar sem login.)*

---

# Parte 2 – Controle de versão com Git e GitHub

## 5. Objetivo
O Git foi usado como sistema de controle de versão e o GitHub como repositório remoto e ferramenta de documentação. O objetivo é manter o histórico das alterações dos códigos da prática (`monitor_led.py`, `parada_led.py` e `monitor_led.service`), permitir que outras pessoas reproduzam o projeto e viabilizar o trabalho em dupla sem que as alterações de um integrante sobrescrevam as do outro.

## 6. Fluxo de trabalho

```text
 Repositório local                                   GitHub (origin / remoto)
┌──────────────────────────────┐   git clone      ┌────────────────────────┐
│ ~/projeto-embarcados         │ ◄─────────────── │ art-ga/SEL0337---      │
│  git add → git commit        │                  │ PRATICA5               │
│                              │ ───────────────► │                        │
│                              │    git push      │                        │
│                              │ ◄─────────────── │                        │
└──────────────────────────────┘    git pull      └────────────────────────┘
```

1. Criação do repositório remoto no GitHub.
2. Trabalho local: edição dos arquivos, `git add` e `git commit`.
3. Envio das atualizações ao remoto com `git push`.
4. Recebimento de atualizações do colega com `git pull`.

## 7. Configuração e comandos

```bash
git config --global user.name "usuario_github"
git config --global user.email "seu_email"
git clone https://github.com/art-ga/SEL0337---PRATICA5.git
cd SEL0337---PRATICA5
git add .
git commit -m "mensagem descrevendo a alteração"
git push
```

| Comando | Função | Situação neste projeto |
| :--- | :--- | :--- |
| `git clone <url>` | Copia o repositório remoto para a máquina local | Utilizado |
| `git add <arquivo>` | Coloca alterações na área de preparação (*staging*) | Utilizado |
| `git commit -m "msg"` | Registra um ponto no histórico com mensagem | Utilizado |
| `git push` | Envia commits locais ao GitHub | Utilizado |
| `git log` | Mostra o histórico de commits | Utilizado (ver seção 9) |
| `git init` | Cria um repositório local | Estudado (usamos o repositório criado no GitHub) |
| `git pull` | Traz alterações do remoto para o local | Estudado (útil para sincronizar a dupla) |
| `git reset` / `git checkout` | Desfazer alterações / voltar a versões anteriores | Estudado conceitualmente |
| `git rm` | Remove arquivo do versionamento | Estudado conceitualmente |
| `.gitignore` | Lista arquivos que o Git deve ignorar | Estudado (recomendado para o arquivo do token) |

## 8. Autenticação com Token de Acesso Pessoal
O GitHub não aceita a senha da conta no `git push` via HTTPS. Em seu lugar, usa-se um *Personal Access Token (classic)*, gerado em *Settings → Developer Settings → Personal Access Tokens*, com o menor prazo de expiração. No `git push`, informa-se o usuário do GitHub e, no campo de senha, o token.

> O arquivo que guarda o token deve ser listado no `.gitignore` e **nunca** enviado ao repositório. Um token exposto deve ser revogado imediatamente nas configurações do GitHub.

## 9. Histórico de versões
O histórico de commits pode ser consultado na aba **Commits** do repositório e no arquivo `historico_git.txt`, gerado com:

```bash
git log > historico_git.txt
```

## 10. Limitações desta entrega
* A prática não foi concluída em laboratório: houve uma tentativa de execução com um comando de teste, mas não conseguimos finalizá-la.
* Não há fotografias da montagem, prints nem vídeo do funcionamento; a pasta `evidencias/` não contém registros reais de execução.
* O funcionamento do serviço no boot da Raspberry Pi e o comportamento do `ExecStop` não foram validados em hardware.
* Os códigos, o unit file e o procedimento de validação seguem o roteiro e podem ser reproduzidos conforme a seção 4.

## 11. Conclusão
O projeto reuniu os conceitos de boot em Linux embarcado, gerenciamento de serviços com `systemd` e versionamento com Git/GitHub. Apesar de a validação prática não ter sido concluída, o repositório documenta a arquitetura, o hardware previsto, os programas em Python, o unit file e o fluxo de versionamento, de modo que outras pessoas possam reproduzir e continuar o trabalho.
