import cv2
import os
import csv
from datetime import datetime
from deepface import DeepFace

DB_PATH = "database"
LOG_PATH = "registros.csv"
MODEL_NAME = "Facenet"
DETECTOR_BACKEND = "mtcnn"
MINUTOS_ENTRE_REGISTROS = 5  # evita registrar a mesma pessoa 2x seguidas em pouco tempo


def garantir_csv():
    """Cria o CSV com cabeçalho se ele ainda não existir."""
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["nome", "data", "hora", "timestamp"])


def ja_registrado_recentemente(nome):
    """Verifica se essa pessoa já foi registrada nos últimos N minutos."""
    if not os.path.exists(LOG_PATH):
        return False

    agora = datetime.now()
    with open(LOG_PATH, mode="r", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))

    for linha in reversed(linhas):
        if linha["nome"] == nome:
            registrado_em = datetime.fromisoformat(linha["timestamp"])
            diferenca_min = (agora - registrado_em).total_seconds() / 60
            return diferenca_min < MINUTOS_ENTRE_REGISTROS

    return False


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
            enforce_detection=True,  # aqui queremos garantir que É um rosto
            silent=True
        )

        if len(resultados) > 0 and not resultados[0].empty:
            identidade = resultados[0].iloc[0]["identity"]
            return identidade.split(os.sep)[-2]

    except Exception as e:
        print(f"[Aviso] Não foi possível identificar um rosto: {e}")

    return None


def ponto_webcam():
    if not os.path.exists(DB_PATH) or not os.listdir(DB_PATH):
        print(f"Pasta '{DB_PATH}' vazia ou não existe. Cadastre pessoas primeiro com cadastrar.py")
        return

    garantir_csv()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro: não foi possível acessar a webcam.")
        return

    print("=" * 50)
    print("SISTEMA DE PONTO - Reconhecimento Facial")
    print("=" * 50)
    print("Pressione ESPAÇO para registrar presença")
    print("Pressione ESC para sair")
    print("=" * 50)

    mensagem = ""
    cor_mensagem = (255, 255, 255)
    frames_mensagem_restantes = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar frame da webcam.")
            break

        # Mostra instrução fixa no topo
        cv2.putText(frame, "ESPACO = registrar | ESC = sair", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Mostra mensagem temporária de resultado (últimos ~60 frames, ~2s)
        if frames_mensagem_restantes > 0:
            cv2.putText(frame, mensagem, (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_mensagem, 2)
            frames_mensagem_restantes -= 1

        cv2.imshow("Ponto - Reconhecimento Facial", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            break

        elif key == 32:  # ESPAÇO
            print("Identificando...")
            nome = identificar_pessoa(frame)

            if nome is None:
                mensagem = "Rosto nao reconhecido"
                cor_mensagem = (0, 0, 255)
                print("[X] Rosto não reconhecido / não cadastrado.")

            elif ja_registrado_recentemente(nome):
                mensagem = f"{nome} ja registrado (aguarde)"
                cor_mensagem = (0, 165, 255)
                print(f"[!] {nome} já registrado há menos de {MINUTOS_ENTRE_REGISTROS} min.")

            else:
                registrar_presenca(nome)
                mensagem = f"Presenca registrada: {nome}"
                cor_mensagem = (0, 255, 0)
                print(f"[OK] Presença registrada para: {nome}")

            frames_mensagem_restantes = 60

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    ponto_webcam()