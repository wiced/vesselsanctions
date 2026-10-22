// Power Query M. Create a blank Excel query named SanktsiooniVasted and paste in Advanced Editor.
// Public data only; do not upload Insure Consult's private workbook or vessel register to GitHub.
// This query intentionally FAILS instead of claiming no match when sources are stale/incomplete.
let
    Base = "https://wiced.github.io",
    Status = Json.Document(Web.Contents(Base, [RelativePath = "vesselsanctions/data/status.json"])),
    Data = Json.Document(Web.Contents(Base, [RelativePath = "vesselsanctions/data/vessels.json"])),
    Sources = {"EU", "OFAC", "UK"},
    AgeDays = Duration.TotalDays(DateTimeZone.UtcNow() - DateTimeZone.FromText(Status[generated_at])),
    SourceComplete = List.AllTrue(List.Transform(
        Sources,
        (key) => Record.HasFields(Status[sources], key)
            and Record.HasFields(Data[sources], key)
            and Record.Field(Status[sources], key)[record_count] > 0
            and Record.Field(Data[sources], key)[record_count] > 0
    )),
    Valid = Status[ready] = true
        and Status[schema_version] = 1
        and Data[schema_version] = 1
        and Status[generated_at] = Data[generated_at]
        and AgeDays <= Status[stale_after_days]
        and AgeDays >= -0.042
        and SourceComplete
        and Status[total_imo_count] > 0
        and Record.FieldCount(Data[vessels]) = Status[total_imo_count],
    Rows = if not Valid then
        error Error.Record(
            "SANCTIONS_DATA_INVALID",
            "Sanktsioonide andmed on aegunud, poolikud või eri versioonidest. Ära kasuta vanu/puuduvaid vasteid kontrolli tulemusena.",
            Status
        )
    else
        List.Combine(List.Transform(
            Record.FieldNames(Data[vessels]),
            (imo) =>
                let
                    Vessel = Record.Field(Data[vessels], imo),
                    Matches = Vessel[matches]
                in
                    List.Transform(Matches, (m) => [
                        IMO = Text.From(imo),
                        Laev = Text.From(Record.FieldOrDefault(m, "name", Vessel[name])),
                        Allikas = Text.From(m[source]),
                        Programm = Text.From(Record.FieldOrDefault(m, "program", "")),
                        Viide = Text.From(Record.FieldOrDefault(m, "reference", "")),
                        NimekirjaKuupaev = Text.From(Record.FieldOrDefault(m, "listed_date", "")),
                        AndmedSeisugaUTC = Text.From(Data[generated_at])
                    ])
        )),
    Output = Table.FromRecords(
        Rows,
        type table [
            IMO = text, Laev = text, Allikas = text,
            Programm = text, Viide = text, NimekirjaKuupaev = text,
            AndmedSeisugaUTC = text
        ]
    )
in
    Output
