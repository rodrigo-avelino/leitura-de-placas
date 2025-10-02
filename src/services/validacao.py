import re

class Validacao:
    # Mapa de correções especulativas para caracteres com BAIXA CONFIANÇA
    MAPA_ERROS_CONFIANCA = {
        'H': 'M', 'V': 'W', 'O': 'Q', 'Q': 'O',
        'B': '8', 'S': '5', 'I': '1', 'Z': '2'
    }

    # Mapas para correção posicional (Letra <-> Número)
    mapa_numero = { "O": "0", "Q": "0", "D": "0", "I": "1", "Z": "2", "S": "5", "G": "6", "B": "8", "T": "7", "A": "4" }
    mapa_letra = { "0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B", "9": "G", "4": "A", "7": "T" }
    
    padrao_antigo   = ["L","L","L","N","N","N","N"]
    padrao_mercosul = ["L","L","L","N","L","N","N"]
    
    padroes_regex = [
        r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$', # Mercosul
        r'^[A-Z]{3}[0-9]{4}$'             # Antiga
    ]

    @staticmethod
    def _tenta_validar(placa: str):
        """Função auxiliar para verificar se uma string corresponde a um padrão de placa."""
        for padrao in Validacao.padroes_regex:
            if re.fullmatch(padrao, placa):
                return True
        return False

    # --- FUNÇÃO RESTAURADA ---
    @staticmethod
    def corrigirPorPosicao(placa: str):
        """Aplica a correção Letra <-> Número baseada na posição."""
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
    def executar(texto: str, confiancas: list = None):
        if not texto or len(texto.strip()) != 7:
            return None

        placa = texto.strip().upper().replace("-", "").replace(" ", "")
        confiancas = confiancas or []

        # TENTATIVA 1: Validar a placa como ela veio do OCR
        if Validacao._tenta_validar(placa):
            return placa

        # TENTATIVA 2: Correção posicional (Letra <-> Número)
        candidatos_posicionais = Validacao.corrigirPorPosicao(placa)
        for cand in candidatos_posicionais:
            if Validacao._tenta_validar(cand):
                return cand

        # TENTATIVA 3: Correção especulativa baseada em BAIXA CONFIANÇA
        if len(confiancas) == 7:
            placa_corrigida = list(placa)
            houve_correcao = False
            for i in range(7):
                char = placa_corrigida[i]
                conf = confiancas[i]
                
                if conf < 0.65 and char in Validacao.MAPA_ERROS_CONFIANCA:
                    placa_corrigida[i] = Validacao.MAPA_ERROS_CONFIANCA[char]
                    houve_correcao = True
            
            if houve_correcao:
                placa_corrigida_str = "".join(placa_corrigida)
                if Validacao._tenta_validar(placa_corrigida_str):
                    return placa_corrigida_str
                
                candidatos_finais = Validacao.corrigirPorPosicao(placa_corrigida_str)
                for cand in candidatos_finais:
                    if Validacao._tenta_validar(cand):
                        return cand
        
        return None