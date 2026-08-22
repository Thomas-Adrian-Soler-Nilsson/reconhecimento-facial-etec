import os

import cv2
from deepface import DeepFace

DB_PATH = "database"
MODEL_NAME = "Facenet"
DETECTOR_BACKEND = "mtcnn"
PROCESSAR_A_CADA_N_FRAMES = 15


def reconhecer_webcam():
    if not os.path.exists(DB_PATH) or not os.listdir(DB_PATH):
        print(f"Pasta '{DB_PATH}' vazia ou não existe. Cadastre pessoas primeiro com python -m scripts.cadastrar")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro: não foi possível acessar a webcam.")
        return

    print("Reconhecimento iniciado. Pressione ESC para sair.")

    nome_detectado = "Desconhecido"
    cor = (0, 0, 255)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar frame da webcam.")
            break

        frame_count += 1

        if frame_count % PROCESSAR_A_CADA_N_FRAMES == 0:
            try:
                resultados = DeepFace.find(
                    img_path=frame,
                    db_path=DB_PATH,
                    model_name=MODEL_NAME,
                    detector_backend=DETECTOR_BACKEND,
                    enforce_detection=False,
                    silent=True
                )

                if len(resultados) > 0 and not resultados[0].empty:
                    identidade = resultados[0].iloc[0]["identity"]
                    nome_detectado = identidade.split(os.sep)[-2]
                    cor = (0, 255, 0)
                else:
                    nome_detectado = "Desconhecido"
                    cor = (0, 0, 255)

            except Exception:
                nome_detectado = "Desconhecido"
                cor = (0, 0, 255)

        cv2.putText(frame, nome_detectado, (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, cor, 2)

        cv2.imshow("Reconhecimento Facial", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    reconhecer_webcam()