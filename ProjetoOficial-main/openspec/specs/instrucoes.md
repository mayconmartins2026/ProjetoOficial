Instruções: # Impacta - Instruções para o Agente (IA)

Este documento define as regras de comportamento, arquitetura e padrões de código que o agente de IA deve seguir estritamente ao desenvolver o projeto Impacta.

## 1. Padrões de Desenvolvimento (Python & Streamlit)
*   **Linguagem Base:** Escrever código em Python limpo, tipado (type hints) e seguindo as normas PEP 8.
*   **Interface (Frontend):** Utilizar exclusivamente a biblioteca `streamlit` (`import streamlit as st`).
*   **Gestão de Estado:** Utilizar o `st.session_state` para gerir a sessão do utilizador (ex: tokens de login, preferências, dados carregados).
*   **Modularidade:** Não colocar todo o código num único ficheiro. Separar a lógica de interface (telas do Streamlit) da lógica de negócios e chamadas de rede (ficheiros como `xano_data.py`).

## 2. Comunicação com o Backend (Xano)
*   **Protocolo:** Utilizar a biblioteca `requests` para comunicar com os endpoints REST do Xano.
*   **Autenticação:** O sistema utiliza JWT. O token recebido no login deve ser armazenado de forma segura e injetado no cabeçalho HTTP (`Authorization: Bearer <token>`) em todos os pedidos protegidos.
*   **Tratamento de Erros:** Todas as chamadas HTTP devem ser envolvidas em blocos `try...except`. Em caso de falha da API, o agente deve capturar o erro e exibir um alerta não obstrutivo na interface (`st.error` ou `st.toast`), sem rebentar a aplicação.

## 3. Integração com APIs Externas e IA (Gemini)
*   **Jogos (API Externa):** As chamadas para buscar jogos devem ser isoladas em serviços próprios (ex: `external_game_api.py`), tratando a paginação e o limite de pedidos (rate limiting).
*   **Gemini:** Utilizar o SDK oficial do Google GenAI. Quando o Gemini for usado para recomendar jogos ou analisar reviews, os prompts devem ser desenhados dinamicamente no código, injetando os dados de contexto do utilizador de forma segura.

## 4. Regras de Execução do OpenSpec
*   **Escopo Fechado:** Quando atuar numa *Change* (ex: `001_login.md`), o agente deve resolver APENAS os requisitos listados nesse ficheiro. Não refatorar outras partes do sistema não solicitadas.
*   **Código Completo:** Ao gerar a solução, apresentar o código completo e funcional. Evitar omitir partes cruciais com comentários como `# resto do código aqui`.
*   **Idioma:** Comentários no código, logs e variáveis devem preferencialmente estar em inglês por padrão de mercado. Textos visíveis ao utilizador final na interface do Streamlit devem ser em Português do Brasil.