using Backend.Common.Models.Achievements;

namespace Backend.Common.Interfaces.Achievements;

public interface IAchievementsUpdater
{
    Task AddAchievementAsync(string userId, AchievementType achievementType);
}