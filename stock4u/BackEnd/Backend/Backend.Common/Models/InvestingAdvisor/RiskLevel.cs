using System.Text.Json.Serialization;

namespace Backend.Common.Models.InvestingAdvisor;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum RiskLevel
{
    Low,
    Medium,
    High
}