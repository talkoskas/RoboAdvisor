using Backend.Common.Interfaces.InvestingAdvisor;
using Backend.Common.Interfaces.Positions;
using Backend.InvestingAdvisor.Configuration;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Backend.InvestingAdvisor.Lib.PositionsFeedback
{
    public class ClassifyPositionsService(
        PositionsFeedbackConfiguration positionsFeedbackConfiguration,
        IPositionsRetriever positionsRetriever,
        IPositionFeedbackClassifier positionFeedbackClassifier,
        IPositionsUpdater positionsUpdater,
        ILogger<ClassifyPositionsService> logger)
        : IHostedService
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
                    logger.LogError(exception, "Failed classifying positions");
                    throw;
                }
            });
            return Task.CompletedTask;
        }

        private async Task BackgroundProcessing(CancellationToken cancellationToken)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                var positionsToClassify = await positionsRetriever.GetNonFeedbackedClosedPositions();
                foreach (var positionToClassify in positionsToClassify)
                {
                    var positionFeedback = await positionFeedbackClassifier.GetPositionFeedbackAsync(positionToClassify);
                    await positionsUpdater.SetPositionFeedbackAsync(positionToClassify, positionFeedback);
                }

                logger.LogInformation("Successfully updated positions feedback");

                await Task.Delay(TimeSpan.FromMinutes(positionsFeedbackConfiguration.FeedbackCalculationIntervalInMinutes),
                    cancellationToken);
            }
        }

        public async Task StopAsync(CancellationToken cancellationToken)
        {
            await _cancellationTokenSource.CancelAsync();
            await Task.WhenAny(_backgroundTask, Task.Delay(Timeout.Infinite, cancellationToken));
        }
    }
}
