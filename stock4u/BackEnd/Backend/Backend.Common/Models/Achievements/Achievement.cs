using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace Backend.Common.Models.Achievements;

[BsonIgnoreExtraElements]
public class Achievement
{
    [BsonRepresentation(BsonType.String)]
    public AchievementType Type { get; set; }
    
    public string Description { get; set; } = null!;
    
    public int PointsNumber { get; set; }
}