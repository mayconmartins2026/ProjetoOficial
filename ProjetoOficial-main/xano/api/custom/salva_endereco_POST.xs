query salvaEndereco verb=POST {
  api_group = "Custom"

  input {
    int cliente_id?
    text logradouro? filters=trim
    text numero? filters=trim
    text complemento? filters=trim
    text bairro? filters=trim
    text referencia? filters=trim
    bool padrao?
    text cep? filters=trim
    text uf? filters=trim
    text cidade? filters=trim
  }

  stack {
    api.request {
      url = "https://x8ki-letl-twmt.n7.xano.io/api:G7AfZhmf/Upsercep"
      method = "POST"
      params = {cep: $input.cep, uf: $input.uf, cidade: $input.cidade}
      headers = ["Content-Type: application/json"]
    } as $api1
  
    api.request {
      url = "https://x8ki-letl-twmt.n7.xano.io/api:Ep7gGIVC/endereco"
      method = "POST"
      params = {
        cliente_id : $input.cliente_id
        logradouro : $input.logradouro
        numero     : $input.numero
        complemento: $input.complemento
        bairro     : $input.bairro
        referencia : $input.referencia
        padrao     : $input.padrao
        cep_id     : $api1.response.result.id
      }
    
      headers = ["Content-Type: application/json"]
    } as $api2
  }

  response = {
    result2: ```
      { 
          "cliente_id"    : $var.api2.response.result.cliente_id, 
          "logradouro"    : $var.api2.response.result.logradouro, 
          "numero"        : $var.api2.response.result.numero, 
          "complemento"   : $var.api2.response.result.complemento, 
          "bairro"        : $var.api2.response.result.bairro, 
          "referencia"    : $var.api2.response.result.referencia, 
          "padrao"        : $var.api2.response.result.padrao, 
          "cep" :
              { 
                  "cep_id" : $var.api1.response.result.id, 
                  "uf"     : $var.api1.response.result.uf, 
                  "cidade" : $var.api1.response.result.cidade 
              } 
      }
      ```
  }

  guid = "GEU7j9NGwqBInfAeVmZ7KS61NUo"
}