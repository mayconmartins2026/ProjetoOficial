# user-auth Specification

## Purpose
Permite que pessoas criem e acessem uma conta GGReviews com segurança para usar recursos associados ao usuário, mantendo a autenticação entre interações da interface e oferecendo recuperação de acesso.

## Requirements

### Requirement: Cadastro de conta
O sistema MUST permitir que uma pessoa crie uma conta usando nome, e-mail válido e senha com pelo menos 8 caracteres, uma letra e um número. O e-mail MUST ser normalizado e único; uma tentativa com e-mail já cadastrado MUST ser rejeitada sem criar outra conta.

#### Scenario: Cadastro válido
- **WHEN** uma pessoa envia nome, e-mail válido ainda não cadastrado e senha válida
- **THEN** o sistema cria a conta e inicia uma sessão autenticada

#### Scenario: E-mail já cadastrado
- **WHEN** uma pessoa tenta cadastrar um e-mail que já pertence a uma conta
- **THEN** o sistema rejeita o cadastro, informa que não foi possível criar a conta e não cria um usuário duplicado

#### Scenario: Dados de cadastro inválidos
- **WHEN** uma pessoa envia e-mail inválido ou senha que não atende ao comprimento e à composição exigidos
- **THEN** o sistema rejeita o cadastro e informa os campos que precisam ser corrigidos

### Requirement: Login com credenciais
O sistema MUST autenticar contas por e-mail e senha e fornecer uma sessão para credenciais válidas. Falhas de autenticação MUST apresentar uma mensagem genérica que não revele se o e-mail existe.

#### Scenario: Login válido
- **WHEN** uma pessoa envia e-mail e senha correspondentes a uma conta
- **THEN** o sistema inicia a sessão e apresenta a interface autenticada

#### Scenario: Credenciais inválidas
- **WHEN** uma pessoa envia e-mail ou senha que não correspondem a uma conta
- **THEN** o sistema não inicia uma sessão e apresenta a mesma mensagem genérica de falha para ambos os casos

### Requirement: Sessão autenticada
O sistema MUST manter a autenticação durante as interações da interface até o logout ou a expiração do token Xano, validar a sessão antes de exibir recursos privados e não expor senha ou token em conteúdo visível, mensagens ou logs da interface.

#### Scenario: Reutilização de sessão válida
- **WHEN** uma pessoa autenticada interage novamente com a aplicação enquanto seu token Xano ainda é válido
- **THEN** o sistema mantém a pessoa autenticada sem solicitar novo login

#### Scenario: Sessão expirada
- **WHEN** uma requisição protegida é feita com token expirado ou inválido
- **THEN** o sistema descarta a sessão local, impede o acesso ao recurso e solicita novo login

### Requirement: Logout
O sistema MUST encerrar a sessão atual no Streamlit e remover o token do estado local quando a pessoa fizer logout. A interface MUST NOT afirmar que o logout revoga o token no Xano.

#### Scenario: Logout concluído
- **WHEN** uma pessoa autenticada seleciona sair
- **THEN** o sistema remove as credenciais da sessão Streamlit e apresenta a interface não autenticada

### Requirement: Recuperação e redefinição de senha
O sistema MUST permitir solicitar a redefinição por e-mail e usar um link de uso único com expiração para definir uma nova senha com pelo menos 8 caracteres, uma letra e um número. A resposta à solicitação MUST ser equivalente para endereços cadastrados e não cadastrados.

#### Scenario: Solicitação de recuperação
- **WHEN** uma pessoa solicita recuperação para um endereço de e-mail
- **THEN** o sistema apresenta uma confirmação genérica sem revelar se há uma conta associada

#### Scenario: Link válido e senha válida
- **WHEN** uma pessoa envia uma nova senha válida usando um link de redefinição não expirado e ainda não utilizado
- **THEN** o sistema atualiza a senha, invalida o link e exige autenticação com a nova senha

#### Scenario: Link inválido, expirado ou reutilizado
- **WHEN** uma pessoa tenta redefinir a senha usando um link inválido, expirado ou já utilizado
- **THEN** o sistema rejeita a operação e orienta a solicitar um novo link

#### Scenario: Nova senha inválida
- **WHEN** uma pessoa envia senha que não atende ao comprimento e à composição exigidos ou campos de senha divergentes
- **THEN** o sistema rejeita a redefinição e mantém a senha atual

### Requirement: Interface de autenticação
O sistema MUST oferecer na interface Streamlit formulários de cadastro, login e recuperação de senha, além de uma ação de logout para sessões autenticadas, comunicando sucesso e falhas sem expor detalhes sensíveis.

#### Scenario: Navegação entre fluxos
- **WHEN** uma pessoa não autenticada usa a interface
- **THEN** ela pode escolher cadastro, login ou recuperação de senha e recebe o formulário correspondente

#### Scenario: Recurso privado sem autenticação
- **WHEN** uma pessoa não autenticada tenta acessar um recurso reservado a contas
- **THEN** o sistema bloqueia o acesso e oferece o fluxo de login
