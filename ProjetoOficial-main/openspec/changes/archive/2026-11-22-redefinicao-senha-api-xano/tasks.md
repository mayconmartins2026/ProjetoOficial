# Tasks

## 1. API Xano de redefinição

- [x] 1.1 Migrar o envio de `POST /reset/request-reset-link` para o contrato Brevo e preservar a resposta genérica/log seguro; validar o endpoint com o validador XanoScript.
- [x] 1.2 Ajustar `POST /reset/complete` para validar link, validade, uso, política de senha e confirmação antes de atualizar a conta, invalidar o link e não emitir sessão; validar os arquivos Xano alterados com o validador XanoScript.
- [ ] 1.3 Após a publicação manual, validar o envio imediato (HTTP 201) pelo Brevo com as variáveis de ambiente configuradas e confirmar que o link abre a interface pública, sem registrar segredos.

## 2. Contrato e documentação

- [x] 2.1 Atualizar testes em `tests/test_auth_client.py` e `tests/test_app.py` para confirmar que a integração usa apenas o endpoint Xano e não expõe credenciais Brevo; executar a suíte completa.
- [x] 2.2 Atualizar `openspec/specs/authentication.md` com o endpoint, as variáveis e o status de sucesso do Brevo; confirmar que não restaram referências ao provedor anterior.

## 3. Verificação integrada

- [ ] 3.1 Após a publicação manual no Xano, exercitar o fluxo completo em ambiente de teste — solicitação, recebimento do e-mail, troca da senha, rejeição de link reutilizado e login com a nova senha — sem armazenar tokens ou credenciais.
