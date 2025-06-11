using Backend.Bl.Configuration;
using Backend.Bl.Interfaces;
using Backend.Common.Interfaces.Achievements;
using Backend.Common.Interfaces.Positions;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Backend.Bl.Lib.Achievements;

public class UserToAchievementService(
    UserToAchievementConfiguration userToAchievementConfiguration,
    IPositionsRetriever positionsRetriever,
    IAchievementsRetriever achievementsRetriever,
    IUserToAchievementConnector userToAchievementConnector,
    IAchievementsUpdater achievementsUpdater,
    ILogger<UserToAchievementService> logger) : IHostedService
{
    private Task _backgroundTask = null!;
    private CancellationTokenSource _cancellationTokenSource = null!;

    public Task StartAsync(CancellationToken cancellationToken)
    {
        _cancellationTokenSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        _backgroundTask = Task.Run(async () =>
        {
            try
            {
                await BackgroundProcessing(_cancellationTokenSource.Token);
            }
            catch (Exception exception)
            {
                logger.LogError(exception, "Failed updating user achievements");
                throw;
            }
        });
        return Task.CompletedTask;
    }

    private async Task BackgroundProcessing(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            var allUsersPositions = await positionsRetriever.GetAllUserPositionsAsync();
            foreach (var userPositions in allUsersPositions)
            {
                var currentUserAchievements =
                    await achievementsRetriever.GetUserAchievementsAsync(userPositions.UserId);
                var achievementTypes =
                    currentUserAchievements.Select(achievement => achievement.AchievementType).ToList();
                var newUserAchievements =
                    await userToAchievementConnector.GetUserNewAchievementsAsync(userPositions.UserId,
                        achievementTypes);
                newUserAchievements.ForEach(async achievement =>
                    await achievementsUpdater.AddAchievementAsync(userPositions.UserId, achievement));

                logger.LogInformation("Successfully updated users achievements");

                await Task.Delay(
                    TimeSpan.FromMinutes(userToAchievementConfiguration.UserToAchievementCalculationTimeInMinutes),
                    cancellationToken);
            }
        }
    }

    public async Task StopAsync(CancellationToken cancellationToken)
    {
        await _cancellationTokenSource.CancelAsync();
        await Task.WhenAny(_backgroundTask, Task.Delay(Timeout.Infinite, cancellationToken));
    }
}