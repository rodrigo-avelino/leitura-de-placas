import cv2
from datetime import datetime
from src.config.db import SessionLocal
from src.models.acessoModel import TabelaAcesso

class Persistencia:
    @staticmethod
    def salvar(placa, score, img_source, img_crop, img_annot, data_captura=None, placa_padrao: str = None): # <-- Adicionado placa_padrao
        if not placa:
            print("[WARN] Placa inválida, não será salva.")
            return

        try:
            db = SessionLocal()

            _, buf_source = cv2.imencode(".jpg", img_source)
            _, buf_annot  = cv2.imencode(".jpg", img_annot)
            
            # Converte crop RGB (do painel) de volta para BGR para salvar
            img_crop_bgr = cv2.cvtColor(img_crop, cv2.COLOR_RGB2BGR)
            _, buf_crop = cv2.imencode(".jpg", img_crop_bgr)
            
            novo_registro = TabelaAcesso(
                plate_text=placa,
                confidence=score,
                plate_type=placa_padrao, # <-- Salva o novo campo
                source_image=buf_source.tobytes(),
                plate_crop_image=buf_crop.tobytes(),
                annotated_image=buf_annot.tobytes(),
                created_at=data_captura or datetime.utcnow()
            )

            db.add(novo_registro)
            db.commit()
            print(f"[INFO] Placa '{placa}' (Tipo: {placa_padrao}) salva no banco.")
        except Exception as e:
            print(f"[ERRO] Erro ao salvar no banco: {e}")
        finally:
            db.close()