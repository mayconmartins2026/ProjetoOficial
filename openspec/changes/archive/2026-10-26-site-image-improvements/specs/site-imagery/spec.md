# Spec: Site image improvements

## Summary

A interface do GGReviews deve exibir imagens mais refinadas e consistentes para perfis de usuário e capas de jogos, evitando telas quebradas quando imagens não existem ou estão indisponíveis.

## Functional Requirements

1. O sistema deve renderizar perfis de usuário com imagem ou placeholder visual quando o campo de imagem estiver ausente.
2. O sistema deve renderizar capas de jogo com fallback visual quando o RAWG não fornecer imagem válida.
3. O app deve manter URLs externas de perfil e RAWG quando elas estiverem disponíveis.
4. A interface deve aplicar estilo visual harmonizado para imagens em cards, sidebar e revisão.
5. O comportamento principal da autenticação, da sessão e do catálogo deve continuar funcionando sem regressões.

## Non-Functional Requirements

1. A solução deve usar Streamlit como frontend e não introduzir outra tecnologia de UI.
2. Os placeholders devem ser gerados com SVG embutido em data URI para evitar dependência de arquivos externos.
3. O app deve continuar compatível com os testes automatizados do repositório.
