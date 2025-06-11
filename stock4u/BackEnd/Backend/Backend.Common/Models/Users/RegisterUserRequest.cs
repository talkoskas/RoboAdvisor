using Backend.Common.Models.InvestingAdvisor;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace Backend.Common.Models.Users;

public class RegisterUserRequest
{
    public string Email { get; set; } = null!;

    public string UserId { get; set; } = null!;
    
    public string Password { get; set; } = null!;

    public string FirstName { get; set; } = null!;

    public string LastName { get; set; } = null!;

    [BsonRepresentation(BsonType.String)]
    public RiskLevel RiskLevel { get; set; }
}
