import cv2
from datetime import datetime

from src.config.db import SessionLocal
from src.models.acessoModel import TabelaAcesso
# --- CORREÇÃO APLICADA AQUI ---
class Persistencia:
    @staticmethod
    def salvar(placa, score, img_source, img_crop, img_annot, data_captura = None):
        if not placa:
            print("[WARN] Placa inválida, não será salva.")
            return

        try:
            db = SessionLocal()

            # converter imagens OpenCV (numpy) em bytes
            _, buf_source = cv2.imencode(".jpg", img_source)
            _, buf_annot  = cv2.imencode(".jpg", img_annot)
            # --- CORREÇÃO APLICADA AQUI ---
            # A imagem 'img_crop' está em RGB, então a convertemos de volta para BGR
            # antes de salvá-la com a função do OpenCV.
            img_crop_bgr = cv2.cvtColor(img_crop, cv2.COLOR_RGB2BGR)
            _, buf_crop = cv2.imencode(".jpg", img_crop_bgr)
            # aqui cria o objeto do modelo ORM com os dados para salvar no banco 
            novo_registro = TabelaAcesso(
                plate_text=placa,
                confidence=score,
                source_image=buf_source.tobytes(),
                plate_crop_image=buf_crop.tobytes(),
                annotated_image=buf_annot.tobytes(),
                created_at=data_captura or datetime.utcnow()
            )

            db.add(novo_registro)
            db.commit()
            print(f"[INFO] Placa '{placa}' salva no banco com sucesso.")
        except Exception as e:
            print(f"[ERRO] Erro ao salvar no banco: {e}")
        finally:
            db.close()