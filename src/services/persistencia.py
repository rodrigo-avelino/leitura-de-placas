import cv2
from datetime import datetime
from src.config.db import SessionLocal
from src.models.acessoModel import TabelaAcesso

class Persistencia:
    @staticmethod
    def salvar(placa, score, img_source, img_crop, img_annot, data_captura=None, placa_padrao: str = None):
        """
        Salva o registro de placa no banco de dados e retorna o objeto TabelaAcesso salvo, 
        incluindo o ID gerado pelo banco.
        """
        if not placa:
            print("[WARN] Placa inválida, não será salva.")
            return None # Retorna None se a placa for inválida (boa prática)

        db = SessionLocal()
        try:
            _, buf_source = cv2.imencode(".jpg", img_source)
            _, buf_annot  = cv2.imencode(".jpg", img_annot)
            
            # Converte crop RGB (do painel) de volta para BGR para salvar
            img_crop_bgr = cv2.cvtColor(img_crop, cv2.COLOR_RGB2BGR)
            _, buf_crop = cv2.imencode(".jpg", img_crop_bgr)
            
            novo_registro = TabelaAcesso(
                plate_text=placa,
                confidence=score,
                plate_type=placa_padrao,
                source_image=buf_source.tobytes(),
                plate_crop_image=buf_crop.tobytes(),
                annotated_image=buf_annot.tobytes(),
                created_at=data_captura or datetime.now()  # Alterado de utcnow para now (horário local)
            )

            db.add(novo_registro)
            db.commit()
            
            # --- CORREÇÃO CRÍTICA DO ID ---
            # 1. Atualiza o objeto 'novo_registro' com os dados do banco, incluindo o ID gerado
            db.refresh(novo_registro) 
            
            print(f"[INFO] Placa '{placa}' (Tipo: {placa_padrao}) salva no banco. ID: {novo_registro.id}")
            
            # 2. Retorna o objeto completo, que agora contém o ID
            return novo_registro

        except Exception as e:
            db.rollback() # Garante que a transação é desfeita em caso de erro
            print(f"[ERRO] Erro ao salvar no banco: {e}")
            return None # Retorna None em caso de falha na persistência
        finally:
            db.close()