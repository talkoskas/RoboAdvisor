using Backend.Common.Models.Achievements;

namespace Backend.Bl.Interfaces;

public interface IUserToAchievementConnector
{
    Task<List<AchievementType>> GetUserNewAchievementsAsync(string userId, List<AchievementType> currentAchievements);
}