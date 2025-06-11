using Backend.Common.Models.Achievements;

namespace Backend.Common.Interfaces.Achievements;

public interface IAchievementsRetriever
{
    Task<List<Achievement>> GetAllAchievementsAsync();

    Task<List<UserToAchievement>> GetUserAchievementsAsync(string userId);

    Task<List<Achievement>> GetAchievementsByTypesAsync(List<AchievementType> achievementTypes);
}