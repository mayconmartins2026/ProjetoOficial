// Query all OE records
query oe verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query OE {
      return = {type: "list"}
    } as $oe
  }

  response = $oe
  guid = "am39MNUKEYbnaxNRArQxy0k5O9Q"
}