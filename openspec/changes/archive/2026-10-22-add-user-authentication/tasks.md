# Tasks

## 1. APIs de autenticação Xano

- [x] 1.1 Adaptar cadastro e login para normalizar/validar e-mail, exigir senha de pelo menos 8 caracteres com letra e número e manter erros de login indistinguíveis; verificar cenários de cadastro válido, duplicado, dados inválidos e credenciais inválidas, confirmando que hash de senha não aparece em respostas nem metadados de eventos.
- [x] 1.2 Ajustar os endpoints de identidade e recuperação, incluindo conclusão atômica da redefinição por link, resposta genérica para solicitações e retorno somente de campos permitidos; verificar link de uso único/expirável e rejeição de link inválido, expirado ou reutilizado.
- [x] 1.3 Documentar os contratos e configurações dos endpoints Xano de autenticação nos documentos do projeto; verificar que cada fluxo e variável/configuração necessária está descrito sem incluir segredos.

## 2. Base da aplicação Streamlit e cliente Xano

- [x] 2.1 Criar a estrutura mínima da aplicação Streamlit e declarar suas dependências; verificar instalação e inicialização, incluindo erro explícito quando a URL do backend não estiver configurada.
- [x] 2.2 Implementar cliente HTTP para cadastro, login, identidade, solicitação e conclusão de recuperação Xano, usando configuração externa e sem registrar credenciais; verificar respostas de sucesso, erros de API, timeout e ausência de token/senha nos logs com testes unitários.
- [x] 2.3 Documentar como configurar e executar a aplicação Streamlit e conectar ao Xano; verificar as instruções em um ambiente limpo sem exigir segredos versionados.

## 3. Fluxos de interface e sessão

- [x] 3.1 Implementar formulários Streamlit de cadastro, login e recuperação com validação e mensagens seguras; verificar cada fluxo com o cliente Xano simulado, incluindo sucesso e erros recuperáveis.
- [x] 3.2 Implementar estado de sessão, consulta de identidade e proteção dos recursos autenticados; verificar persistência durante reruns, bloqueio de sessão expirada e remoção do token ao fazer logout.

## 4. Integração

- [ ] 4.1 Executar testes integrados dos fluxos completos de cadastro, login, sessão, logout e recuperação usando a interface e um backend Xano de teste; verificar redirecionamentos entre estados e que tokens Xano continuam sujeitos à expiração de 24 horas após logout local.
