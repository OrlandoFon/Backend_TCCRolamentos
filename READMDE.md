# Backend: Sistema de Prognóstico de Rolamentos

Este é o repositório da camada de backend do sistema de Manutenção Preditiva (PdM) de código aberto desenvolvido como parte do TCC do curso de Bacharelado em Engenharia de Controle e Automação do IFSP - Campus Guarulhos por Orlando Fonseca. O backend é responsável por toda a lógica de negócio, processamento de dados e comunicação com o frontend, executando os algoritmos de prognóstico (ESI e EKF) para predição da vida útil remanescente (RUL) de rolamentos.

A metodologia implementada reproduz fielmente o método de cálculo de RUL descrito no trabalho científico:

> WEN, H.; ZHANG, L.; SINHA, J. K. Early Prediction of Remaining Useful Life for Rolling Bearings Based on Envelope Spectral Indicator and Bayesian Filter. Applied Sciences, v. 14, n. 1, p. 436, 2024. DOI: 10.3390/app14010436. Disponível em: https://doi.org/10.3390/app14010436..

A arquitetura do backend combina **Node.js** para orquestração e comunicação web com **Python** para processamento científico de dados, proporcionando alta performance e escalabilidade.

-----

## 1. Funcionalidades Principais

* **Processamento de Sinais em Tempo Real**: Executa algoritmos de Envelope Spectral Indicator (ESI) e Extended Kalman Filter (EKF) para análise de vibração de rolamentos.
* **API REST Robusta**: Oferece endpoints para controle de simulações, obtenção de dados e gerenciamento do sistema.
* **Comunicação em Tempo Real**: Utiliza Server-Sent Events (SSE) para transmitir dados de simulação em tempo real para o frontend.
* **Arquitetura Híbrida**: Combina a flexibilidade do Node.js com o poder de processamento científico do Python.
* **Gestão de Processos**: Controla a execução de simulações Python como processos filhos, garantindo isolamento e estabilidade.
* **Padrão Repositório**: Implementa abstração para acesso aos dados do dataset XJTU-SY.

-----

## 2. Arquitetura e Padrões de Projeto do Backend

O backend é estruturado em duas camadas principais que trabalham em conjunto, seguindo princípios de separação de responsabilidades e baixo acoplamento.

### 2.1. API de Orquestração (Node.js/Express)

A camada de orquestração atua como a **Camada de Aplicação** do sistema, sendo responsável pela comunicação externa e controle de fluxo.

**Componentes Principais:**

* **`server.js`**: Ponto de entrada que inicializa o servidor Express, configura middlewares (CORS, JSON parsing) e monta as rotas da aplicação.
* **`routes/api.js`**: Centraliza a definição de todos os endpoints da API, seguindo o padrão de roteamento RESTful.
* **`controllers/simulationController.js`**: Implementa o padrão **Controller**, gerenciando requisições HTTP e coordenando a comunicação entre as camadas.
* **`services/simulationService.js`**: Implementa a lógica de negócio principal utilizando os padrões **Singleton** e **Observer** (EventEmitter).

### 2.2. Motor de Processamento (Python)

A camada de processamento executa todos os cálculos científicos e análises de dados, implementando algoritmos especializados em processamento de sinais.

**Componentes Principais:**

* **`main.py`**: Ponto de entrada que recebe argumentos via linha de comando e orquestra a execução da simulação.
* **`simulation.py`**: Contém a classe `BearingSimulator` que implementa o padrão **Generator** para processamento incremental de dados.
* **`repository.py`**: Implementa o **Padrão Repositório** para abstração do acesso aos dados do dataset XJTU-SY.
* **`processing.py`**: Módulo de funções puras para processamento matemático e análise de sinais.
* **`config.py`**: Centraliza configurações e constantes do sistema (FCFs, frequências de amostragem, metadados).

### 2.3. Comunicação Entre Camadas

A comunicação entre as camadas Node.js e Python é feita através de:

1. **Spawning de Processos**: O Node.js executa scripts Python como processos filhos usando `child_process.spawn`.
2. **Streaming de Dados**: O Python envia resultados via `stdout` em formato JSON, capturados pelo Node.js em tempo real.
3. **Event-Driven Architecture**: Utiliza EventEmitter para propagar eventos entre os componentes Node.js.

-----

## 3. Tecnologias e Bibliotecas

### Backend API (Node.js)

| Categoria | Tecnologia/Biblioteca | Versão (Recomendada) | Papel no Projeto |
| :--- | :--- | :--- | :--- |
| **Runtime** | Node.js | 18.x+ | Ambiente de execução JavaScript do servidor. |
| **Framework** | Express.js | 4.x | Framework web para criação da API REST. |
| **Middleware** | cors | 2.x | Habilitação de Cross-Origin Resource Sharing. |
| **Processo** | child_process | Nativo | Execução de scripts Python como processos filhos. |

### Motor de Processamento (Python)

