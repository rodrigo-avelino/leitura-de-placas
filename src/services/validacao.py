import re

class Validacao:
    mapa_numero = {"O": "0", "I": "1", "Z": "2", "B": "8", "Q": "0", "S": "5", "G": "6", "D": "0"}
    mapa_letra  = {"0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B", "9": "G"}
    mapa_confusao = {"X": "Y", "Y": "X"}

    # define padrões esperados
    padrao_antigo   = ["L","L","L","N","N","N","N"]
    padrao_mercosul = ["L","L","L","N","L","N","N"]

    @staticmethod
    def corrigirPorPosicao(placa: str):
        placa = placa.upper().replace(" ", "").replace("-", "")
        if len(placa) != 7:
            return placa

        candidatos = []

        for padrao in [Validacao.padrao_antigo, Validacao.padrao_mercosul]:
            corrigido = list(placa)
            for i, tipo in enumerate(padrao):
                ch = corrigido[i]
                # deve ser letra
                if tipo == "L":
                    if ch.isdigit() and ch in Validacao.mapa_letra:
                        corrigido[i] = Validacao.mapa_letra[ch]
                    elif ch in Validacao.mapa_confusao:
                        corrigido[i] = Validacao.mapa_confusao[ch]
                # deve ser número
                elif tipo == "N":
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

        # regex de validação
        padroes = [
            r'^[A-Z]{3}[0-9]{4}$',             # Antiga
            r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$'    # Mercosul
        ]

        for cand in candidatos:
            for padrao in padroes:
                if re.fullmatch(padrao, cand):
                    return cand  # retorna o primeiro válido

        return None
