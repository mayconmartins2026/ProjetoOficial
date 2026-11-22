# Proposal

## Why

O fluxo de recuperação precisa oferecer um contrato explícito e seguro entre a interface Streamlit e as APIs Xano, sem revelar se um e-mail possui conta nem permitir reutilizar links. A especificação atual descreve o comportamento esperado, mas os endpoints ainda estão identificados como quick start e precisam ser consolidados como API do GGReviews.

## What Changes

- Consolidar no grupo Authentication os endpoints públicos para solicitar um link de redefinição e concluir a troca de senha, preservando os caminhos já usados pelo cliente Streamlit.
- Definir o uso de link temporário e de uso único, validação completa da política de senha e resposta genérica para solicitações com e-mails cadastrados ou não.
- Integrar o envio do link pelo Xano com o provedor de e-mail configurado por variáveis de ambiente, sem expor segredos no repositório.
- Não alterar os formulários nem os demais fluxos de autenticação da interface Streamlit.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `user-auth`: especificar o contrato e as garantias da API Xano para solicitar e concluir a redefinição de senha.

## Impact

- Endpoints em `xano/api/authentication/reset/` e geração do token em `xano/function/getting_started_template/generate_magic_link.xs`.
- Campos de redefinição na tabela `user` do Xano e configurações do provedor de e-mail.
- Compatibilidade com as chamadas existentes em `ggreviews/auth_client.py` e com a interface Streamlit atual.
