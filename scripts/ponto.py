import cv2

import core


def ponto_webcam():
    if not core.listar_pessoas_cadastradas():
        print("Nenhuma pessoa cadastrada ainda. Use python -m scripts.cadastrar primeiro.")
        return

    cfg = core.carregar_config()
    minutos = cfg.get("minutos_entre_registros", 5)

    salas_existentes = core.carregar_salas()
    if salas_existentes:
        print("Salas/turmas cadastradas:", ", ".join(salas_existentes))
    sala = input("Sala/turma deste registro (opcional, Enter para pular): ").strip()

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

        cv2.putText(frame, "ESPACO = registrar | ESC = sair", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        if frames_mensagem_restantes > 0:
            cv2.putText(frame, mensagem, (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_mensagem, 2)
            frames_mensagem_restantes -= 1

        cv2.imshow("Ponto - Reconhecimento Facial", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:
            break
        elif key == 32:
            print("Identificando...")
            nome_chave = core.identificar_pessoa(frame, exigir_rosto=True)

            if nome_chave is None:
                mensagem = "Rosto nao reconhecido"
                cor_mensagem = (0, 0, 255)
                print("[X] Rosto não reconhecido / não cadastrado.")
            elif core.ja_registrado_recentemente(nome_chave, minutos, sala=sala or None):
                mensagem = f"{nome_chave} ja registrado (aguarde)"
                cor_mensagem = (0, 165, 255)
                print(f"[!] {nome_chave} já registrado há menos de {minutos} min.")
            else:
                core.registrar_presenca(nome_chave, tipo="Entrada", sala=sala)
                mensagem = f"Presenca registrada: {nome_chave}"
                cor_mensagem = (0, 255, 0)
                print(f"[OK] Presença registrada para: {nome_chave}")

            frames_mensagem_restantes = 60

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    ponto_webcam()