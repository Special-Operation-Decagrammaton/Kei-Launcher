using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace KeiLauncher.Models;

[JsonConverter(typeof(BranchConverter))]
enum Branch
{
    None,
    EnOri,
    EnExt,
    PtBr
}

class BranchConverter : JsonConverter<Branch>
{
    public override Branch Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) =>
        reader.TokenType == JsonTokenType.String
            ? BranchExtensions.FromValue(reader.GetString() ?? "")
            : Branch.None;

    public override void Write(Utf8JsonWriter writer, Branch value, JsonSerializerOptions options) =>
        writer.WriteStringValue(value.ToValue());
}

static class BranchExtensions
{
    public static string ToValue(this Branch branch) => branch switch
    {
        Branch.EnOri => "en-ori",
        Branch.EnExt => "en-ext",
        Branch.PtBr => "pt-br",
        _ => "none"
    };

    public static Branch FromValue(string? value) => value?.Trim().ToLowerInvariant() switch
    {
        "en-ori" or "enori" => Branch.EnOri,
        "en-ext" or "enext" => Branch.EnExt,
        "pt-br" or "ptbr" => Branch.PtBr,
        _ => Branch.None
    };

    public static string[] AllDisplayValues() => ["none", "en-ori", "en-ext", "pt-br"];
}
