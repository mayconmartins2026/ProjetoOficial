# Requisito: Ofertas de jogos

## História

Como usuário autenticado, quero encontrar jogos em promoção e comparar o preço
atual com o preço normal para decidir se quero visitar a loja.

## Requisitos

### Requisito: Consultar e converter ofertas

O sistema DEVE apresentar ofertas ativas da CheapShark e converter os preços de
USD para BRL usando uma cotação identificável e atualizada.

#### Cenário: Ofertas disponíveis

- **Dado** que a CheapShark retorna ofertas válidas em USD e a cotação USD/BRL
  está disponível
- **Quando** o usuário abre a tela de promoções
- **Então** o sistema apresenta título, preço promocional, preço normal,
  percentual de desconto, preços aproximados em reais e link para a oferta

#### Cenário: Nenhuma oferta corresponde aos filtros

- **Dado** que o usuário informa um termo ou desconto mínimo
- **Quando** nenhum jogo corresponde aos filtros
- **Então** o sistema informa que não encontrou ofertas correspondentes

#### Cenário: Falha ao consultar ofertas

- **Dado** que a fonte de ofertas ou a cotação está indisponível ou retorna dados
  inválidos
- **Quando** o usuário abre a tela
- **Então** o sistema informa que não foi possível carregar as ofertas sem
  interromper a aplicação nem apresentar valores em dólar como reais

### Requisito: Buscar jogos para avaliação

O sistema DEVE usar o catálogo da CheapShark para buscar jogos que possam ser
avaliados e exibir capas e o menor preço convertido quando disponíveis.

#### Cenário: Jogos em destaque disponíveis sem busca

- **Dado** que existem ofertas de jogos carregadas na tela inicial
- **Quando** o usuário ainda não informa um termo de busca
- **Então** o catálogo exibe jogos distintos em cartões com capa e acesso direto
  ao formulário de avaliação

#### Cenário: Busca de jogo

- **Dado** que o usuário informa o nome de um jogo
- **Quando** a CheapShark retorna correspondências
- **Então** o sistema permite abrir o formulário de avaliação e exibe preços
  convertidos para reais quando a cotação USD/BRL está disponível

#### Cenário: Falha na cotação do catálogo

- **Dado** que a cotação USD/BRL está indisponível
- **Quando** jogos são encontrados
- **Então** o sistema informa que não pode converter os preços e mantém os jogos
  e os formulários de avaliação acessíveis

### Requisito: Navegação autenticada

A tela de promoções DEVE estar disponível no menu dos usuários autenticados e
DEVE preservar as telas de avaliações, perfil e configurações existentes.

### Requisito: Carrossel de ofertas na tela inicial

A tela inicial DEVE exibir ofertas de jogos em um carrossel navegável e apresentar
em cada cartão uma imagem ampliada, o ícone da plataforma PC, a loja, o percentual
de desconto, o preço normal e o preço promocional convertido para reais. O
carrossel DEVE exibir dois cartões por página. A tela inicial NÃO DEVE exibir as
métricas estáticas de jogos registrados, avaliações ou jogadores ativos.

#### Cenário: Navegar pelas ofertas em destaque

- **Dado** que existem mais ofertas do que cabem na página atual do carrossel
- **Quando** o usuário avança para as próximas ofertas
- **Então** o carrossel exibe o próximo grupo de cartões com plataforma, loja e
  desconto de cada jogo

#### Cenário: Remoção das métricas sem utilidade

- **Quando** o usuário abre a tela inicial
- **Então** o sistema apresenta o carrossel no lugar das métricas estáticas de
  dashboard

### Requisito: Transparência do Raio-X técnico

O sistema DEVE oferecer uma tela de Raio-X acessível pelos cards de jogos,
promoções e pela tela de avaliação. Cada critério DEVE exibir seu estado,
confiança, última verificação e evidência; dados ausentes DEVEM ser identificados
explicitamente como “Sem dados ainda”, sem inferir que o jogo seja livre de
problemas.

#### Cenário: Jogo ainda não avaliado

- **Dado** que não há avaliação técnica persistida para o jogo
- **Quando** o usuário abre o Raio-X
- **Então** os três critérios aparecem como “Sem dados ainda”, sem selo genérico
  de auditado, data ou fonte inventadas
- **E** a tela explica os critérios, estados possíveis e como a confiança deve
  ser interpretada

#### Cenário: Navegar ao Raio-X a partir de um card

- **Dado** que um jogo aparece em um card da tela inicial ou de promoções
- **Quando** o usuário clica em “Não avaliado”
- **Então** a tela de detalhes abre para o jogo selecionado e o tooltip explica
  que falta de dados não indica ausência de DRM, launchers ou stuttering

#### Cenário: Reavaliação técnica

- **Dado** que uma avaliação técnica venha a ser cadastrada
- **Quando** um patch relevante for lançado ou passarem 90 dias
- **Então** a avaliação deve ser revalidada, e dados vencidos devem ser
  identificados como desatualizados

### Requisito: Médias de avaliações nos cards

Os cards de jogos devem exibir a média das avaliações publicadas no GGReviews e
o total de avaliações, obtidos em uma única consulta agregada por tela. Se o
jogo ainda não tiver avaliações, isso deve ser informado. Se a consulta falhar,
a interface deve distinguir a indisponibilidade de uma média zero ou inexistente.

#### Cenário: Jogo com avaliações

- **Dado** que o Xano retorna uma média e a quantidade de avaliações para um jogo
- **Quando** o jogo aparece em um card
- **Então** o card exibe a média na escala de 1 a 5 e o total correspondente

#### Cenário: Jogo sem avaliações

- **Dado** que o Xano não retorna uma média para o jogo
- **Quando** o jogo aparece em um card
- **Então** o card informa “Ainda sem avaliações da comunidade”

#### Cenário: Falha no endpoint agregado

- **Dado** que a consulta em lote não está disponível ou retorna dados inválidos
- **Quando** a tela carrega os cards
- **Então** os cards indicam “Média da comunidade indisponível” sem interromper
  a exibição dos jogos
