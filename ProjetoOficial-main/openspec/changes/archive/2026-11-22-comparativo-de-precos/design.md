# Design

## Contexto

O catálogo e a tela de ofertas devem usar CheapShark, eliminando a dependência da
RAWG e da vitrine regional da Steam. Como a CheapShark retorna preços em dólar,
os valores apresentados ao usuário precisam ser convertidos para reais.

## Decisões

- Isolar as chamadas à API pública `https://www.cheapshark.com/api/1.0/` em um
  cliente próprio.
- Buscar jogos pelo título em `/games` para o catálogo de avaliações e consultar
  `/deals` para encontrar ofertas em diferentes lojas.
- Converter os preços USD da CheapShark com a cotação mais recente USD/BRL do
  Frankfurter, mantendo o valor e a data da cotação em cache por uma hora.
- Arredondar preços convertidos para centavos e identificá-los como estimativas;
  o preço final pode variar na loja.
- Armazenar buscas de jogos e ofertas em cache para reduzir chamadas externas e
  usar links de redirecionamento `dealID` da CheapShark para ofertas.
- Exibir ofertas em destaque na tela inicial como grupos navegáveis de dois
  cartões, usando controles nativos do Streamlit e mostrando plataforma PC com
  ícone, loja, desconto e preços convertidos.
- Exibir no catálogo inicial até seis jogos distintos das ofertas já carregadas,
  com capas maiores em cartões e acesso direto ao fluxo de avaliação, sem exigir
  uma busca prévia.
- Calcular o percentual de desconto a partir do preço promocional e do preço
  normal retornados pela CheapShark.
- Resolver o nome da loja com a rota `/stores` e armazenar o mapeamento em cache
  por 24 horas.
- Remover as métricas estáticas de dashboard que não representam dados reais.
- Manter o formulário de avaliação disponível sem exigir dados descritivos de
  jogos que não são fornecidos pela CheapShark.
- Exibir um acesso compacto ao Raio-X técnico nos cards e na avaliação do jogo.
  Enquanto não há fonte de dados integrada, todos os critérios devem permanecer
  explicitamente como “Sem dados ainda”, sem inventar classificações ou fontes.
- Disponibilizar uma tela Raio-X com critérios, estados possíveis, níveis de
  confiança, campos de evidência, versão e verificação, metodologia e aviso de
  desatualização. Nesta etapa, os dados não são persistidos.
- Orientar reavaliação após patches relevantes e em até 90 dias quando houver
  avaliações cadastradas.
- Mostrar a média comunitária e a quantidade de avaliações nos cards de jogos,
  obtidas em lote pelo endpoint autenticado `POST /avaliacoes/medias` do Xano.
  Uma resposta sem linha para um jogo significa que ainda não há avaliações;
  falha no endpoint deve ser identificada como média indisponível.

### Contrato proposto para médias no Xano

- Requisição: `{"nomes_jogo": ["Hades", "God of War"]}` com token Bearer.
- Resposta: `{"medias": [{"nome_jogo": "Hades", "media": 4.5, "total": 12}]}`
- `media` é a média das notas válidas de 1 a 5 e `total` é a quantidade
  correspondente. Retornar somente jogos com pelo menos uma avaliação; a
  aplicação apresenta os demais como “Ainda sem avaliações da comunidade”.
- A rota não está implementada neste repositório e precisa ser publicada no
  Xano antes das médias ficarem disponíveis na aplicação implantada.

## Limites

- Os valores em reais são conversões indicativas, não preços regionais garantidos
  pelos varejistas.
- A cotação usada pode ser de um dia útil anterior, conforme a fonte de câmbio.
- Falhas de rede, respostas inválidas ou ausência da cotação devem ser informadas;
  o sistema não deve exibir preços em dólar como se fossem reais.
