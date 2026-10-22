// Query name: LaevadeKontroll. Requires the Sanktsioonid query.
// Reads existing private Excel Table: Vessel_List, column: Vessel IMO No.
// Load results to a NEW sheet, never over the source Vessel_List.
let
    Source = try Excel.CurrentWorkbook(){[Name="Vessel_List"]}[Content]
        otherwise error Error.Record("VESSEL_LIST_TABLE_NOT_FOUND",
            "Selles töövihikus puudub Exceli tabel Vessel_List. Märgista Vessel List andmed, vali Ctrl+T, kinnita päised ja määra Table Design menüüs tabeli nimeks Vessel_List.", null),
    // Works with both the original workbook and the smaller exported snapshot.
    RemoveOld = Table.RemoveColumns(Source,
        List.Intersect({Table.ColumnNames(Source), {"EU Sanctions", "OFAC SDN", "UK Sanctions", "IMO kontroll", "Koondtulemus", "AndmedSeisugaUTC"}})),
    Key = Table.AddColumn(RemoveOld, "IMO_key", each
        let v = [Vessel IMO No], s = if v = null then "" else Text.Trim(Text.From(v))
        in if Text.StartsWith(Text.Upper(s), "IMO") then Text.Trim(Text.Range(s, 3)) else s, type text),
    ValidIMO = (s as text) as logical =>
        let
            Digits = Text.Length(s) = 7 and Text.Remove(s, {"0".."9"}) = "",
            Weights = {7,6,5,4,3,2},
            Check = if not Digits then false else Number.Mod(
                List.Sum(List.Transform({0..5}, (i) =>
                    Number.FromText(Text.Middle(s, i, 1))*Weights{i})), 10)
                = Number.FromText(Text.End(s, 1))
        in Check,
    Validated = Table.AddColumn(Key, "IMO kontroll", each
        if ValidIMO([IMO_key]) then "OK" else "VIGANE IMO", type text),
    FreshData = Sanktsioonid,
    DataTimestamp = FreshData{0}[AndmedSeisugaUTC],
    Joined = Table.NestedJoin(Validated, {"IMO_key"}, FreshData, {"IMO"}, "Matches", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Joined, "Matches", {"EU","OFAC","UK"},
        {"EU_vaste","OFAC_vaste","UK_vaste"}),
    EUResult = Table.AddColumn(Expanded, "EU Sanctions", each
        if [IMO kontroll]<>"OK" then "KONTROLLIMATA"
        else if [EU_vaste]=1 then "VASTE LEITUD" else "VASTET EI LEITUD", type text),
    OFACResult = Table.AddColumn(EUResult, "OFAC SDN", each
        if [IMO kontroll]<>"OK" then "KONTROLLIMATA"
        else if [OFAC_vaste]=1 then "VASTE LEITUD" else "VASTET EI LEITUD", type text),
    UKResult = Table.AddColumn(OFACResult, "UK Sanctions", each
        if [IMO kontroll]<>"OK" then "KONTROLLIMATA"
        else if [UK_vaste]=1 then "VASTE LEITUD" else "VASTET EI LEITUD", type text),
    Summary = Table.AddColumn(UKResult, "Koondtulemus", each
        if [IMO kontroll]<>"OK" then "KONTROLLIMATA – VIGANE IMO"
        else if List.Contains({[EU_vaste],[OFAC_vaste],[UK_vaste]},1) then "VASTE LEITUD"
        else "VASTET EI LEITUD KONTROLLITUD LOENDITEST", type text),
    Dated = Table.AddColumn(Summary, "AndmedSeisugaUTC", each DataTimestamp, type text),
    Clean = Table.RemoveColumns(Dated, {"IMO_key","EU_vaste","OFAC_vaste","UK_vaste"})
in
    Clean
