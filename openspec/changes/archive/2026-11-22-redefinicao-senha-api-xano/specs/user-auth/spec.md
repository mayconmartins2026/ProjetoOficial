# Spec Delta

## MODIFIED Requirements

### Requirement: Recuperação e redefinição de senha
O sistema MUST oferecer APIs públicas no grupo Authentication para solicitar a redefinição por e-mail e concluir a troca usando um link de uso único, válido por uma hora. A senha nova MUST ter pelo menos 8 caracteres, uma letra e um número. A resposta à solicitação MUST ser equivalente para endereços cadastrados e não cadastrados.

#### Scenario: Solicitação de recuperação
- **WHEN** uma pessoa envia `POST /reset/request-reset-link` com um endereço de e-mail
- **THEN** a API retorna a mesma confirmação genérica e o mesmo formato de resposta para e-mails cadastrados e não cadastrados
- **AND** envia o link somente ao endereço associado a uma conta

#### Scenario: Falha no envio do link
- **WHEN** o provedor de e-mail falha ao enviar um link para uma conta existente
- **THEN** a API retorna a mesma confirmação genérica e o mesmo formato usados para uma conta inexistente
- **AND** registra apenas um diagnóstico sem incluir endereço, chave, link, token ou outros dados sensíveis

#### Scenario: Link válido e senha válida
- **WHEN** uma pessoa envia `POST /reset/complete` com `magic_token`, `email`, `password` e `confirm_password` válidos para um link ainda não expirado e não utilizado
- **THEN** a API atualiza a senha, invalida o link e não cria uma sessão autenticada
- **AND** a pessoa pode entrar usando a nova senha

#### Scenario: Link inválido, expirado ou reutilizado
- **WHEN** uma pessoa tenta concluir a redefinição com um link inválido, expirado ou já utilizado
- **THEN** a API rejeita a operação com uma mensagem genérica para link inválido ou expirado e mantém a senha atual

#### Scenario: Nova senha inválida
- **WHEN** uma pessoa envia uma senha que não atende à política exigida ou `password` e `confirm_password` não correspondem
- **THEN** a API rejeita a operação e mantém a senha atual
