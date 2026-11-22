# Design

## Context

Veja [proposal.md](./proposal.md) para a motivação e [specs/user-auth/spec.md](./specs/user-auth/spec.md) para o contrato. O grupo Xano `Authentication` já contém `POST /reset/request-reset-link` e `POST /reset/complete`, e `ggreviews/auth_client.py` já chama esses caminhos. A solicitação gera token com validade de 60 minutos, armazena os dados em `user.password_reset` e envia e-mail por um provedor transacional configurado no Xano. O campo de senha do usuário exige oito caracteres, uma letra e um número. Os endpoints ainda carregam tags de quick start; há também endpoints legados usados pela demonstração.

## Goals / Non-Goals

**Goals:**
- Consolidar os endpoints atuais como o fluxo oficial de redefinição da aplicação, atendendo aos contratos da especificação.
- Preservar a compatibilidade das chamadas Streamlit e evitar emissão de sessão autenticada ao concluir a redefinição.
- Manter os segredos e a entrega de e-mail sob configuração do ambiente Xano.

**Non-Goals:**
- Alterar as telas Streamlit, os fluxos de cadastro/login ou a duração das sessões autenticadas.
- Remover os endpoints legados de demonstração ou alterar o modelo geral de usuários.
- Adicionar dependências externas ou outro provedor além do Brevo.

## Decisions

- **Reutilizar os caminhos consumidos pelo cliente Streamlit.** Manter `POST /reset/request-reset-link` e `POST /reset/complete` no grupo `Authentication`, em vez de criar uma segunda API. O cliente já envia os campos desses contratos e a troca por uma nova rota não oferece benefício funcional.
- **Concluir a troca sem autenticar a pessoa.** Validar `magic_token`, `email`, validade e uso anterior, validar senha e confirmação, atualizar a senha e marcar o link como usado. Não emitir token de sessão; depois da confirmação, a pessoa entra com as novas credenciais. O fluxo legado de login por magic link permanece separado para a demonstração.
- **Reutilizar o estado de redefinição associado ao usuário.** O campo `password_reset` já armazena token, expiração e estado de uso, com o token tipado como senha. A geração de um novo link substitui o anterior. Manter a validade de uma hora e não introduzir tabela ou token persistido em texto aberto.
- **Preservar respostas públicas genéricas.** A solicitação usa `POST` com e-mail normalizado e devolve uma resposta com o mesmo formato para endereços existentes e inexistentes, inclusive quando a entrega falha. O diagnóstico no Xano não pode incluir e-mail, senha, token, link ou credenciais.
- **Validar política e confirmação antes de alterar dados.** Aplicar na conclusão as mesmas regras da tabela `user` (oito caracteres, ao menos uma letra e um número) e rejeitar senha divergente antes da atualização. Erros de link não devem modificar a senha.
- **Enviar e-mail pelo endpoint transacional do Brevo.** Fazer `POST https://api.brevo.com/v3/smtp/email` com `api-key: $env.brevo_api_key`, `Content-Type: application/json` e os campos `sender`, `to`, `subject` e `htmlContent`. Esperar HTTP 201 para envio imediato; HTTP 202 é reservado a mensagens agendadas. Usar `brevo_from_email` e `ggreviews_frontend_url` como variáveis de ambiente, sem mover segredos para o Streamlit ou arquivos versionados. A referência oficial é [Send a transactional email](https://developers.brevo.com/reference/send-transac-email).

## Risks / Trade-offs

- **Variáveis do Brevo ou URL pública ausentes podem impedir o envio** → validar a configuração no ambiente Xano antes da publicação e manter a falha disponível para diagnóstico operacional, sem revelar a existência da conta na resposta pública.
- **O cliente e o backend podem divergir nos nomes dos campos** → manter os nomes atuais (`magic_token`, `email`, `password`, `confirm_password`) e validar o contrato no cliente HTTP e nos endpoints.
- **Os endpoints legados mantêm outro caminho de redefinição para a demonstração** → não usá-los na interface GGReviews e documentar claramente que o cliente usa `/reset/complete`.

## Migration Plan

1. Ajustar o endpoint Xano para o contrato Brevo sem alterar os caminhos ou os campos já enviados pelo Streamlit.
2. Validar o Xano com cenários de e-mail existente/inexistente, falha do provedor, senha válida/inválida e link válido, expirado ou reutilizado.
3. Após a publicação manual, confirmar em ambiente de teste o envio pelo Brevo e o retorno ao formulário configurado na URL pública.
4. Em caso de falha, reverter o endpoint Xano sem modificar contas ou senhas existentes.
