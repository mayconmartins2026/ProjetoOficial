# Proposta

## Por quê

Quem usa o GGReviews precisa encontrar jogos em promoção sem sair do fluxo
principal da plataforma de avaliações.

## O que muda

- Adicionar uma tela autenticada de ofertas, acessível pelo menu lateral.
- Substituir a RAWG pela CheapShark no catálogo usado para buscar jogos para
  avaliação e carregar capas.
- Exibir ofertas de várias lojas com preço promocional e preço normal convertidos
  de dólar para real, percentual de desconto e link para a loja.
- Permitir filtrar por nome do jogo e desconto mínimo.

## Escopo

A CheapShark fornece o catálogo de jogos e as ofertas em dólar. Os valores serão
convertidos para reais usando uma cotação USD/BRL pública e identificada como
aproximada.

## Impacto

- A interface Streamlit ganha uma nova página acessível a usuários autenticados.
- Uma integração isolada consulta jogos e ofertas na CheapShark e cotações no
  Frankfurter.
- Nenhuma alteração é necessária no Xano ou na autenticação.
