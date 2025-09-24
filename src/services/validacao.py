import re

class Validacao:
    # quando ESPERA NÚMERO, mas veio letra
    mapa_numero = { "O": "0", "Q": "0", "D": "0", "I": "1", "Z": "2", "S": "5", "G": "6", "B": "8", "T": "7", "A": "4" }
    # quando ESPERA LETRA, mas veio número
    mapa_letra = { "0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B", "9": "G", "4": "A", "7": "T" }

    padrao_antigo   = ["L","L","L","N","N","N","N"]
    padrao_mercosul = ["L","L","L","N","L","N","N"]

    @staticmethod
    def corrigirPorPosicao(placa: str):
        if len(placa) != 7: return [placa]
        candidatos = []
        for padrao in [Validacao.padrao_mercosul, Validacao.padrao_antigo]:
            corrigido = list(placa)
            for i, tipo in enumerate(padrao):
                ch = corrigido[i]
                if tipo == "L" and ch.isdigit() and ch in Validacao.mapa_letra:
                    corrigido[i] = Validacao.mapa_letra[ch]
                elif tipo == "N" and ch.isalpha() and ch in Validacao.mapa_numero:
                    corrigido[i] = Validacao.mapa_numero[ch]
            candidatos.append("".join(corrigido))
        return candidatos

    @staticmethod
    def executar(texto: str):
        if not texto or len(texto.strip()) != 7:
            return None

        placa = texto.strip().upper().replace("-", "").replace(" ", "")
        
        padroes_regex = [
            r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$', # Mercosul
            r'^[A-Z]{3}[0-9]{4}$'             # Antiga
        ]

        # --- LÓGICA CORRIGIDA ---
        # 1. Primeiro, tenta validar o texto original
        for padrao in padroes_regex:
            if re.fullmatch(padrao, placa):
                return placa # Se já for válido, retorna imediatamente

        # 2. Se não for válido, SÓ ENTÃO tenta corrigir
        candidatos_corrigidos = Validacao.corrigirPorPosicao(placa)
        for cand in candidatos_corrigidos:
            for padrao in padroes_regex:
                if re.fullmatch(padrao, cand):
                    return cand  # Retorna o primeiro candidato corrigido que for válido
        
        return None