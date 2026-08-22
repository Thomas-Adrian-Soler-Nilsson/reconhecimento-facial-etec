import cv2
import os
import csv
from datetime import datetime
from deepface import DeepFace

DB_PATH = "database"
LOG_PATH = "registros.csv"
MODEL_NAME = "Facenet"
DETECTOR_BACKEND = "mtcnn"
PROCESSAR_A_CADA_N_FRAMES = 15  # equilíbrio entre fluidez da câmera e velocidade de reconhecimento


def garantir_csv():
    """Cria o CSV com cabeçalho se ele ainda não existir."""
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["nome", "data", "hora", "timestamp"])


def registrar_presenca(nome):
    """Grava uma nova linha no CSV com nome, data e hora."""
    agora = datetime.now()
    with open(LOG_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            nome,
            agora.strftime("%d/%m/%Y"),
            agora.strftime("%H:%M:%S"),
            agora.isoformat()
        ])


def identificar_pessoa(frame):
    """Roda o DeepFace no frame e retorna o nome identificado ou None."""
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
            return identidade.split(os.sep)[-2]

    except Exception:
        pass

    return None


def chamada_webcam():
    if not os.path.exists(DB_PATH) or not os.listdir(DB_PATH):
        print(f"Pasta '{DB_PATH}' vazia ou não existe. Cadastre pessoas primeiro com cadastrar.py")
        return

    garantir_csv()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro: não foi possível acessar a webcam.")
        return

    print("=" * 55)
    print("CHAMADA AUTOMÁTICA - Reconhecimento Facial Contínuo")
    print("=" * 55)
    print("A câmera vai reconhecer e registrar automaticamente")
    print("cada pessoa UMA VEZ durante esta sessão.")
    print("Pressione ESC para encerrar a chamada.")
    print("=" * 55)

    ja_registrados_na_sessao = set()  # evita duplicar a mesma pessoa na mesma chamada
    nome_atual = "Procurando rosto..."
    cor_atual = (200, 200, 200)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar frame da webcam.")
            break

        frame_count += 1

        if frame_count % PROCESSAR_A_CADA_N_FRAMES == 0:
            nome = identificar_pessoa(frame)

            if nome is None:
                nome_atual = "Desconhecido"
                cor_atual = (0, 0, 255)

            elif nome in ja_registrados_na_sessao:
                nome_atual = f"{nome} (ja registrado)"
                cor_atual = (0, 165, 255)

            else:
                registrar_presenca(nome)
                ja_registrados_na_sessao.add(nome)
                nome_atual = f"{nome} - REGISTRADO!"
                cor_atual = (0, 255, 0)
                print(f"[OK] Presença registrada: {nome}  ({len(ja_registrados_na_sessao)} pessoa(s) na sessão)")

        # Barra de status fixa
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (40, 40, 40), -1)
        cv2.putText(frame, f"Registrados nesta sessao: {len(ja_registrados_na_sessao)} | ESC = encerrar",
                    (10, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        cv2.putText(frame, nome_atual, (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, cor_atual, 2)

        cv2.imshow("Chamada - Reconhecimento Facial", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

    print("=" * 55)
    print(f"Chamada encerrada. Total de pessoas registradas: {len(ja_registrados_na_sessao)}")
    if ja_registrados_na_sessao:
        print("Presentes:", ", ".join(sorted(ja_registrados_na_sessao)))
    print("=" * 55)


if __name__ == "__main__":
    chamada_webcam()