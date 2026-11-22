# Proposal

## Why

O GGReviews precisa identificar cada pessoa para associar sua biblioteca e suas avaliações a uma conta, mas cadastro e login ainda constam como decisões pendentes na visão do projeto. Há endpoints de autenticação Xano no repositório, porém eles pertencem a um quick start e ainda não formam um fluxo de produto integrado à interface Streamlit.

## What Changes

- Consolidar autenticação por e-mail e senha no Xano, incluindo cadastro, login, consulta da identidade autenticada, logout e ciclo de sessão.
- Oferecer recuperação e redefinição de senha por link único e temporário.
- Criar a interface Streamlit para cadastro, login, logout e recuperação de senha, integrando-a às APIs Xano e preservando o estado de autenticação entre interações da aplicação.
- Substituir ou adaptar comportamentos de demonstração existentes para atender aos fluxos de autenticação do GGReviews.

## Capabilities

### New Capabilities
- `user-auth`: cadastro, autenticação, sessão e recuperação de acesso para usuários do GGReviews, incluindo a experiência correspondente na interface.

### Modified Capabilities
- Nenhuma. O projeto ainda não possui especificações OpenSpec existentes.

## Impact

- APIs e grupo Xano existentes em `xano/api/authentication/`, incluindo cadastro, login, identidade autenticada e recuperação de senha.
- Modelo de usuário Xano e configuração de autenticação por token.
- Nova aplicação/interface Streamlit e integração com os endpoints Xano; não há arquivos Python/Streamlit atualmente no repositório.
- Configuração de URL e credenciais/segredos necessários para conectar a interface ao backend, sem expor segredos no código.
