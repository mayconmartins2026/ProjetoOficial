query papeis verb=GET {
  api_group = "APIsGestao"

  input {
  }

  stack {
    db.query PAPEL {
      return = {type: "list"}
    } as $PAPEL1
  }

  response = $PAPEL1
  guid = "NVBJxylf62w-5P5uPsZ_Qbtx05c"
}