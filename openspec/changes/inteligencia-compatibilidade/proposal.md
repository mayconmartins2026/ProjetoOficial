# Proposal

## Why

O GGReviews já ajuda a encontrar jogos e publicar avaliações, mas ainda não
orienta a descoberta a partir do perfil de cada jogador. Uma área de
compatibilidade com critérios explícitos e justificativas verificáveis pode
reduzir buscas genéricas e tornar as recomendações mais úteis e confiáveis.

## What Changes

- Adicionar uma área autenticada do Streamlit chamada **Inteligência de
  Compatibilidade**, preservando as telas e os fluxos existentes.
- Coletar e permitir atualizar preferências de gêneros, temas, modos de jogo e
  plataformas a partir das características disponíveis no IGDB.
- Salvar e recuperar as preferências da conta autenticada por endpoints Xano.
- Recomendar jogos a partir de gêneros, temas, modos e plataformas retornados
  pelo IGDB, com pontuação determinística e explicável.
- Apresentar capa, nome, gênero, descrição, percentual, justificativa e
  cobertura dos metadados usados no cálculo.
- Manter no Xano somente o perfil privado de preferências por conta autenticada;
  obter o catálogo e as características diretamente do IGDB.

## Capabilities

### New Capabilities

- `game-compatibility`: coleta e persistência de preferências, catálogo IGDB,
  pontuação determinística e apresentação explicável de recomendações.

### Modified Capabilities

Nenhuma. A autenticação existente será reutilizada sem alterar seus requisitos.

## Impact

- Interface Streamlit e navegação autenticada em `app.py`.
- Cliente Xano e endpoints autenticados para ler/salvar preferências.
- Integração IGDB autenticada pelas credenciais de aplicação da Twitch para
  consultar características, capas e descrições dos jogos.
- Integração CheapShark existente permanece limitada a ofertas e preços.
- Testes da pontuação, explicações, validação dos contratos, persistência e
  estados de falha.
- Nenhuma nova dependência de IA é necessária: Gemini não participará do cálculo
  determinístico nem inventará atributos de jogos.
