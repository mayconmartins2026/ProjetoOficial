# Proposal

## Why

O GGReviews precisava melhorar a apresentação visual das capas de jogos, perfis de usuário e cartões de review para tornar a experiência mais moderna e consistente. O projeto já tinha suporte para imagens externas e upload de perfil, mas o comportamento visual era básico e não tratava corretamente casos em que o conteúdo faltava ou era inválido.

## What Changes

- Melhorar a renderização de imagens de perfil e capas de jogos com bordas, sombras e ajuste responsivo. 
- Adicionar placeholders SVG gerados localmente quando uma imagem não está disponível, evitando que o app apresente blocos vazios ou URLs quebradas.
- Preservar a funcionalidade existente de carregamento de imagens em RAWG, perfil de usuário e uploads do usuário.
- Manter a arquitetura atual do Streamlit, sem introduzir outra tecnologia de frontend. 

## Capabilities

### New Capabilities
- `site-imagery`: apresentação visual mais refinada e robusta para capas, perfis e outros ativos visuais do app.

### Modified Capabilities
- `authenticated-user-profile`: imagens de perfil com fallback seguro e visual consistente.
- `game-catalog`: capas de jogos com fallback e estilização visual aprimorada.

## Impact

- Interface Streamlit principal em `app.py`.
- Fluxos de perfil de usuário, game cards e reviews existentes.
- URLs públicas e placeholders de imagem sem expor dados sensíveis.
- Nenhuma mudança arquitetural no frontend; o app continua usando Streamlit.

## Notes

- A melhoria prioriza consistência visual, robustez para imagens ausentes e compatibilidade com os testes existentes do projeto.
- A solução preserva a experiência de autenticação e sessões já validadas, sem quebrar o comportamento principal da aplicação.
