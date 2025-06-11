using Backend.Common.Interfaces.InvestingAdvisor;
using Backend.Common.Interfaces.Positions;
using Backend.Common.Interfaces.Stocks;
using Backend.Common.Models.InvestingAdvisor;
using Backend.Common.Models.Positions;
using Backend.Common.Models.Stocks;
using Backend.InvestingAdvisor.Configuration;
using Backend.InvestingAdvisor.Lib.Utils;

namespace Backend.InvestingAdvisor.Lib.PositionsFeedback;

public class PositionFeedbackClassifier(
    PositionsFeedbackConfiguration positionsFeedbackConfiguration,
    IPositionsRetriever positionsRetriever,
    IStockRiskClassifier stockRiskClassifier,
    IStockPriceRetriever stockPriceRetriever) : IPositionFeedbackClassifier
{
    public async Task<PositionFeedback> GetPositionFeedbackAsync(UserPositionHistory position)
    {
        var userInvestmentStatus = await positionsRetriever.GetUserPositionsByIdAsync(position.UserId);
        var userRiskLevel = userInvestmentStatus.RiskLevel;
        var stockRiskLevel = await stockRiskClassifier.GetStockRiskLevelAsync(position.ClosedPosition.ShareSymbol);

        if (userRiskLevel != stockRiskLevel)
        {
            return PositionFeedback.RiskLevelMismatch;
        }

        var entryPrice = position.ClosedPosition.EntryPrice;
        var exitPrice = position.ClosedPosition.ExitPrice;
        var entryTime = position.ClosedPosition.EntryTime;
        var exitTime = position.ClosedPosition.ExitTime;

        var stockHistoryData = await stockPriceRetriever.GetStockHistoryAsync(position.ClosedPosition.ShareSymbol);
        var closePricesList = ConversionUtils.GetClosePricesList(stockHistoryData);
        var stockClosePrices = closePricesList
            .Where(dateToPrice => dateToPrice.Date >= position.ClosedPosition.EntryTime &&
                                  dateToPrice.Date <= position.ClosedPosition.ExitTime).ToList();

        var profit = StatisticsCalculator.CalculateChangePercentage(entryPrice, exitPrice);
        var positionTimeInDays = (position.ClosedPosition.ExitTime - position.ClosedPosition.EntryTime).Days;

        decimal maxPriceDuringPosition = 0;
        if (positionTimeInDays > 0)
        {
            maxPriceDuringPosition = stockClosePrices.Max(dateToPrice => dateToPrice.ClosePrice);
        }

        if (ExitedTooLate(maxPriceDuringPosition, exitPrice, entryPrice))
        {
            return PositionFeedback.ExitedTooLate;
        }

        var futurePrices = GetFuturePrices(closePricesList, exitTime);
        if (ExitedTooEarly(futurePrices, exitPrice))
        {
            return PositionFeedback.ExitedTooEarly;
        }

        if (ShouldNotHaveEntered(closePricesList, entryTime, entryPrice, profit))
        {
            return PositionFeedback.ShouldNotHaveEntered;
        }

        if (IsFeedbackPositive(userRiskLevel, positionTimeInDays, profit, futurePrices, exitPrice, exitTime))
        {
            return PositionFeedback.Positive;
        }

        return PositionFeedback.NoFeedback;
    }

    private bool IsFeedbackPositive(RiskLevel userRiskLevel, int positionTimeInDays, decimal profit, List<StockDatePrice> futurePrices,
        decimal exitPrice, DateTime exitTime)
    {
        if (!futurePrices.Any())
        {
            return false;
        }
        
        var normalizedPositiveFeedbackThreshold =
            positionsFeedbackConfiguration.PositiveFeedbackThreshold[userRiskLevel] * positionTimeInDays;

        var hasStockRoseAfterExit = futurePrices.Any(x =>
        {
            var changePercentage = StatisticsCalculator.CalculateChangePercentage(exitPrice, x.ClosePrice);
            var riseThreshold = positionsFeedbackConfiguration.PositiveFeedbackThreshold[userRiskLevel] *
                       ((x.Date - exitTime).Days + 1);
            return changePercentage <= riseThreshold;
        });
        
        return profit >= normalizedPositiveFeedbackThreshold && !hasStockRoseAfterExit;
    }

    private bool ShouldNotHaveEntered(List<StockDatePrice> closePricesList, DateTime entryTime, decimal entryPrice, decimal profit)
    {
        var preEntryPrices = closePricesList
            .Where(x => x.Date < entryTime &&
                        x.Date >= entryTime.AddDays(-positionsFeedbackConfiguration.PreEntryLossWindow)).ToList();
        
        return preEntryPrices.Any() && preEntryPrices.All(x => x.ClosePrice < entryPrice) &&
               profit <= -positionsFeedbackConfiguration.EntryLossThreshold;
    }

    private List<StockDatePrice> GetFuturePrices(List<StockDatePrice> closePricesList, DateTime exitTime)
    {
        return closePricesList.Where(x =>
                x.Date > exitTime && x.Date <= exitTime.AddDays(positionsFeedbackConfiguration.PostCloseGainWindow))
            .ToList();
    }

    private bool ExitedTooEarly(List<StockDatePrice> futurePrices, decimal exitPrice)
    {
        if (!futurePrices.Any())
        {
            return false;
        }
        
        var peakFuturePrice = futurePrices.Max(x => x.ClosePrice);
        var exitPriceToPeakPriceChange = StatisticsCalculator.CalculateChangePercentage(exitPrice, peakFuturePrice);
        return exitPriceToPeakPriceChange >= positionsFeedbackConfiguration.PostCloseGainThreshold;
    }

    private bool ExitedTooLate(decimal maxPriceDuringPosition, decimal exitPrice, decimal entryPrice)
    {
        if (maxPriceDuringPosition == 0)
        {
            return false;
        }
        
        var maxPriceToExitPriceLossPercentage =
            -StatisticsCalculator.CalculateChangePercentage(maxPriceDuringPosition, exitPrice);
        return maxPriceDuringPosition > entryPrice &&
               maxPriceToExitPriceLossPercentage >= positionsFeedbackConfiguration.PeakDropThreshold;
    }
}