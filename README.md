# Sistema de Reconhecimento Facial para Registro de Presença

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![DeepFace](https://img.shields.io/badge/DeepFace-facial%20recognition-6c5ce7)
![OpenCV](https://img.shields.io/badge/OpenCV-4.10-5C3EE8?logo=opencv&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

Sistema de reconhecimento facial com interface gráfica, feito com Python, OpenCV, DeepFace e CustomTkinter. Permite cadastrar pessoas e registrar presença automaticamente — genérico o suficiente para uso em escolas (chamada de alunos) ou empresas (ponto de funcionários).

> Projeto desenvolvido para a ETEC/FATEC Itu como alternativa digital à chamada manual, usando reconhecimento facial em tempo real.

## Sumário

- [Estrutura do projeto](#estrutura-do-projeto)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Usar o executável Windows](#usar-o-executável-windows)
- [Como usar (interface gráfica)](#como-usar-interface-gráfica--recomendado)
- [Como usar (scripts de terminal)](#como-usar-scripts-de-terminal--alternativa)
- [Configurações ajustáveis](#configurações-ajustáveis-dentro-de-reconhecerpy)
- [Problemas comuns](#problemas-comuns)
- [Próximos passos possíveis](#próximos-passos-possíveis)
- [Licença](#licença)

## Estrutura do projeto

```
projeto_facial/
├── database/                 # fotos das pessoas cadastradas (dados locais, ignorados pelo Git)
├── img/                      # imagens da interface
│   └── logo.png              # logo exibida na sidebar
├── ui/                       # tema e componentes reutilizáveis da interface
│   ├── __init__.py           # definição do pacote de interface
│   ├── theme.py              # cores, fontes e dimensões visuais
│   ├── components.py         # botões, painéis e helpers de UI
│   └── screens/              # telas da interface gráfica
│       ├── common.py         # helpers compartilhados pelas telas
│       ├── inicio.py
│       ├── cadastro.py
│       ├── pessoas.py
│       ├── salas.py
│       ├── registro_individual.py
│       ├── registro_grupo.py
│       ├── relatorios.py
│       ├── importar_csv.py
│       └── configuracoes.py
├── docs/                     # especificações e planos de evolução do projeto
│   └── superpowers/
│       ├── plans/
│       └── specs/
├── app.py                    # janela principal, navegação e câmera
├── core.py                   # lógica compartilhada: reconhecimento e regras da aplicação
├── db.py                     # persistência e consultas do banco SQLite
├── models.py                 # modelos de dados do sistema
├── scripts/                  # pontos de entrada para uso pelo terminal
│   ├── __init__.py
│   ├── cadastrar.py          # cadastro de pessoas
│   ├── reconhecer.py         # reconhecimento facial contínuo
│   ├── ponto.py              # registro individual de presença
│   └── chamada.py            # chamada em grupo
├── config.json               # configurações locais da organização
├── sistema_presenca.db       # banco SQLite local (gerado automaticamente)
├── registros.csv             # arquivo de importação/exportação de registros
├── requirements.txt          # dependências Python
├── LICENSE                   # licença MIT
└── README.md                 # documentação do projeto
```

A logo da organização muda conforme o tema: `img/fatec_etec_fundo_claro_transparente.png` no modo claro e `img/fatec_etec_modo_escuro_transparente.png` no modo escuro. Para usar outras imagens, altere `logo_claro_path` e `logo_escuro_path` no `config.json`.

> Os scripts de linha de comando em `scripts/` continuam funcionando e são úteis para testes rápidos, mas o `app.py` reúne tudo isso numa única interface gráfica e é a forma recomendada de uso.

## Requisitos

- Windows 10/11
- Python 3.11 (o TensorFlow ainda não suporta versões mais novas, como 3.13/3.14)
- Webcam funcional
- Conexão com internet (necessária na primeira execução, para baixar os pesos dos modelos)

## Instalação

### 1. Instalar o Python 3.11

Pelo PowerShell ou CMD:

```powershell
winget install --id Python.Python.3.11 -e --source winget
```

Feche e abra um novo terminal depois de instalar. Confirme com:

```powershell
py -3.11 --version
```

### 2. Criar e ativar o ambiente virtual

Dentro da pasta do projeto:

```powershell
py -3.11 -m venv venv
venv\Scripts\activate
```

> **Erro de política de execução no PowerShell?**
> Se aparecer `A execução de scripts foi desabilitada neste sistema`, rode uma vez:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Depois tente ativar o venv novamente.

Com o venv ativado, o prompt deve começar com `(venv)`.

### 3. Instalar as dependências

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

| Pacote | Para que serve |
|---|---|
| `tensorflow` | motor de deep learning usado pelos modelos de reconhecimento |
| `tf-keras` | camada de compatibilidade exigida pelo TensorFlow 2.x + DeepFace |
| `deepface` | biblioteca de reconhecimento facial |
| `opencv-python` | captura e exibição de vídeo da webcam (fixado na `4.10.0.84`, pois versões `5.x` vieram com bug faltando arquivos internos) |
| `customtkinter` | interface gráfica moderna (usada pelo `app.py`) |
| `pillow` | conversão dos frames da webcam para exibição na interface gráfica |
| `iconipy` | geração dos ícones usados nos botões da interface |

## Como usar (interface gráfica — recomendado)

Sempre ative o venv antes de rodar:

```powershell
cd "caminho\para\projeto_facial"
venv\Scripts\activate
python app.py
```

Isso abre a janela principal do sistema, com um menu lateral:

- **🏠 Início** — visão geral: quantas pessoas estão cadastradas, quantos registros já existem.
- **➕ Cadastrar Pessoa** — abre a câmera, digite o nome e clique em "Capturar foto" (repita 3–5 vezes). O cache de reconhecimento é limpo automaticamente a cada novo cadastro.
- **👥 Pessoas Cadastradas** — lista nome, sala/turma, RA/matrícula e quantidade de fotos, permitindo excluir um cadastro com confirmação.
- **🏫 Salas / Turmas** — cadastra e remove salas ou turmas usadas nos registros.
- **✅ Registrar Presença** — modo individual: a pessoa se posiciona na câmera, escolhe "Entrada" ou "Saída" e clica em Registrar. Ideal para um totem ou recepção.
- **👥 Chamada em Grupo** — modo contínuo: clique em "Iniciar chamada" e a câmera reconhece automaticamente cada pessoa que passar, registrando uma vez por sessão. Clique em "Encerrar chamada" ao final. Ideal para início de aula/reunião.
- **📊 Relatórios** — lista todos os registros salvos (nome, tipo, data, hora), com botão de atualizar.
- **📥 Importar Pessoas (CSV)** — importa nomes, salas e RA/matrícula de um arquivo CSV, com mapeamento manual das colunas.
- **⚙️ Configurações** — define o nome da instituição/empresa, se é "Escola" ou "Empresa" (aparece no cabeçalho), o tema claro/escuro, o intervalo mínimo entre registros repetidos, e permite limpar o cache de reconhecimento manualmente.

> **Primeira execução:** assim como nos scripts de terminal, o DeepFace baixa os pesos dos modelos na primeira vez que uma foto é processada — pode levar um tempinho sem feedback visual, é normal.

## Usar o executável Windows

Para usar uma versão já compilada, copie a pasta completa `dist/SistemaPresenca` para o computador Windows e abra:

```text
SistemaPresenca/SistemaPresenca.exe
```

Não copie apenas o arquivo `.exe`: a pasta `_internal/` contém bibliotecas necessárias para o funcionamento do sistema. A webcam precisa estar conectada e a primeira execução pode exigir internet para baixar os pesos do DeepFace.

Os dados da instalação ficam na mesma pasta de execução:

- `database/` — fotos cadastradas;
- `sistema_presenca.db` — pessoas, turmas e registros de presença;
- `config.json` — configurações, tema e caminho da logo;
- `registros.csv` — arquivos CSV importados ou relatórios exportados.

Faça cópias de segurança desses arquivos antes de trocar ou remover a pasta do sistema.

## Gerar o executável Windows

Esta seção é destinada a quem mantém o projeto. Com o ambiente virtual configurado, execute no PowerShell:

```powershell
.\build_exe.ps1
```

O executável será criado em `dist/SistemaPresenca/SistemaPresenca.exe`. Distribua a pasta inteira `dist/SistemaPresenca`, não apenas o arquivo `.exe`.

## Como usar (scripts de terminal — alternativa)

Sempre ative o venv antes de rodar qualquer script:

```powershell
cd "caminho\para\projeto_facial"
venv\Scripts\activate
```

### 1. Cadastrar uma pessoa

```powershell
python -m scripts.cadastrar
```

- Digite o nome da pessoa quando solicitado.
- Uma janela da webcam vai abrir.
- Pressione **ESPAÇO** para tirar uma foto (repita 3–5 vezes, variando ângulo e expressão — melhora a precisão).
- Pressione **ESC** para terminar o cadastro.

As fotos são salvas em `database/<nome>/`.

### 2. Reconhecer rostos ao vivo

```powershell
python -m scripts.reconhecer
```

- A janela da webcam abre mostrando o nome da pessoa reconhecida (verde) ou "Desconhecido" (vermelho).
- Pressione **ESC** para encerrar.

> **Primeira execução:** o DeepFace baixa automaticamente os pesos dos modelos (Facenet, MTCNN etc.) na primeira vez que reconhece um rosto. Isso pode levar de alguns segundos a poucos minutos, sem barra de progresso — é normal parecer "travado".

## Configurações ajustáveis (dentro de `scripts/reconhecer.py`)

```python
MODEL_NAME = "Facenet"           # modelo de reconhecimento: Facenet, VGG-Face, ArcFace, Dlib...
DETECTOR_BACKEND = "mtcnn"       # detector de rosto: mtcnn, opencv, retinaface...
PROCESSAR_A_CADA_N_FRAMES = 15   # a cada quantos frames roda o reconhecimento
```

- **`PROCESSAR_A_CADA_N_FRAMES`**: o reconhecimento facial é pesado e travava a câmera se rodasse em todo frame. Esse número controla o equilíbrio entre fluidez e velocidade de atualização do nome:
  - valores **maiores** (ex: 25–30) → câmera mais fluida, nome atualiza mais devagar
  - valores **menores** (ex: 5–10) → nome atualiza mais rápido, porém mais travadinho

## Cadastrando novas pessoas depois de já ter usado o reconhecimento

O DeepFace pode criar um arquivo de cache `.pkl` dentro de `database/` para acelerar comparações futuras. Se uma pessoa nova não for reconhecida, limpe esse cache antes de executar o reconhecimento novamente.

```powershell
del database\*.pkl
```

## Problemas comuns

| Erro | Causa | Solução |
|---|---|---|
| `ModuleNotFoundError: No module named 'cv2'` | Scripts rodando fora do venv | Ative o venv antes: `venv\Scripts\activate` |
| `ResolutionImpossible` ao instalar deepface | Python muito novo (3.13/3.14), sem build de TensorFlow disponível | Use Python 3.11 no venv |
| `ValueError: ...requires tf-keras package` | TensorFlow 2.x usa Keras 3 por padrão | `pip install tf-keras` |
| `Confirm that opencv is installed... haarcascade_frontalface_default.xml` | Pacote `opencv-python` corrompido/incompleto (ex: versão `5.x`) | Reinstale: `pip uninstall opencv-python opencv-python-headless -y` seguido de `pip install opencv-python==4.10.0.84` |
| Câmera travando muito | Reconhecimento rodando em todo frame | Ajuste `PROCESSAR_A_CADA_N_FRAMES` em `scripts/reconhecer.py` |
| Webcam não abre / tela preta | Índice de câmera errado ou em uso por outro app | Troque `cv2.VideoCapture(0)` para `cv2.VideoCapture(1)` |

## Próximos passos possíveis

- Aprimorar a gestão de embeddings e o desempenho do reconhecimento
- Expor o reconhecimento como API (FastAPI/Flask)
- Adicionar registro de log de acessos (quem foi reconhecido e quando)
- Separar registros por turma/matéria ou por setor da empresa
- Gerar relatório de faltas comparando presentes x lista total de cadastrados

## Licença

Este projeto está sob a licença MIT — veja o arquivo [LICENSE](LICENSE) para mais detalhes.