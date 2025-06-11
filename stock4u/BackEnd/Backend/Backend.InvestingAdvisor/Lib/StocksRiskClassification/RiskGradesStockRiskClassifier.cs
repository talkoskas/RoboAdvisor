using Backend.Common.Interfaces.Stocks;
using Backend.Common.Models.InvestingAdvisor;
using Backend.InvestingAdvisor.Interfaces;

namespace Backend.InvestingAdvisor.Lib.StocksRiskClassification;

public class RiskGradesStockRiskClassifier(IStockPriceRetriever stockPriceRetriever) : IRiskGradesStockRiskClassifier
{
    public async Task<RiskLevel> GetStockRiskGradesRiskLevelAsync(string symbol)
    {
        var standardDeviation = await stockPriceRetriever.GetStockStandardDeviationAsync(symbol);
        var stockRiskGrades = (standardDeviation / 12) * 5 * 100 * 100;
        return stockRiskGrades switch
        {
            < 100 => RiskLevel.Low,
            < 300 => RiskLevel.Medium,
            _ => RiskLevel.High
        };
    }
}