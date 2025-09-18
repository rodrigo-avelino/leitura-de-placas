import re

class Montagem:
    @staticmethod
    def executar(texto_raw: str):
        if not texto_raw:
            return ""

        texto = texto_raw.upper().replace(" ", "").replace("-", "")

        padroes = [
            r'[A-Z]{3}[0-9]{4}',             # Antiga: ABC1234
            r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}' # Mercosul: ABC1D23
        ]

        candidatos = []
        for padrao in padroes:
            candidatos.extend(re.findall(padrao, texto))

        if not candidatos:
            return texto  # retorna bruto se regex falhar

        return max(candidatos, key=len)