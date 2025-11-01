# src/services/ocr.py

import cv2
from paddleocr import PaddleOCR
import numpy as np
# import logging # REMOVIDO
# import sys     # REMOVIDO
# import os      # REMOVIDO
# import contextlib # REMOVIDO

# --- REMOVIDO: Configuração de logging e função suppress_stderr ---

class OCR:

    @staticmethod
    def _parse_resultado(resultado):
        """
        Função auxiliar para extrair texto e confianças do formato de saída do PaddleOCR.
        """
        texto_final = ''
        confiancas = []
        if resultado and resultado[0]:
            for linha in resultado[0]:
                if linha and len(linha) > 1:
                    texto_info = linha[1]
                    if texto_info and len(texto_info) > 1:
                        texto = texto_info[0]
                        conf = texto_info[1]
                        if isinstance(conf, (int, float)):
                           texto_final += texto
                           confiancas.extend([conf] * len(texto))
                        else:
                            texto_final += texto
                            confiancas.extend([0.0] * len(texto))
        return (texto_final, confiancas)

    @staticmethod
    def executarImg(imagem):
        """
        Realiza OCR na imagem inteira da placa.
        Cria uma nova instância do leitor a cada chamada para garantir estabilidade.
        """
        reader = None
        try:
            # A instância é criada aqui, sem supressão de stderr
            reader = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
        except Exception as e:
            # import sys # Descomente se sys não estiver importado globalmente
            # print(f"ERRO ao inicializar PaddleOCR: {e}", file=sys.stderr)
            print(f"ERRO ao inicializar PaddleOCR: {e}") # Imprime no stdout padrão
            return "", []

        if reader is None:
             return "", []

        try:
            resultado = reader.ocr(imagem)
            texto, confiancas = OCR._parse_resultado(resultado)
            return (texto.strip().upper(), confiancas)
        except Exception as e:
             # import sys # Descomente se sys não estiver importado globalmente
             # print(f"ERRO durante a execução do OCR: {e}", file=sys.stderr)
             print(f"ERRO durante a execução do OCR: {e}") # Imprime no stdout padrão
             return "", []