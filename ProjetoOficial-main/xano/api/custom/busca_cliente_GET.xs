query buscaCliente verb=GET {
  api_group = "Custom"

  input {
    text authtoken? filters=trim
  }

  stack {
    api.request {
      url = "https://x8ki-letl-twmt.n7.xano.io/api:ZnpRG7wg/auth/me"
      method = "GET"
      params = $input.authtoken
      headers = [
        "Authorization: Bearer " ~ $input.authtoken
        "Content-Type: application/json"
      ]
    
    } as $api1
  
    conditional {
      if ($api1.response.status == 200) {
        db.get CLIENTE {
          field_name = "id"
          field_value = `$var.api1.response.result.id`
        } as $CLIENTE1
      }
    
      else {
        var $CLIENTE1 {
          value = {}
        }
      }
    }
  }

  response = $CLIENTE1
  tags = ["modulo 01"]
  guid = "vZbcQqXncVTBIGQSxkoThIQ_1Q0"
}