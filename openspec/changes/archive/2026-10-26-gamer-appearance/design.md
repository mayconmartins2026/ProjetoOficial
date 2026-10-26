# Design

## Context

A proposta de aparência gamer busca elevar a identidade visual do GGReviews sem mudar a arquitetura de frontend. O app principal já usa Streamlit e a melhoria deve focar em tema visual, espaçamento, contraste e reforço do sentimento de jogos e comunidade.

## Goals / Non-Goals

**Goals:**
- Criar um visual mais gamer e imersivo.
- Reforçar a consistência visual entre sidebar, cards, imagens e textos.
- Preservar a legibilidade e o comportamento atual da aplicação.

**Non-Goals:**
- Trocar para outra tecnologia frontend.
- Modificar regras de autenticação ou API.

## Decisions

- **Tema escuro com acentos neon.** Usar paleta de roxo, azul e cinza escuro para reforçar o tom gamer.
- **Estilo consistente em cards e imagens.** Bordas suaves, sombras e gradientes ajudam a criar profundidade visual sem poluir a leitura.
- **Manter a experiência funcional.** Os ajustes visuais devem ficar em CSS/HTML do Streamlit e não afetar lógica, fluxo ou testes da aplicação.

## Risks / Trade-offs

- **Tema muito agressivo pode prejudicar legibilidade** → priorizar contraste e espaços suficientes.
- **Mudanças visuais excessivas podem mascarar foco** → manter elementos principais simples e consistentes.
- **Compatibilidade com padrões do Streamlit** → usar estilos alinhados com componentes padrão da ferramenta.
