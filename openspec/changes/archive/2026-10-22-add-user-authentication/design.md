# Design

## Context

Consulte [proposal.md](./proposal.md) para a motivação e [specs/user-auth/spec.md](./specs/user-auth/spec.md) para os requisitos. O repositório contém endpoints Xano de quick start para cadastro, login, identidade e recuperação de senha, com tokens de 24 horas. A tabela Xano `user` exige senhas com pelo menos oito caracteres, uma letra e um número. Não há aplicação Python/Streamlit implementada no repositório. O fluxo de login atual seleciona o hash de senha junto aos dados do usuário e encaminha o objeto completo para metadados de log.

## Goals / Non-Goals

**Goals:**
- Reaproveitar o backend Xano e integrar os fluxos de autenticação a uma interface Streamlit.
- Preservar compatibilidade com as contas e endpoints existentes, adaptando o comportamento inadequado do quick start.
- Manter token e dados de autenticação fora de respostas, logs e armazenamento persistente não protegido.

**Non-Goals:**
- Implementar login social, MFA, verificação obrigatória de e-mail ou gestão administrativa de contas.
- Alterar regras de biblioteca, reviews ou papéis além do necessário para identificar o usuário autenticado.

## Decisions

- **Xano permanece a fonte de verdade da identidade e das sessões.** Adaptar o grupo `xano/api/authentication/`, mantendo e-mail/senha, emissão de token Xano e o mecanismo existente de link de redefinição quando adequado. Uma autenticação local no Streamlit ou um provedor novo duplicaria a identidade e a gestão de credenciais.
- **O envio de recuperação usará SendGrid configurado por segredos do Xano.** A função de envio existente no repositório está vazia e a demonstração do `util.send_email` não direciona mensagens para o endereço da conta. Usar `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL` e `GGREVIEWS_FRONTEND_URL` como configurações do ambiente Xano; nunca guardar a chave em código ou no Streamlit.
- **A interface será construída em Streamlit e chamará os endpoints Xano.** Como não há código Python no repositório, a implementação deverá introduzir a estrutura mínima da aplicação, um cliente HTTP para o backend e as telas dos fluxos da especificação. URLs e segredos serão obtidos de configuração do ambiente, nunca de valores secretos versionados.
- **O token ficará no estado da sessão Streamlit e será enviado somente em chamadas protegidas.** Validar a identidade via endpoint autenticado antes de liberar conteúdo privado. O token atual expira em 24 horas; preservar esse prazo no primeiro incremento evita uma mudança de sessão sem requisito. Persistência do token em disco ou em armazenamento de navegador não será introduzida.
- **A redefinição concluirá a validação do link e a troca de senha em uma chamada anônima ao Xano.** Um endpoint dedicado verifica o token de uso único, o e-mail e a expiração, valida a nova senha e atualiza a senha antes de marcar o token como usado. Isso evita emitir e manter um token de sessão apenas para redefinir a senha.
- **O logout encerrará apenas a sessão atual no Streamlit.** Remover o token do estado local ao sair e não adicionar armazenamento/validação de revogação no Xano neste incremento. A decisão mantém o escopo pequeno, mas não invalida cópias do token que tenham sido expostas; essas continuam válidas até a expiração Xano de 24 horas.
- **O cadastro e login retornarão somente dados explicitamente permitidos.** A consulta de login ainda precisa ler o hash internamente para verificar a senha, mas o hash nunca será colocado em respostas nem metadados de eventos. As falhas de login usarão resposta indistinguível para usuário inexistente e senha incorreta. A solicitação de recuperação será pública, não revelará a existência da conta e usará token de uso único e expirável.
- **Manter os fluxos da interface separados por estado de autenticação.** Pessoas não autenticadas recebem cadastro, login e recuperação; pessoas autenticadas recebem a ação de logout e os recursos protegidos. Erros de API serão apresentados de forma útil sem incluir token, senha ou dados internos.

## Risks / Trade-offs

- **A interface pode depender de configuração Xano ainda ausente no repositório** → documentar as variáveis necessárias e falhar com mensagem explícita quando a configuração não estiver definida.
- **O envio de e-mail depende de uma conta SendGrid e de um domínio remetente verificado** → exigir as variáveis do ambiente Xano e documentar a configuração antes de habilitar recuperação em produção.
- **O token armazenado em memória da sessão perde-se ao encerrar ou reiniciar a sessão Streamlit** → exigir novo login nesses casos, evitando persistência local de credenciais.
- **Tokens expostos permanecem utilizáveis até a expiração após logout** → manter tokens somente no estado de sessão Streamlit, não registrar credenciais e preservar o prazo atual de 24 horas; considerar revogação server-side em uma mudança futura se o modelo de ameaça exigir.
- **Endpoints gerados pelo quick start podem ter contratos ou logs incompatíveis com a interface proposta** → atualizar contratos em conjunto, manter respostas de sucesso mínimas e testar cenários de credenciais inválidas, recuperação e sessão expirada.

## Migration Plan

1. Adaptar os endpoints Xano e validar os contratos de cadastro, login, sessão, logout e recuperação sem remover as contas existentes.
2. Introduzir a aplicação Streamlit e integrar seus fluxos aos endpoints usando configuração externa.
3. Validar sessão válida/expirada, logout e respostas de erro antes de habilitar recursos privados.
4. Se a implantação apresentar falha, desabilitar temporariamente as novas telas e reverter a interface; manter os dados de usuários existentes. Reverter alterações de API sem invalidar senhas ou links de recuperação emitidos.
