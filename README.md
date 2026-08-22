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
- [Como usar (interface gráfica)](#como-usar-interface-gráfica--recomendado)
- [Como usar (scripts de terminal)](#como-usar-scripts-de-terminal--alternativa)
- [Configurações ajustáveis](#configurações-ajustáveis-dentro-de-reconhecerpy)
- [Problemas comuns](#problemas-comuns)
- [Próximos passos possíveis](#próximos-passos-possíveis)
- [Licença](#licença)

## Estrutura do projeto

```
projeto_facial/
├── database/            # fotos das pessoas cadastradas (criado automaticamente)
│   ├── thomas/
│   │   └── thomas_1.jpg
│   └── thomas2/
│       └── thomas2_1.jpg
├── venv/                 # ambiente virtual Python (criado na instalação)
├── core.py               # lógica compartilhada: reconhecimento, config e registros
├── app.py                # ⭐ interface gráfica principal (use este para o dia a dia)
├── config.json            # configurações da organização (criado automaticamente)
├── registros.csv          # log de presenças (criado automaticamente)
├── cadastrar.py           # script de linha de comando (cadastro via terminal)
├── reconhecer.py          # script de linha de comando (reconhecimento contínuo)
├── ponto.py               # script de linha de comando (registro individual sob demanda)
├── chamada.py             # script de linha de comando (chamada em grupo)
└── README.md
```

> Os scripts de linha de comando (`cadastrar.py`, `reconhecer.py`, `ponto.py`, `chamada.py`) continuam funcionando e são úteis para testes rápidos, mas o `app.py` reúne tudo isso numa única interface gráfica e é a forma recomendada de uso.

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
pip install tensorflow deepface tf-keras opencv-python==4.10.0.84 customtkinter pillow
```

| Pacote | Para que serve |
|---|---|
| `tensorflow` | motor de deep learning usado pelos modelos de reconhecimento |
| `tf-keras` | camada de compatibilidade exigida pelo TensorFlow 2.x + DeepFace |
| `deepface` | biblioteca de reconhecimento facial |
| `opencv-python` | captura e exibição de vídeo da webcam (fixado na `4.10.0.84`, pois versões `5.x` vieram com bug faltando arquivos internos) |
| `customtkinter` | interface gráfica moderna (usada pelo `app.py`) |
| `pillow` | conversão dos frames da webcam para exibição na interface gráfica |

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
- **✅ Registrar Presença** — modo individual: a pessoa se posiciona na câmera, escolhe "Entrada" ou "Saída" e clica em Registrar. Ideal para um totem ou recepção.
- **👥 Chamada em Grupo** — modo contínuo: clique em "Iniciar chamada" e a câmera reconhece automaticamente cada pessoa que passar, registrando uma vez por sessão. Clique em "Encerrar chamada" ao final. Ideal para início de aula/reunião.
- **📊 Relatórios** — lista todos os registros salvos (nome, tipo, data, hora), com botão de atualizar.
- **⚙️ Configurações** — define o nome da instituição/empresa, se é "Escola" ou "Empresa" (aparece no cabeçalho), o intervalo mínimo entre registros repetidos, e permite limpar o cache de reconhecimento manualmente.

> **Primeira execução:** assim como nos scripts de terminal, o DeepFace baixa os pesos dos modelos na primeira vez que uma foto é processada — pode levar um tempinho sem feedback visual, é normal.

## Como usar (scripts de terminal — alternativa)

Sempre ative o venv antes de rodar qualquer script:

```powershell
cd "caminho\para\projeto_facial"
venv\Scripts\activate
```

### 1. Cadastrar uma pessoa

```powershell
python cadastrar.py
```

- Digite o nome da pessoa quando solicitado.
- Uma janela da webcam vai abrir.
- Pressione **ESPAÇO** para tirar uma foto (repita 3–5 vezes, variando ângulo e expressão — melhora a precisão).
- Pressione **ESC** para terminar o cadastro.

As fotos são salvas em `database/<nome>/`.

### 2. Reconhecer rostos ao vivo

```powershell
python reconhecer.py
```

- A janela da webcam abre mostrando o nome da pessoa reconhecida (verde) ou "Desconhecido" (vermelho).
- Pressione **ESC** para encerrar.

> **Primeira execução:** o DeepFace baixa automaticamente os pesos dos modelos (Facenet, MTCNN etc.) na primeira vez que reconhece um rosto. Isso pode levar de alguns segundos a poucos minutos, sem barra de progresso — é normal parecer "travado".

## Configurações ajustáveis (dentro de `reconhecer.py`)

```python
MODEL_NAME = "Facenet"           # modelo de reconhecimento: Facenet, VGG-Face, ArcFace, Dlib...
DETECTOR_BACKEND = "mtcnn"       # detector de rosto: mtcnn, opencv, retinaface...
PROCESSAR_A_CADA_N_FRAMES = 15   # a cada quantos frames roda o reconhecimento
```

- **`PROCESSAR_A_CADA_N_FRAMES`**: o reconhecimento facial é pesado e travava a câmera se rodasse em todo frame. Esse número controla o equilíbrio entre fluidez e velocidade de atualização do nome:
  - valores **maiores** (ex: 25–30) → câmera mais fluida, nome atualiza mais devagar
  - valores **menores** (ex: 5–10) → nome atualiza mais rápido, porém mais travadinho

## Cadastrando novas pessoas depois de já ter usado o reconhecimento

O DeepFace cria um arquivo de cache `.pkl` dentro de `database/` na primeira vez que roda `reconhecer.py`, para acelerar comparações futuras. Se você cadastrar uma pessoa nova, **apague esse arquivo `.pkl`** antes de rodar `reconhecer.py` de novo — senão a pessoa nova não será reconhecida.

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
| Câmera travando muito | Reconhecimento rodando em todo frame | Ajuste `PROCESSAR_A_CADA_N_FRAMES` em `reconhecer.py` |
| Webcam não abre / tela preta | Índice de câmera errado ou em uso por outro app | Troque `cv2.VideoCapture(0)` para `cv2.VideoCapture(1)` |

## Próximos passos possíveis

- Salvar embeddings em banco de dados (SQLite/PostgreSQL) em vez de comparar imagens a cada execução
- Expor o reconhecimento como API (FastAPI/Flask)
- Adicionar registro de log de acessos (quem foi reconhecido e quando)
- Separar registros por turma/matéria ou por setor da empresa
- Gerar relatório de faltas comparando presentes x lista total de cadastrados

## Licença

Este projeto está sob a licença MIT — veja o arquivo [LICENSE](LICENSE) para mais detalhes.