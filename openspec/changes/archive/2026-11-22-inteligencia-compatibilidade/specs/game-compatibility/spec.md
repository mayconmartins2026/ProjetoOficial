# Spec Delta

## Purpose

Permite que jogadores recebam recomendações de jogos compatíveis com suas
preferências, com pontuação determinística, explicações verificáveis e dados
mantidos no Xano por conta autenticada.

## ADDED Requirements

### Requirement: Coleta de preferências de compatibilidade

O sistema MUST permitir que usuários autenticados informem gêneros, temas,
modos de jogo e plataformas disponíveis no IGDB. Preferências podem ser
alteradas sem duplicar o perfil.

#### Scenario: Preencher preferências

- **WHEN** o usuário responde ao questionário de compatibilidade
- **THEN** o sistema valida os valores contra as opções disponíveis e permite
  solicitar recomendações

#### Scenario: Preferências parcialmente informadas

- **WHEN** o usuário deixa critérios sem preferência
- **THEN** o sistema não trata os critérios omitidos como incompatibilidade e
  identifica a cobertura de preferências usada no resultado

### Requirement: Persistência privada das preferências

O sistema MUST salvar e recuperar as preferências associadas à conta autenticada,
sem permitir leitura ou alteração das preferências de outro usuário.

#### Scenario: Carregar preferências salvas

- **WHEN** um usuário autenticado abre a área de compatibilidade
- **THEN** o sistema carrega as preferências anteriormente salvas para essa
  conta, ou apresenta o questionário sem valores salvos

#### Scenario: Salvar preferências

- **WHEN** o usuário autenticado salva alterações no perfil
- **THEN** o sistema atualiza um único perfil pertencente à conta autenticada e
  confirma o salvamento

#### Scenario: Falha ao persistir preferências

- **WHEN** o Xano rejeita ou não consegue salvar o perfil
- **THEN** o sistema informa a falha e não apresenta as alterações como salvas

### Requirement: Metadados verificáveis do catálogo de compatibilidade

O sistema MUST recomendar jogos a partir de características do IGDB obtidas
pela API da Twitch, incluindo gêneros, temas, modos, plataformas, descrição e
capa. Narrativa, exploração e dificuldade MUST NOT ser inferidas quando não
forem retornadas pela API. A ausência de metadados MUST ser tratada como
desconhecida, nunca como atributo negativo ou confirmado.

#### Scenario: Jogo com metadados do IGDB

- **WHEN** o IGDB retorna características para um jogo elegível
- **THEN** o sistema pode usá-los no cálculo e apresenta nome, gênero, descrição
  e plataformas informadas, sem depender do catálogo Xano

#### Scenario: Jogo sem metadados suficientes

- **WHEN** um candidato não possui dados suficientes para avaliar os critérios
- **THEN** o sistema não inventa atributos nem exibe uma pontuação enganosa para
  esse candidato

### Requirement: Pontuação determinística e explicável

O sistema MUST calcular compatibilidade de 0 a 100 usando somente preferências
informadas e atributos conhecidos do jogo, com pesos e regras documentados. A
mesma entrada MUST produzir a mesma pontuação e justificativa.

#### Scenario: Compatibilidade calculada

- **WHEN** preferências e metadados suficientes estão disponíveis
- **THEN** o sistema apresenta a porcentagem e uma justificativa derivada dos
  critérios correspondentes e divergentes

#### Scenario: Metadados incompletos

- **WHEN** alguns atributos do jogo são desconhecidos
- **THEN** esses atributos não contam como incompatibilidade, a cobertura de dados
  é apresentada e a pontuação só aparece se a cobertura atingir o mínimo
  documentado

#### Scenario: Preferências insuficientes para pontuar

- **WHEN** o usuário não informa nenhum critério pontuável
- **THEN** o sistema solicita preferências antes de gerar recomendações e não
  atribui porcentagens aleatórias ou genéricas

### Requirement: Apresentação e ordenação das recomendações

O sistema MUST apresentar recomendações com capa, nome, gênero, descrição,
percentual de compatibilidade e justificativa. As recomendações MUST respeitar
as plataformas selecionadas e ser ordenadas de modo determinístico.

#### Scenario: Exibir recomendações compatíveis

- **WHEN** há candidatos com dados suficientes e suporte a uma plataforma
  selecionada pelo usuário
- **THEN** o sistema exibe os dados exigidos e uma justificativa específica para
  cada jogo, ordenando pela compatibilidade decrescente

#### Scenario: Nenhum jogo compatível

- **WHEN** nenhum candidato atende aos filtros de plataforma e cobertura de dados
- **THEN** o sistema informa que não encontrou recomendações confiáveis e permite
  revisar as preferências

#### Scenario: Erro ao obter catálogo ou recomendações

- **WHEN** o IGDB ou o serviço Xano de preferências está indisponível ou retorna
  dados inválidos
- **THEN** o sistema comunica que as recomendações não puderam ser carregadas,
  preserva as preferências já salvas e não mostra resultados inventados
