"""Leitura serial de UIDs enviada pelo Arduino."""

import time

import serial


class LeitorRFID:
    def __init__(self, porta="COM11", velocidade=9600, timeout=2):
        self.porta = porta
        self.velocidade = velocidade
        self.timeout = timeout

    @staticmethod
    def ler_uid(conexao):
        conexao.write(b"P")
        time.sleep(0.1)
        conexao.reset_input_buffer()
        print("\nAproxime o cartão ou a tag do leitor...")
        conexao.write(b"L")
        try:
            while True:
                linha = conexao.readline().decode(
                    "utf-8", errors="ignore"
                ).strip()
                if linha.startswith("UID:"):
                    uid = linha[4:].strip().upper()
                    print(f"\nUID identificada: {uid}")
                    return uid
        finally:
            conexao.write(b"P")

    def executar(self):
        try:
            with serial.Serial(
                self.porta, self.velocidade, timeout=self.timeout
            ) as arduino:
                time.sleep(2)
                print("Sistema RFID iniciado!")
                print("Aproxime um cartão ou uma tag.\n")
                while True:
                    linha = arduino.readline().decode(
                        "utf-8", errors="ignore"
                    ).strip()
                    if linha.startswith("UID:"):
                        print(f"UID identificada: {linha[4:].strip().upper()}")
        except serial.SerialException as erro:
            print(f"Erro de comunicação: {erro}")
            print("Verifique a porta COM e se ela está livre.")
        except KeyboardInterrupt:
            print("\nSistema encerrado.")


if __name__ == "__main__":
    LeitorRFID().executar()
