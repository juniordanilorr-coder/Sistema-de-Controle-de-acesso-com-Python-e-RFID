"""Compatibilidade para o leitor RFID organizado em src/."""
from src.infraestrutura.hardware.leitor_rfid import LeitorRFID

if __name__ == "__main__":
    LeitorRFID().executar()
