# Tasks

## 1. Preferências privadas no Xano

- [ ] 1.1 Publicar a tabela e os endpoints autenticados de preferências,
  validar as entradas e executar testes de isolamento entre usuários. O catálogo
  de jogos não precisa ser publicado no Xano: é obtido diretamente do IGDB.

## 2. Cliente e lógica de compatibilidade

- [x] 2.1 Implementar no cliente Xano leitura e gravação do perfil, com
  validação explícita das respostas; cobrir contratos, erros HTTP, respostas
  inválidas e autorização com testes unitários.
- [x] 2.2 Implementar função pura de compatibilidade com pesos, normalização,
  regra de cobertura mínima e filtro de plataforma; testar correspondências,
  divergências, preferências omitidas, metadados ausentes, limite de cobertura,
  ordenação e resultados determinísticos.
- [x] 2.3 Integrar o catálogo de compatibilidade ao IGDB via OAuth Twitch,
  derivando opções de gêneros, temas, modos e plataformas dos jogos retornados.

## 3. Interface Inteligência de Compatibilidade

- [x] 3.1 Adicionar tela Streamlit autenticada e questionário com vocabulários do
  catálogo; testar carregamento do perfil, estado sem perfil, edição, salvamento
  confirmado e erro de persistência sem sucesso falso.
- [x] 3.2 Exibir recomendações em cards com capa, nome, gêneros, descrição,
  percentual, cobertura e justificativas; testar campos exigidos, ordem estável,
  filtro de plataformas e estado de dados insuficientes.
- [x] 3.3 Integrar a tela ao menu existente sem alterar os fluxos atuais; validar
  navegação e executar os testes de regressão das telas de autenticação,
  avaliações, promoções, configurações e Raio-X.

## 4. Validação integrada

- [x] 4.1 Executar testes automatizados de cliente, domínio e Streamlit e
  `python -m compileall`; corrigir regressões sem alterar fluxos fora do escopo.
- [x] 4.2 Validar os artefatos com
  `openspec validate inteligencia-compatibilidade --strict` e revisar se
  contratos Xano, regras de pontuação e testes correspondem à especificação.

## Workflow follow-up

- A tela obtém características do IGDB e depende apenas dos endpoints Xano de
  preferências para persistência.
- Publicar os endpoints Xano de preferências antes de habilitar a persistência
  da tela em produção; validar isolamento por usuário no workspace.
- Arquivar a Change depois que implementação, validação e aprovação estiverem
  concluídas.
