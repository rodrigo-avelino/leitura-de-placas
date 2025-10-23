import cv2
from paddleocr import PaddleOCR
import numpy as np

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
                        texto_final += texto
                        for _ in range(len(texto)):
                            confiancas.append(conf)
        return (texto_final, confiancas)

    @staticmethod
    def executarImg(imagem):
        """
        Realiza OCR na imagem inteira da placa. Esta é a nossa única estratégia de OCR.
        Cria uma nova instância do leitor a cada chamada para garantir estabilidade.
        """
        # print("[INFO OCR] Criando nova instância do PaddleOCR...")
        reader = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
        
        resultado = reader.ocr(imagem)
        texto, confiancas = OCR._parse_resultado(resultado)
        return (texto.strip().upper(), confiancas)

    # A função executarCaracteres foi permanentemente removida.