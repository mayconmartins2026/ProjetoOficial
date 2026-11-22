// atualiza endereço de um cliente
query atualizaEndereco verb=PATCH {
  api_group = "Custom"

  input {
    int endereco_id? {
      table = "ENDERECO"
    }
  
    text logradouro? filters=trim
    text numero? filters=trim
    text complemento? filters=trim
    text bairro? filters=trim
    text referencia? filters=trim
    text cep? filters=trim
    text cidade? filters=trim
    text uf? filters=trim
    bool padrao?
    int cliente_id? {
      table = "CLIENTE"
    }
  }

  stack {
    api.request {
      url = "https://x8ki-letl-twmt.n7.xano.io/api:G7AfZhmf/Upsercep"
      method = "POST"
      params = {cep: $input.cep, cidade: $input.cidade, uf: $input.uf}
      headers = ["Content-Type: application/json"]
    } as $api1
  
    api.request {
      url = "https://x8ki-letl-twmt.n7.xano.io/api:Ep7gGIVC/endereco/" ~$input.endereco_id
      method = "PATCH"
      params = {
        endereco_id: $input.endereco_id
        cliente_id : $input.cliente_id
        logradouro : $input.logradouro
        numero     : $input.numero
        complemento: $input.complemento
        bairro     : $input.bairro
        referencia : $input.referencia
        cep_id     : $api1.response.result.id
        padrao     : $input.padrao
      }
    
      headers = ["Content-Type: application/json"]
    } as $api2
  }

  response = {
    result2: ```
      {
          "logradouro": $var.api2.response.result.logradouro,
          "numero": $var.api2.response.result.numero,
          "complemento": $var.api2.response.result.complemento,
          "bairro": $var.api2.response.result.bairro,
          "referencia": $var.api2.response.result.referencia,
          "padrao": $var.api2.response.result.padrao,
          "cliente_id": $var.api2.response.result.cliente_id,
          "cep":
              {
                  "cep_id": $var.api1.response.result.id,
                  "cidade": $var.api1.response.result.cidade,
                  "uf": $var.api1.response.result.uf
              }
      }
      ```
  }

  guid = "i17iwzF6ar1qEY6evySVYjlcNk8"
}