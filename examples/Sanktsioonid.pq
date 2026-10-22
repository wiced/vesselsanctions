// Insure Consult public sanctions import; Power Query name: Sanktsioonid.
// Public source data only. Customer vessel register remains inside private Excel.
let
    Base = "https://wiced.github.io",
    Status = Json.Document(Web.Contents(Base, [RelativePath = "vesselsanctions/data/status.json"])),
    Raw = Json.Document(Web.Contents(Base, [RelativePath = "vesselsanctions/data/vessels.json"])),
    Required = {"EU", "OFAC", "UK"},
    Timestamp = DateTimeZone.FromText(Status[generated_at]),
    AgeDays = Duration.TotalDays(DateTimeZone.UtcNow() - Timestamp),
    AllSources = List.AllTrue(List.Transform(Required, (id) =>
        Record.HasFields(Status[sources], id) and Record.HasFields(Raw[sources], id)
        and Record.Field(Status[sources], id)[record_count] >= 10
        and Record.Field(Raw[sources], id)[record_count] >= 10
    )),
    Verified = Status[ready] = true and Status[schema_version] = 1
        and Raw[schema_version] = 1
        and Status[generated_at] = Raw[generated_at]
        and Status[total_imo_count] = Record.FieldCount(Raw[vessels])
        and Status[total_imo_count] > 0 and AgeDays >= -0.042
        and AgeDays <= Status[stale_after_days] and AllSources,
    Data = if not Verified then
        error Error.Record("SANCTIONS_DATA_INVALID",
            "Sanktsioonide andmed on aegunud või puudulikud. Ära käsitle kontrolli negatiivse tulemusena.", Status)
        else Raw[vessels],
    Rows = List.Transform(Record.FieldNames(Data), (imo) =>
        let
            Ship = Record.Field(Data, imo),
            Sources = List.Transform(Ship[matches], (x) => Text.From(x[source])),
            Labels = List.Select(Required, each List.Contains(Sources, _))
        in
            [IMO = Text.From(imo),
             EU = if List.Contains(Sources, "EU") then 1 else 0,
             OFAC = if List.Contains(Sources, "OFAC") then 1 else 0,
             UK = if List.Contains(Sources, "UK") then 1 else 0,
             Allikad = Text.Combine(Labels, ", "),
             AndmedSeisugaUTC = Text.From(Raw[generated_at])]
    ),
    Result = Table.FromRecords(Rows, type table [
        IMO = text, EU = Int64.Type, OFAC = Int64.Type, UK = Int64.Type,
        Allikad = text, AndmedSeisugaUTC = text])
in
    Result
