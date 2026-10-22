// Power Query M. Optional second query named LaevadeKontroll.
// PREREQUISITES:
//   1. Create query SanktsiooniVasted from examples/SanktsiooniVasted.pq.
//   2. Make the private vessel register an Excel Table named Laevad with text column IMO.
//   3. Keep the original vessel master/premium formulas in Excel/SharePoint, NOT in GitHub.
// DO NOT use a previous cached result as a current screening if Refresh All fails.
let
    Source = Excel.CurrentWorkbook(){[Name="Laevad"]}[Content],
    Clean = Table.TransformColumns(Source, {{"IMO", each
        let
            Raw = if _ = null then "" else Text.Trim(Text.From(_)),
            Cleaned = if Text.StartsWith(Text.Upper(Raw), "IMO")
                      then Text.Trim(Text.Range(Raw, 3)) else Raw
        in
            Cleaned, type text}}),
    Weight = {7, 6, 5, 4, 3, 2},
    IsValidIMO = (imo as text) as logical =>
        let
            Digits = Text.Length(imo) = 7 and Text.Remove(imo, {"0".."9"}) = "",
            Check = if not Digits then false
                    else Number.Mod(
                        List.Sum(List.Transform({0..5},
                            (i) => Number.FromText(Text.Middle(imo, i, 1)) * Weight{i})),
                        10
                    ) = Number.FromText(Text.End(imo, 1))
        in
            Check,
    // This reference evaluates the freshness checks in SanktsiooniVasted.
    Matches = SanktsiooniVasted,
    Grouped = Table.Group(Matches, {"IMO"}, {
        {"SanctionSources", each Text.Combine(List.Sort(List.Distinct([Allikas])), ", "), type text},
        {"SanctionEntries", each Table.RowCount(_), Int64.Type}
    }),
    Joined = Table.NestedJoin(Clean, {"IMO"}, Grouped, {"IMO"}, "Sanctions", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Joined, "Sanctions",
        {"SanctionSources", "SanctionEntries"}, {"SanctionSources", "SanctionEntries"}),
    Status = Table.AddColumn(Expanded, "SanctionScreening", each
        if not IsValidIMO([IMO]) then "KONTROLLIMATA – vigane IMO"
        else if [SanctionEntries] <> null then "VASTE LEITUD"
        else "VASTET EI LEITUD KONTROLLITUD NIMEKIRJADEST",
        type text),
    GeneratedAt = Matches{0}[AndmedSeisugaUTC],
    Stamped = Table.AddColumn(Status, "SanctionsDataAtUTC", each GeneratedAt, type text)
in
    Stamped
