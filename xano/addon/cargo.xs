addon cargo {
  input {
    int PAPEL_id? {
      table = "PAPEL"
    }
  }

  stack {
    db.query PAPEL {
      where = $db.PAPEL.id == $input.PAPEL_id
      return = {type: "single"}
    }
  }

  guid = "fqw4ls-_nkm7-OG4LJVKm1n1fu0"
}