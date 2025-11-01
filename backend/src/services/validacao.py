import re

class Validacao:
    # Mapas e padrões permanecem os mesmos da sua versão anterior
    mapa_numero = { "O": "0", "Q": "0", "D": "0", "I": "1", "Z": "2", "S": "5", "G": "6", "B": "8", "T": "7", "A": "4" }
    mapa_letra = { "0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B", "9": "G", "4": "A", "7": "T" }
    padrao_antigo_tipos = ["L","L","L","N","N","N","N"] # Renomeado para clareza
    padrao_mercosul_tipos = ["L","L","L","N","L","N","N"] # Renomeado para clareza
    padroes_regex = [
        (r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$', "MERCOSUL"),
        (r'^[A-Z]{3}[0-9]{4}$', "ANTIGA")
    ]

    @staticmethod
    def _corrigir_e_validar(placa: str):
        """
        Tenta corrigir erros comuns e valida contra os padrões regex.
        Retorna uma lista de tuplas (placa_valida, padrao) válidas possíveis.
        (Função idêntica à sua versão anterior)
        """
        placas_validas_set = set() # Usar set para evitar duplicatas internas

        # 1. Tenta validar a placa como está (após limpeza inicial)
        for padrao_regex, nome_padrao in Validacao.padroes_regex:
            if re.fullmatch(padrao_regex, placa):
                placas_validas_set.add((placa, nome_padrao))

        # 2. Tenta a correção posicional genérica (para ambos os padrões)
        for padrao_posicional, nome_padrao_tentativa in [(Validacao.padrao_mercosul_tipos, "MERCOSUL"), (Validacao.padrao_antigo_tipos, "ANTIGA")]:
            corrigido_lista = list(placa)
            possivel = True
            for i, tipo in enumerate(padrao_posicional):
                ch = corrigido_lista[i]
                if tipo == "L" and ch.isdigit():
                    if ch in Validacao.mapa_letra:
                        corrigido_lista[i] = Validacao.mapa_letra[ch]
                    else:
                        possivel = False; break # Correção impossível
                elif tipo == "N" and ch.isalpha():
                    if ch in Validacao.mapa_numero:
                        corrigido_lista[i] = Validacao.mapa_numero[ch]
                    else:
                        possivel = False; break # Correção impossível

            if possivel:
                cand = "".join(corrigido_lista)
                # Verifica se o resultado corrigido bate com ALGUM padrão válido
                for padrao_regex, nome_padrao_final in Validacao.padroes_regex:
                    if re.fullmatch(padrao_regex, cand):
                        placas_validas_set.add((cand, nome_padrao_final))

        return list(placas_validas_set)

    @staticmethod
    def executar(texto: str, confiancas: list = None): # Assinatura mantida
        """
        Valida a placa. Se o texto original contiver '-' ou ':',
        prioriza e retorna apenas o resultado 'ANTIGA', se válido.
        Caso contrário, retorna todas as possibilidades válidas.
        """
        if not texto:
            return []

        texto_original = texto.strip() # Guarda o texto original (com Hífen/Dois Pontos)

        # --- NOVA LÓGICA DE DETECÇÃO DE HÍFEN/DOIS PONTOS ---
        is_provavelmente_antiga = '-' in texto_original or ':' in texto_original
        # --- FIM DA NOVA LÓGICA ---

        # Limpeza: Remove tudo que não for A-Z, 0-9 e converte para maiúsculas
        # Inclui a remoção explícita de '-' e ':' caso existam
        placa_limpa = re.sub(r'[^A-Z0-9]', '', texto_original.upper())

        # Validação de tamanho após limpeza
        if len(placa_limpa) != 7:
            return []

        # Chama a função principal de correção e validação
        resultados_possiveis = Validacao._corrigir_e_validar(placa_limpa)

        # --- FILTRO FINAL BASEADO NO INDICADOR ---
        if is_provavelmente_antiga:
            # Filtra a lista para manter apenas o resultado 'ANTIGA'
            resultado_antiga = [res for res in resultados_possiveis if res[1] == "ANTIGA"]
            return resultado_antiga # Retorna a lista filtrada (pode ser vazia)
        else:
            # Se não tinha hífen/dois pontos, retorna todos os resultados válidos encontrados
            return resultados_possiveis
        # --- FIM DO FILTRO ---