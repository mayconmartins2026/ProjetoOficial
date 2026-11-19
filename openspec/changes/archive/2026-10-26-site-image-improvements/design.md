# Design

## Context

Consulte [proposal.md](./proposal.md). A interface principal do app em Streamlit já renderiza imagens de perfis e capas, mas a experiência visual era mínima e sensível a URLs ausentes ou quebradas. Mantendo o stack atual e os fluxos de autenticação e catálogo, a melhoria de imagens deve reforçar a identidade visual do produto sem criar regressões no comportamento funcional.

## Goals / Non-Goals

**Goals:**
- Melhorar a estética das imagens do app sem alterar a arquitetura principal.
- Usar placeholders elegantes e seguros quando a imagem não estiver disponível.
- Preservar o carregamento de imagens de RAWG e de perfil do usuário.

**Non-Goals:**
- Introduzir React/Vue/Angular ou outra tecnologia de frontend.
- Alterar regras de autenticação ou negócio do projeto.

## Decisions

- **Manter Streamlit como único frontend.** Os ajustes visuais serão feitos em CSS/HTML embutido no Streamlit, preservando a estrutura atual.
- **Gerar placeholders SVG em data URI.** Isso evita depender de imagens externas indisponíveis e mantém a aparência consistente.
- **Fallback centralizado para imagens vazias/ausentes.** A mesma lógica será reutilizada em perfis e capas.
- **Preservar APIs existentes.** A busca em RAWG e a URL pública de arquivos do usuário continuam sendo os mecanismos de origem de imagem.

## Risks / Trade-offs

- **Imagens externas podem falhar ou demorar a responder** → o app usa fallback visual sem quebrar a página.
- **Componentes com imagens muito grandes podem perceber perda de qualidade** → o CSS mantém `object-fit: cover` e proporções consistentes.
- **Autenticação e sessões já validadas devem continuar funcionando** → os testes garantem que a melhoria visual não altere o fluxo principal.
