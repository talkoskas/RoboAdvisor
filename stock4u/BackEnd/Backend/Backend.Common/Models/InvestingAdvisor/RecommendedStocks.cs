using System.Text.Json.Serialization;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace Backend.Common.Models.InvestingAdvisor;

[BsonIgnoreExtraElements]
public class RecommendedStocks
{
    [BsonRepresentation(BsonType.String)]
    public RiskLevel RiskLevel { get; set; }

    public string Symbol { get; set; } = null!;
}