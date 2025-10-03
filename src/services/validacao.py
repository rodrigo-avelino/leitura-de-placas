import re

class Validacao:
    mapa_numero = { "O": "0", "Q": "0", "D": "0", "I": "1", "Z": "2", "S": "5", "G": "6", "B": "8", "T": "7", "A": "4" }
    mapa_letra = { "0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B", "9": "G", "4": "A", "7": "T" }
    padrao_antigo = ["L","L","L","N","N","N","N"]
    padrao_mercosul = ["L","L","L","N","L","N","N"]
    padroes_regex = [
        (r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$', "MERCOSUL"),
        (r'^[A-Z]{3}[0-9]{4}$', "ANTIGA")
    ]

    @staticmethod
    def _corrigir_e_validar(placa: str):
        """Tenta corrigir e retorna uma lista de tuplas (placa_valida, padrao)"""
        placas_validas = []
        
        # 1. Tenta validar a placa original
        for padrao_regex, nome_padrao in Validacao.padroes_regex:
            if re.fullmatch(padrao_regex, placa):
                placas_validas.append((placa, nome_padrao))

        # 2. Tenta a correção posicional
        for padrao_posicional in [Validacao.padrao_mercosul, Validacao.padrao_antigo]:
            corrigido = list(placa)
            for i, tipo in enumerate(padrao_posicional):
                ch = corrigido[i]
                if tipo == "L" and ch.isdigit() and ch in Validacao.mapa_letra:
                    corrigido[i] = Validacao.mapa_letra[ch]
                elif tipo == "N" and ch.isalpha() and ch in Validacao.mapa_numero:
                    corrigido[i] = Validacao.mapa_numero[ch]
            
            cand = "".join(corrigido)
            for padrao_regex, nome_padrao in Validacao.padroes_regex:
                if re.fullmatch(padrao_regex, cand):
                    placas_validas.append((cand, nome_padrao))
        
        # Remove duplicatas
        return list(set(placas_validas))

    @staticmethod
    def executar(texto: str, confiancas: list = None):
        """
        Retorna uma LISTA de todas as interpretações válidas possíveis.
        Ex: para 'PP02283', retorna [('PPO2283', 'ANTIGA'), ('PPO2Z83', 'MERCOSUL')]
        """
        if not texto or len(texto.strip()) != 7:
            return []
        placa = texto.strip().upper()
        return Validacao._corrigir_e_validar(placa)