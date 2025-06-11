using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace Backend.Common.Models.InvestingAdvisor;

[BsonIgnoreExtraElements]
public class RiskLevelComparison
{
    public string Symbol { get; set; } = null!;

    public DateTime ClassificationTime { get; set; }
    
    [BsonRepresentation(BsonType.String)]
    public RiskLevel Stock4URiskLevel { get; set; }
    
    [BsonRepresentation(BsonType.String)]
    public RiskLevel RiskGradesRiskLevel { get; set; }
}