| Categoria | Tecnologia/Biblioteca | Versão (Recomendada) | Papel no Projeto |
| :--- | :--- | :--- | :--- |
| **Linguagem** | Python | 3.9+ | Linguagem principal para processamento científico. |
| **Computação Científica** | NumPy | 1.24+ | Operações matriciais e processamento de arrays. |
| **Análise de Dados** | Pandas | 2.0+ | Manipulação e análise de dados estruturados. |
| **Processamento de Sinais** | SciPy | 1.10+ | Algoritmos avançados de processamento de sinais. |

-----

## 4. Estrutura de Pastas do Backend

```
backend/
├── backend-api/                 # API de Orquestração (Node.js)
│   ├── server.js               # Ponto de entrada do servidor Express
│   ├── routes/
│   │   └── api.js              # Definição de rotas da API REST
│   ├── controllers/
│   │   └── simulationController.js  # Controller para gerenciamento de simulações
│   ├── services/
│   │   └── simulationService.js     # Lógica de negócio e comunicação com Python
│   └── package.json            # Dependências e scripts do Node.js
└── python-engine/              # Motor de Processamento (Python)
    ├── main.py                 # Ponto de entrada da simulação Python
    ├── simulation.py           # Classe principal do simulador
    ├── repository.py           # Acesso aos dados do dataset
    ├── processing.py           # Funções de processamento de sinais
    ├── config.py               # Configurações e constantes
    └── requirements.txt        # Dependências Python
```

-----

## 5. API Endpoints

A API oferece os seguintes endpoints RESTful:

| Método | Endpoint | Descrição | Corpo da Requisição |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/start-simulation` | Inicia uma nova simulação para um rolamento específico | `{"bearingName": "Bearing1_2"}` |
| **GET** | `/api/stop-simulation` | Interrompe a simulação em andamento | N/A |
| **GET** | `/api/events` | Estabelece conexão SSE para dados em tempo real | N/A |
| **GET** | `/api/bearings` | Retorna lista de rolamentos disponíveis | N/A |

### Exemplo de Uso da API

```bash
# Iniciar simulação
curl -X POST http://localhost:3001/api/start-simulation \
  -H "Content-Type: application/json" \
  -d '{"bearingName": "Bearing1_2"}'

# Conectar ao stream de eventos (SSE)
curl -N http://localhost:3001/api/events

# Parar simulação
curl http://localhost:3001/api/stop-simulation
```

-----

## 6. Instalação e Execução

### Pré-requisitos

* Node.js (versão 18.x ou superior)
* Python (versão 3.9 ou superior)
* npm e pip instalados
* Dataset XJTU-SY baixado e descompactado

### Passos

1. **Clone o repositório** e navegue até a pasta do backend:

   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd tcc-prognostico-rolamentos/backend
   ```

2. **Configuração do Motor Python**:

   ```bash
   cd python-engine

   # Criar ambiente virtual (recomendado)
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

   # Instalar dependências
   pip install numpy pandas scipy
   ```

3. **Configuração da API Node.js**:

   ```bash
   cd ../backend-api

   # Instalar dependências
   npm install
   ```

4. **Configuração do Dataset**:

   Abra o arquivo `backend-api/controllers/simulationController.js` e atualize o caminho do dataset:

   ```javascript
   const basePath = "/caminho/completo/para/XJTU-SY/Data/XJTU-SY_Bearing_Datasets";
   ```

5. **Executar o servidor**:

   ```bash
   npm start
   ```

6. **Verificar funcionamento**:

   O servidor estará rodando em [http://localhost:3001](http://localhost:3001)

> **Importante**: Certifique-se de que o dataset XJTU-SY esteja corretamente configurado antes de iniciar simulações.

-----

## 7. Fluxo de Execução

1. **Requisição**: Frontend envia `POST /api/start-simulation` com nome do rolamento
2. **Validação**: Controller valida a requisição e verifica disponibilidade do sistema
3. **Spawn Process**: Service executa o script Python como processo filho
4. **Processamento**: Motor Python processa dados incrementalmente (minuto a minuto)
5. **Streaming**: Resultados são enviados via stdout em formato JSON
6. **Broadcasting**: Node.js captura dados e transmite via SSE para clientes conectados
7. **Finalização**: Processo termina e eventos de fim são enviados

-----

## 8. Monitoramento e Logs

O sistema oferece logs detalhados para acompanhamento:

* **Logs da API**: Registram requisições, erros e eventos do servidor Node.js
* **Logs de Simulação**: Capturam saída do processo Python e eventos de processamento
* **Logs de SSE**: Monitoram conexões de clientes e transmissão de dados

-----

## 9. Contribuição

Contribuições são bem-vindas! Áreas para melhoria incluem:

* Implementação de cache para otimização de performance
* Adição de autenticação e autorização
* Melhorias nos algoritmos de processamento de sinais
* Implementação de testes unitários e de integração
* Dockerização do ambiente de desenvolvimento

Para contribuir, siga o processo de *fork* e *pull request*, mantendo a qualidade do código e documentação atualizada.
