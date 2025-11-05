import asyncio
import websockets
import json
import os
import base64
import numpy as np
import cv2
import re # Para limpar o prefixo do Base64

async def test_processing(image_path):
    # Aumenta o limite de tamanho da mensagem para 10MB
    uri = "ws://127.0.0.1:8000/ws/processar-imagem"
    
    try:
        async with websockets.connect(uri, max_size=10_000_000) as websocket:
            print(f"Conectado a {uri}")

            try:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
            except FileNotFoundError:
                print(f"ERRO: Imagem de teste não encontrada em {image_path}")
                return

            print(f"Enviando imagem: {image_path} ({len(image_bytes)} bytes)")
            await websocket.send(image_bytes)

            print("\n--- Respostas do Servidor (Tempo Real) ---")
            
            # Dicionário para rastrear os candidatos (rank -> imagem)
            candidate_images = {}

            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    print(f"\n[EVENTO RECEBIDO: {data.get('step')}]")
                    step_name = data.get('step')

                    # Imprime os dados e decodifica imagens
                    for key, value in data.items():
                        if key in ["image", "imagem"] or (isinstance(value, str) and value.startswith("data:image")):
                            print(f"  {key}: [Imagem Base64 (exibindo...)]")
                            
                            # --- BLOCO DE VISUALIZAÇÃO DE IMAGEM ---
                            try:
                                # 1. Remove o prefixo "data:image/png;base64,"
                                img_b64 = re.sub(r'^data:image/png;base64,', '', value)
                                # 2. Decodifica de Base64 para bytes
                                img_bytes = base64.b64decode(img_b64)
                                # 3. Converte bytes para array NumPy
                                nparr = np.frombuffer(img_bytes, np.uint8)
                                # 4. Decodifica para imagem OpenCV (RGB)
                                img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                                # 5. Converte de RGB (web) para BGR (padrão OpenCV)
                                img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
                                
                                # 6. Exibe a imagem em uma janela
                                window_name = f"Etapa: {step_name} ({key})"
                                cv2.imshow(window_name, img_bgr)
                                
                            except Exception as e:
                                print(f"    ERRO ao decodificar/exibir imagem: {e}")
                            # --- FIM DO BLOCO ---

                        elif key == "data" and step_name == "candidates_found":
                            print(f"  {key}: [Lista de {len(value)} candidatos]")
                            for cand in value:
                                rank = cand.get('rank')
                                print(f"    - Rank {rank}, Score: {cand.get('score'):.3f}, SegScore: {cand.get('seg_score'):.3f}")
                                # Armazena a imagem do candidato para exibição
                                candidate_images[rank] = cand.get("imagem") # Guarda a string Base64

                        else:
                            print(f"  {key}: {value}")
                    
                    # --- Lógica de Exibição de Candidatos Escolhidos ---
                    if step_name == "candidate_chosen" or step_name == "fallback_attempt":
                        rank_escolhido = data.get("candidate_rank")
                        if rank_escolhido in candidate_images:
                            print(f"  -> Exibindo imagem do Candidato #{rank_escolhido}...")
                            try:
                                img_b64 = re.sub(r'^data:image/png;base64,', '', candidate_images[rank_escolhido])
                                img_bytes = base64.b64decode(img_b64)
                                nparr = np.frombuffer(img_bytes, np.uint8)
                                img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                                img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
                                cv2.imshow(f"Candidato #{rank_escolhido} (Selecionado para OCR)", img_bgr)
                            except Exception as e:
                                print(f"    ERRO ao exibir imagem do candidato: {e}")


                    # Adiciona um waitKey(1) para permitir que o OpenCV
                    # processe seus eventos de janela e exiba as imagens
                    cv2.waitKey(1) 

                    if data.get("step") == "final_result":
                        print("\n--- Processamento Finalizado ---")
                        print("Pressione 'q' nas janelas de imagem para fechar.")
                        break
                        
                except websockets.exceptions.ConnectionClosedOK:
                    print("Conexão fechada pelo servidor.")
                    break
            
            # Mantém as janelas abertas até o usuário pressionar 'q'
            while True:
                if cv2.waitKey(50) & 0xFF == ord('q'):
                    break

    except Exception as e:
        print(f"Erro ao conectar ou comunicar: {e}")
    finally:
        # Fecha todas as janelas abertas do OpenCV
        cv2.destroyAllWindows()
        print("Janelas fechadas. Script encerrado.")

if __name__ == "__main__":
    # --- MUDE AQUI O CAMINHO DA IMAGEM ---
    caminho_da_imagem = r"C:\Users\rodri\Documents\TrabalhoPDI\Fotos\fotosjuntas\img_013952.jpg" # Usei o 'r'
    
    if not os.path.exists(caminho_da_imagem):
        print(f"ERRO: Caminho da imagem de teste não encontrado.")
        print(f"Por favor, edite 'caminho_da_imagem' no script test_websocket.py")
    else:
        asyncio.run(test_processing(caminho_da_imagem))