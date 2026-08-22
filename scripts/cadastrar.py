import cv2

import core


def cadastrar_pessoa(nome_exibicao, sala=""):
    nome_chave = nome_exibicao.strip().lower().replace(" ", "_")

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

        cv2.imshow(f"Cadastro - {nome_exibicao}", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:
            break
        elif key == 32:
            caminho = core.salvar_foto_cadastro(nome_chave, frame)
            contador += 1
            print(f"[OK] Foto salva: {caminho}")

    cap.release()
    cv2.destroyAllWindows()

    if contador == 0:
        print("Nenhuma foto foi salva.")
        return

    core.definir_pessoa_meta(nome_chave, nome_exibicao=nome_exibicao, sala=sala)
    core.limpar_cache_embeddings()

    print(f"\nCadastro finalizado. {contador} foto(s) salva(s) para '{nome_exibicao}'.")
    if sala:
        print(f"Associado à sala/turma: {sala}")


if __name__ == "__main__":
    nome = input("Digite o nome da pessoa a cadastrar: ").strip()
    if not nome:
        print("Nome inválido.")
    else:
        salas_existentes = core.carregar_salas()
        if salas_existentes:
            print("Salas/turmas cadastradas:", ", ".join(salas_existentes))
        sala = input("Sala/turma (opcional, Enter para pular): ").strip()
        cadastrar_pessoa(nome, sala=sala)