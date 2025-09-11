import argparse, os, glob
from .pipeline import process_image

def main():
    parser = argparse.ArgumentParser(description="Processa imagens para leitura de placas (ALPR)")
    parser.add_argument("--input", required=True, help="Caminho de imagem ou pasta com imagens")
    parser.add_argument("--pattern", default="*.jpg", help="Padrão glob ao usar pasta (ex: *.png)")
    args = parser.parse_args()

    path = args.input
    if os.path.isdir(path):
        files = glob.glob(os.path.join(path, args.pattern))
        if not files:
            print("Nenhuma imagem encontrada.")
            return
        for f in files:
            try:
                res = process_image(f)
                print(f"OK: {f} -> {res['plate_text']} (conf={res['confidence']:.2f}) id={res['id']}")
            except Exception as e:
                print(f"ERRO: {f}: {e}")
    else:
        res = process_image(path)
        print(res)

if __name__ == "__main__":
    main()