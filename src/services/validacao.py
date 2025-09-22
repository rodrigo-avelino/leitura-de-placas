import re

class Validacao:
    # quando ESPERA NÚMERO, mas veio letra
    mapa_numero = {
        "O": "0", "Q": "0", "D": "0",
        "I": "1",
        "Z": "2",
        "S": "5",
        "G": "6",
        "B": "8",
        "T": "7",   # ocasional
        "A": "4",   # ocasional
    }

    # quando ESPERA LETRA, mas veio número
    mapa_letra = {
        "0": "O",
        "1": "I",
        "2": "Z",
        "5": "S",
        "6": "G",
        "8": "B",
        "9": "G",
        "4": "A",   # ocasional
        "7": "T",   # ocasional
    }

    # padrões esperados
    padrao_antigo   = ["L","L","L","N","N","N","N"]
    padrao_mercosul = ["L","L","L","N","L","N","N"]

    @staticmethod
    def corrigirPorPosicao(placa: str):
        placa = placa.upper().replace(" ", "").replace("-", "")
        if len(placa) != 7:
            return placa

        candidatos = []

        # Mercosul é mais comum hoje; tentamos primeiro
        for padrao in [Validacao.padrao_mercosul, Validacao.padrao_antigo]:
            corrigido = list(placa)
            for i, tipo in enumerate(padrao):
                ch = corrigido[i]
                if tipo == "L":  # deve ser LETRA
                    if ch.isdigit() and ch in Validacao.mapa_letra:
                        corrigido[i] = Validacao.mapa_letra[ch]
                elif tipo == "N":  # deve ser NÚMERO
                    if ch.isalpha() and ch in Validacao.mapa_numero:
                        corrigido[i] = Validacao.mapa_numero[ch]
            candidatos.append("".join(corrigido))

        return candidatos

    @staticmethod
    def executar(texto: str):
        if not texto:
            return None

        placa = texto.strip().upper().replace(" ", "").replace("-", "")
        if len(placa) != 7:
            return None

        candidatos = Validacao.corrigirPorPosicao(placa)

        padroes = [
            r'^[A-Z]{3}[0-9]{4}$',             # Antiga
            r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$'    # Mercosul
        ]

        for cand in candidatos:
            for padrao in padroes:
                if re.fullmatch(padrao, cand):
                    return cand  # retorna o primeiro válido

        return None
