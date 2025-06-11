using Backend.Common.Interfaces.Achievements;
using Backend.Common.Models.Achievements;
using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using Microsoft.Extensions.Logging;
using MongoDB.Driver;
using MongoDB.Driver.Linq;

namespace Backend.Dal.Lib;

public class AchievementsRetriever(
    IMongoHandler mongoHandler,
    MongoConfiguration mongoConfiguration,
    ILogger<PositionsRetriever> logger) : IAchievementsRetriever
{
    private readonly IMongoCollection<Achievement> _achievementsCollection =
        mongoHandler.GetCollection<Achievement>(mongoConfiguration.AchievementsCollectionName);

    private readonly IMongoCollection<UserToAchievement> _userToAchievementsCollection =
        mongoHandler.GetCollection<UserToAchievement>(mongoConfiguration.UserToAchievementCollectionName);

    public async Task<List<Achievement>> GetAllAchievementsAsync()
    {
        List<Achievement> achievements;
        try
        {
            achievements = await _achievementsCollection.AsQueryable().ToListAsync();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting achievements");
            throw;
        }

        return achievements;
    }

    public async Task<List<UserToAchievement>> GetUserAchievementsAsync(string userId)
    {
        List<UserToAchievement> achievements;
        try
        {
            achievements = await _userToAchievementsCollection.AsQueryable()
                .Where(userToAchievement => userToAchievement.UserId == userId).ToListAsync();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting achievements for user {userId}", userId);
            throw;
        }

        return achievements;
    }

    public async Task<List<Achievement>> GetAchievementsByTypesAsync(List<AchievementType> achievementTypes)
    {
        List<Achievement> achievements;
        try
        {
            achievements = await _achievementsCollection.AsQueryable()
                .Where(achievement => achievementTypes.Contains(achievement.Type)).ToListAsync();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting achievements");
            throw;
        }

        return achievements;
    }
}