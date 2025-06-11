using Backend.Common.Interfaces.Achievements;
using Backend.Common.Models.Achievements;
using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using Microsoft.Extensions.Logging;
using MongoDB.Driver;

namespace Backend.Dal.Lib;

public class AchievementsUpdater(
    IMongoHandler mongoHandler,
    MongoConfiguration mongoConfiguration,
    ILogger<PositionsRetriever> logger) : IAchievementsUpdater
{
    private readonly IMongoCollection<UserToAchievement> _userToAchievementsCollection =
        mongoHandler.GetCollection<UserToAchievement>(mongoConfiguration.UserToAchievementCollectionName);
    
    public async Task AddAchievementAsync(string userId, AchievementType achievementType)
    {
        var userToAchievement = new UserToAchievement
        {
            UserId = userId,
            AchievementType = achievementType,
            AchievedTime = DateTime.Now
        };

        try
        {
            await _userToAchievementsCollection.InsertOneAsync(userToAchievement);
        }
        catch (Exception exception)
        {
            logger.LogError("Error inserting user to achievement {userId} {achievementType}", userId, achievementType);
            throw;
        }
    }
}