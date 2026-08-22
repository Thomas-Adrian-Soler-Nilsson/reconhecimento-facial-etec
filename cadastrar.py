import cv2
import os

def cadastrar_pessoa(nome):
    pasta = os.path.join("database", nome)
    os.makedirs(pasta, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro: não foi possível acessar a webcam.")
        return

    contador = 0
    print("Pressione ESPAÇO para capturar uma foto, ESC para sair")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar frame da webcam.")
            break

        cv2.imshow(f"Cadastro - {nome}", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            break
        elif key == 32:  # ESPAÇO
            contador += 1
            caminho = os.path.join(pasta, f"{nome}_{contador}.jpg")
            cv2.imwrite(caminho, frame)
            print(f"[OK] Foto salva: {caminho}")

    cap.release()
    cv2.destroyAllWindows()

    if contador == 0:
        print("Nenhuma foto foi salva.")
    else:
        print(f"\nCadastro finalizado. {contador} foto(s) salva(s) para '{nome}'.")

if __name__ == "__main__":
    nome = input("Digite o nome da pessoa a cadastrar: ").strip().lower().replace(" ", "_")
    if nome:
        cadastrar_pessoa(nome)
    else:
        print("Nome inválido.")