query criarclienteassas verb=POST {
  api_group = "Pagamento"

  input {
    text authtoken? filters=trim
  }

  stack {
    // Altere a url abaixo para o seu endpoint de consultacliente no Xano
    api.request {
      url = "https://x8ki-letl-twmt.n7.xano.io/api:G7AfZhmf/buscaCliente"
      method = "GET"
      params = {authtoken: $input.authtoken}
    } as $api1
  
    conditional {
      if (`$var.api1.response.status` == 200) {
        db.get user {
          field_name = "id"
          field_value = `$var.api1.response.result.cliente.user_id`
        } as $user1
      
        db.get tokens {
          field_name = "Plataforma"
          field_value = "Asaas"
        } as $tokens1
      
        api.request {
          url = "https://api-sandbox.asaas.com/v3/customers"
          method = "POST"
          params = {
            name   : $user1.name
            cpfCnpj: $api1.response.result.cliente.cpf
          }
        
          headers = []
            |push:"User-Agent: XanoApp/1.0 (contact: otakai@gmail.com)"
            |push:"Accept: application/json"
            |push:$tokens1.token
            |push:"Content-Type: application/json"
        } as $api2
      
        var $codigoclienteassas {
          value = `$var.api2.response.result.id`
        }
      
        db.get STATUS_TTOKENIZACAO {
          field_name = "status"
          field_value = `"Criada"`
        } as $STATUS_TTOKENIZACAO1
      
        db.add TTOKENIZACAO {
          enforce_hidden_fields = false
          data = {
            created_at            : "now"
            cliente_id            : `$var.api1.response.result.cliente.id`
            det_cartao_encript    : ""
            status_ttokenizacao_id: `$var.STATUS_TTOKENIZACAO1.id`
          }
        } as $TTOKENIZACAO1
      
        db.add CARTAOTOKNZD {
          enforce_hidden_fields = false
          data = {
            created_at        : "now"
            cliente_id        : `$var.api1.response.result.cliente.id`
            token             : ""
            codigoclienteassas: `$var.codigoclienteassas`
          }
        } as $CARTAOTOKNZD1
      
        var $status {
          value = {status: true, mensagem: "Cliente cadastrado no Assas."}
        }
      }
    
      else {
        var $status {
          value = {
            status  : false
            mensagem: "Cliente não pôde ser cadastrado no Assas."
          }
        }
      }
    }
  }

  response = {status: $status}
  guid = "yfyfNZWfNtEURTIINfAtMRQ52Zc"
}