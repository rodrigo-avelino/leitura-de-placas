import re

class Montagem:
    @staticmethod
    def executar(texto_raw: str):
        if not texto_raw:
            return ""

        # Usa uma expressão regular para remover QUALQUER caractere que não seja A-Z ou 0-9
        texto_limpo = re.sub(r'[^A-Z0-9]', '', texto_raw.upper())
        
        # A lógica de extrair o maior candidato permanece, útil caso o OCR gere lixo
        padroes = [
            r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}', # Padrão genérico de 7 caracteres
            r'[A-Z]{3}[0-9]{4}'
        ]
        candidatos = []
        for padrao in padroes:
            candidatos.extend(re.findall(padrao, texto_limpo))
        if not candidatos:
            return texto_limpo # Retorna o texto limpo se nenhum padrão for encontrado

        return max(candidatos, key=len)