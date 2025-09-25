#serve para mostrar as etapas do processamento de imagens
import streamlit as st

def mostrar_etapas(result):
    st.subheader("📸 Etapas do Processamento")
    # imagem original
    if result.get("original") is not None:
        st.image(result["original"], caption="Imagem Original", channels="BGR")
    #preprocessamento: ifs verificam se as etapas foram realizadas e mostram as imagens correspondentes
    if result.get("preprocessamento") is not None:
        st.image(result["preprocessamento"], caption="Pré-processamento (Gray + Blur)", channels="GRAY")
        
    if result.get("bordas") is not None:
        st.image(result["bordas"], caption="Bordas (Canny)", channels="GRAY")
    #recorte da placa: esse if verifica se a chave existe no dicionario e se o valor nao é None
    if result.get("recorte") is not None:
        st.image(result["recorte"], caption="Recorte da Placa", channels="BGR")
    #binarizacao e segmentacao
    if result.get("binarizacao") is not None:
        st.image(result["binarizacao"], caption="Binarização", channels="GRAY")

    if result.get("segmentacao"):
        for i, char in enumerate(result["segmentacao"]):
            st.image(char, caption=f"Caractere {i+1}", channels="GRAY")

