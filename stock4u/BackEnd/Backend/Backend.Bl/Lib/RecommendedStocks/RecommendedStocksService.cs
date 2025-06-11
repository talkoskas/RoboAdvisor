using Backend.Common.Interfaces.InvestingAdvisor;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Backend.Bl.Lib.RecommendedStocks;

public class RecommendedStocksService(
    IRecommendedStocksRetriver recommendedStocksRetriver,
    IStockRiskClassifier stockRiskClassifier,
    IRecommendedStocksUpdater recommendedStocksUpdater,
    ILogger<RecommendedStocksService> logger) : IHostedService
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
                logger.LogError(exception, "Failed making order commands");
                throw;
            }
        });
        return Task.CompletedTask;
    }

    private async Task BackgroundProcessing(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            foreach (var recommendedStock in await recommendedStocksRetriver.GetAllRecommendedStocksAsync())
            {
                var risklevel = await stockRiskClassifier.GetStockRiskLevelAsync(recommendedStock.Symbol);
                await recommendedStocksUpdater.AddRecommendedStockAsync(recommendedStock.Symbol,risklevel);
            }
            logger.LogInformation("Successfully risk level assign to symbol");

            await Task.Delay(
                TimeSpan.FromHours(1), cancellationToken);
        }
    }

    public async Task StopAsync(CancellationToken cancellationToken)
    {
        await _cancellationTokenSource.CancelAsync();
        await Task.WhenAny(_backgroundTask, Task.Delay(Timeout.Infinite, cancellationToken));
    }
}