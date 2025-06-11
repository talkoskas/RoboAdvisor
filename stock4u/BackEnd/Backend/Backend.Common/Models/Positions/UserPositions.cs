using Backend.Common.Models.InvestingAdvisor;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace Backend.Common.Models.Positions;

[BsonIgnoreExtraElements]
public class UserPositions
{
    public string UserId { get; set; } = null!;
    
    [BsonRepresentation(BsonType.Decimal128)]
    public decimal AccountBalance { get; set; }
    
    [BsonRepresentation(BsonType.String)]
    public RiskLevel RiskLevel { get; set; }
    
    public List<Position> Positions { get; set; } = null!;
}