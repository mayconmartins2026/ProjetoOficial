# Design

## Context

Consulte [proposal.md](./proposal.md) para motivação e
[specs/game-compatibility/spec.md](./specs/game-compatibility/spec.md) para
comportamentos exigidos. O Streamlit já autentica usuários pelo Xano, oferece
um cliente HTTP autenticado e mantém CheapShark isolada em
`ggreviews/cheapshark_client.py`.

O Xano autentica os usuários e armazena as preferências privadas. O catálogo e
as características dos jogos vêm do IGDB, serviço acessado com as credenciais de
aplicação da Twitch. A CheapShark fornece apenas ofertas e preços de PC. O
projeto determina Streamlit como frontend e não usa IA generativa para pontuar
recomendações.

## Goals / Non-Goals

**Goals:**

- Fazer recomendações reproduzíveis a partir de atributos do IGDB e de
  preferências explicitamente salvas pelo próprio usuário.
- Manter os dados pessoais sob autenticação Xano e obter dados dos jogos
  diretamente do IGDB.
- Expor pontuação, cobertura e justificativas com critérios compreensíveis.

**Non-Goals:**

- Usar Gemini ou outro modelo generativo para inventar metadados, pontuações ou
  justificativas.
- Inferir disponibilidade para consoles a partir de uma oferta de PC.
- Inferir características que a API não fornece, como dificuldade ou
  intensidade narrativa.
- Alterar o fluxo atual de avaliações, autenticação ou promoções.

## Decisions

### Catálogo de jogos no IGDB

Consultar o endpoint IGDB `/v4/games` usando o fluxo de credenciais de aplicação
da Twitch. O catálogo carrega até 500 títulos populares e usa somente atributos
retornados pela API: gêneros, temas, modos de jogo, plataformas, descrição e
capa. O resultado é armazenado em cache por seis horas; a busca de catálogo não
depende do endpoint Xano `/compatibilidade/catalogo`.

O IGDB é a fonte de verdade para os atributos usados pelo cálculo. Não inferir
dificuldade, narrativa ou exploração a partir de títulos, descrições ou gênero.
Se algum campo estiver ausente, tratá-lo como desconhecido.

### Preferências privadas e APIs autenticadas

Persistir um registro de preferências por usuário, com `user_id` obtido sempre
do contexto autenticado do Xano, arrays de gêneros/temas/modos/plataformas e
`updated_at`. Os campos legados de narrativa, exploração e dificuldade podem
continuar no contrato para preservar perfis existentes, mas não participam do
cálculo. Nunca aceitar um `user_id` fornecido pelo cliente para selecionar o
dono do registro.

Endpoints exportados para o grupo Xano `Authentication`:

- `GET /compatibilidade/preferencias`: retorna `{"preferencias": ...}` ou
  `{"preferencias": null}`.
- `PUT /compatibilidade/preferencias`: valida listas e escalas e faz upsert
  usando `$auth.id`; o cliente não envia o proprietário do perfil.

O catálogo e o vocabulário do questionário são construídos a partir dos jogos
retornados pelo IGDB. Consulte [compatibility-catalog.md](../../../docs/compatibility-catalog.md)
para credenciais e detalhes dos atributos utilizados.

A interface não considera uma preferência salva até receber sucesso do Xano.
Falhas de rede, autorização, validação ou resposta devem ser apresentadas sem
substituir silenciosamente o perfil existente.

**Alternativas consideradas:** armazenar somente em `st.session_state`
(descartada porque perderia o perfil ao encerrar a sessão); perfil no navegador
(descartado para evitar duplicar a fonte de verdade e expor dados).

### Compatibilidade calculada no domínio Python

Implementar uma função de domínio pura, sem acesso a rede ou Streamlit, para
facilitar testes com entradas e resultados determinísticos. Não usar notas de
reviews como atributo de compatibilidade: a nota comunitária mede opinião, não
gênero, tema ou disponibilidade de plataforma.

Pesos dos critérios pontuáveis:

| Critério | Peso |
|---|---:|
| Gêneros | 50 |
| Temas | 30 |
| Modos de jogo | 20 |

Para gêneros, temas e modos, a nota de cada critério é a proporção de valores
preferidos que também existem no jogo. Cada nota é multiplicada pelo peso
correspondente; a pontuação final é a média ponderada arredondada ao inteiro
mais próximo, normalizada pelos pesos que têm preferência informada e
metadados conhecidos.

Critérios sem preferência não entram na pontuação. Critérios sem metadados não
contam como zero nem como incompatibilidade. Exibir cobertura como a soma dos
pesos conhecidos dividida pela soma dos pesos respondidos; somente apresentar
pontuação quando a cobertura for de pelo menos 70%. Abaixo disso, informar
“Dados insuficientes para calcular compatibilidade” e não classificar o jogo.

Plataforma funciona como filtro de elegibilidade, não como peso: quando o perfil
seleciona plataformas, o jogo precisa ter suporte cadastrado a pelo menos uma
delas. Se o suporte for desconhecido, não recomendar esse candidato para aquele
perfil. Sem plataforma escolhida, não aplicar o filtro.

Gerar justificativas determinísticas a partir dos mesmos componentes: indicar
gêneros/temas coincidentes, modos correspondentes e a cobertura considerada.
Ordenar por pontuação decrescente e desempatar por título normalizado e ID
estável. Não usar texto generativo.

**Alternativas consideradas:** pesos iguais (menos representativos da
preferência por gênero); plataforma pontuada (poderia recomendar algo que o
usuário não consegue jogar); tratar ausência de metadados como zero
(penalizaria injustamente jogos não catalogados).

### Integração visual e estado da tela

Adicionar a tela autenticada ao menu existente sem alterar a navegação atual.
Separar o questionário editável dos resultados, preservar preferências
carregadas quando uma chamada de recomendação falhar e mostrar estados de
carregamento, erro e lista vazia. Reutilizar os containers, cartões e helpers de
capa existentes; não introduzir outra tecnologia de frontend.

## Risks / Trade-offs

- **O catálogo IGDB pode estar incompleto ou indisponível** → manter cache,
  informar falhas e excluir atributos ausentes sem inventá-los.
- **Os nomes dos atributos podem mudar no IGDB** → reconstruir o vocabulário do
  catálogo atual e validar as preferências antes de salvá-las.
- **Uma mudança no contrato Xano pode bloquear preferências** → publicar e
  validar endpoints e autorização antes de liberar a tela Streamlit.
- **A pontuação pode parecer precisão científica** → exibir pesos, cobertura e
  fatores de justificativa, descrevendo o resultado como aderência ao perfil,
  não previsão de satisfação.
- **Catálogo completo pode crescer além do limite adequado para uma resposta** →
  manter o limite documentado do IGDB e paginar na integração se necessário;
  preservar ordenação estável na camada de recomendação.

## Migration Plan

1. Implementar/testar a consulta IGDB e a conversão de suas características para
   o catálogo de compatibilidade.
2. Implementar/testar o modelo e a função pura de compatibilidade com fixtures
   que cubram campos ausentes, filtros de plataforma, pontuação e empates.
3. Integrar persistência do questionário e catálogo à aplicação; validar usuário
   sem preferências, salvamento, recarga, erros e sessão expirada.
4. Habilitar a nova tela com credenciais Twitch e endpoints de preferências Xano,
   mantendo o menu e as demais telas inalterados.
5. Se houver regressão, retirar o acesso pelo menu sem apagar os perfis de
   preferências Xano; reativar após correção.
