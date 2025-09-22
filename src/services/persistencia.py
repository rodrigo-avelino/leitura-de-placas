import cv2
from datetime import datetime

from src.config.db import SessionLocal, UPLOAD_DIR, CROP_DIR, ANNOTATED_DIR
from src.models.acessoModel import TabelaAcesso

class Persistencia:
    @staticmethod
    def salvar(placa, score, img_source, img_crop, img_annot):
        if not placa:
            print("[WARN] Placa inválida, não será salva.")
            return

        db = None
        try:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

            # Nomes dos arquivos (simples e únicos)
            src_name   = f"{placa}_{ts}_src.jpg"
            crop_name  = f"{placa}_{ts}_crop.jpg"
            annot_name = f"{placa}_{ts}_annot.jpg"

            # Caminhos finais
            src_path   = UPLOAD_DIR / src_name
            crop_path  = CROP_DIR / crop_name
            annot_path = ANNOTATED_DIR / annot_name

            # Grava as imagens em disco
            cv2.imwrite(str(src_path),   img_source)
            cv2.imwrite(str(crop_path),  img_crop)
            cv2.imwrite(str(annot_path), img_annot)

            # Persiste os PATHS (coerente com consultarRegistros)
            db = SessionLocal()
            novo = TabelaAcesso(
                plate_text=placa,
                confidence=float(score or 0.0),
                source_path=str(src_path),
                plate_crop_path=str(crop_path),
                annotated_path=str(annot_path),
                created_at=datetime.utcnow(),
            )
            db.add(novo)
            db.commit()
            print(f"[INFO] Placa '{placa}' salva no banco com sucesso.")
        except Exception as e:
            print(f"[ERRO] Erro ao salvar no banco: {e}")
        finally:
            if db:
                db.close()

#MUDANÇA PARA VALIDAR O MVP:

#Garante que a tela de consulta consiga ler e exibir as imagens a partir de paths reais (exatamente o que o controller já espera).
#Só muda o jeito de persistir para ficar alinhado com a UI do MVP.