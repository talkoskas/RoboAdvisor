using System.Text.Json.Serialization;

namespace Backend.Common.Models.Positions;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum PositionType
{
    Long,
    Short
}