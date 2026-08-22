import cv2

import core

PROCESSAR_A_CADA_N_FRAMES = 15


def chamada_webcam():
    if not core.listar_pessoas_cadastradas():
        print("Nenhuma pessoa cadastrada ainda. Use cadastrar.py primeiro.")
        return

    salas_existentes = core.carregar_salas()
    if salas_existentes:
        print("Salas/turmas cadastradas:", ", ".join(salas_existentes))
    sala = input("Sala/turma desta chamada (opcional, Enter para pular): ").strip()

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

    ja_registrados_na_sessao = set()
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
            nome_chave = core.identificar_pessoa(frame, exigir_rosto=False)

            if nome_chave is None:
                nome_atual = "Desconhecido"
                cor_atual = (0, 0, 255)

            elif nome_chave in ja_registrados_na_sessao:
                nome_atual = f"{nome_chave} (ja registrado)"
                cor_atual = (0, 165, 255)

            else:
                core.registrar_presenca(nome_chave, tipo="Chamada em grupo", sala=sala)
                ja_registrados_na_sessao.add(nome_chave)
                nome_atual = f"{nome_chave} - REGISTRADO!"
                cor_atual = (0, 255, 0)
                print(f"[OK] Presença registrada: {nome_chave}  ({len(ja_registrados_na_sessao)} pessoa(s) na sessão)")

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